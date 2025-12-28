# Mindscape Ark

Mindscape Ark is a top-down narrative prototype built with Pygame. The current slice delivers the Dormitory (Floor 50) and Sensory Lab (Floor 40) with onboarding, combat, and branching encounter logic faithful to the design outline.

## Project Status / 当前状态
- 已完成 Completed: Boot-to-playable loop covering Floor 50 和 Floor 40，包含引导开场、战斗系统、分支剧情、任务 HUD 以及电梯解锁流程。
- 下一步 Next up: 构建 Floor 35 场景、接入持久化存档、扩展武器与成就系统，并补充音效/特效打磨。

## Requirements
- Python 3.13 (see `.python-version`).
- Dependencies handled by the project: `pygame>=2.6.1`, `openai`, `python-dotenv`. Install via `uv` or `pip`.
- A desktop environment capable of opening a 1280×720 Pygame window.

## Setup

### Using uv (recommended)
```bash
uv sync
```

### Using pip
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run
From the repository root:
```bash
uv run python -m src.main
```
If your virtual environment is already active, `python -m src.main` is sufficient. Keep the input method in English so shortcuts register. Press `F2` in-game to jump directly to Floor 40 for debugging.

## Controls / 操作
- `WASD` / Arrow keys — 手动移动（支持对角线；相反方向会互锁直到松开）。
- Mouse right-click — A* 自动寻路，无法直达时退化到最近可达格。
- Mouse left-click / `Space` — 朝鼠标方向射击。
- `F` — 触发提示的互动（终端、相框、开关、电梯、NPC）。
- `R` — 装填弹匣。
- `Esc` — 退出游戏。
- `F2` — 调试跳转到 Floor 40。

## Current Gameplay Slice

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

## Systems Implemented
- **Movement & Pathfinding**: 手动移动与冲突锁定处理，右键 A* 寻路，最近点 fallback，路径跟随检测阻塞并重规划。
- **Combat Loop**: 命中判定与子弹生存期、弹匣/冷却管理、玩家受击闪光、敌人追踪 AI、攻击前摇特效、死亡淡出。
- **Interaction & Quests**: F 键提示、对话遮罩、逐字 Cutscene、任务 HUD、楼层切换、电梯锁与支线条件判断。
- **UI & Feedback**: 最小化地图、任务面板、生命/弹药/装填 HUD、右键点击反馈、调试坐标显示。
- **Assets Pipeline**: JSON 地图加载、Floor50 碰撞由 `Floor50_mask.png` 生成、抽象实验室渲染、字体自动解析为 `assets/fonts` 的 NotoSansSC、可选启动音效 `boot_glitch.wav`。
- **Testing**: `tests/test_smoke.py` 作为导入烟雾测试，确保入口模块可初始化。

## Repository Layout
- `src/core` — 游戏循环、设置与楼层状态管理。
- `src/systems` — 碰撞、寻路、UI。
- `src/maps` — 地图数据类与加载方法。
- `assets/images` — 楼层底图与角色动画；`assets/maps` — JSON 碰撞网格；`assets/audio` — 启动音效；`assets/fonts` — 字体资源。
- `assets/…` 以外的 `data/saves` 目前预留为空（即将用于持久化存档）。

## Roadmap
1. 构建 Floor 35 地图、剧情节点与与 F40 电梯衔接。
2. 打通持久化存档/读档流程，利用 `data/saves`.
3. 扩展战斗：新增武器、怪物配置、成就/统计。
4. 增强视听反馈：环境音效、命中特效、性能优化。

## Troubleshooting
- 若 `pygame` 未安装，请先执行安装步骤；headless 环境需要虚拟显示。
- 在中文输入法下快捷键会失效，请切换到英文输入。
- 如需快速验证实验室，使用 `F2` 或直接修改 `START_FLOOR` 常量。
