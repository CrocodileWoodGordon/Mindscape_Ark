# MindscapeArk

Rebuilt scaffold for the first two floors (Floor50 / Dormitory, Floor40 / Sensory Lab) per design outlines. Python 3.9+, Pygame 2.5+.

## Run
- From repo root : `python -m MindscapeArk.src.main`
- Click Start to enter Floor50. Controls: WASD/Arrow keys manual move (cancels path); Right-click auto-path (A*); Left mouse or Space to fire toward the mouse; F to interact; R to reload; ESC quits; F2 jumps to Floor40 (test). Keep input method in English so shortcuts work.
- Camera stays centered on player; map is scaled up (MAP_SCALE=3).

## Layout
- `assets/images/Floor50.png`, `Floor40.png`: floor visuals (320x320). Map rendering scales by MAP_SCALE.
- `assets/images/player.png`: player sprite (optional). Loaded and scaled by PLAYER_SCALE; falls back to rectangle if missing.
- `assets/maps/floor50.json`, `floor40.json`: collision grids (cell_size=2), triggers, metadata, and image paths.
- `src/core`: settings, game loop.
- `src/maps/loader.py`: loads map JSON into MapData.
- `src/systems/collision.py`: grid collision with sub-steps.
- `src/systems/pathfinding.py`: A* grid pathing.
- `src/systems/ui.py`: start menu.
- `src/main.py`: entrypoint.
- `data/saves/`: save location placeholder.

## Gameplay & systems
- Intro boot reveal flows into a guided cutscene that teaches movement, shooting, auto-path (RMB), interaction, reload, and input-method reminder.
- Quest/task flow with HUD under the minimap: intro -> explore -> elevator. Elevator stays locked until the log is read; updates to "乘坐电梯前往F40" when unlocked.
- Dialog overlay and cutscene typing; space closes dialogs when open. Camera locks during cutscenes.
- Auto font resolution: prefers bundled fonts from `assets/fonts` (e.g., NotoSansSC) before falling back to system fonts.

## Current Progress / 当前进度
- Implemented playable loop for Floor 50 (Dormitory) and Floor 40 (Sensory Lab) with start menu, boot reveal, guided tutorial, quest HUD, and elevator gating aligned with current map data.
  已实现 50 层宿舍与 40 层感官实验室的可玩循环，包含开始菜单、引导演出、任务 HUD 与基于现有地图数据的电梯解锁流程。
- Core movement, interaction, and combat scaffolding are in place: manual WASD movement, right-click A* autop pathing with nearest fallback, shooting/reload cycle, dialog overlay, and minimap/HUD updates.
  核心移动、交互与战斗脚手架已搭建：WASD 手动移动、右键 A* 自动寻路（含最近可达回退）、射击与装填循环、对话叠层以及小地图与 HUD 刷新。
- Floor 50 interactions cover photo frame and terminal logs, unlocking the elevator after reading; Floor 40 currently loads collision/map art but uses placeholder triggers until narrative events are scripted.
  50 层提供相框与终端日志交互，阅读后可解锁电梯；40 层目前能载入碰撞与地图贴图，但剧情事件仍为占位触发，尚未补全。
- Enemy spawn hooks, multi-floor progression beyond F40, branching choices, achievement/perk systems, and save/data management are not yet implemented.
  敌人刷怪流程、F40 之后的多楼层推进、分支抉择、成就/被动系统与存档数据管理尚未落地。

## Notes
- Collision codes currently use 0=open, 1=blocking. Grid size 160x160 (2px cells for 320px images). Floor40 elevator area set to walkable.
- Triggers include exits and interactables; exits swap floors (F50->F40). Pathfinding treats only 0 as passable.
- Minimap (top-left) shows walkable cells only and player marker.
