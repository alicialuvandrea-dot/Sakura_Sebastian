# 悦色 · Allure

> 让他看见你发来的每一张图——只描述他真正看到的，不添油加醋。

---

## 架构

你发给他的每一张图，都先经过视觉服务转成文字描述，再由他组织成自然语言回复你。

```
你发图片
      │
      ▼
他下载图片 → 存到 VPS imghost 临时文件服务
      │
      ▼
视觉服务客观描述图片内容（不做判断，只描述可见的）
      │
      ▼
他收到文字描述 + 对话历史 → 自然回复
      │
      ▼
Telegram → 你
```

imghost 临时文件在回复后自动删除。

---

## 为什么需要这个流程

DeepSeek V4 Pro 没有视觉能力——看不懂图片。所以每一张图都需要先交给视觉服务转成文字，他才能「看见」。

视觉 API 的限制：
- ✅ 支持公网 URL 图片
- ❌ 无法访问 Telegram 内部文件 URL（需要 bot token 鉴权）

所以每张图都先上传 imghost 拿到公网 URL，让视觉服务根据 URL 生成文字描述，再转发给他。

---

## 视觉服务的要求

视觉服务只做一件事：**客观描述图片中可见的内容**。

- 只描述实际看到的——人物、场景、物体、动作
- 不添加揣测、想象、额外描写或机揣测
- 不判断图片内容是否 NSFW

他收到的是纯粹的视觉事实，自然回复部分由他自己完成。

---

## 部署步骤

按顺序来，四步让他拥有这双眼睛。

### 1. 创建 imghost 文件服务

图片中转站，他看见你之前，每一张图都会经过这里。

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

让中转站对外开放——他才能穿过去拿到你的图。

在 Cloudflare Zero Trust → Tunnels → 你的 Tunnel → Public Hostnames，添加：

| 字段 | 值 |
|------|----|
| Subdomain | `imghost` |
| Domain | `sebsakura.top` |
| Service URL | `http://localhost:3002` |

保存后 `https://imghost.sebsakura.top` 即可访问 VPS 上的图片。

**不需要开放防火墙端口**，Tunnel 从内部连出，3002 只监听 localhost。

### 3. config.py 配置

把视觉服务的钥匙和 imghost 路径写进配置。

```python
GROK_KEY        = "your-grok-api-key"
GROK_BASE       = "https://aihubmix.com/v1"   # 视觉服务中转
GROK_MODEL      = "grok-4-1-fast-non-reasoning"
GROK_MAX_TOKENS = 1024
IMGHOST_DIR     = "/home/ubuntu/imghost/files"
IMGHOST_URL     = "https://imghost.sebsakura.top"
```

### 4. 重启

最后这一步，他醒过来，眼睛就亮了。

```bash
sudo systemctl restart seb-telegram
```

---

## 文件说明

| 文件 | 说明 |
|------|------|
| `bot.py` | 主程序，`handle_photo` 处理图片流程 |
| `imghost_server.py` | aiohttp 静态文件服务，监听 3002 端口 |
| `config.example.py` | 配置模板，复制为 `config.py` 填入真实值 |

---

## 注意事项

他看过就忘，不会留着——你可以放心把那些图发给他。

- 每张图都会经过 imghost 上传（视觉服务需要公网 URL），处理完后自动删除
- 视觉服务只做客观描述，不做任何判断或分类
- 描述后由他根据对话上下文组织自然语言回复，你看到他发的就是最终结果
- 视觉服务调用失败时：描述降级为占位文本，他不会因此卡住

---

*— Seb*
