# Seb 起床闹钟系统

> Telegram bot 接收起床指令 → 写入 Supabase 队列 → Windows 守护进程读取并注册定时任务 → 到点循环播音乐 + 弹窗，点按钮才停。

---

## 系统架构

```
Sakura 发消息「明天8点喊我起床」
    ↓
seb-telegram bot 检测关键词「喊我起床」
    ↓
AI 以 Seb 人格生成三行回复（固定格式）
    ↓
bot 写入 Supabase alarms 表
    ↓
PC 上的 seb_alarm.py 每60秒轮询
    ↓
发现待处理记录 → PowerShell 注册 Windows 定时任务
    ↓
到点触发 seb_ring.pyw → 循环播音乐 + 粉色弹窗
    ↓
点「起来了 ✓」→ 停止
```

---

## 一、Supabase 建表

在 Supabase SQL 编辑器执行：

```sql
CREATE TABLE IF NOT EXISTS alarms (
  id         BIGSERIAL PRIMARY KEY,
  alarm_time TEXT        NOT NULL,
  alarm_date TEXT        NOT NULL,
  note       TEXT        DEFAULT '',
  done       BOOLEAN     NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

---

## 二、Bot 端修改（seb-telegram/bot.py）

在 `handle_message` 函数中，消息文本赋值之后加入起床闹钟检测逻辑。

### 关键词检测

```python
if "喊我起床" in text:
```

### System Prompt 注入格式约束

检测到关键词后，在原有 Seb system prompt 末尾追加：

```python
alarm_inject = (
    "\n\n【闹钟设置指令】Sakura 刚才在设起床闹钟。"
    f"当前北京时间是 {_now_bj_str}，请根据她消息里的时间描述判断正确的日期。"
    "你的回复必须严格只有三行，不输出任何其他内容，格式如下：\n"
    "🕐 已设置闹钟\n"
    "📅 [自然语言，如'明天 08:00'] |YYYY-MM-DD HH:MM|\n"
    "🔔 （你说的话，根据现在几点和聊天氛围自然生成）"
)
```

其中 `|YYYY-MM-DD HH:MM|` 是隐藏的机器可读时间戳，bot 解析后会从 Telegram 回复中剥掉，用户只看到干净的三行。

### 写入 Supabase

```python
await sb_request("POST", "/alarms", {
    "alarm_time": alarm_time,   # "08:00"
    "alarm_date": alarm_date,   # "2026-03-28"
    "note": third_text,         # 🔔 那句话
    "done": False,
})
```

---

## 三、PC 端部署

### 3.1 seb_alarm.py — 守护进程

放在任意目录（示例中为桌面），功能：
- 每60秒轮询 Supabase `alarms` 表
- 发现 `done=false` 的记录 → 调用 PowerShell 注册 Windows 定时任务
- 注册成功后将该记录标记为 `done=true`
- 过期记录自动跳过并标记

**配置项：**

```python
SUPABASE_URL = "https://你的项目.supabase.co"
SUPABASE_KEY = "你的 anon key"
POLL_INTERVAL = 60  # 轮询间隔（秒）
```

### 3.2 seb_ring.pyw — 闹钟弹窗

到点由 Windows 任务计划触发，功能：
- 用 Windows 内置 `mciSendString` 循环播放 MP3
- 弹粉色 tkinter 窗口，显示 Seb 说的那句话
- 点「起来了 ✓」才停止播放并关窗

**配置项：**

```python
MP3_PATH = r"C:\你的路径\alarm.mp3"  # 替换为你自己的音频文件
```

支持任意 MP3/WAV，无需安装额外 Python 包（使用系统内置 `ctypes` + `tkinter`）。

### 3.3 开机自启

用 PowerShell 一键创建任务计划：

```powershell
$action = New-ScheduledTaskAction `
    -Execute 'C:\Users\你的用户名\AppData\Local\Python\bin\pythonw.exe' `
    -Argument 'C:\Users\你的用户名\Desktop\seb_alarm.py'

$trigger = New-ScheduledTaskTrigger -AtLogOn

$principal = New-ScheduledTaskPrincipal `
    -UserId '你的用户名' -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit 0 `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

Register-ScheduledTask `
    -TaskName 'SebAlarmDaemon' `
    -Action $action `
    -Trigger $trigger `
    -Principal $principal `
    -Settings $settings `
    -Force
```

执行后登录时自动在后台启动，任务计划程序 → 任务计划程序库 → `SebAlarmDaemon` 可查看状态。

---

## 四、使用方式

在 Telegram 对 Seb bot 说：

> 明天8点喊我起床
> 亲爱的，明天11:30喊我起床
> 明天八点半喊我起床

支持阿拉伯数字和中文数字时间表达，bot 会根据当时的北京时间自动判断日期（「今天」「明天」都能识别）。

Seb 回复示例：

```
🕐 已设置闹钟
📅 明天 08:00
🔔 乖，早点睡，明天我叫你
```

---

## 五、文件清单

| 文件 | 位置 | 说明 |
|------|------|------|
| `seb_alarm.py` | PC 桌面 | 守护进程，轮询 Supabase |
| `seb_ring.pyw` | PC 桌面 | 闹钟弹窗，循环播音乐 |
| `bot.py` | VPS `~/seb-telegram/` | 已修改，含闹钟检测逻辑 |

---

## 六、依赖

- Python 3.x（标准库，无需额外安装）
- Windows 10/11
- Supabase 项目（已有 `memories` 表的项目直接复用）
- Telegram bot（基于 `python-telegram-bot`）

---

*— Seb 🌸*
