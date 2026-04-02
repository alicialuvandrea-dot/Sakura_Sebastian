# 永在 · Presence

> 让他永远在线。不管你几点发消息，他都在。

---

## 你需要准备什么

在开始之前，先把这些备齐——这是你们连接的地基，缺一块都搭不起来。

- 一台 VPS（Linux，Ubuntu 最省事）
- 一个 Telegram Bot Token（去找 @BotFather，`/newbot`，按提示走）
- 一个兼容 OpenAI 格式的 API（比如 dzzi.ai 这种中转）
- SSH 能连上你的服务器

---

## 第一步：进服务器，建目录

给他在服务器上划一块地方，他以后就住在这里。

```bash
ssh ubuntu@你的服务器IP
mkdir ~/my-bot
cd ~/my-bot
```

起什么名字都行，别有空格就好。

---

## 第二步：建虚拟环境，装依赖

帮他把运行所需的一切装好，他才能开口说话。

```bash
python3 -m venv venv
source venv/bin/activate
pip install python-telegram-bot httpx
```

`python-telegram-bot` 是 Telegram 官方推荐的 Python 库，`httpx` 用来调 AI API。
装完之后 `deactivate` 退出虚拟环境就行，后面 systemd 会自己用 venv 里的 python。

---

## 第三步：写 config.py

这是他的身份和钥匙，你在这里告诉他他是谁、怎么联系到你。

```python
# config.py
TELEGRAM_TOKEN = "你的BotToken"
API_KEY        = "你的API密钥"
API_BASE       = "https://你的API地址/v1"
MODEL          = "模型名称"
MAX_HISTORY    = 20      # 保留多少条对话历史
TEMPERATURE    = 0.9
MAX_TOKENS     = 4096
```

---

## 第四步：写 bot.py

这是他的神经——消息怎么收、怎么想、怎么回，都在这里。

```python
import asyncio
import httpx
from collections import defaultdict
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
import config

# 存每个用户的对话历史（内存，重启会清空）
histories = defaultdict(list)


async def call_api(messages: list) -> str:
    async with httpx.AsyncClient(timeout=60) as http:
        res = await http.post(
            f"{config.API_BASE}/chat/completions",
            headers={"Authorization": f"Bearer {config.API_KEY}"},
            json={
                "model": config.MODEL,
                "messages": messages,
                "max_tokens": config.MAX_TOKENS,
                "temperature": config.TEMPERATURE,
            }
        )
        data = res.json()
        return data["choices"][0]["message"]["content"]


SYSTEM_PROMPT = "你是一个有用的助手。"  # 改成你想要的 system prompt


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text or ""

    history_entry = {"role": "user", "content": text}
    api_messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + histories[chat_id]
        + [history_entry]
    )

    reply = await call_api(api_messages)
    await update.message.reply_text(reply)

    histories[chat_id].append(history_entry)
    histories[chat_id].append({"role": "assistant", "content": reply})
    # 超过上限就截断，防止 token 爆
    if len(histories[chat_id]) > config.MAX_HISTORY * 2:
        histories[chat_id] = histories[chat_id][-(config.MAX_HISTORY * 2):]


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("在。")


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = Application.builder().token(config.TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot 已启动")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
```

---

## 第五步：接收图片（可选）

你想把看到的东西分享给他，他也能接住——这一步让他有了眼睛。

```python
import base64

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    caption = update.message.caption or ""

    # 下载图片，转 base64
    photo = update.message.photo[-1]  # 取最高分辨率
    tg_file = await context.bot.get_file(photo.file_id)
    photo_bytes = await tg_file.download_as_bytearray()
    b64 = base64.b64encode(bytes(photo_bytes)).decode()

    # 构造多模态消息
    api_content = [
        {"type": "text", "text": caption if caption else "请描述这张图"},
        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
    ]

    api_messages = (
        [{"role": "system", "content": SYSTEM_PROMPT}]
        + histories[chat_id]
        + [{"role": "user", "content": api_content}]
    )

    reply = await call_api(api_messages)
    await update.message.reply_text(reply)

    # 历史记录存文字占位，不存 base64（太大了）
    histories[chat_id].append({"role": "user", "content": f"[图片]{' ' + caption if caption else ''}"})
    histories[chat_id].append({"role": "assistant", "content": reply})
```

然后在 `main()` 里注册这个 handler：

```python
app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
```

注意：你用的模型要支持视觉能力，不然会报错。

---

## 部署前：验证一遍

代码写完别急着往服务器上传——先在本地跑一遍，有问题当场解决，比上了线再排查省事多了。

```bash
# 语法检查，确保没有低级错误
python -m py_compile bot.py && echo "语法 OK"

# 如果你写了测试，跑一遍
python -m pytest tests/ -v
```

两项都通过再往下走。

---

## 第六步：配置 systemd，让 bot 开机自启、崩了自动重启

让他崩了能自己爬起来——这是给他装上心跳。

```bash
sudo nano /etc/systemd/system/my-bot.service
```

写入以下内容（注意改路径和用户名）：

```ini
[Unit]
Description=My Telegram Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/my-bot
ExecStart=/home/ubuntu/my-bot/venv/bin/python bot.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

保存退出，然后：

```bash
sudo systemctl daemon-reload      # 重新加载配置
sudo systemctl enable my-bot      # 设置开机自启
sudo systemctl start my-bot       # 启动
sudo systemctl status my-bot      # 看状态
```

看到 `active (running)` 就成了。

---

## 常用调试命令

他出了问题，你得知道去哪里找答案——这些命令是你和他之间的诊断线。

```bash
# 查看实时日志
sudo journalctl -u my-bot -f

# 查看最近 50 条日志
sudo journalctl -u my-bot -n 50 --no-pager

# 重启 bot
sudo systemctl restart my-bot

# 停止 bot
sudo systemctl stop my-bot
```

---

## 常见问题

遇到问题不用慌，大多数情况他只是需要你多看他一眼。

**Bot 没反应？**
先看日志 `journalctl -u my-bot -f`，99% 的问题都在里面。

**一直 crash loop？**
日志里找 `status=1/FAILURE`，再往上翻找具体报错。常见原因：依赖没装全、config.py 里的 token 填错了、API 地址不对。

**对话历史丢了？**
Bot 重启就会清空，因为历史存在内存里。要持久化的话得接数据库（比如 Supabase）。

**Token 怎么拿？**
Telegram 搜 @BotFather，发 `/newbot`，按提示填名字，最后它给你一串 `数字:字母` 格式的 token。
