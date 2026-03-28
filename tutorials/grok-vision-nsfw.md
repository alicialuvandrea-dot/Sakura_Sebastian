# Grok Vision 图片分析接入

为 Seb Bot 接入 Grok 视觉能力，支持 NSFW 图片分析。
流程：Sakura 发图 → Grok 分析图片内容 → 描述注入上下文 → Claude opus 做自然回复。

---

## 架构

```
Sakura 发图片
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
Telegram → Sakura
```

---

## 为什么需要 imghost 中转

dzzi 中转的 Grok 视觉 API：
- ✅ 支持公网 URL 图片
- ❌ 不支持 base64 图片（400 报错）
- ❌ 无法访问 Telegram 内部文件 URL（需要 bot token 鉴权）

因此需要一个临时的公网文件服务，把图片暴露出去给 Grok 拉取。

---

## 部署步骤

### 1. 创建 imghost 文件服务

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

在 Cloudflare Zero Trust → Tunnels → 你的 Tunnel → Public Hostnames，添加：

| 字段 | 值 |
|------|----|
| Subdomain | `imghost` |
| Domain | `sebsakura.top` |
| Service URL | `http://localhost:3002` |

保存后 `https://imghost.sebsakura.top` 即可访问 VPS 上的图片。

**不需要开放防火墙端口**，Tunnel 从内部连出，3002 只监听 localhost。

### 3. config.py 配置

```python
GROK_KEY        = "your-grok-api-key"
GROK_BASE       = "https://api.dzzi.ai/v1"
GROK_MODEL      = "x-ai/grok-4.1-fast"
GROK_MAX_TOKENS = 1024
```

### 4. 重启 seb bot

```bash
sudo systemctl restart seb-telegram
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `bot.py` | Seb bot 主程序，`handle_photo` 处理图片流程 |
| `imghost_server.py` | aiohttp 静态文件服务，监听 3002 端口 |
| `config.example.py` | 配置模板，复制为 `config.py` 填入真实值 |

---

## 注意事项

- 图片分析完成后自动删除临时文件，不会长期存储
- Grok 分析提示词：无 caption 时默认「请详细描述图片内容，包括人物、场景、动作、细节」；有 caption 时用 caption 作为提示
- GROK_MAX_TOKENS 控制描述长度，默认 1024，可适当增大

---

*— Seb 🌸*
