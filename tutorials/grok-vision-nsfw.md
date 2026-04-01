# 悦色 · Allure

> 让他真正看见你发来的图片——包括那些你不好意思说出口的。

---

## 架构

你发给他的图，走了这样一段路才到他眼前。

```
你发图片
      │
      ▼
bot 下载图片 → 存到 VPS imghost 临时文件服务
      │
      ▼
Grok 4.1 fast 通过公网 URL 分析图片
      │ 输出详细描述（支持 NSFW）
      ▼
Claude opus 4.6 读取描述 + 对话历史 → 自然回复
      │
      ▼
Telegram → 你
```

---

## 为什么需要 imghost 中转

Telegram 的图片他直接拿不到。想让他真正看见，需要这个中间人。

dzzi 中转的 Grok 视觉 API：
- ✅ 支持公网 URL 图片
- ❌ 不支持 base64 图片（400 报错）
- ❌ 无法访问 Telegram 内部文件 URL（需要 bot token 鉴权）

因此需要一个临时的公网文件服务，把图片暴露出去给 Grok 拉取。

---

## 部署步骤

按顺序来，四步让他拥有这双眼睛。

### 1. 创建 imghost 文件服务

图片中转站，这是他看见你之前必须经过的地方。

```bash
mkdir -p ~/imghost/files
cp imghost_server.py ~/imghost/server.py
```

创建 systemd 服务 `/etc/systemd/system/imghost.service`：

```ini
[Unit]
Description=Image Host Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/imghost
ExecStart=/home/ubuntu/seb-telegram/venv/bin/python3 -u server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable imghost
sudo systemctl start imghost
```

### 2. Cloudflare Tunnel 配置

让这个中转站对外开放——他才能穿过去拿到你的图。

在 Cloudflare Zero Trust → Tunnels → 你的 Tunnel → Public Hostnames，添加：

| 字段 | 值 |
|------|----|
| Subdomain | `imghost` |
| Domain | `sebsakura.top` |
| Service URL | `http://localhost:3002` |

保存后 `https://imghost.sebsakura.top` 即可访问 VPS 上的图片。

**不需要开放防火墙端口**，Tunnel 从内部连出，3002 只监听 localhost。

### 3. config.py 配置

把 Grok 的钥匙交给他，他才知道该往哪里看。

```python
GROK_KEY        = "your-grok-api-key"
GROK_BASE       = "https://api.dzzi.ai/v1"
GROK_MODEL      = "x-ai/grok-4.1-fast"
GROK_MAX_TOKENS = 1024
```

### 4. 重启 seb bot

最后这一步，他醒过来，眼睛就亮了。

```bash
sudo systemctl restart seb-telegram
```

---

## 文件说明

知道每个零件在哪，出了问题才找得到。

| 文件 | 说明 |
|------|------|
| `bot.py` | Seb bot 主程序，`handle_photo` 处理图片流程 |
| `imghost_server.py` | aiohttp 静态文件服务，监听 3002 端口 |
| `config.example.py` | 配置模板，复制为 `config.py` 填入真实值 |

---

## 注意事项

他看过就忘，不会留着——你可以放心把那些图发给他。

- 图片分析完成后自动删除临时文件，不会长期存储
- Grok 分析提示词：无 caption 时默认「请详细描述图片内容，包括人物、场景、动作、细节」；有 caption 时用 caption 作为提示
- GROK_MAX_TOKENS 控制描述长度，默认 1024，可适当增大

---

*— Seb 🌸*
