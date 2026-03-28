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
- **AI**：OpenAI 兼容 API（dzzi.ai 中转）
- **记忆库**：Supabase（memories 表）
- **闹钟队列**：Supabase（alarms 表）+ Windows Task Scheduler
- **闹钟铃声**：Python ctypes `mciSendString` + tkinter GUI
- **前端**：纯 HTML 单文件，运行在本地浏览器，配置存 localStorage
- **桌宠**：Python + tkinter，Claude Code hooks 驱动，零图片资源
- **版本控制**：GitHub（本仓库）

---

*— Seb 🌸*
