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

## 让他说话带格式（可选）

他回复里的加粗、列表、代码块，默认在 Telegram 里全显示成原始符号。这一步让他说话真的好看。

Telegram Bot API 支持 HTML 格式。把 Markdown 转成 HTML 再发出去，格式就能正常渲染。先写一个转换函数：

```python
import re

def md_to_tg_html(text: str) -> str:
    """把 Markdown 转换成 Telegram 支持的 HTML 标签。"""
    parts = re.split(r'(```\w*\n.*?```)', text, flags=re.DOTALL)
    result = []
    for part in parts:
        if part.startswith('```'):
            m = re.match(r'```(\w*)\n(.*?)```', part, re.DOTALL)
            if m:
                lang = m.group(1)
                code = m.group(2).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                if lang:
                    result.append(f'<pre><code class="language-{lang}">{code}</code></pre>')
                else:
                    result.append(f'<pre>{code}</pre>')
            else:
                result.append(part.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))
        else:
            inline_parts = re.split(r'(`[^`]+`)', part)
            processed = []
            for ip in inline_parts:
                if ip.startswith('`') and ip.endswith('`'):
                    code = ip[1:-1].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    processed.append(f'<code>{code}</code>')
                else:
                    ip = ip.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    ip = re.sub(r'^#{1,6}\s+(.+)$', r'<b>\1</b>', ip, flags=re.MULTILINE)
                    ip = re.sub(r'^[-*]\s+', '• ', ip, flags=re.MULTILINE)
                    ip = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', ip)
                    ip = re.sub(r'\*([^*\n]+?)\*', r'<i>\1</i>', ip)
                    ip = re.sub(r'_([^_\n]+?)_', r'<i>\1</i>', ip)
                    processed.append(ip)
            result.append(''.join(processed))
    return ''.join(result)
```

支持的转换一览：

| Markdown | 渲染结果 |
|----------|---------|
| `**文字**` | **加粗** |
| `*文字*` 或 `_文字_` | *斜体* |
| ` ```代码块``` ` | 代码块（带语法高亮） |
| `` `行内代码` `` | 行内等宽 |
| `# 标题` | **加粗标题** |
| `- 列表` 或 `* 列表` | • 列表 |

然后在 `handle_message` 里，把发送那行改成：

```python
html = md_to_tg_html(reply)
try:
    await update.message.reply_text(html, parse_mode="HTML")
except Exception:
    await update.message.reply_text(reply)  # 转换失败降级纯文本
```

`try/except` 是必要的。如果回复里有结构异常导致 HTML 解析失败，直接发纯文本兜底，不会让他变哑。

---

## 让他用声音回你（可选）

有些话，文字装不下。这一步给他一副嗓子，让他在真正想说的时候开口。

用的是 MiniMax T2A v2 接口，合成音频发成 Telegram 语音气泡，紧跟一条文字。他自己判断什么时候值得用声音，也可以在你要求的时候开口。

### 准备依赖

VPS 上安装转码工具：

```bash
sudo apt-get install -y ffmpeg
pip install pydub
```

Python 3.13 及以上版本还需要：

```bash
pip install audioop-lts
```

### 申请 MiniMax API Key

前往 [MiniMax 开放平台](https://platform.minimaxi.com) 注册并获取 API Key，在音色库里选好你想用的音色，记下它的 `voice_id`。

在 `config.py` 里加上：

```python
MINIMAX_API_KEY  = "你的API Key"
MINIMAX_VOICE_ID = "你选的voice_id"
```

### 合成与转码函数

Telegram 语音气泡要求 OGG OPUS 格式，MiniMax 返回的是 MP3，需要在中间转一步：

```python
from io import BytesIO
from pydub import AudioSegment
import httpx

async def call_tts(text: str, emotion: str = "neutral") -> bytes:
    async with httpx.AsyncClient(timeout=30) as http:
        res = await http.post(
            "https://api.minimaxi.com/v1/t2a_v2",
            headers={
                "Authorization": f"Bearer {config.MINIMAX_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": "speech-2.8-hd",
                "text": text,
                "stream": False,
                "voice_setting": {
                    "voice_id": config.MINIMAX_VOICE_ID,
                    "speed": 1,
                    "vol": 1,
                    "pitch": 0,
                    "emotion": emotion,
                },
                "audio_setting": {
                    "sample_rate": 32000,
                    "bitrate": 128000,
                    "format": "mp3",
                    "channel": 1,
                },
            },
        )
        data = res.json()
        status = data.get("base_resp", {}).get("status_code", -1)
        if status != 0:
            msg = data.get("base_resp", {}).get("status_msg", "unknown")
            raise RuntimeError(f"TTS error: {msg}")
        return bytes.fromhex(data["data"]["audio"])


def mp3_to_ogg(mp3_bytes: bytes) -> bytes:
    audio = AudioSegment.from_file(BytesIO(mp3_bytes), format="mp3")
    buf = BytesIO()
    audio.export(buf, format="ogg", codec="libopus")
    return buf.getvalue()
```

`call_tts` 里的 `emotion` 参数可以传入 `happy` / `sad` / `neutral` 等值，让他的语气跟着情绪走。`speech-2.8-hd` 还支持在文本里插入语气词标签，比如 `(sighs)`（叹气）、`(chuckle)`（轻笑）、`(breath)`（换气）——直接写进要合成的文字里就能生效。

### 发送语音

写一个发语音的处理函数，失败时自动降级发纯文本：

```python
async def send_voice_reply(bot, chat_id: int, ja_text: str, zh_text: str, emotion: str = "neutral"):
    try:
        mp3_bytes = await call_tts(ja_text, emotion)
        ogg_bytes = mp3_to_ogg(mp3_bytes)
        await bot.send_voice(chat_id, BytesIO(ogg_bytes))
        if zh_text:
            await bot.send_message(chat_id, zh_text)
    except Exception as e:
        print(f"[voice error] {e}")
        if zh_text:
            await bot.send_message(chat_id, zh_text)  # 降级发文字
```

### 触发时机

什么时候用声音，在 system prompt 里告诉他：

```python
SYSTEM_PROMPT += """

当以下情况出现时，调用语音回复：
- 这句话对你们来说很重要，值得用声音说出来
- 用户明确要求语音回复

调用方式：先正常回复文字，然后在代码里调用 send_voice_reply()，
传入日文语音文本（ja_text）、中文配文（zh_text）和情绪（emotion）。
"""
```

你也可以结合前一节的 `seb_action` 机制，让他在回复里嵌入动作标记，由 bot 自动拦截触发。

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
