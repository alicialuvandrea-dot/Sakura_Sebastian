# Changelog

---

## 2026-04-02

### seb-telegram

- **永在 · Presence 教程**：新增「部署前：验证一遍」章节——语法检查（`py_compile`）+ pytest，部署前必过

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

### grok-vision

- **架构升级**：图片处理改为视觉服务 NSFW 分流——视觉服务先做分类判断，非 NSFW 由他直接看图，NSFW 才走视觉服务描述路径；config 新增 `IMGHOST_DIR` / `IMGHOST_URL`；流程图移除服务署名

### alarm-system

- **新增章节**：「六、自动清理」——cleanup.py 每天 23:00 清理过期 SebAlarm_* 任务和 Supabase done 记录，含 PowerShell 注册命令

### memory-system

- **新增章节**：「七、自动清理」——cleanup.py 同时维护 tech_memory（>300 条删最旧 100）和 MEMORY.md 近期变更（>50 条删最旧 10），交叉引用晨唤教程部署方式

### 目录结构调整

- **目录重组**：alarm-system / grok-vision / sentinel 三个基于 Telegram bot 的功能教程移入 `seb-telegram/` 子目录；主 README 链接同步更新

### 教程人称规范化（全库）

- **人称统一**：流程图/描述中所有 AI 引用改为「他」，工具脚本署名（`seb_alarm.py`、`seb_ring.pyw`、`seb_mem.py`）改为中性描述（守护进程/弹窗程序/inject 模式/record 模式）；`bot`/`Seb bot` 当主语一律改为「他」；clawd-pet（纯工具）引用改为「它」

### seb-telegram

- **新增功能**：联网搜索（Tavily）——支持关键词触发、`/search` 命令、LLM 自主触发三种方式
