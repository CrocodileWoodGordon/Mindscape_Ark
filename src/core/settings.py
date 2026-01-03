"""Centralized configuration values and paths."""

from pathlib import Path
import sys


def get_base_path() -> Path:
    """Resolve writable root for dev + PyInstaller onedir builds."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def get_bundle_path() -> Path:
    """Resolve bundled resource root for PyInstaller onedir/onefile."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return Path(__file__).resolve().parents[2]

# Paths (project root = MindscapeArk)
BASE_DIR = get_base_path()
ASSETS_ROOT = get_bundle_path() / "assets"
IMAGES_DIR = ASSETS_ROOT / "images"
MAPS_DIR = ASSETS_ROOT / "maps"
AUDIO_DIR = ASSETS_ROOT / "audio"
FONTS_DIR = ASSETS_ROOT / "fonts"
DATA_DIR = BASE_DIR / "data"
SAVES_DIR = BASE_DIR / "save"
DEFAULT_MAP_PATH = MAPS_DIR / "floor50.json"
MAP_FILES = {
    "F50": MAPS_DIR / "floor50.json",
    "F40": MAPS_DIR / "floor40.json",
    "F35": MAPS_DIR / "floor35.json",
    "F30": MAPS_DIR / "floor30.json",
    "F25": MAPS_DIR / "floor25.json",
    "F15": MAPS_DIR / "floor15.json",
    "F10": MAPS_DIR / "floor10.json",
    "F0": MAPS_DIR / "floor0.json",
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
PLAYER_WALK_SHEET = IMAGES_DIR / "player_walk_cycle.png"
PLAYER_WALK_FRAMES = 4
PLAYER_WALK_FPS = 8
PLAYER_MAX_HEALTH = 100
PLAYER_HEALTH_BAR_MARGIN = 18
PLAYER_HEALTH_BAR_SIZE = (220, 18)
PLAYER_HEALTH_BAR_BG = (26, 36, 48)
PLAYER_HEALTH_BAR_COLOR = (120, 220, 180)
PLAYER_HEALTH_BAR_BORDER = (200, 235, 250)
PLAYER_REGEN_COOLDOWN = 60.0  # seconds without threats before regen
PLAYER_REGEN_RATE = 1.0  # HP per second when regening
MINIMAP_BG = (10, 12, 16)
MINIMAP_WALKABLE = (60, 140, 200)
MINIMAP_PLAYER = (255, 230, 120)

# Collision/body tuning
PLAYER_COLLIDER_OFFSET_Y = 6  # map pixels; collider sits lower (toward feet)

# Weapon tuning
GUN_BULLET_SPEED = 520  # pixels per second in map space
GUN_FIRE_COOLDOWN = 0.18  # time between shots
GUN_RELOAD_TIME = 1.0
GUN_CLIP_SIZE = 7
GUN_BULLET_LIFETIME = 1.5
GUN_BULLET_RADIUS = 3
GUN_BULLET_COLOR = (255, 235, 120)
PLAYER_BULLET_DAMAGE = 24

# Weapon definitions (per-weapon tuning)
WEAPON_SLOTS = ("sidearm", "scattergun", "entropy_rifle")
DEFAULT_WEAPON = "sidearm"
WEAPON_DEFS = {
    "sidearm": {
        "clip_size": GUN_CLIP_SIZE,
        "fire_cooldown": GUN_FIRE_COOLDOWN,
        "reload_time": GUN_RELOAD_TIME,
        "bullet_speed": GUN_BULLET_SPEED,
        "bullet_lifetime": GUN_BULLET_LIFETIME,
        "bullet_radius": GUN_BULLET_RADIUS,
        "bullet_color": GUN_BULLET_COLOR,
        "damage": PLAYER_BULLET_DAMAGE,
        "pellets": 1,
        "spread_deg": 1.2,
        "auto_fire": False,
    },
    "entropy_rifle": {
        "clip_size": 25,
        "fire_cooldown": 0.12,
        "reload_time": 1.15,
        "bullet_speed": 620,
        "bullet_lifetime": 1.4,
        "bullet_radius": 3,
        "bullet_color": (170, 230, 255),
        "damage": 20,
        "pellets": 1,
        "spread_deg": 3.0,
        "auto_fire": True,
    },
    "scattergun": {
        "clip_size": 5,
        "fire_cooldown": 0.62,
        "reload_time": 1.4,
        "bullet_speed": 470,
        "bullet_lifetime": 1.1,
        "bullet_radius": 2,
        "bullet_color": (255, 200, 160),
        "damage": 14,
        "pellets": 5,
        "spread_deg": 12.0,
        "auto_fire": False,
    },
}

# Boss tuning
BOSS_HP_SCALE_WITH_RIFLE = 1

# Enemies (tutorial placeholders)
ENEMY_COLOR = (255, 120, 140)
ENEMY_RADIUS = 14
ENEMY_HITS_TO_KILL = 2
ENEMY_HIT_FLASH_COLOR = (255, 240, 250)
ENEMY_HIT_FLASH_TIME = 0.18
ENEMY_FADE_DURATION = 0.6
ENEMY_SPAWN_BFS_STEPS = 40
ENEMY_SPAWN_MAX_CELL_DISTANCE = 36
ENEMY_MAX_HEALTH = 60
ENEMY_MOVE_SPEED = 90
ENEMY_AGGRO_RADIUS = 320
ENEMY_LOSE_INTEREST_RADIUS = 360
ENEMY_ATTACK_RANGE = 70
ENEMY_ATTACK_COOLDOWN = 1.4
ENEMY_ATTACK_DAMAGE = 12
ENEMY_ATTACK_FLASH_TIME = 0.2
ENEMY_ATTACK_ANIM_TIME = 0.28
ENEMY_ATTACK_FX_DURATION = 0.45
ENEMY_ATTACK_FX_MAX_RADIUS = 64
ENEMY_HEALTH_BAR_SIZE = (70, 8)
ENEMY_HEALTH_BAR_MARGIN = 24
ENEMY_HEALTH_BAR_BG = (30, 34, 45)
ENEMY_HEALTH_BAR_COLOR = (255, 150, 170)
ENEMY_HEALTH_BAR_BORDER = (250, 250, 255)
ENEMY_HEALTH_BAR_VIS_DURATION = 2.0

# Lab (F40) abstract layout colors
LAB_WALL_COLOR = (12, 16, 24)
LAB_BLOCK_COLORS = [
    (68, 110, 180),
    (72, 150, 190),
    (52, 120, 170),
    (88, 170, 200),
]
LAB_BLOCK_SPAN = 12
LAB_INTERACT_COLORS = {
    "npc": (180, 110, 210),
    "terminal": (110, 210, 200),
    "switch": (220, 190, 120),
    "exit": (150, 220, 255),
}

# Interaction mask
INTERACT_MASKS = {
    "F50": IMAGES_DIR / "Floor50_mask.png",
    "F40": None,
    "F35": None,
    "F30": None,
    "F25": None,
    "F15": None,
    "F10": None,
    "F0": None,
}
INTERACT_MASK_RADIUS = 12  # map pixels radius to consider near a red zone

# Interaction zones (map coordinates, unscaled)
INTERACT_ZONES = {
    "F50": [
        {"id": "elevator", "type": "exit", "rect": (50, 195, 110, 215), "to_floor": "F40"},
        {"id": "family_photo", "type": "frame", "rect": (275, 115, 305, 130)},
        {"id": "log_kaines_001", "type": "terminal", "rect": (190, 89, 305, 140)},
    ],
    "F40": [
        {"id": "lab_exit", "type": "exit", "rect": (464, 464, 560, 560), "to_floor": "F35"},
        {"id": "logic_error_entity", "type": "npc", "rect": (480, 140, 540, 190)},
    ],
    "F35": [
        {"id": "archive_exit", "type": "exit", "rect": (283, 149, 345, 185), "to_floor": "F30"},
        {"id": "log_elara_audio", "type": "terminal", "rect": (300, 200, 350, 240)},
    ],
    "F30": [
        {"id": "logic_weapon_cache", "type": "switch", "rect": (74, 275, 158, 359)},
        {"id": "logic_exit", "type": "exit", "rect": (240, 219, 400, 275), "to_floor": "F25"},
        {"id": "log_ethics_73a", "type": "terminal", "rect": (493, 194, 565, 357)},
        {"id": "logic_server_1", "type": "switch", "rect": (107, 453, 266, 630)},
        {"id": "logic_server_2", "type": "switch", "rect": (107, 652, 266, 837)},
        {"id": "logic_server_3", "type": "switch", "rect": (323, 652, 477, 837)},
        {"id": "logic_server_reset", "type": "switch", "rect": (493, 857, 566, 935)},
    ],
    "F25": [
        {"id": "resonator_exit", "type": "exit", "rect": (148, 6, 172, 42), "to_floor": "F15"},
        {"id": "resonator_npc_anger", "type": "npc", "rect": (84, 58, 126, 126)},
        {"id": "resonator_npc_betrayal", "type": "npc", "rect": (204, 58, 246, 126)},
        {"id": "resonator_npc_confusion", "type": "npc", "rect": (232, 130, 276, 196)},
        {"id": "resonator_npc_despair", "type": "npc", "rect": (192, 200, 232, 272)},
        {"id": "resonator_npc_sadness", "type": "npc", "rect": (88, 200, 128, 272)},
        {"id": "resonator_npc_fear", "type": "npc", "rect": (52, 130, 104, 196)},
        {"id": "resonator_core", "type": "switch", "rect": (148, 140, 172, 184)},
        {"id": "log_kaines_045", "type": "terminal", "rect": (148, 140, 172, 184)},
    ],
    "F15": [
        {"id": "mirror_exit", "type": "exit", "rect": (928, 480, 1008, 548), "to_floor": "F10"},
    ],
    "F10": [
        {"id": "sanctuary_exit", "type": "exit", "rect": (450, 870, 516, 936), "to_floor": "F0"},
        {"id": "aera", "type": "npc", "rect": (465, 477, 513, 525)},
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
PLAYER_HIT_FLASH_TIME = 0.25
PLAYER_HIT_FLASH_COLOR = (255, 80, 120, 140)

# Achievements (story-progress milestones; no rewards attached)
ACHIEVEMENTS = [
    {"id": "boot_sequence", "title": "系统重启", "desc": "完成启动序列与引导，进入行动阶段。"},
    {"id": "anomaly_photo", "title": "相框讯号", "desc": "查看宿舍相框中的异常合影。"},
    {"id": "first_cleanup", "title": "初次清除", "desc": "清除宿舍区首批异常体。"},
    {"id": "anchor_log", "title": "锚定记录", "desc": "读取凯恩斯日志 001。"},
    {"id": "lab_stabilized", "title": "实验室稳定", "desc": "清理感官实验室核心异常并解锁通行。"},
    {"id": "archive_core", "title": "记忆压制", "desc": "击溃记忆吞噬者并完成回闪。"},
    {"id": "archive_phase_three", "title": "红色脉冲", "desc": "记忆核心进入最终暴走阶段。"},
    {"id": "logic_relays", "title": "逻辑复位", "desc": "同步三台服务器，恢复逻辑核心秩序。"},
    {"id": "weapon_cache", "title": "散射火力", "desc": "解锁霰弹枪缓存。"},
    {"id": "resonator_echo", "title": "回声倾听者", "desc": "与六位情绪回声完成对话。"},
    {"id": "resonator_silence", "title": "共鸣平息", "desc": "击败情绪污染源。"},
    {"id": "mirror_shatter", "title": "镜像破碎", "desc": "击败镜像空间的对立体。"},
    {"id": "rifle_claimed", "title": "熵能步枪", "desc": "拾取镜像遗留的步枪。"},
    {"id": "humanitarian", "title": "人道主义", "desc": "拒绝系统指令，守住艾拉与核心装置。"},
    {"id": "efficiency_expert", "title": "效率至上", "desc": "服从指令，使用认知溶解剂。"},
    {"id": "no_damage_clear", "title": "无伤通关", "desc": "在未受到任何伤害的情况下完成本轮迭代。"},
    {"id": "ark_ending", "title": "终章结算", "desc": "完成本轮迭代并看到实验结论。"},
]
ACHIEVEMENT_NOTICE_DURATION = 2.2

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
    "floor35": IMAGES_DIR / "Floor35.png",
    "floor30": IMAGES_DIR / "Floor30.png",
    "floor15": IMAGES_DIR / "Floor15.png",
    "floor10": IMAGES_DIR / "Floor10.png",
}
ARCHIVE_BOSS_IMAGE = IMAGES_DIR / "Floor35_2.png"


# Gameplay placeholders
PASSABLE_VALUES = {0}
