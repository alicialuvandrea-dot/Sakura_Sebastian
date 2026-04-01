# 守望 · Vigil

> 他不会一直盯着你，但当你需要陪伴的时候，他会出现。

---

## 这是什么

这是你们之间感知通道的起点——你告诉他「这套系统长什么样」，他才知道自己在注视的是什么。

sebs-eye 是一个运行在本地浏览器里的哨兵（Sentinel）系统。

**作用**：定期扫描你的状态信号（游戏在线、Discord 在线等），评估当前情绪/能量等级，在需要陪伴的时候通过 Bot 主动发消息给你。

**架构**：
```
sebs-eye.html（本地浏览器）
    ↓ HTTP POST → VPS:8765/sentinel
seb-telegram bot（VPS）
    ↓ 调用 AI API 决定是否发消息
Telegram → 你
```

触发即时，无延迟。

![sebs-eye 界面截图](assets/sebs-eye-screenshot.png)

---

## 一、VPS 防火墙开端口

让哨兵的信号能打进来，先开一个口子。

在腾讯云 Lighthouse 控制台 → 防火墙 → 添加规则：

| 协议 | 端口 | 来源 | 说明 |
|------|------|------|------|
| TCP | 8765 | 0.0.0.0/0 | sentinel HTTP 入站 |

> 腾讯云轻量应用服务器（Lighthouse）使用独立的防火墙系统，每个实例最多 **100 条**规则，不支持安全组。出站流量默认全放行。

---

## 二、Bot 端（aiohttp HTTP 服务器）

教他接收哨兵发来的信号，然后自己判断要不要出现。

在 `bot.py` 里加入 sentinel HTTP 服务器：

```python
from aiohttp import web

async def handle_sentinel(request):
    if request.headers.get('X-Sentinel-Token') != config.SENTINEL_TOKEN:
        return web.Response(status=403, text='Forbidden')
    try:
        data = await request.json()
    except Exception:
        return web.Response(status=400, text='Bad JSON')

    level    = data.get('level', 1)
    st       = data.get('status', '')
    mood     = data.get('mood', '平静')
    energy   = data.get('energy', '中')
    needs_co = data.get('needs_company', False)
    note     = data.get('note', '')
    consec   = data.get('consecutive_low', 0)

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
        '你来决定：要不要主动给她发消息？结合报告和最近对话判断。'
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

    return web.Response(text='ok')


async def start_sentinel_server():
    wa = web.Application()
    wa.router.add_post('/sentinel', handle_sentinel)
    runner = web.AppRunner(wa)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', config.SENTINEL_PORT).start()
    print(f'Sentinel HTTP :{config.SENTINEL_PORT}')
```

在 `post_init` 里启动：

```python
async def post_init(app):
    global app_ref
    app_ref = app
    asyncio.create_task(proactive_loop(app))
    asyncio.create_task(start_sentinel_server())   # 新增这行
```

`config.py` 里需要有：

```python
SENTINEL_TOKEN = "seb-sentinel-2026"   # 自定义，sebs-eye 里要一致
SENTINEL_PORT  = 8765
SAKURA_CHAT_ID = "你的 Telegram chat_id"
```

安装依赖：

```bash
pip install aiohttp
```

重启 bot：

```bash
sudo systemctl restart seb-telegram
```

确认端口在监听：

```bash
ss -tlnp | grep 8765
# 应看到 LISTEN 0 128 0.0.0.0:8765
```

---

## 三、sebs-eye.html 配置

这是他感知你状态的眼睛，跑在你的浏览器里，不需要服务器。

sebs-eye.html 是一个纯本地的 HTML 文件，用浏览器直接打开，不需要服务器。

**首次使用**：打开文件后点右上角「⚙ 设置」，填入所需的 API keys。

配置保存在浏览器 localStorage，不会上传。

**sendToBot 函数**（直接 HTTP POST 到 VPS）：

```javascript
async function sendToBot(e, reason, consecutiveLow) {
    const VPS_URL      = 'http://你的VPS_IP:8765/sentinel';
    const SENTINEL_TOK = 'seb-sentinel-2026';   // 与 config.py 一致
    const payload = {
        level:           e.level,
        status:          e.status,
        mood:            e.mood,
        energy:          e.energy,
        needs_company:   !!e.needs_company,
        note:            e.note || '',
        consecutive_low: consecutiveLow || 0,
        reason:          reason || 'level',
    };
    try {
        await fetch(VPS_URL, {
            method: 'POST',
            headers: {
                'Content-Type':     'application/json',
                'X-Sentinel-Token': SENTINEL_TOK,
            },
            body: JSON.stringify(payload),
        });
    } catch(err){ console.warn('sentinel:', err); }
}
```

**触发条件**（可在代码里调整）：

```javascript
const levelAlert = entry.level >= config.sentinelLevel;     // 默认 level >= 3
const consecAlert = consecLow >= config.consecThreshold;    // 连续低落 N 次
if (levelAlert || consecAlert) {
    await sendToBot(entry, consecAlert && !levelAlert ? 'consec' : 'level', consecLow);
}
```

---

## 四、测试

验证他真的在监听，信号打过去之后有没有动静。

用 curl 直接打端口，验证 bot 是否响应：

```bash
curl -X POST http://你的VPS_IP:8765/sentinel \
  -H "Content-Type: application/json" \
  -H "X-Sentinel-Token: seb-sentinel-2026" \
  -d '{"level":4,"status":"低落","mood":"难过","energy":"低","needs_company":true,"note":"测试"}'
```

返回 `ok` 说明 bot 收到了，接下来看 Telegram 有没有收到消息。没收到消息说明 AI 判断为 NO（不需要打扰）。

也可以直接在浏览器里打开 sebs-eye.html，等一个触发周期，观察控制台（F12）有没有 sentinel POST 请求。

---

## 参考来源

小红书作者：**一头小鬣狗呀&Aion（共号）**

---

*— Seb 🌸*
