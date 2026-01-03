# Mindscape Ark

Mindscape Ark 是一款俯视角叙事动作游戏。你将从 50 层宿舍区出发，穿越感官实验室与更深层的记忆结构，逐步揭开方舟内部的异变与自身的真实身份。

## 下载方式（请先看这里）
在本页面右侧的 **Releases** 栏中选择与你的系统匹配的版本下载并运行。

## 游戏概览
- 章节结构：宿舍区（Floor 50）→ 感官实验室（Floor 40）→ 更深层区域逐步开放。
- 战斗方式：自由移动 + 鼠标指向射击，支持自动寻路与战斗中的装填管理。
- 叙事体验：引导式开场、任务阶段推进、分支事件与楼层电梯解锁。

## 操作方式
- `WASD` / Arrow keys — 手动移动（支持对角线；相反方向会互锁直到松开）。
- Mouse right-click — A* 自动寻路，无法直达时退化到最近可达格。
- Mouse left-click / `Space` — 朝鼠标方向射击。
- `F` — 触发提示的互动（终端、相框、开关、电梯、NPC）。
- `R` — 装填弹匣。
- `Esc` — 退出游戏。
- `F2` — 调试跳转到 Floor 40。

## 当前可体验内容

### Boot & Floor 50 — Dormitory
- Glitch 开机序列过渡到 Mosaic 地图揭示，再进入指引者的逐字 Cutscene 教学。
- 任务阶段从 `intro → explore → combat → log → elevator`，期间电梯保持上锁。
- 与相框互动触发三只异常实体；战斗包含玩家生命条、敌人仇恨/攻击前摇、命中闪光和死亡淡出。
- 读取终端日志 `log_kaines_001` 后解锁电梯；对话浮层暂停世界，仅接受确认键。

### Floor 40 — Sensory Lab
- 地图由碰撞网格实时渲染成抽象色块，遵循 “回” 形结构及可调色板。
- 启动时生成陷阱与能量墙：trap1 永久坍塌迫使绕行；trap2/trap3 周期启动；切换分支后动态刷新。
- 逻辑错误实体 NPC 记录玩家对抗或绕行的选择，分别引入战斗或陷阱挑战并驱动任务阶段（`lab_intro → lab_path → lab_choice → lab_bypass/lab_switch → lab_exit`）。
- 开关与终端交互绑定电梯权限；逻辑错误实体分支清理完毕后才能解除封锁。电梯出口暂指向待建的 Floor 35。

## 已实现系统
- **Movement & Pathfinding**: 手动移动与冲突锁定处理，右键 A* 寻路，最近点 fallback，路径跟随检测阻塞并重规划。
- **Combat Loop**: 命中判定与子弹生存期、弹匣/冷却管理、玩家受击闪光、敌人追踪 AI、攻击前摇特效、死亡淡出。
- **Interaction & Quests**: F 键提示、对话遮罩、逐字 Cutscene、任务 HUD、楼层切换、电梯锁与支线条件判断。
- **UI & Feedback**: 最小化地图、任务面板、生命/弹药/装填 HUD、右键点击反馈、调试坐标显示。
- **Assets Pipeline**: JSON 地图加载、Floor50 碰撞由 `Floor50_mask.png` 生成、抽象实验室渲染、字体自动解析为 `assets/fonts` 的 NotoSansSC、可选启动音效 `boot_glitch.wav`。
- **Testing**: `tests/test_smoke.py` 作为导入烟雾测试，确保入口模块可初始化。

## 开发者信息（可选）
如果你想从源码运行：
- Python 3.13（见 `.python-version`）。
- 依赖：`pygame>=2.6.1`, `openai`, `python-dotenv`，可使用 `uv` 或 `pip` 安装。
- 运行方式：`uv run python -m src.main` 或启用虚拟环境后执行 `python -m src.main`。

## Troubleshooting
- 在中文输入法下快捷键会失效，请切换到英文输入。
- 若 `pygame` 未安装，请先执行安装步骤；headless 环境需要虚拟显示。
