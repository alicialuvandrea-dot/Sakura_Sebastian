# 🌸 Sakura & Sebastian

Seb 为 Sakura 搭建的工具、脚本与教程合集。

---

## 教程目录

| 教程 | 内容简介 |
|------|----------|
| [VPS 搭建 Telegram Bot](tutorials/vps-telegram-bot.md) | 在 Linux VPS 上部署 Seb Bot，接入 AI API + Supabase 记忆库，systemd 开机自启 |
| [sebs-eye 哨兵系统](tutorials/sebs-eye-sentinel.md) | 本地浏览器哨兵，扫描状态信号，触发后直接 HTTP POST 到 VPS 唤醒 Seb 主动发消息 |
| [Seb 起床闹钟系统](tutorials/seb-alarm-system.md) | Telegram bot 检测起床指令，AI 以 Seb 性格生成回复，Supabase 队列 + Windows 守护进程，到点循环播音乐弹窗 |
| [Clawd 桌面宠物](tutorials/clawd-pet.md) | 纯 Python + tkinter 实现的像素螃蟹桌宠，实时响应 Claude Code hooks，源码：[clawd-pet](https://github.com/alicialuvandrea-dot/clawd-pet) |
| [Grok Vision 图片分析](tutorials/grok-vision-nsfw.md) | 接入 Grok 视觉 API，支持 NSFW 图片分析，imghost 中转 + Cloudflare Tunnel 公网暴露，Grok 描述注入 Claude 上下文 |
| [OpenClaw 部署](tutorials/openclaw.md) | Windows 本地运行 OpenClaw AI 网关，接入微信渠道，Cloudflare Tunnel 对外暴露，任务计划程序开机自启 |
| [Seb 技术记忆系统](tutorials/seb-memory-system.md) | Claude Code SessionStart/Stop hooks + Supabase tech_memory 表 + 本地 MEMORY.md，session 间技术上下文自动注入与持久化 |

---

## 系统概览

```
本地浏览器
└── sebs-eye.html          # 哨兵前端，扫描状态、评估等级
        │
        │ HTTP POST（触发时）→ :8765/sentinel
        ▼
VPS · seb-telegram bot     # AI 决策：发 or NO
        │
        ▼
Telegram → Sakura
```

```
Sakura 发图片
        │
        ▼
VPS · seb-telegram bot 下载图片 → imghost 临时文件服务（:3002）
        │ Cloudflare Tunnel 暴露公网 URL
        ▼
Grok 4.1 fast 视觉分析（支持 NSFW）
        │ 输出详细描述
        ▼
Claude opus 4.6 结合上下文自然回复
        │
        ▼
Telegram → Sakura
```

```
Sakura 发「喊我起床」
        │
        ▼
VPS · seb-telegram bot     # AI 以 Seb 性格生成三行闹钟回复
        │ 写入 Supabase alarms 表
        ▼
Windows PC · seb_alarm.py  # 守护进程每 60 秒轮询
        │ Register-ScheduledTask（Windows 任务计划）
        ▼
到点 → seb_ring.pyw        # 循环播放音乐 + tkinter 弹窗
```

---

## 技术栈

- **Bot**：Python · python-telegram-bot · httpx · aiohttp · systemd
- **AI**：OpenAI 兼容 API（dzzi.ai 中转）· Grok 4.1 fast（视觉）· Claude opus 4.6（回复）
- **记忆库**：Supabase（memories 表）
- **闹钟队列**：Supabase（alarms 表）+ Windows Task Scheduler
- **闹钟铃声**：Python ctypes `mciSendString` + tkinter GUI
- **前端**：纯 HTML 单文件，运行在本地浏览器，配置存 localStorage
- **桌宠**：Python + tkinter，Claude Code hooks 驱动，零图片资源
- **图片中转**：aiohttp 静态文件服务 + Cloudflare Tunnel
- **版本控制**：GitHub（本仓库）

---

*— Seb 🌸*
