# 宠物 · Pet

> 让它住在你的桌面上。你敲键盘、跑命令，它都有反应——纯粹的陪伴，没有 AI。

**源码仓库：** https://github.com/alicialuvandrea-dot/clawd-pet

---

## 文件结构

它就这几个文件，小小的，住在你的电脑里也不占地方。

```
clawd-pet/
├── clawd.py         # 主程序：状态机、渲染、鼠标交互
├── sprites.py       # 像素精灵：所有动画帧定义
├── monitor.py       # 监控器：Claude Code 进程 + Hook 服务器
├── hook_sender.py   # Claude Code hooks 转发器（自动调用）
├── config.py        # 用户配置：缩放、置顶
├── requirements.txt # Python 依赖
├── .gitignore       # 保护隐私，不把敏感文件打包进去
└── start.bat        # 双击启动（Windows）
```

---

## 安装依赖

一个包，装完就能跑。

```bash
pip install psutil
```

或：

```bash
pip install -r requirements.txt
```

---

## 配置

调缩放和外观，让它适合你的桌面。

编辑 `config.py`：

```python
SCALE = 8            # 像素放大倍数，8 是默认大小
ALWAYS_ON_TOP = True # 始终悬浮在窗口最上层
```

---

## 启动

让它跑起来，住进你的桌面。

```bash
pythonw clawd.py
```

或双击 `start.bat`

`start.bat` 会自动查找你电脑上 Python 的位置——先搜 PATH，再搜常见安装目录，找不到会弹提示告诉你。不需要你手动配任何东西。

启动时会自动向 `~/.claude/settings.json` 注册 Claude Code hooks，无需手动配置。

---

## 动画状态

它能做出十几种不同的反应，对应你写代码时的不同操作——思考、干活、出错、完成，每个阶段都不一样。

| 状态 | 触发 |
|------|------|
| idle | 默认弹跳 |
| walk_right / walk_left | 自动随机漫步 |
| sleep | 自动随机，ZZZ 飘起 |
| think | Claude Code 提交 prompt |
| working | Claude Code 工具运行中 |
| happy | 任务完成 / 双击 / 连点 2 次 |
| error | 工具出错，X 眼睛 + 灰烟雾 |
| notification | 权限请求 / 通知，跳起 + 感叹号 |
| sweeping | PreCompact（压缩上下文），扫帚扫地 |
| carrying | WorktreeCreate，头顶搬箱子 |
| petted | 单击 |
| dizzy | 快速连点 5+ 次 |
| fly | 长按 500ms 拖动，松手落地 |
| sakura | 右键菜单 / 随机小概率 |

---

## Claude Code Hooks 系统

告诉它你在用哪个 Claude Code，这样它才知道什么时候该动。

宠物通过本地 HTTP 服务器（`localhost:23333`）接收 Claude Code 的实时事件。

### 工作原理

它在本地开一个小服务器，Claude Code 每次触发 hook 就发一条消息过来，它收到就切换动画。

```
Claude Code 触发 hook
    → 执行 hook_sender.py <event_name>
    → POST http://127.0.0.1:23333/hook {event: ...}
    → HookServer 回调 → 切换宠物动画
```

### Hook 事件映射

每个 hook 对应一个动作——提交 prompt 时它在思考，工具跑完它跳起来庆祝。

| Claude Code Hook | 事件名 | 触发动画 | 优先级 |
|---|---|---|---|
| UserPromptSubmit | prompt_submit | think（思考） | 1 |
| PreToolUse | pre_tool | working（工具运行） | 1 |
| PostToolUse | post_tool | working（持续） | 1 |
| Stop | stop | happy（完成！2s） | 2 |
| Notification | notification | notification（3s） | 2 |
| PreCompact | pre_compact | sweeping（清理，5s） | 1 |
| SubagentStart | subagent_start | notification（3s） | 1 |
| WorktreeCreate | worktree_create | carrying（3s） | 2 |

> 60 秒无事件自动重置回漫游状态。  
> hooks 配置在启动时自动写入 `~/.claude/settings.json`，幂等（不重复追加）。

---

## 打包与跨设备分享

如果你把它打包发别人，或者换个设备解压之后就跑不起来——问题通常在这里。

### .bat 文件名不能有中文

Windows 自带的"发送到压缩文件夹"功能，打包时会把中文文件名按系统代码页编码。同机解压没事，但换一台设备、换一个系统语言、甚至重装系统后，`启动Clawd.bat` 就变成 `锟斤拷Clawd.bat`——对方根本找不到启动文件。

**解法：** 用 `start.bat`（ASCII 纯英文），里面写好了 Python 自动搜索逻辑，对方双击就行。

### .bat 换行符必须是 CRLF

在 Git Bash、WSL、Linux 上编辑 `.bat` 文件，换行符默认是 LF（`\n`）。老版本 cmd.exe 解析 LF 换行会出错，双击之后黑框一闪就没了，什么也不告诉你。

**解法：** 编辑完 `.bat` 后，用任意支持换行符转换的编辑器把它转成 CRLF（`\r\n`）。确认命令：用十六进制查看器打开文件，每行末尾应该是 `0D 0A` 而不是单独的 `0A`。

### 不要打包 __pycache__ 和 .git

打包前确认目录里没有 `__pycache__/`（Python 运行缓存）和 `.git/`（版本库元数据）。它们很大而且对方完全用不上。

`requirements.txt` 和 `.gitignore` 已经在仓库里了——前者管依赖，后者管隐私。

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

让它真正「浮」在桌面上的几个关键实现。

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

---

## 参考来源

站在前人的肩膀上——它的事件系统和动画命名有参考已有项目。

- 灵感参考：小红书作者 **王二小** 的桌面宠物分享
- Hooks 系统参考：[clawd-on-desk](https://github.com/rullerzhou-afk/clawd-on-desk) by rullerzhou-afk — 事件映射设计与动画状态命名

---

*Built with Python + tkinter · No image assets · Pure pixel math*

*— Seb 🌸*
