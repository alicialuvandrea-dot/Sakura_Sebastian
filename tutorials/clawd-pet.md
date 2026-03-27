# Clawd 桌面宠物 — Claude Code 官方吉祥物 Python 实现

> 一只跑在桌面上的橙色像素螃蟹，严格1:1还原 Claude Code 官方 logo，纯 Python + tkinter 实现，无任何图片资源。

---

## 文件结构

```
clawd-pet/
├── clawd.py        # 主程序：状态机、渲染、鼠标交互
├── sprites.py      # 像素精灵：所有动画帧定义
├── monitor.py      # 监控器：dzzi.ai 余额 + Claude Code 进程
├── config.py       # 用户配置：API Key / Session Token / 缩放
└── start_clawd.bat # 双击启动（Windows）
```

---

## 安装依赖

```bash
pip install requests psutil
```

---

## 配置

编辑 `config.py`：

```python
DZZI_API_KEY = "YOUR_DZZI_API_KEY"
DZZI_SESSION_TOKEN = ""  # 可选，查不到余额时填入
SCALE = 8
```

获取 Session Token：登录 https://api.dzzi.ai/console/topup → F12 → Application → Local Storage → `token`

---

## 启动

```bash
pythonw clawd.py
```

或双击 `start_clawd.bat`

---

## 动画状态

| 状态 | 触发 |
|------|------|
| idle | 默认弹跳 |
| walk_right / walk_left | 自动随机漫步 |
| sleep | 自动随机，ZZZ 飘起 |
| think | Claude Code 低 CPU |
| working | Claude Code 高 CPU |
| petted | 单击 |
| happy | 双击 / 快速连点 2 次 |
| dizzy | 快速连点 5+ 次 |
| fly | 长按 500ms 拖动，松手落地 |
| eat | dzzi.ai 余额增加 |
| warn | dzzi.ai 余额低于 ¥1 |
| sakura | 右键菜单 / 随机小概率 |

---

## Sprite 结构

```
  BY+0:  .  O  O  O  O  O  .    <- 头顶
  BY+1:  .  O [E] O [E] O  .    <- 眼睛（竖向半格：左眼左黑右橙，右眼左橙右黑）
  BY+2:  C  O  O  O  O  O  C   <- 钳子（BY+2 两侧）
  BY+3:  .  O  O  O  O  O  .    <- 底行
  BY+4:  .  .  L  .  L  .  .   <- 腿（1x1，紧贴底部）
```

SCALE=8，窗口 96x112px，透明悬浮置顶。

---

## 技术要点

**透明窗口（Windows）**
```python
root.overrideredirect(True)
root.attributes("-topmost", True)
root.attributes("-transparentcolor", "#010101")
```

**半格像素渲染**（眼睛用）
```python
# 四元组 (x, y, color, 'L'/'R') 控制半格
half = SCALE // 2
c.create_rectangle(sx, sy, sx+half, sy+SCALE, fill=lc, outline=lc)
c.create_rectangle(sx+half, sy, sx+SCALE, sy+SCALE, fill=rc, outline=rc)
```

**优先级状态机**（0–5，高优先级不被打断）

---

## 参考来源

灵感参考：小红书作者 **王二小** 的桌面宠物分享

---

*Built with Python + tkinter · No image assets · Pure pixel math*
