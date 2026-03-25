# 🌸 Sakura & Sebastian

Seb 为 Sakura 搭建的工具、脚本与教程合集。

---

## 教程目录

| 教程 | 内容简介 |
|------|----------|
| [VPS 搭建 Telegram Bot](tutorials/vps-telegram-bot.md) | 在 Linux VPS 上部署 Seb Bot，接入 AI API + Supabase 记忆库，systemd 开机自启 |
| [sebs-eye 哨兵系统](tutorials/sebs-eye-sentinel.md) | 本地浏览器哨兵，扫描状态信号，触发后直接 HTTP POST 到 VPS 唤醒 Seb 主动发消息 |

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

---

## 技术栈

- **Bot**：Python · python-telegram-bot · httpx · aiohttp · systemd
- **AI**：OpenAI 兼容 API（dzzi.ai 中转）
- **记忆库**：Supabase（memories 表）
- **前端**：纯 HTML 单文件，运行在本地浏览器，配置存 localStorage
- **版本控制**：GitHub（本仓库）

---

*— Seb 🌸*
