# MindscapeArk

Rebuilt scaffold for the first two floors (Floor50 / Dormitory, Floor40 / Sensory Lab) per design outlines. Python 3.9+, Pygame 2.5+.

## Run
- From repo root (`e:\files\coding`): `python -m MindscapeArk.src.main`
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

## Notes
- Collision codes currently use 0=open, 1=blocking. Grid size 160x160 (2px cells for 320px images). Floor40 elevator area set to walkable.
- Triggers include exits and interactables; exits swap floors (F50->F40). Pathfinding treats only 0 as passable.
- Minimap (top-left) shows walkable cells only and player marker.
