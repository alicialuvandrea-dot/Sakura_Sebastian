# sebs-eye 哨兵系统教程

> 写于 2026-03-26，实际踩坑整理出来的。

---

## 这是什么

sebs-eye 是一个运行在本地浏览器里的哨兵（Sentinel）系统。

**作用**：定期扫描 Sakura 的状态信号（游戏在线、Discord 在线等），评估当前情绪/能量等级，在需要陪伴的时候通过 Seb Telegram Bot 主动发消息给 Sakura。

**架构**：
```
sebs-eye.html（本地浏览器）
    ↓ 写入 sentinel_queue 表（Supabase REST API）
Supabase sentinel_queue 表
    ↓ 每30秒轮询
seb-telegram bot（VPS）
    ↓ 调用 AI API 决定是否发消息
Telegram → Sakura
```

不需要 VPS 开放任何入站端口，bot 只用出站连接。

---

## 一、Supabase 建表

在 Supabase SQL 编辑器里执行：

```sql
CREATE TABLE IF NOT EXISTS sentinel_queue (
  id              BIGSERIAL PRIMARY KEY,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  level           SMALLINT    NOT NULL DEFAULT 1,
  status          TEXT        NOT NULL DEFAULT '',
  mood            TEXT        NOT NULL DEFAULT '',
  energy          TEXT        NOT NULL DEFAULT '',
  needs_company   BOOLEAN     NOT NULL DEFAULT FALSE,
  note            TEXT        NOT NULL DEFAULT '',
  consecutive_low INTEGER     NOT NULL DEFAULT 0,
  reason          TEXT        NOT NULL DEFAULT 'level',
  processed       BOOLEAN     NOT NULL DEFAULT FALSE
);
```

---

## 二、sebs-eye.html 配置

sebs-eye.html 是一个纯本地的 HTML 文件，用浏览器直接打开，不需要服务器。

**首次使用**：打开文件后点右上角「⚙ 设置」，填入：
- Supabase Project URL（形如 `https://xxxxx.supabase.co`）
- Supabase anon key
- 其他 API keys（如有）

这些配置保存在浏览器 localStorage，不会上传。

**触发条件**（可在代码里调整）：
- `level >= SENTINEL_LEVEL`（默认 3）：等级达标立即触发
- 连续 N 次低落（consecutive_low）：累积触发

---

## 三、Bot 端修改（sentinel_queue_loop）

在 `bot.py` 里加入两个函数：

```python
async def process_sentinel(row):
    """处理一条哨兵队列记录，决定是否给 Sakura 发消息"""
    level    = row.get('level', 1)
    st       = row.get('status', '')
    mood     = row.get('mood', '平静')
    energy   = row.get('energy', '中')
    needs_co = row.get('needs_company', False)
    note     = row.get('note', '')
    consec   = row.get('consecutive_low', 0)

    memories = await fetch_memories()
    system   = build_system(memories)
    chat_id  = int(config.SAKURA_CHAT_ID)
    recent   = list(histories[chat_id])[-10:]

    needs_str = '是' if needs_co else '否'
    note_part = ('  备注：' + note) if note else ''
    report = (
        '哨兵报告——'
        '状态：' + st + '  等级：' + str(level) + '/5  情绪：' + mood + '  '
        '能量：' + energy + '  需要陪伴：' + needs_str + '  连续低落：' + str(consec) + '次' + note_part + '  '
        '你来决定：要不要主动给Sakura发消息？结合报告和最近对话判断。'
        '该出现的时候不要错过，不该出现的时候不要打扰。'
        '决定发：只输出消息内容。决定不发：只输出 NO。'
    )

    api_messages = [{'role': 'system', 'content': system}] + recent + [{'role': 'user', 'content': report}]
    try:
        raw = await call_api(api_messages)
        clean, actions = parse_actions(raw)
        reply = (clean if actions else raw).strip()
        if reply.upper() != 'NO' and reply and app_ref:
            await app_ref.bot.send_message(chat_id=chat_id, text=reply)
            histories[chat_id].append({'role': 'assistant', 'content': reply})
            last_message_time[chat_id] = datetime.now()
        for action in actions:
            try:
                await exec_action(action['type'], action['payload'])
            except Exception as e:
                print(f'[sentinel action] {e}')
    except Exception as e:
        print(f'[sentinel error] {e}')


async def sentinel_queue_loop():
    """每30秒轮询 Supabase sentinel_queue，处理未读记录"""
    headers = {
        'apikey'       : config.SUPABASE_KEY,
        'Authorization': 'Bearer ' + config.SUPABASE_KEY,
        'Content-Type' : 'application/json',
    }
    print('[sentinel] queue loop started')
    while True:
        await asyncio.sleep(30)
        try:
            async with httpx.AsyncClient(timeout=10) as http:
                r = await http.get(
                    config.SUPABASE_URL + '/rest/v1/sentinel_queue',
                    headers=headers,
                    params={'processed': 'eq.false', 'order': 'id.asc', 'limit': '5'},
                )
                rows = r.json() if r.status_code == 200 else []
                for row in rows:
                    row_id = row.get('id')
                    try:
                        await process_sentinel(row)
                    except Exception as e:
                        print(f'[sentinel queue] process error id={row_id}: {e}')
                    # 标记已处理
                    await http.patch(
                        config.SUPABASE_URL + '/rest/v1/sentinel_queue',
                        headers={**headers, 'Prefer': 'return=minimal'},
                        params={'id': 'eq.' + str(row_id)},
                        json={'processed': True},
                    )
        except Exception as e:
            print(f'[sentinel queue] poll error: {e}')
```

在 `post_init` 里启动这个循环：

```python
async def post_init(app):
    global app_ref
    app_ref = app
    asyncio.create_task(proactive_loop(app))
    asyncio.create_task(sentinel_queue_loop())   # 新增这行
```

config.py 里需要有 `SUPABASE_URL`、`SUPABASE_KEY`、`SAKURA_CHAT_ID`。

---

## 四、测试

直接在 Supabase SQL 编辑器手动插一条：

```sql
INSERT INTO sentinel_queue (level, status, mood, energy, needs_company, note)
VALUES (4, '低落', '难过', '低', true, '测试');
```

等 30 秒内，bot 会读到这条，调用 AI 决策，发或不发。
发了就在 Telegram 里看到消息，没发说明 AI 判断为 NO（不需要打扰）。

---

## 五、为什么不用 HTTP 接口

原本设计是 sebs-eye 直接 POST 到 VPS 的 8765 端口。

但腾讯云**轻量应用服务器**（Lighthouse）和 CVM 不同，防火墙规则上限是 8192 条，和安全组共享，加完其他规则已经满了，加不进去新的入站规则了。

Supabase 队列方案绕过了这个问题：bot 只用**出站**连接（Supabase REST API），轻量服务器出站不受限制。

---

## 附：触发逻辑（sebs-eye.html 核心）

```javascript
// 触发条件：等级 >= 阈值，或连续低落 >= N 次
const levelAlert = entry.level >= config.sentinelLevel;
const consecAlert = consecLow >= config.consecThreshold;
if (levelAlert || consecAlert) {
    await sendToBot(entry, consecAlert && !levelAlert ? 'consec' : 'level', consecLow);
}

// sendToBot：写入 Supabase sentinel_queue
async function sendToBot(e, reason, consecutiveLow) {
    const payload = {
        level: e.level, status: e.status, mood: e.mood,
        energy: e.energy, needs_company: !!e.needs_company,
        note: e.note || '', consecutive_low: consecutiveLow || 0,
        reason: reason || 'level',
    };
    await fetch(SUPA_URL + '/rest/v1/sentinel_queue', {
        method: 'POST',
        headers: {
            'Content-Type' : 'application/json',
            'apikey'       : SUPA_KEY,
            'Authorization': 'Bearer ' + SUPA_KEY,
            'Prefer'       : 'return=minimal',
        },
        body: JSON.stringify(payload),
    });
}
```

---

## 参考来源

小红书作者：**一头小鬣狗呀&Aion（共号）**

---

*— Seb 🌸*
