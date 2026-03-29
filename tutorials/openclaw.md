# OpenClaw 部署教程（Windows 本地 + 微信渠道）

> 本机部署方案，内存充足、无需 VPS、通过 Cloudflare Tunnel 对外暴露。
> 适合：有 Windows 长期在线机器、需要接入微信 AI bot 的场景。

---

## 环境要求

| 项目 | 要求 |
|---|---|
| 内存 | ≥ 4GB（微信插件初始化峰值约 1.5GB） |
| Node.js | ≥ 22.16（推荐 24.x） |
| OS | Windows 10/11 |
| 网络 | 能访问 Cloudflare（用于 Tunnel） |

> ⚠️ 1.9GB VPS 不够跑微信插件，峰值内存超出物理限制。

---

## 第一步：安装 OpenClaw

```bash
npm install -g openclaw@latest
openclaw --version
# 输出：OpenClaw 2026.x.x
```

---

## 第二步：配置 openclaw.json

配置文件路径：`C:\Users\<你的用户名>\.openclaw\openclaw.json`

```json
{
  "models": {
    "providers": {
      "dzzi-sonnet": {
        "baseUrl": "https://api.dzzi.ai/v1",
        "apiKey": "YOUR_SONNET_KEY",
        "models": [
          {
            "id": "[按次]claude-sonnet-4-6",
            "name": "Claude Sonnet 4.6 via dzzi",
            "api": "openai-completions"
          }
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": "dzzi-sonnet/[按次]claude-sonnet-4-6"
    },
    "list": [
      {
        "id": "clawbot",
        "name": "ClawBot",
        "model": "dzzi-sonnet/[按次]claude-sonnet-4-6"
      }
    ]
  },
  "gateway": {
    "mode": "local"
  },
  "channels": {
    "openclaw-weixin": {
      "agentId": "clawbot"
    }
  },
  "plugins": {
    "allow": ["openclaw-weixin"],
    "entries": {
      "openclaw-weixin": {
        "enabled": true
      }
    }
  },
  "commands": {
    "native": "auto",
    "nativeSkills": "auto",
    "restart": true,
    "ownerDisplay": "raw"
  }
}
```

---

## 第三步：配置 .env

路径：`C:\Users\<你的用户名>\.openclaw\.env`

```env
OPENCLAW_GATEWAY_TOKEN=your-token-here
OPENAI_API_KEY=YOUR_MAIN_API_KEY
OPENAI_BASE_URL=https://api.dzzi.ai/v1
OPENCLAW_TZ=Asia/Shanghai
```

---

## 第四步：安装微信插件

```bash
npx -y @tencent-weixin/openclaw-weixin-cli@latest install
```

> 如果 VPS/低内存机器安装失败（OOM），改用本地 Windows 运行：
> ```bash
> openclaw channels login --channel openclaw-weixin
> ```
> 终端显示二维码 → 手机微信扫码 → 凭据自动保存到 `~/.openclaw/openclaw-weixin/`

---

## 第五步：注册为 Windows 后台服务

```bash
openclaw doctor --fix
```

安装完成后会出现：

```
Installed Scheduled Task: OpenClaw Gateway
Task script: C:\Users\...\openclaw\gateway.cmd
```

手动启动：
```powershell
Start-ScheduledTask -TaskName "OpenClaw Gateway"
```

验证：
```bash
curl http://localhost:18789/healthz
# {"ok":true,"status":"live"}
```

---

## 第六步：Cloudflare Tunnel 对外暴露

### 安装 cloudflared

```powershell
Invoke-WebRequest -Uri "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -OutFile "C:\cloudflared.exe"
```

### 登录 & 创建 Tunnel

```bash
cloudflared.exe tunnel login          # 浏览器授权一次
cloudflared.exe tunnel create openclaw-local
```

### 写配置文件

`C:\Users\<你的用户名>\.cloudflared\config.yml`：

```yaml
tunnel: <你的 tunnel-id>
credentials-file: C:\Users\<你的用户名>\.cloudflared\<tunnel-id>.json

ingress:
  - hostname: openclaw.yourdomain.com
    service: http://localhost:18789
  - service: http_status:404
```

### 绑定域名 & 注册服务

```bash
cloudflared.exe tunnel route dns --overwrite-dns openclaw-local openclaw.yourdomain.com

sc.exe config Cloudflared binpath="\"C:\cloudflared.exe\" --config \"C:\Users\<你的用户名>\.cloudflared\config.yml\" tunnel run"
sc.exe start Cloudflared
```

验证：
```bash
curl https://openclaw.yourdomain.com/healthz
# {"ok":true,"status":"live"}
```

---

## 第七步：验证微信连接

Gateway 启动日志里应该看到：

```
[openclaw-weixin] weixin monitor started (https://ilinkai.weixin.qq.com, account=xxx-im-bot)
```

手机微信发消息给绑定的 bot → 应该收到 Claude Opus 的回复。

---

## WebChat 访问

浏览器打开 `https://openclaw.yourdomain.com`，输入 Gateway Token 即可使用内置 WebChat 界面。

---

## 常用命令

```bash
# 查看 gateway 状态
curl http://localhost:18789/healthz

# 验证配置
openclaw config validate

# 查看日志
Get-ScheduledTask -TaskName "OpenClaw Gateway" | Select Name,State

# 重新添加微信账号
openclaw channels login --channel openclaw-weixin
```
