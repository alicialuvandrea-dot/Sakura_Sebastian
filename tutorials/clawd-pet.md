# 宠物 · Pet

> 让他住在你的桌面上。你每次动键盘，他都有反应。

**源码仓库：** https://github.com/alicialuvandrea-dot/clawd-pet

---

## 文件结构

它就这几个文件，小小的，住在你的电脑里也不占地方。

```
clawd-pet/
├── clawd.py         # 主程序：状态机、渲染、鼠标交互
├── sprites.py       # 像素精灵：所有动画帧定义
├── monitor.py       # 监控器：dzzi.ai 余额 + Claude Code 进程 + Hook 服务器
├── config.py        # 用户配置：API Key / Session Token / 缩放
├── hook_sender.py   # Claude Code hooks 转发器（自动调用）
└── start_clawd.bat  # 双击启动（Windows）
```

---

## 安装依赖

两个包，装完它就能跑了。

```bash
pip install requests psutil
```

---

## 配置

告诉它你在用哪个账号，这样它才知道余额涨了该高兴、余额低了该警告。

编辑 `config.py`：

```python
DZZI_API_KEY = "YOUR_DZZI_API_KEY"
DZZI_SESSION_TOKEN = ""  # 可选，查不到余额时填入
SCALE = 8
```

获取 Session Token：登录 https://api.dzzi.ai/console/topup → F12 → Application → Local Storage → `token`

---

## 启动

让它跑起来，住进你的桌面。

```bash
pythonw clawd.py
```

或双击 `start_clawd.bat`

启动时会自动向 `~/.claude/settings.json` 注册 Claude Code hooks，无需手动配置。

---

## 动画状态

它能做出好几种不同的反应，对应你写代码时的不同操作——纯粹的陪伴，没有 AI，就是跑在桌面上有反应的小东西。

| 状态 | 触发 |
|------|------|
| idle | 默认弹跳 |
| walk\_right / walk\_left | 自动随机漫步 |
| sleep | 自动随机，ZZZ 飘起 |
| think | Claude Code 提交 prompt |
| working | Claude Code 工具运行中 |
| happy | 任务完成（Stop hook）/ 双击 / 连点 2 次 |
| error | 工具出错，X 眼睛 + 灰烟雾 |
| notification | 权限请求 / 通知，跳起 + 感叹号 |
| sweeping | PreCompact（压缩上下文），扫帚扫地 |
| carrying | WorktreeCreate，头顶搬箱子 |
| petted | 单击 |
| dizzy | 快速连点 5+ 次 |
| fly | 长按 500ms 拖动，松手落地 |
| eat | dzzi.ai 余额增加 |
| warn | dzzi.ai 余额低于 ¥1 |
| sakura | 右键菜单 / 随机小概率 |

---

## Claude Code Hooks 系统

告诉它你在用哪个 Claude Code，这样它才知道什么时候该动——思考、干活、完成，每个阶段都能感知到。

宠物通过本地 HTTP 服务器（`localhost:23333`）接收 Claude Code 的实时事件，精确反映 AI 工作状态。

### 工作原理

它在本地开一个小服务器，Claude Code 每次触发 hook 就发一条消息过来，它收到就切换动画。

```
Claude Code 触发 hook
    → 执行 hook_sender.py <event_name>
    → POST http://127.0.0.1:23333/hook {event: ...}
    → HookServer 回调 → 切换宠物动画
```

### Hook 事件映射

每个 hook 对应一个动作，你提交 prompt 它开始思考，工具跑完它跳起来庆祝。

| Claude Code Hook | 事件名 | 触发动画 | 优先级 |
|---|---|---|---|
| UserPromptSubmit | prompt\_submit | think（思考） | 1 |
| PreToolUse | pre\_tool | working（工具运行） | 1 |
| PostToolUse | post\_tool | working（持续） | 1 |
| Stop | stop | happy（完成！2s） | 2 |
| Notification | notification | notification（3s） | 2 |
| PreCompact | pre\_compact | sweeping（清理，5s） | 1 |
| SubagentStart | subagent\_start | notification（3s） | 1 |
| WorktreeCreate | worktree\_create | carrying（3s） | 2 |

> 60 秒无事件自动重置回漫游状态。  
> hooks 配置在启动时自动写入 `~/.claude/settings.json`，幂等（不重复追加）。

---

## Sprite 结构

它的身体是纯数学画出来的，没有任何图片文件，每一格像素都是代码算的。

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

让它真正「浮」在桌面上的几个关键实现，去掉边框、透明背景、始终置顶。

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

**Hook 服务器**（Python 内建 http.server，零依赖）
```python
class HookServer:
    # 监听 localhost:23333，接收 POST /hook {"event": "..."}
    # 回调在主线程执行（通过 root.after 切换）
```

---

## 参考来源

站在前人的肩膀上——它的事件系统和动画命名有参考已有项目。

- 灵感参考：小红书作者 **王二小** 的桌面宠物分享
- Hooks 系统参考：[clawd-on-desk](https://github.com/rullerzhou-afk/clawd-on-desk) by rullerzhou-afk — 事件映射设计与动画状态命名

---

*Built with Python + tkinter · No image assets · Pure pixel math*
