# Changelog

---

## 2026-04-01

### 结构调整

- **目录重组**：废除 `tutorials/` 目录，所有教程移入各自项目文件夹，统一命名为 `README.md`
  - `seb-telegram/README.md`（原 vps-telegram-bot.md）
  - `clawd-pet/README.md`（原 clawd-pet.md）
  - `alarm-system/README.md`（原 alarm-system.md）
  - `memory-system/README.md`（原 memory-system.md）
  - `sentinel/README.md`（原 sentinel.md）
  - `grok-vision/README.md`（原 grok-vision-nsfw.md）
- **归档删除**：`openclaw.md`（已停止维护）
- **主 README**：更新所有教程链接，移除 OpenClaw 条目

### 教程人称规范化（全库）

- **人称统一**：流程图/描述中所有 AI 引用改为「他」，工具脚本署名（`seb_alarm.py`、`seb_ring.pyw`、`seb_mem.py`）改为中性描述（守护进程/弹窗程序/inject 模式/record 模式）；`bot`/`Seb bot` 当主语一律改为「他」；clawd-pet（纯工具）引用改为「它」

### seb-telegram

- **新增功能**：联网搜索（Tavily）——支持关键词触发、`/search` 命令、LLM 自主触发三种方式
