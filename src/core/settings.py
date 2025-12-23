"""Centralized configuration values and paths."""

from pathlib import Path

# Paths (project root = MindscapeArk)
BASE_DIR = Path(__file__).resolve().parents[2]
ASSETS_ROOT = BASE_DIR / "assets"
IMAGES_DIR = ASSETS_ROOT / "images"
MAPS_DIR = ASSETS_ROOT / "maps"
AUDIO_DIR = ASSETS_ROOT / "audio"
FONTS_DIR = ASSETS_ROOT / "fonts"
DATA_DIR = BASE_DIR / "data"
SAVES_DIR = DATA_DIR / "saves"
DEFAULT_MAP_PATH = MAPS_DIR / "floor50.json"
MAP_FILES = {
    "F50": MAPS_DIR / "floor50.json",
    "F40": MAPS_DIR / "floor40.json",
}
START_FLOOR = "F50"

# Display
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
FPS = 60
WINDOW_TITLE = "Mindscape: Ark"
MAP_SCALE = 3  # upscale map rendering for clarity
MINIMAP_SIZE = 150
MINIMAP_MARGIN = 12

# World
TILE_SIZE = 64
CELL_SIZE = 2
MOVE_STEP = 2
COLLISION_SUBSTEP = 2
PLAYER_SPEED = 180  # pixels per second for path follow

# UI colors/styles
BACKGROUND_COLOR = (8, 10, 18)
TITLE_COLOR = (235, 240, 255)
TITLE_SHADOW_COLOR = (40, 60, 120)
TITLE_GLOW_COLOR = (120, 170, 255)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER_COLOR = (90, 150, 200)
BUTTON_TEXT_COLOR = (250, 250, 255)
MAP_BG_COLOR = (12, 16, 24)
MAP_BLOCK_COLOR = (200, 60, 80)
MAP_WALKABLE_COLOR = (40, 120, 160)
PLAYER_COLOR = (80, 200, 120)
PLAYER_SIZE = (18, 18)
PLAYER_SPRITE = IMAGES_DIR / "player.png"
PLAYER_SCALE = 3
MINIMAP_BG = (10, 12, 16)
MINIMAP_WALKABLE = (60, 140, 200)
MINIMAP_PLAYER = (255, 230, 120)

# Collision/body tuning
PLAYER_COLLIDER_OFFSET_Y = 6  # map pixels; collider sits lower (toward feet)

# Weapon tuning
GUN_BULLET_SPEED = 520  # pixels per second in map space
GUN_FIRE_COOLDOWN = 0.18  # time between shots
GUN_RELOAD_TIME = 1.0
GUN_CLIP_SIZE = 10
GUN_BULLET_LIFETIME = 1.5
GUN_BULLET_RADIUS = 3
GUN_BULLET_COLOR = (255, 235, 120)

# Enemies (tutorial placeholders)
ENEMY_COLOR = (255, 120, 140)
ENEMY_RADIUS = 14
ENEMY_HITS_TO_KILL = 2

# Interaction mask
INTERACT_MASKS = {
    "F50": IMAGES_DIR / "Floor50_mask.png",
    "F40": None,
}
INTERACT_MASK_RADIUS = 12  # map pixels radius to consider near a red zone

# Interaction zones (map coordinates, unscaled)
INTERACT_ZONES = {
    "F50": [
        {"id": "elevator", "type": "exit", "rect": (50, 195, 110, 215), "to_floor": "F40"},
        {"id": "family_photo", "type": "frame", "rect": (275, 115, 305, 130)},
        {"id": "log_kaines_001", "type": "terminal", "rect": (190, 89, 305, 140)},
    ],
}

# Fonts
FONT_CJK = None  # resolved at runtime from fonts directory

# Audio
SOUND_BOOT = AUDIO_DIR / "boot_glitch.wav"

# Interaction UI
INTERACT_RADIUS = 50  # map pixels (pre-scale) within which prompts appear
PROMPT_BG = (12, 16, 20)
PROMPT_TEXT = (240, 245, 255)
PROMPT_BORDER = (80, 160, 220)
DIALOG_BG = (0, 0, 0, 180)
DIALOG_TEXT = (230, 235, 245)
DIALOG_PADDING = 10
DIALOG_OVERLAY_ALPHA = 180
DIALOG_OVERLAY_HEIGHT_RATIO = 0.33
DIALOG_TYPE_SPEED_MIN = 14  # chars per second minimum
DIALOG_TYPE_MAX_DURATION = 2.0  # seconds per line cap

# Quest / tasks
QUEST_BG = (0, 0, 0, 140)
QUEST_TEXT = (220, 230, 240)
QUEST_TITLE = (150, 200, 255)
DIALOG_LIFETIME = 4.0

# Click feedback
CLICK_FEEDBACK_COLOR = (255, 230, 120)
CLICK_FEEDBACK_DURATION = 0.2
CLICK_FEEDBACK_RADIUS = 10  # map pixels (pre-scale)

START_BUTTON_SIZE = (260, 76)
UI_FONT_NAME = None  # use default

# Assets keys
FLOOR_IMAGE_FILES = {
    "floor50": IMAGES_DIR / "Floor50.png",
    "floor40": IMAGES_DIR / "Floor40.png",
}

# Gameplay placeholders
PASSABLE_VALUES = {0}
