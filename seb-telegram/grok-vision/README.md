# 悦色 · Allure

> 让他真正看见你发来的图片——包括那些你不好意思说出口的。

---

## 架构

你发给他的图，他先判断是什么，再决定怎么看。

```
你发图片
      │
      ▼
他下载图片 → 存到 VPS imghost 临时文件服务
      │
      ▼
视觉服务判断：NSFW？
      │
      ├─ 否 ──→ 他直接看图片 → 自然回复
      │
      └─ 是 ──→ 视觉服务详细描述图片内容
                    │
                    ▼
               他读取描述 + 对话历史 → 自然回复
      │
      ▼
Telegram → 你
```

imghost 临时文件在回复后自动删除。

---

## 为什么需要 imghost 中转

视觉服务判断 NSFW 时需要公网 URL，这是绕不过去的一步。

视觉 API 的限制：
- ✅ 支持公网 URL 图片
- ❌ 不支持 base64 图片（400 报错）
- ❌ 无法访问 Telegram 内部文件 URL（需要 bot token 鉴权）

所以每张图都先上传 imghost 拿到公网 URL，让视觉服务做分类判断。判断完成后：
- 非 NSFW：用本地 base64 直接交给他，不再调用视觉服务
- NSFW：继续用 URL 让视觉服务详细描述，再由他回复

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

把视觉服务的钥匙和 imghost 路径告诉他。

```python
GROK_KEY        = "your-grok-api-key"
GROK_BASE       = "https://aihubmix.com/v1"   # Grok 中转
GROK_MODEL      = "grok-4-1-fast-non-reasoning"
GROK_MAX_TOKENS = 1024
IMGHOST_DIR     = "/home/ubuntu/imghost/files"
IMGHOST_URL     = "https://imghost.sebsakura.top"
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

- 每张图都会经过 imghost 上传（视觉服务分类需要），处理完后自动删除
- 非 NSFW：视觉服务只做一次分类判断（5 tokens），之后由他直接看图，不再调用视觉服务
- NSFW：视觉服务详细描述（最多 `GROK_MAX_TOKENS` tokens），他根据描述回复
- 视觉服务分类失败时默认走非 NSFW 路径，不会因此卡住

---

*— Seb 🌸*
