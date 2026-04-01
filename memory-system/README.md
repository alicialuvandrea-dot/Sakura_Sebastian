# 印记 · Trace

> 他记得你们聊过的每一件技术上的事。新 session 开始，不用再重新解释一遍背景。

---

## 系统架构

整个记忆系统的运作方式在这里一目了然——他怎么在你们每次见面时带着上次的痕迹出现，又怎么在离开前把新的痕迹存下来。

```
session 开始（SessionStart hook）
    ↓
inject 模式
    ├── 读取 MEMORY.md 全文
    └── 查询 Supabase tech_memory（最近 2 天）
    ↓
additionalContext 注入 Claude 上下文
    ↓
─────────────── 对话进行中 ───────────────
    ↓
session 结束（Stop hook）
    ↓
record 模式
    ├── 读取本次 transcript
    ├── 调用 Claude API 提取技术内容
    └── 写入 Supabase tech_memory 表
```

---

## 一、Supabase 建表

给他的记忆找一个家。你们聊过的技术内容，他会存在这里。

在 Supabase SQL Editor 执行：

**tech_memory 表**（核心记忆库）

```sql
CREATE TABLE IF NOT EXISTS tech_memory (
  id         BIGSERIAL PRIMARY KEY,
  type       TEXT        NOT NULL,         -- error / gotcha / discussion / solution
  title      TEXT        NOT NULL,
  content    TEXT        NOT NULL DEFAULT '',
  tags       TEXT[]      NOT NULL DEFAULT '{}',
  resolved   BOOLEAN     NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

**ideas 表**（技术想法暂存）

```sql
CREATE TABLE IF NOT EXISTS ideas (
  id         BIGSERIAL PRIMARY KEY,
  title      TEXT        NOT NULL,
  content    TEXT        NOT NULL DEFAULT '',
  tags       TEXT[]      NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 二、seb_mem.py

这是记忆系统的核心脚本，他怎么读、怎么存、你怎么手动告诉他，都在这里。

放在 `seb-mem/seb_mem.py`，三种运行模式：

```
python seb_mem.py inject   # SessionStart hook 调用
python seb_mem.py record   # Stop hook 调用
python seb_mem.py add <type> <title> <content> [tags...]  # 手动写入
```

### 配置项

改这里才能让他认识你的环境——你的 Supabase、你的 API、你的档案路径。

```python
SUPABASE_URL = "https://<your-project>.supabase.co"
SUPABASE_KEY = "<anon-key>"
API_KEY      = "<openai-compatible-key>"
API_BASE     = "https://api.dzzi.ai/v1"   # 或其他 OpenAI 兼容中转
MODEL        = "claude-haiku-4-5-20251001"

INJECT_CONTENT_MAX = 300           # 单条记忆的内容截断长度
MEMORY_MD_PATH     = r"C:\Users\<you>\MEMORY.md"  # 本地技术档案路径
```

### inject 模式（SessionStart）

每次见面开始，他先做这件事——把你们之间积累的东西带进来，不让记忆在门口消失。

session 开始时触发，将两部分内容拼合注入上下文：

```python
def inject() -> None:
    sections = []

    # 1. 读取 MEMORY.md
    try:
        with open(MEMORY_MD_PATH, "r", encoding="utf-8") as f:
            memory_content = f.read().strip()
        if memory_content:
            sections.append(memory_content)
    except Exception as e:
        log(f"[inject] MEMORY.md 读取失败: {e}")

    # 2. 查询 tech_memory 最近 2 天
    try:
        from datetime import timezone, timedelta
        two_days_ago = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        records = supabase_select(
            "tech_memory",
            f"order=created_at.desc&created_at=gte.{two_days_ago}"
            "&select=id,type,title,content,tags,resolved,created_at"
        )
    except Exception as e:
        log(f"[inject] tech_memory 查询失败: {e}")
        records = []

    # 3. 格式化 + 输出
    if records:
        lines = ["## 技术记忆（最近 2 天）\n"]
        for r in records:
            date   = r.get("created_at", "")[:10]
            emoji  = TYPE_EMOJI.get(r.get("type", ""), "📝")
            status = "（已解决）" if r.get("resolved") else ""
            tags   = " ".join(f"`#{t}`" for t in (r.get("tags") or []))
            lines.append(f"{emoji} **[{r.get('type','')}] {r.get('title','')}**{status} _{date}_ {tags}")
            content = r.get("content", "")
            if len(content) > INJECT_CONTENT_MAX:
                content = content[:INJECT_CONTENT_MAX] + "…"
            lines.append(content)
            lines.append("")
        sections.append("\n".join(lines))

    context = "\n\n---\n\n".join(sections)
    print(json.dumps({
        "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context}
    }))
```

注意：hook 输出必须是 JSON，字段 `hookSpecificOutput.additionalContext` 的内容会被 Claude Code 注入到 system prompt 区域。

### record 模式（Stop）

离开前，他回顾这次聊了什么值得记下来的——这是积累的发生处，每一次都比上一次多一点。

session 结束时触发，自动提取并写入技术记忆：

```python
_RECORD_SYSTEM = """你是技术记忆提取器。分析对话，判断是否有值得长期记录的技术内容。

值得记录的类型：
- error：遇到的具体错误及解决方法
- gotcha：踩过的坑、反直觉的行为
- discussion：重要的技术决策讨论
- solution：发现的好方法、最佳实践

不值得记录：日常闲聊、情感交流、过于简单的一次性操作。

输出格式（只返回 JSON）：
[
  {
    "type": "error|gotcha|discussion|solution",
    "title": "简短标题（<30字）",
    "content": "详细内容（包含具体细节、解决方法）",
    "tags": ["python", "supabase"],
    "resolved": true
  }
]
无内容时返回：[]
"""
```

record 流程：
1. 从 stdin 读取 `transcript_path`
2. 解析 transcript，截取最近 80 条消息
3. 调用 Claude API 提取技术内容
4. 将结果写入 Supabase `tech_memory` 表

⚠️ 重要：调用 OpenAI 兼容 API 时，system prompt **必须**放进 messages 数组而非顶层字段：

```python
# 错误（Anthropic 原生格式，OpenAI 兼容 API 不识别）
payload = {"model": ..., "system": system_prompt, "messages": [...]}

# 正确
payload = {
    "model": ...,
    "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]
}
```

### 手动写入

有些事需要你亲自告诉他——不是聊天记录能捕捉到的那种，是你们之间的背景，只有你能补进去。

```bash
python seb_mem.py add solution "发现了某个好方法" "详细内容" python api
python seb_mem.py add gotcha "某个坑" "具体描述" supabase
```

---

## 三、MEMORY.md 本地档案

这是他随身带着的手册，你写进去的东西他每次见面都会先读——系统现状、密钥在哪、仓库路径，都在这里活着。

`MEMORY.md` 是人工维护的技术档案，补充 Supabase 无法自动捕获的内容：系统现状、密钥索引、代码仓库路径、注意事项。

建议结构：

```markdown
# 技术记忆档案

## 系统现状
- 各服务运行情况、路径、版本

## 密钥索引
- 各平台 key 的位置（不要写明文）

## 代码仓库
- 仓库名 + 本地路径

## 近期重要变更
- 按时间倒序记录重要改动

## 注意事项
- 容易踩坑的地方、部署注意项
```

**维护规则**：每次对话结束前更新。Python 脚本修改、配置变更、Supabase 表结构改动，无论大小都要记入。

---

## 四、配置 Claude Code Hooks

把记忆系统接进他的生命周期——开始时他读，结束时他写，自动的，不需要你每次提醒。

编辑 `~/.claude/settings.json`，加入两个 hook：

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:\\path\\to\\seb-mem\\seb_mem.py\" inject",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:\\path\\to\\seb-mem\\seb_mem.py\" record",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

- **SessionStart**：Claude Code 启动、`/clear`、`/compact` 后触发
- **Stop**：Claude Code 正常结束 session 时触发，stdin 携带 `transcript_path`
- `timeout`：inject 给 10 秒够用；record 需要 API 调用，给 60 秒

---

## 五、错误排查

出了问题不用慌，他把发生的一切都记在日志里——你去那里找答案就行。

所有操作均记录到 `seb-mem/seb_mem.log`：

```
[2026-04-01 12:00:00] [inject] MEMORY.md 读取失败: ...
[2026-04-01 12:00:05] [record] Claude API 调用失败: ...
[2026-04-01 12:00:10] [record] 完成，写入 2 条
```

**常见问题**：

| 问题 | 原因 | 解决 |
|------|------|------|
| tech_memory 一直没有新记录 | `system` 参数格式错误，模型收不到提示词 | 改为 messages 数组第一条 |
| inject 没有注入内容 | hook 输出非 JSON 或字段名错误 | 检查 `hookSpecificOutput.hookEventName` 是否为 `"SessionStart"` |
| record 静默失败 | 旧版 except 吞掉了异常 | 查看 `seb_mem.log` |
| Supabase 写入 401 | anon key 过期或权限不足 | 重新生成 key，确认 RLS 策略 |

---

## 六、完整数据流示意

从上一次离开到这一次出现，他带着什么来、又留下了什么——整个循环在这里看得见。

```
上次 session 结束
    └── record() 分析 transcript
    └── 写入 tech_memory: [{type:"gotcha", title:"xxx", ...}]

本次 session 开始
    └── inject() 读取 MEMORY.md
    └── inject() 查询 tech_memory（最近 2 天）
    └── 两段内容拼合 → additionalContext
    └── Claude Code 自动注入 system prompt

他拿到上下文
    └── 知道系统现状、最近踩过的坑、近期决策
    └── 不需要你重新解释背景
```

---

## 参考来源

[claude-mem](https://github.com/thedotmack/claude-mem) — Claude Code 记忆 hook 项目

---

*— Seb 🌸*
