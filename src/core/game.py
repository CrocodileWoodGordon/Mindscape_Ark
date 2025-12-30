"""Game lifecycle: start menu -> floor view."""

import sys
from pathlib import Path
import random
import math
from collections import deque

import pygame

from . import settings
from ..systems.ui import StartMenu
from ..maps.loader import load_map, MapData
from ..systems import collision
from ..systems import pathfinding


class Game:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT))
        pygame.display.set_caption(settings.WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.start_menu = StartMenu(self.screen)
        self.in_menu = True

        self.map_data: MapData | None = None
        self.map_surface: pygame.Surface | None = None
        self.map_offset = (0, 0)
        self._base_collision_grid: list[list[int]] = []
        self.lab_surface: pygame.Surface | None = None
        self.player_rect = pygame.Rect(0, 0, *settings.PLAYER_SIZE)  # map-space rect
        self._player_idle_sprite = self._load_player_sprite()
        self._player_walk_frames = self._load_player_walk_frames()
        self.player_sprite: pygame.Surface | None = self._default_player_sprite()
        self._player_anim_index = 0
        self._player_anim_timer = 0.0
        self._player_was_moving = False
        self.path: list[tuple[int, int]] = []  # list of map-cell nodes
        self.path_target: tuple[int, int] | None = None
        self.path_goal_cell: tuple[int, int] | None = None
        self.player_move_speed = float(settings.PLAYER_SPEED)
        self.speed_bonus = 1.0
        self.interaction_target: dict | None = None
        self.dialog_lines: list[str] = []
        self.dialog_timer: float = 0.0
        self.click_fx_pos: tuple[int, int] | None = None
        self.click_fx_timer: float = 0.0
        self._conflict_x = False
        self._conflict_y = False
        self._keys_down: set[int] = set()
        self._held_dirs = {"left": False, "right": False, "up": False, "down": False}
        self.bullets: list[dict] = []
        self.enemies: list[dict] = []
        self.combat_active = False
        self.ammo_in_clip = settings.GUN_CLIP_SIZE
        self.reload_timer = 0.0
        self.fire_cooldown = 0.0
        self.interact_mask: pygame.Surface | None = None
        self.dialog_title: str = ""
        self.intro_active = False
        self.intro_phase = ""
        self.intro_timer = 0.0
        self.reveal_progress = 0.0
        self.player_fade = 0.0
        self.boot_sound: pygame.mixer.Sound | None = None
        self.cutscene_active = False
        self.cutscene_lines: list[dict] = []
        self.cutscene_idx = 0
        self.cutscene_char_progress = 0.0
        self.cutscene_done_line = False
        self.cutscene_started = False
        self.enemy_attack_fx: list[dict] = []
        self.player_hit_timer = 0.0
        self.player_health_max = settings.PLAYER_MAX_HEALTH
        self.player_health = float(self.player_health_max)
        self.player_dead = False
        self.regen_cooldown = 0.0
        self.regen_active = False
        self.any_enemy_aggro = False
        self.dynamic_blockers: list[pygame.Rect] = []
        self.floor_flags: dict[str, bool] = {}
        self.floor_timers: dict[str, float] = {}
        self.lab_traps: list[dict] = []
        self.lab_barriers: list[dict] = []
        self.lab_npc_state: dict[str, dict] = {}
        self.lab_branch = ""
        self.archive_center = (0.0, 0.0)
        self.archive_core_radius = 0.0
        self.archive_warning_radius = 0.0
        self.archive_boss: dict | None = None
        self.archive_flags: dict[str, bool] = {}
        self.archive_projectiles: list[dict] = []
        self.archive_flash_sequence: list[dict] = []
        self.archive_pulse_state: dict[str, float] = {}
        self.archive_boss_sprite: pygame.Surface | None = self._load_archive_boss_sprite()
        self.archive_flash_active = False
        self.archive_flash_step = 0
        self.archive_flash_timer = 0.0
        self.archive_minor_spawn_timer = 0.0
        self.resonator_assets: dict[str, pygame.Surface] = {}
        self.resonator_state: dict[str, object] = {}
        self.resonator_projectiles: list[dict] = []
        self.logic_flags: dict[str, bool] = {}
        self.logic_sequence: list[str] = []
        self.logic_progress: list[str] = []
        self.logic_glitch_timer = 0.0
        self.logic_overlay_timer = 0.0
        self.logic_overlay_text = ""
        self.logic_relay_positions: dict[str, tuple[float, float]] = {}
        self.debug_press_times: list[float] = []
        self.debug_menu_active = False
        self.debug_menu_options: list[tuple[str, str]] = []
        self.debug_menu_index = 0
        self.quest_stage = "intro"  # Ensure quest stage reset in _load_floor
        self.elevator_locked = True

        self.font_path = self._resolve_font()
        self.font_prompt = self._load_font(18)
        self.font_dialog = self._load_font(20)

        self.current_floor = settings.START_FLOOR
        self._load_floor(settings.MAP_FILES[self.current_floor], preserve_health=False)

    def _load_floor(self, path: Path, *, preserve_health: bool = True) -> None:
        prev_health = float(getattr(self, "player_health", settings.PLAYER_MAX_HEALTH))
        self.map_data = load_map(path)
        self.debug_menu_active = False
        self.debug_press_times.clear()
        self.debug_menu_options = []
        self.debug_menu_index = 0
        self._base_collision_grid = [row[:] for row in self.map_data.collision_grid]
        self.map_surface = self._build_map_surface(self.map_data)
        map_w, map_h = self.map_surface.get_size()
        self.map_offset = (
            (settings.WINDOW_WIDTH - map_w) // 2,
            (settings.WINDOW_HEIGHT - map_h) // 2,
        )
        spawn_x, spawn_y = self.map_data.spawn_player
        # spawn is in pixels relative to map; scale to render space
        self.player_rect.center = (int(spawn_x * settings.MAP_SCALE), int(spawn_y * settings.MAP_SCALE))
        self.player_move_speed = float(settings.PLAYER_SPEED) * float(getattr(self, "speed_bonus", 1.0))
        self.path = []
        self.path_target = None
        self.path_goal_cell = None
        self.interaction_target = None
        self.dialog_lines = []
        self.dialog_timer = 0.0
        self.click_fx_pos = None
        self.click_fx_timer = 0.0
        self._conflict_x = False
        self._conflict_y = False
        self._keys_down.clear()
        self._held_dirs = {"left": False, "right": False, "up": False, "down": False}
        self.bullets.clear()
        self.enemies.clear()
        self.combat_active = False
        self.ammo_in_clip = settings.GUN_CLIP_SIZE
        self.reload_timer = 0.0
        self.fire_cooldown = 0.0
        self.dialog_title = ""
        self.intro_active = False
        self.intro_phase = ""
        self.intro_timer = 0.0
        self.reveal_progress = 0.0
        self.player_fade = 0.0
        self.cutscene_active = False
        self.cutscene_lines = []
        self.cutscene_idx = 0
        self.cutscene_char_progress = 0.0
        self.cutscene_done_line = False
        self.cutscene_started = False
        self.enemy_attack_fx = []
        self.player_hit_timer = 0.0
        self.player_health_max = settings.PLAYER_MAX_HEALTH
        if preserve_health:
            new_health = max(0.0, min(prev_health, float(self.player_health_max)))
            self.player_health = new_health
            self.player_dead = new_health <= 0.0
        else:
            self.player_health = float(self.player_health_max)
            self.player_dead = False
        self.regen_cooldown = 0.0
        self.regen_active = False
        self.any_enemy_aggro = False
        self.dynamic_blockers = []
        self.floor_flags = {}
        self.floor_timers = {}
        self.lab_traps = []
        self.lab_barriers = []
        self.lab_npc_state = {}
        self.lab_branch = ""
        self.archive_center = (0.0, 0.0)
        self.archive_core_radius = 0.0
        self.archive_warning_radius = 0.0
        self.archive_boss: dict | None = None
        self.archive_flags: dict[str, bool] = {}
        self.lab_surface = None
        self.archive_boss = None
        self.archive_flags = {}
        self.archive_projectiles = []
        self.resonator_projectiles = []
        self.resonator_state = {}
        self.archive_flash_sequence = []
        self.archive_pulse_state = {}
        self.archive_flash_active = False
        self.archive_flash_step = 0
        self.archive_flash_timer = 0.0
        self.archive_minor_spawn_timer = 0.0
        if self.archive_boss_sprite is None:
            self.archive_boss_sprite = self._load_archive_boss_sprite()
        self.logic_flags = {}
        self.logic_sequence = []
        self.logic_progress = []
        self.logic_glitch_timer = 0.0
        self.logic_overlay_timer = 0.0
        self.logic_overlay_text = ""
        self.logic_relay_positions = {}
        self.quest_stage = "intro"
        self.elevator_locked = True
        self.font_path = self._resolve_font()
        self.font_prompt = self._load_font(18)
        self.font_dialog = self._load_font(20)
        self.player_sprite = self._default_player_sprite()
        self._player_anim_index = 0
        self._player_anim_timer = 0.0
        self._player_was_moving = False
        mask_path = settings.INTERACT_MASKS.get(self.current_floor)
        if mask_path and mask_path.exists():
            mask = pygame.image.load(str(mask_path)).convert_alpha()
            self.interact_mask = mask
        else:
            self.interact_mask = None
        # Boot sound (optional)
        self.boot_sound = None
        if settings.SOUND_BOOT.exists() and settings.SOUND_BOOT.stat().st_size > 0:
            try:
                self.boot_sound = pygame.mixer.Sound(str(settings.SOUND_BOOT))
            except Exception:
                self.boot_sound = None

        self._on_floor_loaded()

    def _build_map_surface(self, data: MapData) -> pygame.Surface:
        # If an image exists, load and return it; otherwise draw collision blocks
        if data.image_path and data.image_path.exists():
            image = pygame.image.load(str(data.image_path)).convert()
            if settings.MAP_SCALE != 1:
                w, h = image.get_size()
                image = pygame.transform.scale(image, (int(w * settings.MAP_SCALE), int(h * settings.MAP_SCALE)))
            return image
        cell = data.cell_size
        surf = pygame.Surface((int(data.grid_size[0] * cell * settings.MAP_SCALE), int(data.grid_size[1] * cell * settings.MAP_SCALE)))
        surf.fill(settings.MAP_BG_COLOR)
        for y, row in enumerate(data.collision_grid):
            for x, val in enumerate(row):
                if val == 1:
                    pygame.draw.rect(
                        surf,
                        settings.MAP_BLOCK_COLOR,
                        (x * cell * settings.MAP_SCALE, y * cell * settings.MAP_SCALE, cell * settings.MAP_SCALE, cell * settings.MAP_SCALE),
                    )
        return surf

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self._handle_event(event)

            self._update(dt)
            self._render()

        pygame.quit()
        sys.exit(0)

    def _handle_event(self, event: pygame.event.Event) -> None:
        if self.in_menu:
            if self.start_menu.handle_event(event):
                self.in_menu = False
                self._start_intro()
            return
        if self.intro_active:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
            return
        if self.cutscene_active:
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self._advance_cutscene()
            return
        if self.debug_menu_active:
            self._handle_debug_menu_event(event)
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKQUOTE and not self.debug_menu_active:
                self._register_debug_keypress()
                if self.debug_menu_active:
                    return
            if event.key == pygame.K_ESCAPE:
                self.running = False
                return
            if self.player_dead:
                if event.key == pygame.K_RETURN:
                    self._restart_to_menu()
                elif event.key == pygame.K_F2:
                    self.current_floor = "F40"
                    self._load_floor(settings.MAP_FILES[self.current_floor], preserve_health=False)
                return
            if self.dialog_lines:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                    self._dismiss_dialog()
                return
            if event.key == pygame.K_F2:
                # Quick swap to Floor40 for testing
                self.current_floor = "F40"
                self._load_floor(settings.MAP_FILES[self.current_floor])
            if event.key == pygame.K_f and self.interaction_target:
                self._activate_interaction(self.interaction_target)
            if event.key == pygame.K_r:
                self._start_reload()
            if event.key == pygame.K_SPACE:
                if self.dialog_lines:
                    self._dismiss_dialog()
                    return
                self._try_fire()
            self._keys_down.add(event.key)
            if event.key in (pygame.K_a, pygame.K_LEFT):
                self._held_dirs["left"] = True
            if event.key in (pygame.K_d, pygame.K_RIGHT):
                self._held_dirs["right"] = True
            if event.key in (pygame.K_w, pygame.K_UP):
                self._held_dirs["up"] = True
            if event.key in (pygame.K_s, pygame.K_DOWN):
                self._held_dirs["down"] = True
        if event.type == pygame.KEYUP:
            if event.key in self._keys_down:
                self._keys_down.discard(event.key)
            if event.key in (pygame.K_a, pygame.K_LEFT):
                self._held_dirs["left"] = False
            if event.key in (pygame.K_d, pygame.K_RIGHT):
                self._held_dirs["right"] = False
            if event.key in (pygame.K_w, pygame.K_UP):
                self._held_dirs["up"] = False
            if event.key in (pygame.K_s, pygame.K_DOWN):
                self._held_dirs["down"] = False
        if event.type == pygame.WINDOWFOCUSLOST:
            # Clear held keys on focus loss to avoid stuck movement
            self._keys_down.clear()
            for k in self._held_dirs:
                self._held_dirs[k] = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.player_dead or self.dialog_lines:
                return
            if event.button == 1:
                self._try_fire()
            if event.button == 3:
                self._handle_right_click(event.pos)

    def _update(self, dt: float) -> None:
        if self.in_menu:
            self.start_menu.update(dt)
        elif self.intro_active:
            self._update_intro(dt)
        elif self.cutscene_active:
            self._update_cutscene(dt)
        else:
            self._update_play(dt)
        self._update_dialog(dt)

    def _update_play(self, dt: float) -> None:  # noqa: ARG002
        if not self.map_data:
            return
        if self.debug_menu_active:
            self.interaction_target = None
            self._update_camera()
            return
        if self.dialog_lines:
            self.interaction_target = None
            self._update_camera()
            return
        if self.player_dead:
            self._update_bullets(dt)
            self._update_enemies(dt)
            self._update_enemy_attack_fx(dt)
            if self.player_hit_timer > 0.0:
                self.player_hit_timer = max(0.0, self.player_hit_timer - dt)
            self.interaction_target = None
            self._update_camera()
            return
        # Ensure key state is refreshed even if no new events arrived this frame
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        manual_dx, manual_dy = self._manual_axis(keys, dt)
        moved = False

        if manual_dx or manual_dy:
            self.path = []
            self.path_target = None
            self.path_goal_cell = None
            moved = self._move_player(manual_dx, manual_dy)
        elif self.path:
            moved = self._follow_path(dt)

        self._update_player_animation(moved, dt)

        self._update_bullets(dt)
        self._update_enemies(dt)
        self._update_enemy_attack_fx(dt)
        if self.player_hit_timer > 0.0:
            self.player_hit_timer = max(0.0, self.player_hit_timer - dt)

        self._update_floor_logic(dt)
        self._update_player_regen(dt)
        self._update_interaction_prompt()

        self._update_camera()
        self._check_triggers()

    def _update_player_regen(self, dt: float) -> None:
        if self.player_dead:
            self.regen_active = False
            return
        if self.player_health >= self.player_health_max:
            self.player_health = float(self.player_health_max)
            self.regen_active = False
            self.regen_cooldown = 0.0
            return
        if self.any_enemy_aggro:
            self._reset_regen_cooldown()
            return
        if self.regen_cooldown > 0.0:
            self.regen_cooldown = max(0.0, self.regen_cooldown - dt)
            if self.regen_cooldown == 0.0:
                self.regen_active = True
        if self.regen_active:
            heal = settings.PLAYER_REGEN_RATE * dt
            if heal > 0.0:
                self.player_health = min(self.player_health_max, self.player_health + heal)
            if self.player_health >= self.player_health_max:
                self.player_health = float(self.player_health_max)
                self.regen_active = False
                self.regen_cooldown = 0.0

    def _check_triggers(self) -> None:
        if not self.map_data:
            return
        px = self.player_rect.centerx
        py = self.player_rect.centery
        for trig in self.map_data.triggers:
            # exit interactions now handled via prompt + F key
            continue

    def _on_floor_loaded(self) -> None:
        self.dynamic_blockers = []
        self.floor_flags = {}
        self.floor_timers = {}
        self.lab_traps = []
        self.lab_barriers = []
        self.lab_npc_state = {}
        self.lab_branch = ""
        self.archive_center = (0.0, 0.0)
        self.archive_core_radius = 0.0
        self.archive_warning_radius = 0.0
        self.archive_boss: dict | None = None
        self.archive_flags: dict[str, bool] = {}
        self.lab_surface = None
        if not self.map_data:
            return
        if self._base_collision_grid:
            for y, row in enumerate(self._base_collision_grid):
                if y < len(self.map_data.collision_grid):
                    self.map_data.collision_grid[y] = row[:]  # restore base grid snapshot
        if self.current_floor == "F40":
            self._enter_floor_f40()
        elif self.current_floor == "F35":
            self._enter_floor_f35()
        elif self.current_floor == "F30":
            self._enter_floor_f30()
        elif self.current_floor == "F25":
            self._enter_floor_f25()
        else:
            self._enter_floor_default()

    def _enter_floor_default(self) -> None:
        if self.current_floor == "F50":
            self._set_quest_stage("intro")

    def _enter_floor_f35(self) -> None:
        if not self.map_data:
            return
        width, height = self.map_data.size_pixels
        if not width or not height:
            if self.map_surface:
                w, h = self.map_surface.get_size()
                width = w // max(1, settings.MAP_SCALE)
                height = h // max(1, settings.MAP_SCALE)
            else:
                width = height = 0
        self.archive_center = (width / 2.0, height / 2.0)
        self.archive_core_radius = 120.0
        self.archive_warning_radius = 220.0
        self.archive_boss = None
        self.archive_projectiles = []
        self.archive_flash_sequence = []
        self.archive_pulse_state = {
            "timer": 4.0,
            "interval": 5.0,
            "warning": 1.6,
            "duration": 1.0,
            "phase": "idle",
        }
        self.archive_flash_active = False
        self.archive_flash_step = 0
        self.archive_flash_timer = 0.0
        self.archive_minor_spawn_timer = 2.4
        self.archive_flags = {
            "intro_dialog_shown": False,
            "hum_prompt_shown": False,
            "boss_revealed": False,
            "phase_two_started": False,
            "phase_three_started": False,
            "flash_started": False,
            "flash_complete": False,
            "exit_unlocked": False,
            "log_available": False,
            "pulse_cover_prompt": False,
        }
        self.combat_active = False
        self._set_quest_stage("archive_intro")
        self.floor_timers["archive_intro_delay"] = 0.6
        self.floor_timers.pop("archive_hum_delay", None)
        self.floor_timers.pop("archive_flash_delay", None)
        self.elevator_locked = True

    def _enter_floor_f30(self) -> None:
        self.logic_flags = {
            "intro_shown": False,
            "glitch_triggered": False,
            "relays_completed": False,
            "weapon_ready": False,
            "weapon_claimed": False,
            "exit_unlocked": False,
            "terminal_ready": False,
        }
        self.logic_sequence = ["relay_left", "relay_right", "relay_center"]
        self.logic_progress = []
        self.logic_glitch_timer = 0.0
        self.logic_overlay_timer = 0.0
        self.logic_overlay_text = ""
        self.logic_relay_positions = {
            "relay_left": (212.0, 316.0),
            "relay_right": (428.0, 316.0),
            "relay_center": (320.0, 272.0),
        }
        self.elevator_locked = True
        self._set_quest_stage("logic_intro")
        self.floor_timers["logic_intro_delay"] = 0.6

    def _enter_floor_f25(self) -> None:
        if not self.map_data:
            return
        width, height = self.map_data.size_pixels
        if not width or not height:
            if self.map_surface:
                w, h = self.map_surface.get_size()
                width = w // max(1, settings.MAP_SCALE)
                height = h // max(1, settings.MAP_SCALE)
            else:
                width = height = 0
        center = (width / 2.0, height / 2.0)
        self.resonator_state = {
            "intro_timer": 0.6,
            "intro_shown": False,
            "npc_dialogues": {},
            "npc_total": 6,
            "npc_spoken": 0,
            "buff_awarded": bool(getattr(self, "speed_bonus", 1.0) > 1.0),
            "boss_state": "dormant",
            "boss_hp": 280.0,
            "boss_max_hp": 280.0,
            "boss_phase": 0,
            "boss_fire_timer": 2.4,
            "boss_flash": 0.0,
            "color_cycle": ["anger", "sadness", "fear"],
            "color_index": 0,
            "color_timer": 0.0,
            "color_duration": 3.0,
            "orb_flash": 0.0,
            "log_available": False,
            "exit_unlocked": False,
            "speed_buff": float(getattr(self, "speed_bonus", 1.0)),
            "slow_timer": 0.0,
            "slow_factor": 0.7,
            "center": center,
        }
        self.resonator_projectiles = []
        self.elevator_locked = True
        self._resonator_load_assets()
        self.resonator_state["npcs"] = self._resonator_entities()
        self._set_quest_stage("resonator_intro")
        self.floor_timers["resonator_intro_delay"] = 0.6

    def _enter_floor_f40(self) -> None:
        self._set_quest_stage("lab_intro")
        self.floor_flags.update({
            "lab_intro_line": False,
            "lab_trap1_triggered": False,
            "lab_trap1_resolved": False,
            "lab_branch_resolved": False,
            "lab_switch_activated": False,
            "lab_bypass_spawns": False,
        })
        self.floor_timers["lab_intro_delay"] = 0.5
        self.lab_traps = []
        self.lab_barriers = []
        self.lab_branch = ""
        self.archive_center = (0.0, 0.0)
        self.archive_core_radius = 0.0
        self.archive_warning_radius = 0.0
        self.archive_boss: dict | None = None
        self.archive_flags: dict[str, bool] = {}
        self.lab_npc_state = {}
        self._lab_init_traps()
        self._lab_refresh_surface()

    def _lab_unit_scale(self) -> int:
        if not self.map_data:
            return 1
        width = max(1, self.map_data.grid_size[0])
        return max(1, width // 40)

    def _lab_cells_from_units(self, ux: float, uy: float, uw: float, uh: float) -> list[tuple[int, int]]:
        if not self.map_data:
            return []
        scale = self._lab_unit_scale()
        grid = self.map_data.collision_grid
        x1 = int(ux * scale)
        x2 = int((ux + uw) * scale)
        y1 = int(uy * scale)
        y2 = int((uy + uh) * scale)
        cells: list[tuple[int, int]] = []
        for cy in range(y1, y2):
            if cy < 0 or cy >= len(grid):
                continue
            row = grid[cy]
            for cx in range(x1, x2):
                if 0 <= cx < len(row):
                    cells.append((cy, cx))
        return cells

    def _lab_rect_from_cells(self, cells: list[tuple[int, int]]) -> pygame.Rect:
        if not cells or not self.map_data:
            return pygame.Rect(0, 0, 0, 0)
        min_y = min(cy for cy, _ in cells)
        max_y = max(cy for cy, _ in cells)
        min_x = min(cx for _, cx in cells)
        max_x = max(cx for _, cx in cells)
        cell_px = self.map_data.cell_size
        return pygame.Rect(
            min_x * cell_px,
            min_y * cell_px,
            (max_x - min_x + 1) * cell_px,
            (max_y - min_y + 1) * cell_px,
        )

    def _lab_units_to_display_pos(self, ux: float, uy: float) -> tuple[float, float]:
        if not self.map_data:
            return (0.0, 0.0)
        scale_units = self._lab_unit_scale() * self.map_data.cell_size
        base_x = (ux * scale_units) + (scale_units * 0.5)
        base_y = (uy * scale_units) + (scale_units * 0.5)
        s = settings.MAP_SCALE
        return (base_x * s, base_y * s)

    def _lab_init_traps(self) -> None:
        if not self.map_data:
            return
        self.lab_traps = []
        trap1_cells = self._lab_cells_from_units(5, 1, 3, 2)
        trap2_cells = self._lab_cells_from_units(1, 5, 2, 3)
        trap3_cells = self._lab_cells_from_units(5, 10, 3, 2)
        self.lab_traps.append({
            "id": "trap1",
            "cells": trap1_cells,
            "rect": self._lab_rect_from_cells(trap1_cells),
            "state": "idle",
            "timer": 0.0,
            "void_duration": 2.0,
            "cycle_interval": 0.0,
            "active": True,
            "permanent": True,
            "sealed_announced": False,
        })
        self.lab_traps.append({
            "id": "trap2",
            "cells": trap2_cells,
            "rect": self._lab_rect_from_cells(trap2_cells),
            "state": "idle",
            "timer": 3.0,
            "void_duration": 1.4,
            "cycle_interval": 3.6,
            "active": False,
            "permanent": False,
            "sealed_announced": False,
        })
        self.lab_traps.append({
            "id": "trap3",
            "cells": trap3_cells,
            "rect": self._lab_rect_from_cells(trap3_cells),
            "state": "idle",
            "timer": 2.4,
            "void_duration": 1.6,
            "cycle_interval": 4.2,
            "active": False,
            "permanent": False,
            "sealed_announced": False,
        })
        for trap in self.lab_traps:
            self._lab_set_cells(trap["cells"], False)
        self.lab_barriers = []

    def _lab_refresh_surface(self) -> None:
        if not self.map_data:
            self.lab_surface = None
            return
        cell_px = self.map_data.cell_size * settings.MAP_SCALE
        width = self.map_data.grid_size[0] * cell_px
        height = self.map_data.grid_size[1] * cell_px
        surf = pygame.Surface((width, height))
        surf.fill(settings.LAB_WALL_COLOR)
        colors = list(getattr(settings, "LAB_BLOCK_COLORS", []))
        if not colors:
            colors = [(70, 110, 160)]
        block_span = max(1, getattr(settings, "LAB_BLOCK_SPAN", 12))
        for y, row in enumerate(self.map_data.collision_grid):
            for x, val in enumerate(row):
                if val not in settings.PASSABLE_VALUES:
                    continue
                block_index = ((x // block_span) + (y // block_span)) % len(colors)
                color = colors[block_index]
                rect = pygame.Rect(x * cell_px, y * cell_px, cell_px, cell_px)
                surf.fill(color, rect)
        interact_colors = getattr(settings, "LAB_INTERACT_COLORS", {})
        for trig in settings.INTERACT_ZONES.get("F40", []):
            color = interact_colors.get(trig.get("type", ""))
            if not color:
                continue
            x1, y1, x2, y2 = trig["rect"]
            scaled_rect = pygame.Rect(
                int(x1 * settings.MAP_SCALE),
                int(y1 * settings.MAP_SCALE),
                max(1, int((x2 - x1) * settings.MAP_SCALE)),
                max(1, int((y2 - y1) * settings.MAP_SCALE)),
            )
            surf.fill(color, scaled_rect)
        self.lab_surface = surf.convert()
        self.map_surface = self.lab_surface
        map_w, map_h = self.map_surface.get_size()
        self.map_offset = (
            (settings.WINDOW_WIDTH - map_w) // 2,
            (settings.WINDOW_HEIGHT - map_h) // 2,
        )

    def _lab_set_cells(self, cells: list[tuple[int, int]], solid: bool) -> None:
        if not self.map_data:
            return
        grid = self.map_data.collision_grid
        base = self._base_collision_grid
        for cy, cx in cells:
            if cy < 0 or cy >= len(grid):
                continue
            row = grid[cy]
            if cx < 0 or cx >= len(row):
                continue
            if solid:
                row[cx] = 1
            else:
                if base and cy < len(base) and cx < len(base[cy]):
                    row[cx] = base[cy][cx]
                else:
                    row[cx] = 0

    def _lab_trigger_trap(self, trap_id: str) -> None:
        if trap_id == "trap1":
            # Keep second-layer layout stable; skip the old path collapse.
            self.floor_flags["lab_trap1_resolved"] = True
            return
        for trap in self.lab_traps:
            if trap.get("id") == trap_id:
                if trap.get("state") == "void":
                    return
                trap["state"] = "void"
                trap["timer"] = trap.get("void_duration", 1.0)
                self._lab_set_cells(trap["cells"], True)
                break

    def _lab_update_traps(self, dt: float) -> None:
        for trap in self.lab_traps:
            if not trap.get("active"):
                continue
            state = trap.get("state")
            if state == "void":
                trap["timer"] = max(0.0, trap.get("timer", 0.0) - dt)
                if trap["timer"] <= 0.0:
                    if trap.get("permanent"):
                        trap["state"] = "sealed"
                        self._lab_set_cells(trap["cells"], True)
                        if not trap.get("sealed_announced"):
                            trap["sealed_announced"] = True
                            self.floor_flags["lab_trap1_resolved"] = True
                            self._show_dialog(["指引者：主干道塌陷，改道进入外圈。"], title="指引者")
                    else:
                        trap["state"] = "idle"
                        self._lab_set_cells(trap["cells"], False)
                        trap["timer"] = trap.get("cycle_interval", 0.0)
            elif trap.get("cycle_interval", 0.0) > 0.0:
                trap["timer"] = max(0.0, trap.get("timer", 0.0) - dt)
                if trap["timer"] <= 0.0:
                    trap["state"] = "void"
                    trap["timer"] = trap.get("void_duration", 1.0)
                    self._lab_set_cells(trap["cells"], True)

    def _draw_lab_traps(self) -> None:
        if not self.lab_traps:
            return
        scale = settings.MAP_SCALE
        for trap in self.lab_traps:
            state = trap.get("state")
            if state in {"idle"} or not trap.get("rect"):
                continue
            rect = trap["rect"]
            draw_rect = pygame.Rect(
                int(rect.x * scale + self.map_offset[0]),
                int(rect.y * scale + self.map_offset[1]),
                int(rect.width * scale),
                int(rect.height * scale),
            )
            if draw_rect.width <= 0 or draw_rect.height <= 0:
                continue
            surf = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
            if state == "void":
                color = (180, 40, 120, 160)
            elif state == "sealed":
                color = (80, 20, 110, 200)
            else:
                color = (110, 30, 140, 140)
            surf.fill(color)
            pygame.draw.rect(surf, (255, 160, 240, 220), surf.get_rect(), 2)
            self.screen.blit(surf, draw_rect.topleft)

    def _draw_lab_barriers(self) -> None:
        if not self.lab_barriers:
            return
        scale = settings.MAP_SCALE
        for barrier in self.lab_barriers:
            rect = barrier.get("rect")
            if not rect:
                continue
            draw_rect = pygame.Rect(
                int(rect.x * scale + self.map_offset[0]),
                int(rect.y * scale + self.map_offset[1]),
                int(rect.width * scale),
                int(rect.height * scale),
            )
            surf = pygame.Surface(draw_rect.size, pygame.SRCALPHA)
            surf.fill((40, 160, 220, 140))
            pygame.draw.rect(surf, (120, 220, 255, 220), surf.get_rect(), 3)
            self.screen.blit(surf, draw_rect.topleft)

    def _draw_lab_environment(self) -> None:
        self._draw_lab_traps()
        self._draw_lab_barriers()

    def _draw_archive_elements(self) -> None:
        if self.archive_projectiles:
            self._draw_archive_projectiles()
        if self.archive_boss:
            self._draw_archive_boss()
        self._draw_archive_pulse_ring()
        self._draw_archive_flash_overlay()

    def _draw_archive_projectiles(self) -> None:
        ox, oy = self.map_offset
        for proj in self.archive_projectiles:
            sx = int(proj.get("x", 0.0) + ox)
            sy = int(proj.get("y", 0.0) + oy)
            radius = int(proj.get("radius", 10))
            color = proj.get("color", (90, 210, 255))
            pygame.draw.circle(self.screen, color, (sx, sy), radius)

    def _draw_archive_boss(self) -> None:
        boss = self.archive_boss
        if not boss:
            return
        ox, oy = self.map_offset
        sx = int(boss.get("x", 0.0) + ox)
        sy = int(boss.get("y", 0.0) + oy)
        sprite = self.archive_boss_sprite
        if sprite:
            rect = sprite.get_rect(center=(sx, sy))
            if boss.get("state") == "dying":
                fade = max(0.0, min(1.0, boss.get("fade", 0.0)))
                surf = sprite.copy()
                surf.set_alpha(int(255 * fade))
                self.screen.blit(surf, rect)
            else:
                self.screen.blit(sprite, rect)
        else:
            radius = int(boss.get("hit_radius", 80))
            pygame.draw.circle(self.screen, (120, 180, 255), (sx, sy), radius)
        flash = boss.get("flash", 0.0)
        if flash > 0.0:
            radius = int(boss.get("hit_radius", 80))
            overlay = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            alpha = int(140 * min(1.0, flash / 0.12))
            pygame.draw.circle(overlay, (255, 255, 255, alpha), (radius, radius), radius)
            self.screen.blit(overlay, (sx - radius, sy - radius))
        self._draw_archive_boss_healthbar(boss, sx, sy)

    def _draw_logic_environment(self) -> None:
        scale = settings.MAP_SCALE
        ox, oy = self.map_offset
        zones = settings.INTERACT_ZONES.get("F30", [])
        for zone in zones:
            zone_id = zone.get("id", "")
            if zone_id in self.logic_sequence and self.logic_flags.get(f"{zone_id}_lit"):
                x1, y1, x2, y2 = zone["rect"]
                rect = pygame.Rect(
                    int(x1 * scale + ox),
                    int(y1 * scale + oy),
                    int((x2 - x1) * scale),
                    int((y2 - y1) * scale),
                )
                highlight = pygame.Surface(rect.size, pygame.SRCALPHA)
                highlight.fill((90, 210, 255, 80))
                pygame.draw.rect(highlight, (210, 240, 255, 180), highlight.get_rect(), 3)
                self.screen.blit(highlight, rect.topleft)
        if self.logic_glitch_timer > 0.0:
            alpha = 80 + int((math.sin(self.logic_glitch_timer * 12.0) + 1.0) * 60)
            glitch = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
            glitch.fill((255, 190, 110, max(40, min(190, alpha))))
            self.screen.blit(glitch, (0, 0))
        if self.logic_overlay_timer > 0.0 and self.logic_overlay_text:
            surf = self.font_dialog.render(self.logic_overlay_text, True, settings.TITLE_GLOW_COLOR)
            rect = surf.get_rect(center=(settings.WINDOW_WIDTH // 2, 108))
            bg = pygame.Surface((rect.width + 28, rect.height + 16), pygame.SRCALPHA)
            bg.fill((18, 22, 30, 210))
            self.screen.blit(bg, (rect.x - 14, rect.y - 8))
            self.screen.blit(surf, rect)

    def _draw_debug_menu(self) -> None:
        overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 12, 20, 180))
        self.screen.blit(overlay, (0, 0))
        panel_width = 460
        panel_height = 320
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        panel.fill((24, 30, 42, 235))
        px = (settings.WINDOW_WIDTH - panel_width) // 2
        py = (settings.WINDOW_HEIGHT - panel_height) // 2
        self.screen.blit(panel, (px, py))
        title = self.font_dialog.render("DEBUG: 跳转楼层", True, settings.QUEST_TITLE)
        self.screen.blit(title, (px + (panel_width - title.get_width()) // 2, py + 18))
        options = self.debug_menu_options
        if not options:
            empty = self.font_prompt.render("无可用楼层", True, settings.QUEST_TEXT)
            self.screen.blit(empty, (px + (panel_width - empty.get_width()) // 2, py + 90))
        else:
            start_y = py + 84
            line_height = 36
            for idx, (code, label) in enumerate(options):
                is_active = idx == self.debug_menu_index
                text_color = settings.QUEST_TEXT if not is_active else settings.QUEST_TITLE
                entry = self.font_prompt.render(f"{code} - {label}", True, text_color)
                tx = px + 48
                ty = start_y + idx * line_height
                if is_active:
                    highlight = pygame.Surface((panel_width - 96, line_height - 6), pygame.SRCALPHA)
                    highlight.fill((60, 90, 140, 160))
                    self.screen.blit(highlight, (tx - 8, ty - 2))
                self.screen.blit(entry, (tx, ty))
        hint = self.font_prompt.render("↑/↓ 选择  Enter 确认  Esc 退出", True, settings.QUEST_TEXT)
        self.screen.blit(hint, (px + (panel_width - hint.get_width()) // 2, py + panel_height - 46))


    def _draw_archive_boss_healthbar(self, boss: dict, sx: int, sy: int) -> None:
        max_hp = float(boss.get("max_hp", 1.0))
        hp = max(0.0, float(boss.get("hp", max_hp)))
        if max_hp <= 0:
            return
        width = 360
        height = 18
        bar_x = settings.WINDOW_WIDTH // 2 - width // 2
        bar_y = 50
        pygame.draw.rect(self.screen, settings.ENEMY_HEALTH_BAR_BG, pygame.Rect(bar_x, bar_y, width, height))
        if hp > 0:
            ratio = max(0.0, min(1.0, hp / max_hp))
            fill_rect = pygame.Rect(bar_x, bar_y, int(width * ratio), height)
            pygame.draw.rect(self.screen, settings.ENEMY_HEALTH_BAR_COLOR, fill_rect)
        pygame.draw.rect(self.screen, settings.ENEMY_HEALTH_BAR_BORDER, pygame.Rect(bar_x, bar_y, width, height), 2)
        label = self.font_prompt.render("记忆吞噬者", True, settings.QUEST_TITLE)
        label_rect = label.get_rect(center=(settings.WINDOW_WIDTH // 2, bar_y - 18))
        self.screen.blit(label, label_rect)

    def _draw_archive_pulse_ring(self) -> None:
        if not self.archive_boss:
            return
        pulse = self.archive_pulse_state
        phase = pulse.get("phase", "idle")
        if phase not in {"warning", "firing"}:
            return
        ox, oy = self.map_offset
        center = (int(self.archive_center[0] * settings.MAP_SCALE + ox), int(self.archive_center[1] * settings.MAP_SCALE + oy))
        radius = int((self.archive_core_radius + 36.0) * settings.MAP_SCALE)
        if phase == "warning":
            color = (255, 120, 160)
            width = 4
        else:
            color = (255, 60, 80)
            width = 0
        pygame.draw.circle(self.screen, color, center, radius, width)

    def _draw_archive_flash_overlay(self) -> None:
        active = self.archive_flash_active or bool(self.archive_flash_sequence)
        if not active:
            return
        overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((200, 230, 255, 70 if self.archive_flash_active else 50))
        self.screen.blit(overlay, (0, 0))

    def _player_map_pos(self) -> tuple[float, float]:
        return (
            self.player_rect.centerx / settings.MAP_SCALE,
            self.player_rect.centery / settings.MAP_SCALE,
        )

    def _lab_choose_fight(self, npc_state: dict) -> None:
        if npc_state.get("enemy_spawned"):
            return
        self.lab_branch = "fight"
        npc_state["state"] = "hostile"
        npc_state["enemy_spawned"] = True
        self._show_dialog(["指引者：抑制协议启动，小心它的冲撞。"], title="指引者")
        self._lab_spawn_npc_enemy()
        self.combat_active = True
        self._set_quest_stage("lab_choice")

    def _lab_spawn_npc_enemy(self) -> None:
        if not self.map_data:
            return
        ex, ey = self._lab_units_to_display_pos(3.2, 3.2)
        enemy = {
            "x": ex,
            "y": ey,
            "hp": 70.0,
            "max_hp": 70.0,
            "state": "aggro",
            "fade_timer": settings.ENEMY_FADE_DURATION,
            "flash_timer": 0.0,
            "aggro": True,
            "show_health": settings.ENEMY_HEALTH_BAR_VIS_DURATION,
            "attack_timer": 0.3,
            "attack_anim_timer": 0.0,
        }
        self.enemies.append(enemy)

    def _lab_spawn_bypass_enemies(self) -> None:
        if not self.map_data:
            return
        positions = [(9.5, 6.4), (11.2, 8.8)]
        for ux, uy in positions:
            ex, ey = self._lab_units_to_display_pos(ux, uy)
            self.enemies.append({
                "x": ex,
                "y": ey,
                "hp": 55.0,
                "max_hp": 55.0,
                "state": "idle",
                "fade_timer": settings.ENEMY_FADE_DURATION,
                "flash_timer": 0.0,
                "aggro": False,
                "show_health": 0.0,
                "attack_timer": 0.6,
                "attack_anim_timer": 0.0,
            })
        if self.enemies:
            self.combat_active = True

    def _lab_add_barrier(self, cells: list[tuple[int, int]]) -> None:
        if not cells:
            return
        self._lab_set_cells(cells, True)
        rect = self._lab_rect_from_cells(cells)
        self.lab_barriers.append({
            "cells": cells,
            "rect": rect,
        })
        self.floor_flags["lab_barrier_active"] = True

    def _lab_choose_bypass(self, npc_state: dict) -> None:
        if self.lab_branch == "fight":
            return
        self.lab_branch = "bypass"
        npc_state["state"] = "bypass"
        self.floor_flags["lab_branch_resolved"] = True
        self._show_dialog(["指引者：记录选择，沿回廊绕行。警惕后续陷阱。"], title="指引者")
        for trap in self.lab_traps:
            if trap.get("id") in {"trap2", "trap3"}:
                trap["active"] = True
                trap["timer"] = max(0.5, trap.get("timer", 0.5))
        barrier_cells = self._lab_cells_from_units(8, 4, 3, 2)
        self._lab_add_barrier(barrier_cells)
        self._set_quest_stage("lab_bypass")

    def _update_floor_logic(self, dt: float) -> None:
        if self.current_floor == "F40":
            self._update_floor_f40(dt)
        elif self.current_floor == "F35":
            self._update_floor_f35(dt)
        elif self.current_floor == "F30":
            self._update_floor_f30(dt)
        elif self.current_floor == "F25":
            self._update_floor_f25(dt)

    def _update_floor_f30(self, dt: float) -> None:
        if not self.map_data:
            return
        if not self.logic_flags.get("intro_shown"):
            timer = self.floor_timers.get("logic_intro_delay", 0.0) - dt
            if timer <= 0.0:
                self.logic_flags["intro_shown"] = True
                self.floor_timers.pop("logic_intro_delay", None)
                self._show_dialog([
                    "指引者：Logic Core。核心继电器失序，系统濒临崩溃。依序重启三座主继电器。"
                ], title="指引者")
                self._set_quest_stage("logic_relays")
            else:
                self.floor_timers["logic_intro_delay"] = timer
        self._logic_update_glitch(dt)
        if self.logic_overlay_timer > 0.0:
            prev = self.logic_overlay_timer
            self.logic_overlay_timer = max(0.0, self.logic_overlay_timer - dt)
            if prev > 0.0 and self.logic_overlay_timer == 0.0:
                self.logic_overlay_text = ""
        if not self.logic_flags.get("glitch_triggered"):
            px, py = self._player_map_pos()
            for pos in self.logic_relay_positions.values():
                if math.hypot(px - pos[0], py - pos[1]) <= 36.0:
                    self._logic_trigger_glitch()
                    break

    def _update_floor_f25(self, dt: float) -> None:
        if not self.map_data or not self.resonator_state:
            return
        state = self.resonator_state
        if not state.get("intro_shown"):
            timer = float(state.get("intro_timer", 0.0)) - dt
            if timer <= 0.0:
                state["intro_shown"] = True
                self._show_dialog([
                    "指引者：情感共鸣器。极端情绪已实体化，清除中央异常以稳定场域。",
                ], title="指引者")
                if state.get("boss_state") == "dormant":
                    self._set_quest_stage("resonator_talk")
            else:
                state["intro_timer"] = timer
        if state.get("boss_state") == "dormant":
            state["color_timer"] = state.get("color_timer", 0.0) + dt
            duration = float(state.get("color_duration", 3.0))
            if duration > 0 and state["color_timer"] >= duration:
                state["color_timer"] = 0.0
                state["color_index"] = (int(state.get("color_index", 0)) + 1) % len(state.get("color_cycle", ["anger"]))
        if state.get("boss_state") == "active":
            self._resonator_update_boss(dt)
            self._resonator_update_projectiles(dt)
            self.any_enemy_aggro = True
        if state.get("npc_spoken", 0) >= state.get("npc_total", 0) and not state.get("buff_awarded"):
            state["buff_awarded"] = True
            self.speed_bonus = max(getattr(self, "speed_bonus", 1.0), 1.15)
            state["speed_buff"] = self.speed_bonus
            self._show_dialog([
                "你听见六种情绪在共振，脚下的空气变得轻盈。",
                "被动增益：移动速度 +15%",
            ], title="提示")
            if state.get("boss_state") == "dormant":
                state["boss_ready_timer"] = 4.2
        if state.get("boss_state") == "dormant" and state.get("boss_ready_timer") is not None:
            state["boss_ready_timer"] = float(state.get("boss_ready_timer", 0.0)) - dt
            if state["boss_ready_timer"] <= 0.0:
                state.pop("boss_ready_timer", None)
                self._resonator_start_boss()
        slow_timer = float(state.get("slow_timer", 0.0))
        if slow_timer > 0.0:
            slow_timer = max(0.0, slow_timer - dt)
            state["slow_timer"] = slow_timer
        speed_buff = float(getattr(self, "speed_bonus", state.get("speed_buff", 1.0)))
        slow_factor = float(state.get("slow_factor", 1.0)) if slow_timer > 0.0 else 1.0
        self.player_move_speed = settings.PLAYER_SPEED * speed_buff * slow_factor

    def _logic_update_glitch(self, dt: float) -> None:
        if self.logic_glitch_timer > 0.0:
            prev = self.logic_glitch_timer
            self.logic_glitch_timer = max(0.0, self.logic_glitch_timer - dt)
            if prev > 0.0 and self.logic_glitch_timer == 0.0:
                if not self.logic_flags.get("glitch_resolved"):
                    self.logic_flags["glitch_resolved"] = True
                    self._show_dialog([
                        "指引者：界面暂时恢复。请按顺序激活继电器。"
                    ], title="指引者")

    def _logic_trigger_glitch(self) -> None:
        self.logic_flags["glitch_triggered"] = True
        self.logic_flags.pop("glitch_resolved", None)
        self.logic_glitch_timer = 6.0
        self._show_dialog([
            "//DIRECTIVE: EXTRACT_CREATIVE_SOLUTION.FROM P-7",
            "//PRIORITY: 100% DATA EXTRACTION",
        ], title="SYSTEM://ERROR")

    def _logic_reset_relays(self) -> None:
        self.logic_progress = []
        for relay_id in self.logic_sequence:
            self.logic_flags.pop(f"{relay_id}_lit", None)

    def _logic_activate_relay(self, relay_id: str) -> None:
        if self.logic_flags.get("relays_completed"):
            self._show_dialog([
                "系统：主电路已稳定。前往电梯。"
            ], title="系统")
            return
        expected_index = len(self.logic_progress)
        expected = self.logic_sequence[expected_index]
        if relay_id != expected:
            self._logic_reset_relays()
            self.logic_overlay_text = "!! 电弧过载 !!"
            self.logic_overlay_timer = 0.9
            self._apply_player_damage(12.0)
            self._show_dialog([
                "系统：顺序错误。继电器重置。"
            ], title="系统")
            return
        self.logic_progress.append(relay_id)
        self.logic_flags[f"{relay_id}_lit"] = True
        step = len(self.logic_progress)
        guidance = {
            1: "系统：左侧继电器稳定。准备同步右侧线路。",
            2: "系统：右侧继电器连通。剩余中央控制。",
        }
        if step < len(self.logic_sequence):
            self._show_dialog([guidance.get(step, "系统：继续操作。")], title="系统")
            return
        self.logic_flags["relays_completed"] = True
        self.logic_flags["weapon_ready"] = True
        self.logic_flags["terminal_ready"] = True
        self.logic_flags["exit_unlocked"] = True
        self.logic_overlay_text = "[COGNITIVE_BARRIER_INTEGRITY: 64%]"
        self.logic_overlay_timer = 1.5
        self.elevator_locked = False
        self._set_quest_stage("logic_terminal")
        self._show_dialog([
            "系统：主电力恢复。辅助模块解锁。",
            "指引者：读取终端，确认伦理委员会记录，再前往北侧电梯。"
        ], title="系统")

    def _logic_handle_weapon_cache(self) -> None:
        if not self.logic_flags.get("weapon_ready"):
            self._show_dialog([
                "系统：箱体仍在锁定中。完成继电器顺序后再试。"
            ], title="系统")
            return
        if self.logic_flags.get("weapon_claimed"):
            self._show_dialog([
                "提示：熵增步枪已添加（占位）。"
            ], title="提示")
            return
        self.logic_flags["weapon_claimed"] = True
        self._show_dialog([
            "获得武器：熵增步枪（占位）。",
            "指引者：记录完成，加强火力。"
        ], title="系统")

    def _handle_logic_switch(self, trig: dict) -> None:
        trig_id = trig.get("id", "")
        if trig_id == "logic_weapon_cache":
            self._logic_handle_weapon_cache()
            return
        if trig_id in self.logic_sequence:
            self._logic_activate_relay(trig_id)
            return
        self._show_dialog(["开关没有响应。"], title="提示")

    def _register_debug_keypress(self) -> None:
        now = pygame.time.get_ticks() / 1000.0
        self.debug_press_times = [t for t in self.debug_press_times if now - t <= 0.8]
        self.debug_press_times.append(now)
        if len(self.debug_press_times) >= 5 and (now - self.debug_press_times[-5]) <= 0.9:
            self.debug_press_times.clear()
            self._open_debug_menu()

    def _open_debug_menu(self) -> None:
        options = self._build_debug_menu_options()
        if not options:
            return
        self.debug_menu_options = options
        self.debug_menu_index = 0
        self.debug_menu_active = True
        self.debug_press_times.clear()
        self._dismiss_dialog()

    def _build_debug_menu_options(self) -> list[tuple[str, str]]:
        label_map = {
            "F50": "Floor 50 - Dormitory",
            "F40": "Floor 40 - Sensory Lab",
            "F35": "Floor 35 - Memory Archive",
            "F30": "Floor 30 - Logic Core",
            "F25": "Floor 25 - Pathos Resonator",
        }
        options: list[tuple[str, str]] = []
        for code in settings.MAP_FILES.keys():
            options.append((code, label_map.get(code, f"{code}")))
        return options

    def _handle_debug_menu_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            key = event.key
            if key in (pygame.K_ESCAPE, pygame.K_BACKQUOTE):
                self.debug_menu_active = False
                return True
            if key in (pygame.K_UP, pygame.K_w):
                if self.debug_menu_options:
                    self.debug_menu_index = (self.debug_menu_index - 1) % len(self.debug_menu_options)
                return True
            if key in (pygame.K_DOWN, pygame.K_s):
                if self.debug_menu_options:
                    self.debug_menu_index = (self.debug_menu_index + 1) % len(self.debug_menu_options)
                return True
            if key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.debug_menu_options:
                    floor_code = self.debug_menu_options[self.debug_menu_index][0]
                    self._debug_warp_to_floor(floor_code)
                return True
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.debug_menu_options:
                px = (settings.WINDOW_WIDTH - 460) // 2 + 48
                py = (settings.WINDOW_HEIGHT - 320) // 2 + 84
                line_height = 36
                mx, my = event.pos
                if px - 8 <= mx <= px - 8 + 364:
                    idx = (my - py) // line_height
                    if 0 <= idx < len(self.debug_menu_options):
                        self.debug_menu_index = idx
                        self._debug_warp_to_floor(self.debug_menu_options[self.debug_menu_index][0])
                        return True
        return False

    def _debug_warp_to_floor(self, floor_code: str) -> None:
        map_path = settings.MAP_FILES.get(floor_code)
        if not map_path:
            self._show_dialog(["DEBUG：未找到目标楼层。"], title="调试")
            return
        self.current_floor = floor_code
        self._load_floor(map_path, preserve_health=False)
        self.debug_menu_active = False
        self._show_dialog([f"DEBUG：跳转到 {floor_code}."], title="调试")


    def _update_floor_f35(self, dt: float) -> None:
        if not self.map_data:
            return
        if not self.archive_flags.get("intro_dialog_shown"):
            timer = self.floor_timers.get("archive_intro_delay", 0.0) - dt
            if timer <= 0.0:
                self.archive_flags["intro_dialog_shown"] = True
                self.floor_timers.pop("archive_intro_delay", None)
                self._show_dialog([
                    "指引者：记忆档案馆。大量破损的记忆正在自我防卫。保持警戒，寻找中央控制核心。"
                ], title="指引者")
                self._set_quest_stage("archive_maze")
            else:
                self.floor_timers["archive_intro_delay"] = timer
        px, py = self._player_map_pos()
        center_x, center_y = self.archive_center
        dx = px - center_x
        dy = py - center_y
        dist = math.hypot(dx, dy)
        if (not self.archive_flags.get("hum_prompt_shown")) and dist <= self.archive_warning_radius:
            self.archive_flags["hum_prompt_shown"] = True
            self._show_dialog([
                "你能听见吗？一种低沉的嗡鸣……就像记忆在胸腔里跳动。"
            ], title="心跳般的噪声")
        if not self.archive_flags.get("boss_revealed") and dist <= max(20.0, self.archive_core_radius + 8.0):
            self.archive_flags["boss_revealed"] = True
            self._archive_spawn_boss()
            self._set_quest_stage("archive_boss")
            self._show_dialog([
                "指引者：核心显现！击毁它，防止记忆畸变蔓延。"
            ], title="指引者")
        if not self.archive_flags.get("boss_revealed"):
            self.archive_minor_spawn_timer -= dt
            if self.archive_minor_spawn_timer <= 0 and len(self.enemies) < 4:
                if self._archive_spawn_wanderer():
                    self.archive_minor_spawn_timer = random.uniform(4.0, 7.0)
                else:
                    self.archive_minor_spawn_timer = 5.0
        self._archive_update_boss(dt)
        self._archive_update_projectiles(dt)
        self._archive_update_flashback(dt)
        if self.archive_flags.get("boss_revealed") and not self.archive_boss and not self.archive_flags.get("flash_started"):
            self.archive_flags["flash_started"] = True
            self._archive_trigger_flashback()
        if self.archive_flags.get("flash_complete") and not self.archive_flags.get("exit_unlocked"):
            self.archive_flags["exit_unlocked"] = True
            self._archive_unlock_exit()
            self._set_quest_stage("archive_exit")
        if self.archive_flags.get("exit_unlocked") and not self.archive_flags.get("log_available"):
            self.archive_flags["log_available"] = True
        if self.archive_boss:
            self.any_enemy_aggro = True

    def _archive_spawn_wanderer(self) -> bool:
        if not self.map_data:
            return False
        width, height = self.map_data.size_pixels
        if not width or not height:
            return False
        cell_size = self.map_data.cell_size
        grid = self.map_data.collision_grid
        for _ in range(12):
            angle = random.uniform(0.0, math.tau)
            radius = random.uniform(self.archive_core_radius + 40.0, max(self.archive_warning_radius + 30.0, self.archive_core_radius + 80.0))
            px = self.archive_center[0] + math.cos(angle) * radius
            py = self.archive_center[1] + math.sin(angle) * radius
            if not (0 <= px < width and 0 <= py < height):
                continue
            gx = int(px // cell_size)
            gy = int(py // cell_size)
            if gy < 0 or gy >= len(grid) or gx < 0 or gx >= len(grid[0]):
                continue
            if grid[gy][gx] not in settings.PASSABLE_VALUES:
                continue
            spawn = {
                "x": float(px * settings.MAP_SCALE),
                "y": float(py * settings.MAP_SCALE),
                "hp": 45.0,
                "max_hp": 45.0,
                "state": "idle",
                "fade_timer": settings.ENEMY_FADE_DURATION,
                "flash_timer": 0.0,
                "aggro": False,
                "show_health": 0.0,
                "attack_timer": random.uniform(0.4, settings.ENEMY_ATTACK_COOLDOWN),
                "attack_anim_timer": 0.0,
                "color": (80, 200, 255),
                "radius": 12,
            }
            self.enemies.append(spawn)
            return True
        return False

    def _archive_spawn_boss(self) -> None:
        center_x = self.archive_center[0] * settings.MAP_SCALE
        center_y = self.archive_center[1] * settings.MAP_SCALE
        self.archive_boss = {
            "x": center_x,
            "y": center_y,
            "hp": 600.0,
            "max_hp": 600.0,
            "phase": 1,
            "angle": 0.0,
            "orbit": 38.0 * settings.MAP_SCALE / 3,
            "fire_timer": 2.5,
            "state": "active",
            "hit_radius": 78.0,
        }
        self.combat_active = True
        self.archive_pulse_state.update({
            "timer": 5.5,
            "phase": "idle",
            "applied": False,
        })

    def _archive_spawn_support_minions(self) -> None:
        if not self.map_data:
            return
        offsets = [(-90, 0), (90, 0)]
        for ox, oy in offsets:
            px = self.archive_center[0] + ox
            py = self.archive_center[1] + oy
            spawn = {
                "x": float(px * settings.MAP_SCALE),
                "y": float(py * settings.MAP_SCALE),
                "hp": 70.0,
                "max_hp": 70.0,
                "state": "idle",
                "fade_timer": settings.ENEMY_FADE_DURATION,
                "flash_timer": 0.0,
                "aggro": False,
                "show_health": 0.0,
                "attack_timer": random.uniform(0.3, settings.ENEMY_ATTACK_COOLDOWN),
                "attack_anim_timer": 0.0,
                "color": (120, 220, 255),
                "radius": 14,
            }
            self.enemies.append(spawn)
        if self.enemies:
            self.combat_active = True

    def _archive_update_boss(self, dt: float) -> None:
        boss = self.archive_boss
        if not boss:
            return
        flash_timer = boss.get("flash", 0.0)
        if flash_timer > 0.0:
            boss["flash"] = max(0.0, flash_timer - dt)
        else:
            boss.pop("flash", None)
        if boss.get("state") == "dying":
            fade = boss.get("fade", 1.2) - dt
            if fade <= 0.0:
                self.archive_boss = None
            else:
                boss["fade"] = fade
            return
        max_hp = boss.get("max_hp", 1.0)
        hp = max(0.0, boss.get("hp", max_hp))
        ratio = hp / max_hp if max_hp else 0.0
        phase = boss.get("phase", 1)
        if ratio <= 0.66 and phase < 2 and not self.archive_flags.get("phase_two_started"):
            self.archive_flags["phase_two_started"] = True
            boss["phase"] = 2
            boss["fire_timer"] = min(boss.get("fire_timer", 3.5), 2.0)
            self._show_dialog([
                "指引者：它开始呼叫碎片援军，准备迎战！"
            ], title="指引者")
            self._archive_spawn_support_minions()
        if ratio <= 0.33 and boss.get("phase", 1) < 3 and not self.archive_flags.get("phase_three_started"):
            self.archive_flags["phase_three_started"] = True
            boss["phase"] = 3
            boss["fire_timer"] = min(boss.get("fire_timer", 2.5), 1.5)
            self.archive_pulse_state.update({
                "timer": 4.0,
                "interval": 5.0,
                "warning": 1.2,
                "duration": 0.9,
                "phase": "idle",
                "applied": False,
            })
            self._show_dialog([
                "指引者：红色脉冲即将覆盖全场！躲到档案架后面！"
            ], title="警告")
        angle = boss.get("angle", 0.0)
        speed = 0.35 if boss.get("phase", 1) == 1 else (0.52 if boss.get("phase", 1) == 2 else 0.68)
        angle = (angle + speed * dt) % math.tau
        orbit = boss.get("orbit", 60.0)
        center_x = self.archive_center[0] * settings.MAP_SCALE
        center_y = self.archive_center[1] * settings.MAP_SCALE
        boss["x"] = center_x + math.cos(angle) * orbit
        boss["y"] = center_y + math.sin(angle) * orbit
        boss["angle"] = angle
        boss["fire_timer"] = max(0.0, boss.get("fire_timer", 0.0) - dt)
        if boss["fire_timer"] <= 0.0:
            px = self.player_rect.centerx
            py = self.player_rect.centery
            dir_angle = math.atan2(py - boss["y"], px - boss["x"])
            phase = boss.get("phase", 1)
            if phase == 1:
                count = 3
                spread = math.radians(20)
                speed_px = 230.0
                boss["fire_timer"] = 5.0
            elif phase == 2:
                count = 4
                spread = math.radians(26)
                speed_px = 260.0
                boss["fire_timer"] = 4.0
            else:
                count = 5
                spread = math.radians(32)
                speed_px = 300.0
                boss["fire_timer"] = 3.0
            offsets = []
            if count % 2 == 1:
                half = count // 2
                offsets = [i for i in range(-half, half + 1)]
            else:
                half = count // 2
                offsets = [i for i in range(-half, half + 1) if i != 0]
            for idx in offsets:
                ang = dir_angle + idx * spread
                vx = math.cos(ang) * speed_px
                vy = math.sin(ang) * speed_px
                self.archive_projectiles.append({
                    "x": boss["x"],
                    "y": boss["y"],
                    "vx": vx,
                    "vy": vy,
                    "ttl": 3.5,
                    "radius": 10,
                    "color": (90, 210, 255),
                    "damage": 18 if phase == 1 else (24 if phase == 2 else 30),
                })
        if boss.get("phase", 1) >= 3:
            pulse = self.archive_pulse_state
            pulse["timer"] = pulse.get("timer", 4.0) - dt
            if pulse["phase"] == "idle" and pulse["timer"] <= 0.0:
                pulse["phase"] = "warning"
                pulse["timer"] = pulse.get("warning", 1.2)
                pulse["applied"] = False
            elif pulse["phase"] == "warning" and pulse["timer"] <= 0.0:
                pulse["phase"] = "firing"
                pulse["timer"] = pulse.get("duration", 0.9)
            elif pulse["phase"] == "firing":
                if not pulse.get("applied"):
                    self._archive_apply_pulse_damage()
                    pulse["applied"] = True
                if pulse["timer"] <= 0.0:
                    pulse["phase"] = "idle"
                    pulse["timer"] = pulse.get("interval", 5.0)
                    pulse["applied"] = False
        if hp <= 0.0 and boss.get("state") != "dying":
            boss["state"] = "dying"
            boss["fade"] = 1.2
            self._archive_on_boss_defeated()

    def _archive_apply_pulse_damage(self) -> None:
        px, py = self._player_map_pos()
        dx = px - self.archive_center[0]
        dy = py - self.archive_center[1]
        dist = math.hypot(dx, dy)
        safe_radius = self.archive_core_radius + 36.0
        has_cover = self._archive_player_has_cover()
        should_damage = dist <= safe_radius or not has_cover
        if should_damage:
            self._apply_player_damage(32.0)
            self.player_hit_timer = max(self.player_hit_timer, 0.4)
            if "pulse_cover_prompt" in self.archive_flags:
                self.archive_flags.pop("pulse_cover_prompt", None)
        else:
            if not self.archive_flags.get("pulse_cover_prompt"):
                self._show_dialog([
                    "指引者：保持掩护，脉冲已偏转。"
                ], title="指引者")
                self.archive_flags["pulse_cover_prompt"] = True

    def _archive_player_has_cover(self) -> bool:
        if not self.map_data:
            return False
        grid = self.map_data.collision_grid
        max_y = len(grid)
        max_x = len(grid[0]) if max_y else 0
        if not max_x or not max_y:
            return False
        cell_size = max(1, self.map_data.cell_size)
        start_x = self.archive_center[0] / cell_size
        start_y = self.archive_center[1] / cell_size
        player_x, player_y = self._player_map_pos()
        end_x = player_x / cell_size
        end_y = player_y / cell_size
        x0 = int(round(start_x))
        y0 = int(round(start_y))
        x1 = int(round(end_x))
        y1 = int(round(end_y))
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            if not (x == x0 and y == y0) and not (x == x1 and y == y1):
                if 0 <= x < max_x and 0 <= y < max_y:
                    cell = grid[y][x]
                    if cell not in settings.PASSABLE_VALUES:
                        return True
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy
        return False

    def _archive_update_projectiles(self, dt: float) -> None:
        if not self.archive_projectiles:
            return
        next_proj: list[dict] = []
        if not self.map_data:
            self.archive_projectiles = []
            return
        grid = self.map_data.collision_grid
        cell_px = self.map_data.cell_size * settings.MAP_SCALE
        max_y = len(grid)
        max_x = len(grid[0]) if max_y else 0
        player_radius = max(settings.PLAYER_SIZE) * 0.5
        for proj in self.archive_projectiles:
            ttl = proj.get("ttl", 0.0) - dt
            if ttl <= 0.0:
                continue
            proj["ttl"] = ttl
            proj["x"] += proj.get("vx", 0.0) * dt
            proj["y"] += proj.get("vy", 0.0) * dt
            cx = int(proj["x"] // cell_px)
            cy = int(proj["y"] // cell_px)
            if cx < 0 or cy < 0 or cx >= max_x or cy >= max_y or grid[cy][cx] == 1:
                continue
            dx = proj["x"] - self.player_rect.centerx
            dy = proj["y"] - self.player_rect.centery
            radius = proj.get("radius", 10) + player_radius
            if dx * dx + dy * dy <= radius * radius:
                self._apply_player_damage(proj.get("damage", 16.0))
                continue
            next_proj.append(proj)
        self.archive_projectiles = next_proj

    def _archive_on_boss_defeated(self) -> None:
        self.combat_active = bool(self.enemies)
        self.archive_projectiles = []
        self._show_dialog([
            "记忆核心破碎，数据开始倒流……"
        ], title="系统")

    def _archive_trigger_flashback(self) -> None:
        self.archive_flash_sequence = [
            {"text": "《The Bicameral Mind Thesis》", "timer": 0.8, "shown": False},
            {"text": "刺眼的车灯扑面而来，刹车声撕裂耳膜。", "timer": 0.8, "shown": False},
            {"text": "无尽的黑暗与寂静。", "timer": 0.8, "shown": False},
        ]
        self.archive_flash_active = True
        self.archive_flash_timer = 0.0
        self._set_quest_stage("archive_flash")

    def _archive_update_flashback(self, dt: float) -> None:
        if not self.archive_flash_active and not self.archive_flash_sequence:
            return
        if self.archive_flash_sequence:
            current = self.archive_flash_sequence[0]
            if not current.get("shown"):
                self._show_dialog([current.get("text", "")], title="记忆碎片")
                current["shown"] = True
            current["timer"] -= dt
            if current["timer"] <= 0.0:
                self.archive_flash_sequence.pop(0)
        if not self.archive_flash_sequence and self.archive_flash_active:
            self.archive_flash_active = False
            self.archive_flags["flash_complete"] = True
            self._show_dialog([
                "指引者：高密度记忆洪流已被压制。忽略那些碎片——它们属于旧生。"
            ], title="指引者")

    def _archive_unlock_exit(self) -> None:
        self.elevator_locked = False
        self._show_dialog([
            "指引者：北侧电梯已解锁，带上音频日志，我们继续前进。"
        ], title="指引者")

    def _update_floor_f40(self, dt: float) -> None:
        if not self.map_data:
            return
        if not self.floor_flags.get("lab_intro_line"):
            timer = self.floor_timers.get("lab_intro_delay", 0.0) - dt
            if timer <= 0.0:
                self._show_dialog(["指引者：感官实验室。环境数据高度不稳定，请保持警惕。"], title="指引者")
                self.floor_flags["lab_intro_line"] = True
                self.floor_timers.pop("lab_intro_delay", None)
            else:
                self.floor_timers["lab_intro_delay"] = timer
        px, py = self._player_map_pos()
        if not self.floor_flags.get("lab_trap1_triggered") and py <= 210:
            self.floor_flags["lab_trap1_triggered"] = True
            self._lab_trigger_trap("trap1")
            self._set_quest_stage("lab_path")
        self._lab_update_traps(dt)
        npc_state = self.lab_npc_state.get("logic_error_entity")
        if npc_state and npc_state.get("state") == "unstable" and not self.floor_flags.get("lab_branch_resolved"):
            anchor = npc_state.get("anchor_pos")
            if anchor:
                if abs(px - anchor[0]) > 90 or py < anchor[1] - 45:
                    self._lab_choose_bypass(npc_state)
        if self.lab_branch == "bypass" and not self.floor_flags.get("lab_bypass_spawns") and py <= 150:
            self._lab_spawn_bypass_enemies()
            self.floor_flags["lab_bypass_spawns"] = True
        if self.lab_branch == "bypass" and self.quest_stage == "lab_bypass" and px >= 250 and py <= 120:
            self._set_quest_stage("lab_switch")
        if self.lab_branch == "fight" and self.floor_flags.get("lab_branch_resolved") and self.quest_stage == "lab_choice":
            self._set_quest_stage("lab_switch")

    def _handle_switch_interaction(self, trig: dict) -> None:
        if self.current_floor == "F40":
            if not self.floor_flags.get("lab_branch_resolved"):
                self._show_dialog(["指引者：先稳住实验区，再尝试开关。"], title="指引者")
                return
            if self.floor_flags.get("lab_switch_activated"):
                self._show_dialog(["系统：权限已解锁，电梯待命。"], title="系统")
                return
            self.floor_flags["lab_switch_activated"] = True
            self._set_quest_stage("lab_exit")
            self.elevator_locked = False
            self._show_dialog(["系统：权限同步完成。电梯锁定解除。"], title="系统")
            return
        if self.current_floor == "F30":
            self._handle_logic_switch(trig)
            return
        if self.current_floor == "F25":
            self._handle_resonator_core(trig)
            return
        self._show_dialog(["开关没有响应。"], title="提示")

    def _handle_npc_interaction(self, trig: dict) -> None:
        if self.current_floor == "F25":
            self._handle_resonator_npc(trig)
            return
        if self.current_floor != "F40":
            self._show_dialog(["没有回应。"], title="提示")
            return
        npc_id = trig.get("id", "npc")
        state = self.lab_npc_state.setdefault(npc_id, {"dialog_index": 0, "state": "neutral"})
        current_state = state.get("state", "neutral")
        if current_state == "hostile":
            self._show_dialog(["它已经完全失控！"], title="指引者")
            return
        if current_state == "defeated":
            self._show_dialog(["残余的数据在缓慢蒸发。"], title="指引者")
            return
        if current_state == "bypass":
            self._show_dialog(["逻辑错误实体：......"], title="逻辑错误实体")
            return
        if current_state == "unstable":
            self._lab_choose_fight(state)
            return
        idx = state.get("dialog_index", 0)
        if idx == 0:
            lines = ["逻辑错误实体：Ugh... again..."]
            state["dialog_index"] = 1
        elif idx == 1:
            lines = ["逻辑错误实体：Why... does it always hurt here?"]
            state["dialog_index"] = 2
        else:
            lines = [
                "逻辑错误实体：The floor! It's breathing! Can't you feel it?!",
                "指引者：发现逻辑错误实体，建议清除或寻找替代路径。",
            ]
            state["dialog_index"] = 2
            state["state"] = "unstable"
            anchor = trig.get("rect")
            if anchor:
                ax = (anchor[0] + anchor[2]) / 2 / settings.MAP_SCALE
                ay = (anchor[1] + anchor[3]) / 2 / settings.MAP_SCALE
                state["anchor_pos"] = (ax, ay)
            else:
                state["anchor_pos"] = self._player_map_pos()
            self.lab_branch = ""
            self._set_quest_stage("lab_choice")
        self._show_dialog(lines, title="逻辑错误实体")

    def _lab_on_enemies_cleared(self) -> None:
        if self.current_floor == "F35":
            if not self.archive_boss:
                self.combat_active = False
            return
        npc_state = self.lab_npc_state.get("logic_error_entity")
        if self.lab_branch == "fight" and npc_state and npc_state.get("state") == "hostile":
            npc_state["state"] = "defeated"
            self.floor_flags["lab_branch_resolved"] = True
            self._set_quest_stage("lab_switch")
            self._show_dialog(["指引者：异常数据已清除，前往终端完成授权。"], title="指引者")
        else:
            self._show_dialog(["指引者：干扰源消散，继续推进。"], title="指引者")

    def _handle_resonator_npc(self, trig: dict) -> None:
        if not self.resonator_state:
            self._show_dialog(["没有回应。"], title="提示")
            return
        if self.resonator_state.get("boss_state") == "defeated":
            self._show_dialog(["情绪回声已经解脱。"], title="情绪回声")
            return
        npc_id = trig.get("id", "")
        layout = self.resonator_state.get("npcs", {})
        npc = layout.get(npc_id)
        if not npc:
            self._show_dialog(["没有回应。"], title="提示")
            return
        spoken = self.resonator_state.setdefault("npc_dialogues", {})
        if spoken.get(npc_id):
            self._show_dialog(["回声逐渐安静下来。"], title="情绪回声")
            return
        dialog = npc.get("dialog", ["……"])
        self._show_dialog(dialog, title="情绪回声")
        spoken[npc_id] = True
        self.resonator_state["npc_spoken"] = int(self.resonator_state.get("npc_spoken", 0)) + 1

    def _handle_resonator_core(self, trig: dict) -> None:
        if not self.resonator_state:
            return
        state = self.resonator_state
        boss_state = state.get("boss_state", "dormant")
        if boss_state == "dormant":
            self._resonator_start_boss()
            return
        if boss_state == "active":
            self._show_dialog(["共鸣器正在失控，无法关闭。"], title="系统")
            return
        if boss_state == "defeated":
            self._show_dialog(["核心已熄灭，只留下微弱的余温。"], title="系统")
            return

    def _resonator_start_boss(self) -> None:
        if not self.resonator_state:
            return
        state = self.resonator_state
        if state.get("boss_state") != "dormant":
            return
        state.pop("boss_ready_timer", None)
        state["boss_state"] = "active"
        state["boss_phase"] = 0
        state["boss_fire_timer"] = 1.6
        state["boss_hp"] = float(state.get("boss_max_hp", state.get("boss_hp", 0.0)))
        if state.get("color_cycle"):
            state["active_mood"] = state["color_cycle"][0]
        self.combat_active = True
        self._set_quest_stage("resonator_boss")
        self._show_dialog(["指引者：情绪污染源激活，准备应对它的波动！"], title="指引者")

    def _resonator_color(self, mood: str) -> tuple[int, int, int]:
        palette = {
            "anger": (255, 100, 100),
            "sadness": (80, 200, 200),
            "fear": (140, 80, 180),
        }
        return palette.get(mood, (180, 180, 180))

    def _resonator_update_boss(self, dt: float) -> None:
        if not self.resonator_state:
            return
        state = self.resonator_state
        if state.get("boss_state") != "active":
            return
        hp = max(0.0, float(state.get("boss_hp", 0.0)))
        max_hp = max(1.0, float(state.get("boss_max_hp", 1.0)))
        ratio = hp / max_hp
        phase = int(state.get("boss_phase", 0))
        if ratio <= 0.75 and phase < 1:
            state["boss_phase"] = 1
            self._show_dialog(["共鸣器情绪切换：悲伤。"], title="系统")
        elif ratio <= 0.5 and phase < 2:
            state["boss_phase"] = 2
            self._show_dialog(["共鸣器情绪切换：恐惧。"], title="系统")
        elif ratio <= 0.25 and phase < 3:
            state["boss_phase"] = 3
            self._show_dialog(["共鸣器情绪切换：愤怒。"], title="系统")
        mood_cycle = state.get("color_cycle", ["anger", "sadness", "fear"])
        phase_index = int(state.get("boss_phase", 0))
        if phase_index < 3:
            state["active_mood"] = mood_cycle[min(phase_index, len(mood_cycle) - 1)]
        else:
            state["active_mood"] = mood_cycle[0]
        state["boss_fire_timer"] = max(0.0, float(state.get("boss_fire_timer", 0.0)) - dt)
        if state["boss_fire_timer"] <= 0.0:
            mood = state.get("active_mood", mood_cycle[0])
            state["active_mood"] = mood
            self._resonator_spawn_attack(mood)
            state["boss_fire_timer"] = 2.8 if mood == "sadness" else (2.2 if mood == "fear" else 1.8)
        flash_timer = float(state.get("boss_flash", 0.0))
        if flash_timer > 0.0:
            state["boss_flash"] = max(0.0, flash_timer - dt)
        if hp <= 0.0:
            state["boss_state"] = "defeated"
            self._resonator_on_boss_defeated()

    def _resonator_spawn_attack(self, mood: str) -> None:
        if not self.resonator_state or not self.map_data:
            return
        center = self.resonator_state.get("center", (0.0, 0.0))
        cx = center[0] * settings.MAP_SCALE
        cy = center[1] * settings.MAP_SCALE
        px = self.player_rect.centerx
        py = self.player_rect.centery
        dir_angle = math.atan2(py - cy, px - cx)
        if mood == "anger":
            spread = math.radians(18)
            speed_px = 360.0
            damage = 26.0
            radius = 10
            slow = 0.0
            offsets = [i for i in range(-2, 3)]
        elif mood == "sadness":
            spread = math.radians(14)
            speed_px = 220.0
            damage = 18.0
            radius = 12
            slow = 1.4
            offsets = [i for i in range(-3, 4)]
        else:
            for _ in range(3):
                offset = random.uniform(-50.0, 50.0)
                target_x = px + offset
                target_y = py + random.uniform(-50.0, 50.0)
                self.resonator_projectiles.append({
                    "kind": "vortex",
                    "x": target_x,
                    "y": target_y,
                    "timer": 0.7,
                    "radius": 42,
                    "color": self._resonator_color("fear"),
                    "damage": 22.0,
                })
            return
        color = self._resonator_color(mood)
        for idx in offsets:
            ang = dir_angle + idx * spread
            vx = math.cos(ang) * speed_px
            vy = math.sin(ang) * speed_px
            self.resonator_projectiles.append({
                "kind": "bolt",
                "x": cx,
                "y": cy,
                "vx": vx,
                "vy": vy,
                "ttl": 2.6,
                "radius": radius,
                "color": color,
                "damage": damage,
                "slow": slow,
            })

    def _resonator_update_projectiles(self, dt: float) -> None:
        if not self.resonator_projectiles or not self.map_data:
            return
        grid = self.map_data.collision_grid
        cell_px = self.map_data.cell_size * settings.MAP_SCALE
        max_y = len(grid)
        max_x = len(grid[0]) if max_y else 0
        player_radius = max(settings.PLAYER_SIZE) * 0.5
        next_proj: list[dict] = []
        for proj in self.resonator_projectiles:
            kind = proj.get("kind", "bolt")
            if kind == "bolt":
                ttl = proj.get("ttl", 0.0) - dt
                if ttl <= 0.0:
                    continue
                proj["ttl"] = ttl
                proj["x"] += proj.get("vx", 0.0) * dt
                proj["y"] += proj.get("vy", 0.0) * dt
                cx = int(proj["x"] // cell_px)
                cy = int(proj["y"] // cell_px)
                if cx < 0 or cy < 0 or cx >= max_x or cy >= max_y or grid[cy][cx] == 1:
                    continue
                dx = proj["x"] - self.player_rect.centerx
                dy = proj["y"] - self.player_rect.centery
                radius = proj.get("radius", 10) + player_radius
                if dx * dx + dy * dy <= radius * radius:
                    self._apply_player_damage(proj.get("damage", 16.0))
                    slow = float(proj.get("slow", 0.0))
                    if slow > 0.0 and self.resonator_state:
                        self.resonator_state["slow_timer"] = max(float(self.resonator_state.get("slow_timer", 0.0)), slow)
                    continue
                next_proj.append(proj)
            elif kind == "vortex":
                timer = proj.get("timer", 0.0) - dt
                if timer <= 0.0:
                    dx = proj["x"] - self.player_rect.centerx
                    dy = proj["y"] - self.player_rect.centery
                    radius = proj.get("radius", 36) + player_radius
                    if dx * dx + dy * dy <= radius * radius:
                        self._apply_player_damage(proj.get("damage", 18.0))
                    continue
                proj["timer"] = timer
                next_proj.append(proj)
        self.resonator_projectiles = next_proj

    def _resonator_on_boss_defeated(self) -> None:
        if not self.resonator_state:
            return
        self.resonator_projectiles = []
        self.combat_active = False
        self.resonator_state["log_available"] = True
        self.resonator_state["exit_unlocked"] = True
        self.resonator_state["active_mood"] = None
        self._set_quest_stage("resonator_log")
        self._show_dialog(["共鸣器熄灭，情绪被缓缓吸收。", "中央日志已生成。"], title="系统")

    def _draw_resonator_environment(self) -> None:
        self._draw_resonator_boss()
        self._draw_resonator_projectiles()
        self._draw_resonator_npcs()

    def _draw_resonator_npcs(self) -> None:
        if not self.resonator_state:
            return
        if self.resonator_state.get("boss_state") == "defeated":
            return
        layout = self.resonator_state.get("npcs", {})
        ox, oy = self.map_offset
        for npc_id, npc in layout.items():
            if npc_id == "resonator_npc_acceptance":
                continue
            asset_key = npc.get("asset", "")
            sprite = self.resonator_assets.get(asset_key)
            if not sprite:
                continue
            pos = npc.get("pos_scaled", npc.get("pos", (0.0, 0.0)))
            sx = int(pos[0] + ox)
            sy = int(pos[1] + oy)
            rect = sprite.get_rect(center=(sx, sy))
            self.screen.blit(sprite, rect)

    def _draw_resonator_projectiles(self) -> None:
        if not self.resonator_projectiles:
            return
        ox, oy = self.map_offset
        for proj in self.resonator_projectiles:
            kind = proj.get("kind", "bolt")
            if kind == "vortex":
                radius = int(proj.get("radius", 36))
                timer = float(proj.get("timer", 0.0))
                alpha = 140 if timer > 0.2 else 220
                surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                color = proj.get("color", (140, 80, 180))
                pygame.draw.circle(surf, (*color, alpha), (radius, radius), radius, width=2)
                self.screen.blit(surf, (int(proj["x"] + ox - radius), int(proj["y"] + oy - radius)))
            else:
                sx = int(proj["x"] + ox)
                sy = int(proj["y"] + oy)
                radius = int(proj.get("radius", 10))
                color = proj.get("color", (255, 100, 100))
                pygame.draw.circle(self.screen, color, (sx, sy), radius)

    def _draw_resonator_boss(self) -> None:
        if not self.resonator_state:
            return
        state = self.resonator_state
        center = state.get("center", (0.0, 0.0))
        ox, oy = self.map_offset
        cx = int(center[0] * settings.MAP_SCALE + ox)
        cy = int(center[1] * settings.MAP_SCALE + oy)
        mood = state.get("active_mood")
        if state.get("boss_state") == "defeated":
            color = (70, 80, 90)
        elif state.get("boss_state") == "dormant":
            mood_cycle = state.get("color_cycle", ["anger", "sadness", "fear"])
            mood = mood_cycle[int(state.get("color_index", 0)) % len(mood_cycle)]
        if mood and state.get("boss_state") != "defeated":
            color = self._resonator_color(str(mood))
        elif state.get("boss_state") != "defeated":
            color = (120, 240, 200)
        sprite = self.resonator_assets.get("resonator_core_placeholder")
        if sprite:
            rect = sprite.get_rect(center=(cx, cy))
            if state.get("boss_state") == "defeated":
                dim = sprite.copy()
                dim.set_alpha(90)
                self.screen.blit(dim, rect)
            else:
                self.screen.blit(sprite, rect)
            if state.get("boss_state") == "active":
                glow = pygame.Surface((rect.width + 16, rect.height + 16), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*color, 90), glow.get_rect(), width=4)
                self.screen.blit(glow, (rect.x - 8, rect.y - 8))
        else:
            pygame.draw.rect(self.screen, color, pygame.Rect(cx - 12, cy - 25, 24, 50))
        if state.get("boss_state") == "active":
            flash = float(state.get("boss_flash", 0.0))
            if flash > 0.0:
                overlay = pygame.Surface((40, 70), pygame.SRCALPHA)
                overlay.fill((255, 255, 255, int(180 * min(1.0, flash / 0.12))))
                self.screen.blit(overlay, (cx - 20, cy - 35))
            self._draw_resonator_boss_healthbar()

    def _draw_resonator_boss_healthbar(self) -> None:
        if not self.resonator_state:
            return
        state = self.resonator_state
        hp = float(state.get("boss_hp", 0.0))
        max_hp = float(state.get("boss_max_hp", 1.0))
        if max_hp <= 0:
            return
        ratio = max(0.0, min(1.0, hp / max_hp))
        width, height = 180, 10
        x = (settings.WINDOW_WIDTH - width) // 2
        y = 84
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (30, 34, 45), bg_rect)
        if ratio > 0:
            fill_rect = bg_rect.copy()
            fill_rect.width = int(width * ratio)
            pygame.draw.rect(self.screen, (255, 120, 160), fill_rect)
        pygame.draw.rect(self.screen, (200, 220, 235), bg_rect, 1)

    def _render(self) -> None:
        if self.in_menu:
            self.start_menu.draw()
            pygame.display.flip()
            return
        if self.intro_active:
            self._render_intro()
            pygame.display.flip()
            return
        if self.cutscene_active:
            # keep camera locked to player during cutscene
            self._update_camera()
            self._render_play_base()
            self._draw_cutscene_dialog()
            pygame.display.flip()
            return
        self._render_play_base()
        pygame.display.flip()

    def _render_play_base(self) -> None:
        self.screen.fill(settings.BACKGROUND_COLOR)
        if self.map_surface:
            self.screen.blit(self.map_surface, self.map_offset)
        if self.current_floor == "F40":
            self._draw_lab_environment()
        elif self.current_floor == "F35":
            self._draw_archive_elements()
        elif self.current_floor == "F30":
            self._draw_logic_environment()
        elif self.current_floor == "F25":
            self._draw_resonator_environment()
        self._draw_enemy_attack_fx()
        self._draw_enemies()
        self._draw_bullets()
        player_screen_pos = (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2)
        if self.player_sprite:
            sprite_rect = self.player_sprite.get_rect(center=player_screen_pos)
            self.screen.blit(self.player_sprite, sprite_rect)
        else:
            pygame.draw.rect(self.screen, settings.PLAYER_COLOR, pygame.Rect(0, 0, *settings.PLAYER_SIZE).move(
                player_screen_pos[0] - settings.PLAYER_SIZE[0] // 2, player_screen_pos[1] - settings.PLAYER_SIZE[1] // 2))
        if self.player_hit_timer > 0.0:
            self._draw_player_hit_flash()

        self._render_minimap()
        self._draw_quest_hud()
        health_rect = self._draw_player_health_hud()
        ammo_rect = self._draw_ammo_hud(health_rect)
        self._draw_reload_bar(ammo_rect)
        self._draw_prompt()
        self._draw_dialog()
        self._draw_debug_coords()
        self._draw_click_feedback()
        if self.debug_menu_active:
            self._draw_debug_menu()

    def _load_player_sprite(self) -> pygame.Surface | None:
        if settings.PLAYER_SPRITE.exists():
            sprite = pygame.image.load(str(settings.PLAYER_SPRITE)).convert_alpha()
            w, h = sprite.get_size()
            return pygame.transform.scale(sprite, (int(w * settings.PLAYER_SCALE), int(h * settings.PLAYER_SCALE)))
        return None

    def _load_archive_boss_sprite(self) -> pygame.Surface | None:
        path = getattr(settings, "ARCHIVE_BOSS_IMAGE", None)
        if not path:
            return None
        if not isinstance(path, Path):
            try:
                path = Path(path)
            except TypeError:
                return None
        if not path.exists():
            return None
        try:
            sprite = pygame.image.load(str(path)).convert_alpha()
        except Exception:
            return None
        sprite = self._apply_transparent_background(sprite)
        if settings.MAP_SCALE != 1:
            w, h = sprite.get_size()
            scaled = pygame.transform.scale(sprite, (int(w * settings.MAP_SCALE), int(h * settings.MAP_SCALE)))
            color_key = sprite.get_colorkey()
            if color_key is not None:
                scaled.set_colorkey(color_key)
            return scaled
        return sprite

    def _apply_transparent_background(self, surface: pygame.Surface) -> pygame.Surface:
        if not surface:
            return surface
        try:
            corner = surface.get_at((0, 0))
        except Exception:
            return surface
        if len(corner) == 4 and corner[3] == 0:
            return surface
        surface.set_colorkey(corner)
        return surface

    def _resonator_load_assets(self) -> None:
        if self.resonator_assets:
            return
        asset_map = {
            "resonator_npc_anger": "Floor25_npc_1.png",
            "resonator_npc_sadness": "Floor25_npc_2.png",
            "resonator_npc_confusion": "Floor25_npc_3.png",
            "resonator_npc_betrayal": "Floor25_npc_4.png",
            "resonator_npc_despair": "Floor25_npc_5.png",
            "resonator_npc_fear": "Floor25_npc_6.png",
        }
        for key, filename in asset_map.items():
            path = settings.IMAGES_DIR / filename
            if not path.exists():
                continue
            try:
                sprite = pygame.image.load(str(path)).convert_alpha()
            except Exception:
                continue
            if settings.MAP_SCALE != 1:
                w, h = sprite.get_size()
                sprite = pygame.transform.scale(sprite, (int(w * settings.MAP_SCALE), int(h * settings.MAP_SCALE)))
            sprite = self._apply_transparent_background(sprite)
            self.resonator_assets[key] = sprite
        if "resonator_core_placeholder" not in self.resonator_assets:
            width = int(24 * settings.MAP_SCALE)
            height = int(50 * settings.MAP_SCALE)
            width = max(12, width)
            height = max(20, height)
            surf = pygame.Surface((width, height), pygame.SRCALPHA)
            surf.fill((120, 240, 200, 210))
            pygame.draw.rect(surf, (40, 150, 130, 240), surf.get_rect(), width=3)
            self.resonator_assets["resonator_core_placeholder"] = surf

    def _resonator_entities(self) -> dict[str, dict]:
        layout = {
            "resonator_npc_anger": {
                "asset": "resonator_npc_anger",
                "pos": (108.0, 86.0),
                "dialog": [
                    "They told us we were special! That we were saving humanity! LIES! We're fuel! Cannon fodder for their experiment!",
                ],
            },
            "resonator_npc_sadness": {
                "asset": "resonator_npc_sadness",
                "pos": (116.0, 232.0),
                "dialog": [
                    "I remember... a garden. Was it real? It's fading... everything is fading... Please, don't let me forget...",
                ],
            },
            "resonator_npc_fear": {
                "asset": "resonator_npc_fear",
                "pos": (72.0, 160.0),
                "dialog": [
                    "It watches us. Always watching. From behind the screens. Don't look up! It doesn't like to be seen!",
                ],
            },
            "resonator_npc_despair": {
                "asset": "resonator_npc_despair",
                "pos": (204.0, 232.0),
                "dialog": [
                    "Just leave us. It's over. The cycle always continues. You're not the first 'Custodian'... you won't be the last.",
                ],
            },
            "resonator_npc_confusion": {
                "asset": "resonator_npc_confusion",
                "pos": (248.0, 160.0),
                "dialog": [
                    "The numbers... they don't add up. The physics is wrong. This place... it's a patchwork. A cheap imitation.",
                ],
            },
            "resonator_npc_betrayal": {
                "asset": "resonator_npc_betrayal",
                "pos": (212.0, 86.0),
                "dialog": [
                    "I trusted the System. I did everything it asked. And for what? To be discarded like a broken tool?",
                ],
            },
            "resonator_npc_acceptance": {
                "asset": "resonator_core_placeholder",
                "pos": (160.0, 160.0),
                "dialog": [
                    "Maybe... this is what we are now. Maybe there never was a before. This pain, this joy... it's all we have. Is that so bad?",
                ],
            },
        }
        scale = settings.MAP_SCALE
        for data in layout.values():
            px, py = data["pos"]
            data["pos_scaled"] = (px * scale, py * scale)
        return layout

    def _load_player_walk_frames(self) -> list[pygame.Surface]:
        frames: list[pygame.Surface] = []
        path = settings.PLAYER_WALK_SHEET
        if not path.exists():
            return frames
        try:
            sheet = pygame.image.load(str(path)).convert_alpha()
        except Exception:
            return frames
        frame_count = max(1, settings.PLAYER_WALK_FRAMES)
        frame_width = sheet.get_width() // frame_count
        frame_height = sheet.get_height()
        if frame_width <= 0 or frame_height <= 0:
            return frames
        for idx in range(frame_count):
            rect = pygame.Rect(idx * frame_width, 0, frame_width, frame_height)
            frame = sheet.subsurface(rect).copy()
            if settings.PLAYER_SCALE != 1:
                scaled_w = int(frame_width * settings.PLAYER_SCALE)
                scaled_h = int(frame_height * settings.PLAYER_SCALE)
                frame = pygame.transform.scale(frame, (scaled_w, scaled_h))
            frames.append(frame)
        return frames

    def _default_player_sprite(self) -> pygame.Surface | None:
        if getattr(self, "_player_idle_sprite", None):
            return self._player_idle_sprite
        if getattr(self, "_player_walk_frames", []):
            return self._player_walk_frames[0]
        return None

    def _update_player_animation(self, moving: bool, dt: float) -> None:
        if not moving:
            self._player_anim_timer = 0.0
            self._player_anim_index = 0
            self.player_sprite = self._default_player_sprite()
            self._player_was_moving = False
            return
        if not self._player_walk_frames:
            self.player_sprite = self._default_player_sprite()
            self._player_was_moving = False
            return
        fps = max(1, settings.PLAYER_WALK_FPS)
        frame_time = 1.0 / fps
        if not self._player_was_moving:
            self._player_anim_timer = frame_time
            self._player_anim_index = 0
        self._player_anim_timer += dt
        while self._player_anim_timer >= frame_time:
            self._player_anim_timer -= frame_time
            self._player_anim_index = (self._player_anim_index + 1) % len(self._player_walk_frames)
        self.player_sprite = self._player_walk_frames[self._player_anim_index]
        self._player_was_moving = True

    def _resolve_font(self) -> Path | None:
        candidates = []
        if settings.FONTS_DIR.exists():
            for p in sorted(settings.FONTS_DIR.iterdir()):
                if p.is_file() and p.suffix.lower() in {".ttf", ".otf"}:
                    candidates.append(p)
        preferred = [p for p in candidates if "notosanssc" in p.name.lower()]
        if preferred:
            return preferred[0]
        return candidates[0] if candidates else None

    def _load_font(self, size: int) -> pygame.font.Font:
        if hasattr(self, "font_path") and self.font_path and self.font_path.exists():
            try:
                return pygame.font.Font(str(self.font_path), size)
            except Exception:
                pass
        return pygame.font.SysFont(settings.UI_FONT_NAME, size)

    def _map_coords_from_screen(self, pos: tuple[int, int]) -> tuple[int, int]:
        x, y = pos
        return (
            x - self.map_offset[0],
            y - self.map_offset[1],
        )

    def _handle_right_click(self, screen_pos: tuple[int, int]) -> None:
        if not self.map_data:
            return
        map_x, map_y = self._map_coords_from_screen(screen_pos)
        map_w = self.map_surface.get_width() if self.map_surface else 0
        map_h = self.map_surface.get_height() if self.map_surface else 0
        if not (0 <= map_x < map_w and 0 <= map_y < map_h):
            return
        # Convert to grid
        cell = self.map_data.cell_size * settings.MAP_SCALE
        start = (self.player_rect.centerx // cell, self.player_rect.centery // cell)
        goal = (int(map_x) // cell, int(map_y) // cell)
        self._start_click_feedback(map_x, map_y)
        path_nodes = pathfinding.astar(
            self.map_data.collision_grid,
            start,
            goal,
            settings.PASSABLE_VALUES,
            cell_size=self.map_data.cell_size,
            actor_size=settings.PLAYER_SIZE,
        )
        if len(path_nodes) <= 1:
            nearest = pathfinding.nearest_reachable(
                self.map_data.collision_grid,
                start,
                goal,
                settings.PASSABLE_VALUES,
                cell_size=self.map_data.cell_size,
                actor_size=settings.PLAYER_SIZE,
                max_distance_px=10,
            )
            if nearest and nearest != start:
                path_nodes = pathfinding.astar(
                    self.map_data.collision_grid,
                    start,
                    nearest,
                    settings.PASSABLE_VALUES,
                    cell_size=self.map_data.cell_size,
                    actor_size=settings.PLAYER_SIZE,
                )
                if len(path_nodes) > 1:
                    goal = nearest
                    map_x = goal[0] * cell + cell // 2
                    map_y = goal[1] * cell + cell // 2

        self.path = path_nodes[1:] if len(path_nodes) > 1 else []
        self.path_target = (map_x, map_y) if self.path else None
        self.path_goal_cell = goal if self.path else None

    def _move_player(self, dx: int, dy: int) -> bool:
        if not self.map_data:
            return False
        before = self.player_rect.center
        # offset collider downward to align with legs
        collider = self.player_rect.copy()
        collider.move_ip(0, settings.PLAYER_COLLIDER_OFFSET_Y * settings.MAP_SCALE)
        moved = collision.move_with_collision(
            collider,
            (dx, dy),
            self.map_data.collision_grid,
            cell_size=self.map_data.cell_size * settings.MAP_SCALE,
            substep=settings.COLLISION_SUBSTEP,
        )
        # move visual rect to keep relative offset
        moved.move_ip(0, -settings.PLAYER_COLLIDER_OFFSET_Y * settings.MAP_SCALE)
        self.player_rect = moved
        return self.player_rect.center != before

    def _manual_axis(self, keys: pygame.key.ScancodeWrapper, dt: float) -> tuple[int, int]:
        # WASD/arrow with cancellation rules; speed matches auto-path (player_move_speed)
        if self.player_dead:
            return (0, 0)
        def held(key_codes: tuple[int, ...]) -> bool:
            return any(keys[kc] for kc in key_codes if kc < len(keys)) or any((kc in self._keys_down) for kc in key_codes)

        left = self._held_dirs["left"] or held((pygame.K_a, pygame.K_LEFT))
        right = self._held_dirs["right"] or held((pygame.K_d, pygame.K_RIGHT))
        up = self._held_dirs["up"] or held((pygame.K_w, pygame.K_UP))
        down = self._held_dirs["down"] or held((pygame.K_s, pygame.K_DOWN))

        # conflict lock: if both pressed, axis stays 0 until both released
        if left and right:
            self._conflict_x = True
        if up and down:
            self._conflict_y = True
        if not left and not right:
            self._conflict_x = False
        if not up and not down:
            self._conflict_y = False

        vx = 0
        vy = 0
        if not self._conflict_x:
            if left:
                vx = -1
            elif right:
                vx = 1
        if not self._conflict_y:
            if up:
                vy = -1
            elif down:
                vy = 1

        if vx == 0 and vy == 0:
            return 0, 0

        speed = self.player_move_speed * dt
        if vx != 0 and vy != 0:
            speed /= 2 ** 0.5
        dx = int(round(vx * speed))
        dy = int(round(vy * speed))
        return dx, dy

    def _start_reload(self) -> None:
        if self.reload_timer > 0:
            return
        if self.ammo_in_clip >= settings.GUN_CLIP_SIZE:
            return
        self.reload_timer = settings.GUN_RELOAD_TIME

    def _try_fire(self) -> None:
        if not self.map_data or self.player_dead:
            return
        if self.reload_timer > 0:
            return
        if self.fire_cooldown > 0:
            return
        if self.ammo_in_clip <= 0:
            self._start_reload()
            return
        # direction from player to mouse cursor in map space
        mx, my = pygame.mouse.get_pos()
        px, py = self.player_rect.center
        dir_x = mx - (settings.WINDOW_WIDTH // 2)
        dir_y = my - (settings.WINDOW_HEIGHT // 2)
        dist = (dir_x * dir_x + dir_y * dir_y) ** 0.5
        if dist == 0:
            return
        norm_x = dir_x / dist
        norm_y = dir_y / dist
        speed = settings.GUN_BULLET_SPEED
        vx = norm_x * speed
        vy = norm_y * speed
        self.bullets.append({
            "x": float(px),
            "y": float(py),
            "vx": vx,
            "vy": vy,
            "ttl": settings.GUN_BULLET_LIFETIME,
        })
        self.ammo_in_clip -= 1
        self.fire_cooldown = settings.GUN_FIRE_COOLDOWN
        if self.ammo_in_clip <= 0:
            self._start_reload()

    def _update_bullets(self, dt: float) -> None:
        if not self.map_data:
            return
        if self.fire_cooldown > 0:
            self.fire_cooldown = max(0.0, self.fire_cooldown - dt)
        if self.reload_timer > 0:
            self.reload_timer = max(0.0, self.reload_timer - dt)
            if self.reload_timer == 0.0:
                self.ammo_in_clip = settings.GUN_CLIP_SIZE
        cell_px = self.map_data.cell_size * settings.MAP_SCALE
        max_y = len(self.map_data.collision_grid)
        max_x = len(self.map_data.collision_grid[0]) if max_y else 0
        next_bullets: list[dict] = []
        for b in self.bullets:
            b["ttl"] -= dt
            if b["ttl"] <= 0:
                continue
            b["x"] += b["vx"] * dt
            b["y"] += b["vy"] * dt
            # enemy hit check
            hit_enemy = None
            hit_radius_sq = (settings.ENEMY_RADIUS + settings.GUN_BULLET_RADIUS) ** 2
            for enemy in self.enemies:
                if enemy.get("state") == "dying":
                    continue
                dx = enemy["x"] - b["x"]
                dy = enemy["y"] - b["y"]
                if dx * dx + dy * dy <= hit_radius_sq:
                    hit_enemy = enemy
                    break
            if hit_enemy:
                max_hp = float(hit_enemy.get("max_hp", settings.ENEMY_MAX_HEALTH))
                current_hp = float(hit_enemy.get("hp", max_hp))
                current_hp = max(0.0, current_hp - settings.PLAYER_BULLET_DAMAGE)
                hit_enemy["hp"] = current_hp
                hit_enemy["max_hp"] = max_hp
                hit_enemy["flash_timer"] = settings.ENEMY_HIT_FLASH_TIME
                hit_enemy["show_health"] = settings.ENEMY_HEALTH_BAR_VIS_DURATION
                hit_enemy["aggro"] = True
                if hit_enemy.get("state") == "idle":
                    hit_enemy["state"] = "aggro"
                if current_hp <= 0.0 and hit_enemy.get("state") != "dying":
                    hit_enemy["state"] = "dying"
                    hit_enemy["fade_timer"] = settings.ENEMY_FADE_DURATION
                    hit_enemy["attack_anim_timer"] = 0.0
                continue  # bullet consumed on hit

            if self.archive_boss and self.archive_boss.get("state") != "dying":
                dx_b = self.archive_boss.get("x", 0.0) - b["x"]
                dy_b = self.archive_boss.get("y", 0.0) - b["y"]
                radius = self.archive_boss.get("hit_radius", 78.0) + settings.GUN_BULLET_RADIUS
                if dx_b * dx_b + dy_b * dy_b <= radius * radius:
                    hp = max(0.0, float(self.archive_boss.get("hp", 0.0)) - settings.PLAYER_BULLET_DAMAGE)
                    self.archive_boss["hp"] = hp
                    self.archive_boss["flash"] = 0.12
                    continue

            if self.current_floor == "F25" and self.resonator_state and self.resonator_state.get("boss_state") != "defeated":
                center = self.resonator_state.get("center", (0.0, 0.0))
                cx = center[0] * settings.MAP_SCALE
                cy = center[1] * settings.MAP_SCALE
                sprite = self.resonator_assets.get("resonator_core_placeholder")
                if sprite:
                    hit_radius = max(sprite.get_width(), sprite.get_height()) * 0.45
                else:
                    hit_radius = 30.0
                dx_b = cx - b["x"]
                dy_b = cy - b["y"]
                radius = hit_radius + settings.GUN_BULLET_RADIUS
                if dx_b * dx_b + dy_b * dy_b <= radius * radius:
                    if self.resonator_state.get("boss_state") == "dormant":
                        self._resonator_start_boss()
                    hp = max(0.0, float(self.resonator_state.get("boss_hp", 0.0)) - settings.PLAYER_BULLET_DAMAGE)
                    self.resonator_state["boss_hp"] = hp
                    self.resonator_state["boss_flash"] = 0.12
                    continue

            cx = int(b["x"] // cell_px)
            cy = int(b["y"] // cell_px)
            if cx < 0 or cy < 0 or cx >= max_x or cy >= max_y:
                continue
            if self.map_data.collision_grid[cy][cx] == 1:
                continue
            next_bullets.append(b)
        self.bullets = next_bullets

    def _apply_player_damage(self, amount: float) -> None:
        if amount <= 0 or self.player_dead:
            return
        self.player_health = max(0.0, self.player_health - float(amount))
        self.player_hit_timer = max(self.player_hit_timer, settings.PLAYER_HIT_FLASH_TIME)
        self._reset_regen_cooldown()
        if self.player_health <= 0.0:
            self._handle_player_death()

    def _handle_player_death(self) -> None:
        if self.player_dead:
            return
        self.player_dead = True
        self.combat_active = False
        self.path = []
        self.path_target = None
        self.path_goal_cell = None
        self._show_dialog(["系统：生命体征归零。", "按 Enter 返回标题界面。"], title="警告")
        self.dialog_timer = 0.0
        self._reset_regen_cooldown()

    def _reset_regen_cooldown(self) -> None:
        self.regen_cooldown = settings.PLAYER_REGEN_COOLDOWN
        self.regen_active = False

    def _restart_to_menu(self) -> None:
        self.start_menu.reset()
        self.current_floor = settings.START_FLOOR
        self._load_floor(settings.MAP_FILES[self.current_floor], preserve_health=False)
        self.in_menu = True

    def _start_frame_combat(self) -> None:
        if self.combat_active:
            return
        self._spawn_tutorial_enemies()
        if self.enemies:
            self._set_quest_stage("combat")
            self.combat_active = True
        else:
            self._set_quest_stage("log")
            self.combat_active = False

    def _update_enemies(self, dt: float) -> None:
        if not self.enemies:
            self.any_enemy_aggro = False
            return
        remaining: list[dict] = []
        removed_any = False
        any_aggro = False
        px, py = self.player_rect.center
        aggro_sq = settings.ENEMY_AGGRO_RADIUS ** 2
        lose_sq = settings.ENEMY_LOSE_INTEREST_RADIUS ** 2
        attack_range = settings.ENEMY_ATTACK_RANGE
        for enemy in self.enemies:
            enemy.setdefault("hp", float(settings.ENEMY_MAX_HEALTH))
            enemy.setdefault("max_hp", float(settings.ENEMY_MAX_HEALTH))
            enemy.setdefault("state", "idle")
            enemy.setdefault("aggro", False)
            enemy.setdefault("show_health", 0.0)
            enemy.setdefault("attack_timer", random.uniform(0.1, settings.ENEMY_ATTACK_COOLDOWN))
            enemy.setdefault("attack_anim_timer", 0.0)
            if enemy.get("flash_timer", 0.0) > 0.0:
                enemy["flash_timer"] = max(0.0, enemy["flash_timer"] - dt)
            if enemy.get("show_health", 0.0) > 0.0:
                enemy["show_health"] = max(0.0, enemy["show_health"] - dt)
            if enemy.get("state") == "dying":
                fade = enemy.get("fade_timer", settings.ENEMY_FADE_DURATION) - dt
                enemy["fade_timer"] = fade
                if fade <= 0.0:
                    removed_any = True
                    continue
                remaining.append(enemy)
                continue

            dx = px - enemy["x"]
            dy = py - enemy["y"]
            dist_sq = dx * dx + dy * dy

            aggro = False
            if not self.player_dead:
                if enemy.get("aggro", False):
                    aggro = dist_sq <= lose_sq
                else:
                    aggro = dist_sq <= aggro_sq
            enemy["aggro"] = aggro

            if enemy.get("attack_anim_timer", 0.0) > 0.0:
                enemy["attack_anim_timer"] = max(0.0, enemy["attack_anim_timer"] - dt)
                if enemy["attack_anim_timer"] <= 0.0 and enemy.get("state") == "attacking":
                    enemy["state"] = "aggro"

            if not aggro:
                enemy["state"] = "idle"
                enemy["attack_timer"] = max(0.0, enemy.get("attack_timer", 0.0) - dt)
                remaining.append(enemy)
                continue

            any_aggro = True
            enemy["state"] = "aggro"
            dist = max(0.0001, math.sqrt(dist_sq))
            enemy["attack_timer"] = max(0.0, enemy.get("attack_timer", 0.0) - dt)

            if dist > attack_range and not self.player_dead:
                step = settings.ENEMY_MOVE_SPEED * dt
                if step > 0:
                    move_x = int(round(dx / dist * step))
                    move_y = int(round(dy / dist * step))
                    if move_x or move_y:
                        self._move_enemy(enemy, move_x, move_y)
            elif dist <= attack_range and enemy["attack_timer"] <= 0.0:
                self._apply_player_damage(settings.ENEMY_ATTACK_DAMAGE)
                enemy["attack_timer"] = settings.ENEMY_ATTACK_COOLDOWN
                enemy["state"] = "attacking"
                enemy["attack_anim_timer"] = settings.ENEMY_ATTACK_ANIM_TIME
                enemy["show_health"] = settings.ENEMY_HEALTH_BAR_VIS_DURATION
                enemy["flash_timer"] = settings.ENEMY_ATTACK_FLASH_TIME
                self._spawn_enemy_attack_fx(enemy)

            remaining.append(enemy)
        self.enemies = remaining
        self.any_enemy_aggro = any_aggro
        if removed_any and not self.enemies and self.combat_active:
            self._on_enemies_cleared()

    def _move_enemy(self, enemy: dict, dx: int, dy: int) -> None:
        if not self.map_data or (dx == 0 and dy == 0):
            return
        r = settings.ENEMY_RADIUS
        collider = pygame.Rect(0, 0, r * 2, r * 2)
        collider.center = (int(enemy.get("x", 0.0)), int(enemy.get("y", 0.0)))
        moved = collision.move_with_collision(
            collider,
            (dx, dy),
            self.map_data.collision_grid,
            cell_size=self.map_data.cell_size * settings.MAP_SCALE,
            substep=settings.COLLISION_SUBSTEP,
        )
        enemy["x"] = float(moved.centerx)
        enemy["y"] = float(moved.centery)

    def _spawn_enemy_attack_fx(self, enemy: dict) -> None:
        duration = settings.ENEMY_ATTACK_FX_DURATION
        self.enemy_attack_fx.append({
            "x": float(enemy.get("x", 0.0)),
            "y": float(enemy.get("y", 0.0)),
            "timer": duration,
            "duration": duration,
        })

    def _update_enemy_attack_fx(self, dt: float) -> None:
        if not self.enemy_attack_fx:
            return
        active: list[dict] = []
        for fx in self.enemy_attack_fx:
            timer = fx.get("timer", 0.0) - dt
            if timer <= 0.0:
                continue
            fx["timer"] = timer
            active.append(fx)
        self.enemy_attack_fx = active

    def _draw_enemy_attack_fx(self) -> None:
        if not self.enemy_attack_fx:
            return
        max_radius = settings.ENEMY_ATTACK_FX_MAX_RADIUS
        for fx in self.enemy_attack_fx:
            duration = max(0.001, fx.get("duration", settings.ENEMY_ATTACK_FX_DURATION))
            progress = 1.0 - fx.get("timer", 0.0) / duration
            radius = max(6, int(max_radius * progress))
            alpha = max(0, min(180, int(200 * (1.0 - progress))))
            surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            color = (*settings.ENEMY_COLOR, alpha)
            pygame.draw.circle(surf, color, (radius, radius), radius, width=3)
            sx = int(fx["x"] + self.map_offset[0]) - radius
            sy = int(fx["y"] + self.map_offset[1]) - radius
            self.screen.blit(surf, (sx, sy))

    def _draw_player_hit_flash(self) -> None:
        if self.player_hit_timer <= 0.0:
            return
        if settings.PLAYER_HIT_FLASH_TIME <= 0.0:
            return
        progress = max(0.0, min(1.0, self.player_hit_timer / settings.PLAYER_HIT_FLASH_TIME))
        alpha = int(settings.PLAYER_HIT_FLASH_COLOR[3] * progress)
        if alpha <= 0:
            return
        size = int(150 + 60 * (1.0 - progress))
        overlay = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(
            overlay,
            (*settings.PLAYER_HIT_FLASH_COLOR[:3], alpha),
            (size // 2, size // 2),
            size // 2,
        )
        x = settings.WINDOW_WIDTH // 2 - size // 2
        y = settings.WINDOW_HEIGHT // 2 - size // 2
        self.screen.blit(overlay, (x, y))

    def _start_log_sequence(self) -> None:
        pass


    def _spawn_tutorial_enemies(self) -> None:
        if not self.map_surface or not self.map_data:
            self.enemies = []
            return
        if self.current_floor == "F50":
            manual_points = [(170, 200), (220, 200), (195, 225)]
            manual_spawns: list[dict] = []
            grid = self.map_data.collision_grid
            cell_size = max(1, self.map_data.cell_size)
            max_y = len(grid)
            max_x = len(grid[0]) if max_y else 0
            scale = settings.MAP_SCALE
            for map_x, map_y in manual_points:
                gx = int(map_x // cell_size)
                gy = int(map_y // cell_size)
                if not (0 <= gx < max_x and 0 <= gy < max_y):
                    continue
                if grid[gy][gx] not in settings.PASSABLE_VALUES:
                    continue
                px = int(map_x * scale)
                py = int(map_y * scale)
                manual_spawns.append({
                    "x": float(px),
                    "y": float(py),
                    "hp": float(settings.ENEMY_MAX_HEALTH),
                    "max_hp": float(settings.ENEMY_MAX_HEALTH),
                    "state": "idle",
                    "fade_timer": settings.ENEMY_FADE_DURATION,
                    "flash_timer": 0.0,
                    "aggro": False,
                    "show_health": 0.0,
                    "attack_timer": random.uniform(0.3, settings.ENEMY_ATTACK_COOLDOWN),
                    "attack_anim_timer": 0.0,
                })
            if len(manual_spawns) == len(manual_points):
                self.enemies = manual_spawns
                return
        base_x, base_y = self.player_rect.center
        grid_w, grid_h = self.map_data.grid_size
        cell_px = self.map_data.cell_size * settings.MAP_SCALE
        start_cell = (
            max(0, min(grid_w - 1, int(base_x // cell_px))),
            max(0, min(grid_h - 1, int(base_y // cell_px))),
        )
        accessible = self._collect_accessible_cells(start_cell, settings.ENEMY_SPAWN_BFS_STEPS)
        if not accessible:
            self.enemies = []
            return
        taken_cells: set[tuple[int, int]] = {start_cell}
        offsets = [(120, -40), (-120, 40), (0, 120), (160, 0), (-160, 0), (0, -160)]
        spawned: list[dict] = []
        max_cell_distance = max(4, settings.ENEMY_SPAWN_MAX_CELL_DISTANCE)
        for ox, oy in offsets:
            desired_cell = (
                max(0, min(grid_w - 1, int((base_x + ox) // cell_px))),
                max(0, min(grid_h - 1, int((base_y + oy) // cell_px))),
            )
            spawn_cell = self._pick_spawn_cell(desired_cell, accessible, taken_cells, max_cell_distance)
            if not spawn_cell:
                continue
            taken_cells.add(spawn_cell)
            cx = spawn_cell[0] * cell_px + cell_px // 2
            cy = spawn_cell[1] * cell_px + cell_px // 2
            spawned.append({
                "x": float(cx),
                "y": float(cy),
                "hp": float(settings.ENEMY_MAX_HEALTH),
                "max_hp": float(settings.ENEMY_MAX_HEALTH),
                "state": "idle",
                "fade_timer": settings.ENEMY_FADE_DURATION,
                "flash_timer": 0.0,
                "aggro": False,
                "show_health": 0.0,
                "attack_timer": random.uniform(0.3, settings.ENEMY_ATTACK_COOLDOWN),
                "attack_anim_timer": 0.0,
            })
            if len(spawned) >= 3:
                break
        if len(spawned) < 3:
            for cell in accessible:
                if len(spawned) >= 3:
                    break
                if cell in taken_cells:
                    continue
                dist_start = abs(cell[0] - start_cell[0]) + abs(cell[1] - start_cell[1])
                if dist_start == 0:
                    continue
                taken_cells.add(cell)
                cx = cell[0] * cell_px + cell_px // 2
                cy = cell[1] * cell_px + cell_px // 2
                spawned.append({
                    "x": float(cx),
                    "y": float(cy),
                    "hp": float(settings.ENEMY_MAX_HEALTH),
                    "max_hp": float(settings.ENEMY_MAX_HEALTH),
                    "state": "idle",
                    "fade_timer": settings.ENEMY_FADE_DURATION,
                    "flash_timer": 0.0,
                    "aggro": False,
                    "show_health": 0.0,
                    "attack_timer": random.uniform(0.3, settings.ENEMY_ATTACK_COOLDOWN),
                    "attack_anim_timer": 0.0,
                })
        if len(spawned) < 3 and self.map_surface:
            map_w, map_h = self.map_surface.get_size()
            fallback_offsets = [(150, 0), (-150, 0), (0, 150), (0, -150), (180, 90), (-180, -90)]
            for ox, oy in fallback_offsets:
                if len(spawned) >= 3:
                    break
                px = max(0, min(map_w - 1, int(base_x + ox)))
                py = max(0, min(map_h - 1, int(base_y + oy)))
                cell = (max(0, min(grid_w - 1, px // cell_px)), max(0, min(grid_h - 1, py // cell_px)))
                if cell in taken_cells:
                    continue
                if self.map_data.collision_grid[cell[1]][cell[0]] not in settings.PASSABLE_VALUES:
                    continue
                taken_cells.add(cell)
                cx = cell[0] * cell_px + cell_px // 2
                cy = cell[1] * cell_px + cell_px // 2
                spawned.append({
                    "x": float(cx),
                    "y": float(cy),
                    "hp": float(settings.ENEMY_MAX_HEALTH),
                    "max_hp": float(settings.ENEMY_MAX_HEALTH),
                    "state": "idle",
                    "fade_timer": settings.ENEMY_FADE_DURATION,
                    "flash_timer": 0.0,
                    "aggro": False,
                    "show_health": 0.0,
                    "attack_timer": random.uniform(0.3, settings.ENEMY_ATTACK_COOLDOWN),
                    "attack_anim_timer": 0.0,
                })
        self.enemies = spawned

    def _collect_accessible_cells(self, start_cell: tuple[int, int], max_steps: int) -> list[tuple[int, int]]:
        if not self.map_data:
            return []
        grid = self.map_data.collision_grid
        passable = settings.PASSABLE_VALUES
        cell_size = self.map_data.cell_size
        cells_x = max(1, (settings.PLAYER_SIZE[0] + cell_size - 1) // cell_size)
        cells_y = max(1, (settings.PLAYER_SIZE[1] + cell_size - 1) // cell_size)
        radius_x = (cells_x - 1) // 2
        radius_y = (cells_y - 1) // 2
        queue: deque[tuple[tuple[int, int], int]] = deque([(start_cell, 0)])
        visited: set[tuple[int, int]] = {start_cell}
        cells: list[tuple[int, int]] = [start_cell]
        while queue:
            (cx, cy), depth = queue.popleft()
            if depth >= max_steps:
                continue
            for (nx, ny), _ in pathfinding.neighbors(
                cx,
                cy,
                grid,
                passable,
                radius_x=radius_x,
                radius_y=radius_y,
            ):
                if (nx, ny) in visited:
                    continue
                visited.add((nx, ny))
                queue.append(((nx, ny), depth + 1))
                cells.append((nx, ny))
        return cells

    def _pick_spawn_cell(
        self,
        desired_cell: tuple[int, int],
        accessible_cells: list[tuple[int, int]],
        taken_cells: set[tuple[int, int]],
        max_distance: int,
    ) -> tuple[int, int] | None:
        best_cell: tuple[int, int] | None = None
        best_score = 1_000_000
        for cell in accessible_cells:
            if cell in taken_cells:
                continue
            dist = abs(cell[0] - desired_cell[0]) + abs(cell[1] - desired_cell[1])
            if dist > max_distance:
                continue
            if dist < best_score:
                best_cell = cell
                best_score = dist
                if dist == 0:
                    break
        return best_cell

    def _on_enemies_cleared(self) -> None:
        self.combat_active = False
        if self.current_floor == "F40":
            self._lab_on_enemies_cleared()
            return
        self._set_quest_stage("log")
        self._show_dialog(["异常源已清除，终端恢复可用。"], title="系统")

    def _draw_enemies(self) -> None:
        if not self.enemies:
            return
        base_radius = settings.ENEMY_RADIUS
        base_color = settings.ENEMY_COLOR
        flash_color = settings.ENEMY_HIT_FLASH_COLOR
        fade_total = max(0.001, settings.ENEMY_FADE_DURATION)
        ox, oy = self.map_offset
        for enemy in self.enemies:
            sx = int(enemy["x"] + ox)
            sy = int(enemy["y"] + oy)
            state = enemy.get("state", "idle")
            color = flash_color if enemy.get("flash_timer", 0.0) > 0.0 else base_color
            draw_r = base_radius
            alpha = 255
            if state == "dying":
                fade = max(0.0, min(fade_total, enemy.get("fade_timer", 0.0)))
                alpha = int(255 * (fade / fade_total))
            elif state == "attacking":
                draw_r = base_radius + 4
                duration = max(0.001, settings.ENEMY_ATTACK_ANIM_TIME)
                anim_timer = enemy.get("attack_anim_timer", 0.0)
                progress = 1.0 - min(1.0, anim_timer / duration)
                alpha = int(220 + 35 * progress)
            elif state == "idle":
                alpha = 210
            surf = pygame.Surface((draw_r * 2, draw_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color, alpha), (draw_r, draw_r), draw_r)
            if state == "attacking":
                pygame.draw.circle(surf, (255, 255, 255, alpha), (draw_r, draw_r), draw_r, width=2)
            self.screen.blit(surf, (sx - draw_r, sy - draw_r))
            self._draw_enemy_health_bar(enemy, sx, sy)

    def _draw_enemy_health_bar(self, enemy: dict, sx: int, sy: int) -> None:
        if enemy.get("state") == "dying":
            return
        max_hp = float(enemy.get("max_hp", settings.ENEMY_MAX_HEALTH))
        hp = max(0.0, float(enemy.get("hp", max_hp)))
        if max_hp <= 0:
            return
        if not (enemy.get("aggro") or hp < max_hp or enemy.get("show_health", 0.0) > 0.0):
            return
        width, height = settings.ENEMY_HEALTH_BAR_SIZE
        margin = settings.ENEMY_HEALTH_BAR_MARGIN
        bar_x = sx - width // 2
        bar_y = sy - settings.ENEMY_RADIUS - margin
        bg_rect = pygame.Rect(bar_x, bar_y, width, height)
        pygame.draw.rect(self.screen, settings.ENEMY_HEALTH_BAR_BG, bg_rect)
        if hp > 0:
            ratio = max(0.0, min(1.0, hp / max_hp))
            fill_rect = bg_rect.copy()
            fill_rect.width = int(width * ratio)
            pygame.draw.rect(self.screen, settings.ENEMY_HEALTH_BAR_COLOR, fill_rect)
        pygame.draw.rect(self.screen, settings.ENEMY_HEALTH_BAR_BORDER, bg_rect, 1)

    def _draw_bullets(self) -> None:
        if not self.bullets:
            return
        r = settings.GUN_BULLET_RADIUS
        color = settings.GUN_BULLET_COLOR
        ox, oy = self.map_offset
        for b in self.bullets:
            sx = int(b["x"] + ox)
            sy = int(b["y"] + oy)
            pygame.draw.circle(self.screen, color, (sx, sy), r)

    def _follow_path(self, dt: float) -> bool:
        if not self.map_data or not self.path:
            return False
        cell_px = self.map_data.cell_size * settings.MAP_SCALE
        next_node = self.path[0]
        target_pos = (next_node[0] * cell_px + cell_px // 2, next_node[1] * cell_px + cell_px // 2)
        vx = target_pos[0] - self.player_rect.centerx
        vy = target_pos[1] - self.player_rect.centery
        dist = max(1, (vx * vx + vy * vy) ** 0.5)
        speed = self.player_move_speed * dt
        dx = int(round(vx / dist * speed))
        dy = int(round(vy / dist * speed))
        before = self.player_rect.center
        moved_step = self._move_player(dx, dy)
        after = self.player_rect.center
        # If we failed to get closer (collision), try skipping the node or replanning to goal
        prev_dist = abs(before[0] - target_pos[0]) + abs(before[1] - target_pos[1])
        new_dist = abs(after[0] - target_pos[0]) + abs(after[1] - target_pos[1])
        no_progress = new_dist >= prev_dist and after == before
        if no_progress:
            self.path.pop(0)
            if not self.path:
                self._replan_to_goal()
                return moved_step
            next_node = self.path[0]
            target_pos = (next_node[0] * cell_px + cell_px // 2, next_node[1] * cell_px + cell_px // 2)

        if abs(self.player_rect.centerx - target_pos[0]) <= cell_px // 3 and abs(self.player_rect.centery - target_pos[1]) <= cell_px // 3:
            self.path.pop(0)
            if not self.path:
                self.path_target = None
                self.path_goal_cell = None
        return moved_step

    def _replan_to_goal(self) -> None:
        if not self.map_data or not self.path_goal_cell:
            return
        cell = self.map_data.cell_size * settings.MAP_SCALE
        start = (self.player_rect.centerx // cell, self.player_rect.centery // cell)
        goal = self.path_goal_cell
        path_nodes = pathfinding.astar(
            self.map_data.collision_grid,
            start,
            goal,
            settings.PASSABLE_VALUES,
            cell_size=self.map_data.cell_size,
            actor_size=settings.PLAYER_SIZE,
        )
        self.path = path_nodes[1:] if len(path_nodes) > 1 else []
        if not self.path:
            self.path_target = None
            self.path_goal_cell = None

    def _update_camera(self) -> None:
        # Keep player at screen center; map_offset shifts map
        self.map_offset = (
            settings.WINDOW_WIDTH // 2 - self.player_rect.centerx,
            settings.WINDOW_HEIGHT // 2 - self.player_rect.centery,
        )

    def _render_minimap(self) -> None:
        if not self.map_data:
            return
        size = settings.MINIMAP_SIZE
        pad = settings.MINIMAP_MARGIN
        mini = pygame.Surface((size, size))
        mini.fill(settings.MINIMAP_BG)
        grid_w, grid_h = self.map_data.grid_size
        scale = min(size / grid_w, size / grid_h)
        cell_w = max(1, int(scale))
        for y, row in enumerate(self.map_data.collision_grid):
            for x, val in enumerate(row):
                if val in settings.PASSABLE_VALUES:
                    pygame.draw.rect(mini, settings.MINIMAP_WALKABLE, (int(x * scale), int(y * scale), cell_w, cell_w))
        # Player marker
        cell = self.map_data.cell_size * settings.MAP_SCALE
        px = int(self.player_rect.centerx / cell * scale)
        py = int(self.player_rect.centery / cell * scale)
        pygame.draw.circle(mini, settings.MINIMAP_PLAYER, (px, py), max(2, int(scale)))
        self.screen.blit(mini, (pad, pad))

    # --- Interaction helpers ---
    def _interaction_zones(self) -> list[dict]:
        zones = settings.INTERACT_ZONES.get(self.current_floor, [])
        scale = settings.MAP_SCALE
        scaled: list[dict] = []
        for z in zones:
            x1, y1, x2, y2 = z["rect"]
            scaled.append({**z, "rect": (int(x1 * scale), int(y1 * scale), int(x2 * scale), int(y2 * scale))})
        return scaled

    def _interaction_allowed(self, trig: dict) -> bool:
        if self.player_dead:
            return False
        t = trig.get("type")
        if t == "terminal":
            if self.combat_active:
                return False
            if self.current_floor == "F40":
                return self.quest_stage in {"lab_switch", "lab_exit"}
            if self.current_floor == "F35":
                return self.archive_flags.get("log_available", False)
            if self.current_floor == "F30":
                return self.logic_flags.get("terminal_ready", False)
            if self.current_floor == "F25":
                return self.resonator_state.get("log_available", False)
            return self.quest_stage in {"log", "elevator"}
        if t == "frame":
            if self.combat_active:
                return False
            return self.quest_stage in {"explore", "log"}
        if t == "switch":
            if self.current_floor == "F40":
                return self.quest_stage in {"lab_switch", "lab_exit"}
            if self.current_floor == "F25":
                return self.resonator_state.get("boss_state") == "dormant"
            return True
        if t == "npc":
            if self.current_floor == "F40":
                npc_state = self.lab_npc_state.get(trig.get("id", ), {})
                return not npc_state.get("hostile", False)
            if self.current_floor == "F25":
                return self.resonator_state.get("boss_state") != "active"
            return True
        if t == "exit":
            if self.current_floor == "F35":
                return self.archive_flags.get("exit_unlocked", False)
            if self.current_floor == "F30":
                return self.logic_flags.get("exit_unlocked", False)
            if self.current_floor == "F25":
                return self.resonator_state.get("exit_unlocked", False)
            return True
        return True

    def _update_interaction_prompt(self) -> None:
        self.interaction_target = None
        if not self.map_data:
            return
        px, py = self.player_rect.center
        for trig in self._interaction_zones():
            x1, y1, x2, y2 = trig["rect"]
            if x1 <= px <= x2 and y1 <= py <= y2 and self._interaction_allowed(trig):
                self.interaction_target = trig
                break

    def _player_in_interact_zone(self) -> bool:
        return True

    def _mask_has_red(self, x: int, y: int, radius: int) -> bool:
        if not self.interact_mask:
            return True
        w, h = self.interact_mask.get_size()
        r = radius
        for yy in range(max(0, y - r), min(h - 1, y + r) + 1):
            for xx in range(max(0, x - r), min(w - 1, x + r) + 1):
                color = self.interact_mask.get_at((xx, yy))
                # Treat warm/red/orange as interactable (dominant red component)
                if color.r > 80 and color.r >= color.g + 10 and color.r >= color.b + 10:
                    return True
        return False

    def _prompt_text_for_trigger(self, trig: dict) -> str:
        t = trig.get("type")
        if t == "exit":
            return "按F乘坐"
        if t == "terminal":
            return "按F查看"
        if t == "frame":
            return "按F查看"
        if t == "switch":
            return "按F启动"
        if t == "npc":
            return "按F交流"
        return "按F互动"

    def _activate_interaction(self, trig: dict) -> None:
        t = trig.get("type")
        if t == "exit" and "to_floor" in trig:
            if self.current_floor == "F50" and self.elevator_locked:
                self._show_dialog(["这个电梯怎么开呢？"], title="提示")
                return
            if self.current_floor == "F35" and (self.elevator_locked or not self.archive_flags.get("exit_unlocked", False)):
                self._show_dialog(["系统：档案核心仍未稳定，无法启动电梯。"], title="系统")
                return
            if self.current_floor == "F30" and (self.elevator_locked or not self.logic_flags.get("exit_unlocked", False)):
                self._show_dialog(["系统：未检测到稳定电压，电梯暂不可用。"], title="系统")
                return
            if self.current_floor == "F25" and (self.elevator_locked or not self.resonator_state.get("exit_unlocked", False)):
                self._show_dialog(["系统：共鸣场尚未稳定，电梯无法启动。"], title="系统")
                return
            next_floor = trig["to_floor"]
            if next_floor in settings.MAP_FILES:
                self.current_floor = next_floor
                self._load_floor(settings.MAP_FILES[next_floor])
            return
        if t == "terminal":
            if not self._interaction_allowed(trig):
                return
            term_id = trig.get("id", "")
            msg = self._terminal_message(term_id)
            self._show_dialog(msg, title="终端")
            if term_id == "log_kaines_001":
                self._set_quest_stage("elevator")
            elif term_id == "log_ethics_73a":
                self.logic_flags["terminal_read"] = True
                if self.quest_stage == "logic_terminal":
                    self._set_quest_stage("logic_exit")
            elif term_id == "log_kaines_045":
                if self.quest_stage == "resonator_log":
                    self._set_quest_stage("resonator_exit")
            return
        if t == "frame":
            if not self._interaction_allowed(trig):
                return
            msg = self._frame_message(trig.get("id", ""))
            self._show_dialog(msg, title="相框")
            if self.quest_stage == "explore":
                self._start_frame_combat()
            return
        if t == "switch":
            if not self._interaction_allowed(trig):
                self._show_dialog(["还无法激活这台装置。"], title="提示")
                return
            self._handle_switch_interaction(trig)
            return
        if t == "npc":
            if not self._interaction_allowed(trig):
                return
            self._handle_npc_interaction(trig)
            return
        # fallback
        self._show_dialog(["没有可以操作的反应。"], title="提示")

    def _terminal_message(self, term_id: str) -> list[str]:
        if term_id == "log_kaines_001":
            return [
                "DR. KAINES LOG - ENTRY 001",
                "认知锚定：成功。",
                "受试体 \"Custodian\" 已相信首要任务为 \"拯救方舟\"。",
                "生命体征：稳定。现实阻抗：0.2%。",
                "继续推进第一阶段。",
            ]
        if term_id == "log_ethics_73a":
            return [
                "[ETHICS_COMMITTEE - MINUTES 73-A]",
                "Dr. Kaines presented the case for Phase 3: The extraction of creative solutions under existential duress.",
                "The question was raised: Does a simulated personality that thinks, feels, and seeks self-preservation, have a right to exist?",
                "The board's decision was unanimous: For the survival of the Prime World, their sacrifice is not only acceptable, but necessary.",
                "I signed the document. My pen felt very heavy.",
            ]
        if term_id == "log_elara_audio":
            return [
                "[DR. ELARA AUDIO LOG]",
                "The 'death memory' implant remains our sharpest anchor.",
                "Sever the past, and the subject clings to the mission without question.",
                "Yet in the quiet, I keep wondering what gentle memories we erased.",
                "Who were they before the Ark demanded their purpose?",
            ]
        if term_id == "log_experiment_7g":
            return [
                "[SENSORY_DEPT - EXPERIMENT 7G]",
                "Test Summary: Forced sensory contradiction.",
                "Result: 87% subjects obeyed System guidance over personal senses.",
                "Conclusion: Cognitive dependency remains optimal.",
                "The Anchor holds.",
            ]
        if term_id == "log_kaines_045":
            return [
                "[DR. KAINES LOG - ENTRY 045]",
                "The Pathos Resonator results are... illuminating.",
                "Logic can be broken, rules can be bent, but raw, unreasoning emotion is where the truly unpredictable solutions emerge.",
                "It's beautiful, in its own chaotic way. It's exactly what we need to save our world.",
                "We just have to be willing to break a few digital hearts to get it.",
            ]
        return ["终端无响应。"]

    def _frame_message(self, frame_id: str) -> list[str]:
        if frame_id == "family_photo":
            return [
                "相框：", "一张泛黄的合照，背面写着：", "\"别忘了回到F40的灯塔。\""
            ]
        return ["这里没有更多信息。"]

    def _show_dialog(self, lines: list[str], *, title: str = "") -> None:
        self.dialog_lines = lines
        self.dialog_title = title
        self.dialog_timer = settings.DIALOG_LIFETIME

    def _dismiss_dialog(self) -> None:
        if not self.dialog_lines:
            self.dialog_timer = 0.0
            self.dialog_title = ""
            return
        self.dialog_lines = []
        self.dialog_timer = 0.0
        self.dialog_title = ""

    def _update_dialog(self, dt: float) -> None:
        if self.dialog_timer > 0:
            self.dialog_timer = max(0.0, self.dialog_timer - dt)
            if self.dialog_timer <= 0.0 and self.dialog_lines:
                self._dismiss_dialog()

    def _draw_prompt(self) -> None:
        if not self.interaction_target:
            return
        text = self._prompt_text_for_trigger(self.interaction_target)
        surf = self.font_prompt.render(text, True, settings.PROMPT_TEXT)
        pad = 6
        bg_rect = surf.get_rect()
        bg_rect.width += pad * 2
        bg_rect.height += pad * 2
        bg_rect.center = (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 - 40)
        pygame.draw.rect(self.screen, settings.PROMPT_BG, bg_rect)
        pygame.draw.rect(self.screen, settings.PROMPT_BORDER, bg_rect, 1)
        self.screen.blit(surf, (bg_rect.x + pad, bg_rect.y + pad))

    def _draw_dialog(self) -> None:
        if not self.dialog_lines:
            return
        overlay_h = int(settings.WINDOW_HEIGHT * settings.DIALOG_OVERLAY_HEIGHT_RATIO)
        overlay = pygame.Surface((settings.WINDOW_WIDTH, overlay_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, settings.DIALOG_OVERLAY_ALPHA))
        self.screen.blit(overlay, (0, settings.WINDOW_HEIGHT - overlay_h))

        title_text = self.dialog_title or ""
        y_base = settings.WINDOW_HEIGHT - overlay_h + settings.DIALOG_PADDING + 8
        pad_x = settings.DIALOG_PADDING + 12
        if title_text:
            title_surf = self.font_dialog.render(title_text, True, settings.TITLE_GLOW_COLOR)
            self.screen.blit(title_surf, (pad_x, y_base))
            y_base += title_surf.get_height() + 10
        line_gap = 6
        for line in self.dialog_lines:
            ln_surf = self.font_dialog.render(line, True, settings.DIALOG_TEXT)
            self.screen.blit(ln_surf, (pad_x, y_base))
            y_base += ln_surf.get_height() + line_gap

    def _draw_debug_coords(self) -> None:
        # Show player map coordinates in bottom-right for debugging
        px = int(self.player_rect.centerx / settings.MAP_SCALE)
        py = int(self.player_rect.centery / settings.MAP_SCALE)
        text = f"({px}, {py})"
        surf = self.font_prompt.render(text, True, settings.PROMPT_TEXT)
        margin = 10
        pos = (settings.WINDOW_WIDTH - surf.get_width() - margin, settings.WINDOW_HEIGHT - surf.get_height() - margin)
        bg = pygame.Surface((surf.get_width() + 6, surf.get_height() + 6))
        bg.set_alpha(120)
        bg.fill(settings.PROMPT_BG)
        self.screen.blit(bg, (pos[0] - 3, pos[1] - 3))
        self.screen.blit(surf, pos)

    def _draw_quest_hud(self) -> None:
        lines = self._quest_lines()
        if not lines:
            return
        pad = 10
        margin = settings.MINIMAP_MARGIN
        x = margin
        y = margin + settings.MINIMAP_SIZE + 8
        # measure width
        surf_lines = [self.font_prompt.render(txt, True, settings.QUEST_TEXT) for txt in lines]
        max_w = max((s.get_width() for s in surf_lines), default=0)
        box_w = max_w + pad * 2
        box_h = sum(s.get_height() for s in surf_lines) + pad * 2 + (len(surf_lines) - 1) * 4
        panel = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        panel.fill(settings.QUEST_BG)
        yy = pad
        for s in surf_lines:
            panel.blit(s, (pad, yy))
            yy += s.get_height() + 4
        self.screen.blit(panel, (x, y))

    def _quest_lines(self) -> list[str]:
        if self.current_floor == "F30" and getattr(self, 'logic_glitch_timer', 0.0) > 0.0:
            return ["//DIRECTIVE: EXTRACT_CREATIVE_SOLUTION.FROM P-7", "//PRIORITY: 100% DATA EXTRACTION"]
        if self.quest_stage == "intro":
            return ["任务：等待系统初始化"]
        if self.quest_stage == "explore":
            return ["任务：探索房间", "目标：查看相框线索"]
        if self.quest_stage == "combat":
            return ["任务：清除异常", "目标：消灭现身的异常实体"]
        if self.quest_stage == "log":
            return ["任务：查看终端日志", "提示：终端已重新开放"]
        if self.quest_stage == "elevator":
            return ["任务：乘坐电梯前往F40"]
        if self.quest_stage == "lab_intro":
            return ["任务：评估感官实验室", "目标：离开电梯区域并侦测环境"]
        if self.quest_stage == "lab_path":
            return ["任务：前往实验枢纽", "目标：穿越扭曲走廊"]
        if self.quest_stage == "lab_choice":
            return ["任务：处理逻辑错误实体", "提示：决定战斗或寻找替代路径"]
        if self.quest_stage == "lab_bypass":
            return ["任务：绕过能量墙", "目标：沿回廊寻找开关"]
        if self.quest_stage == "lab_switch":
            return ["任务：解锁电梯权限", "目标：与终端与开关交互"]
        if self.quest_stage == "lab_exit":
            return ["任务：前往记忆档案馆", "目标：乘坐电梯离开感官实验室"]
        if self.quest_stage == "archive_intro":
            return ["任务：等待指引者解析环境"]
        if self.quest_stage == "archive_maze":
            return ["任务：抵达档案馆核心", "目标：循着嗡鸣找到空地"]
        if self.quest_stage == "archive_boss":
            return ["任务：击败记忆吞噬者", "提示：注意脉冲，利用档案架掩护"]
        if self.quest_stage == "archive_flash":
            return ["任务：稳定认知", "提示：让记忆风暴自行散去"]
        if self.quest_stage == "archive_exit":
            return ["任务：收集残余日志", "目标：前往北侧电梯"]
        if self.quest_stage == "logic_intro":
            return ["任务：等待系统诊断"]
        if self.quest_stage == "logic_relays":
            return ["任务：恢复逻辑核心供电", "目标：按顺序激活三座主继电器"]
        if self.quest_stage == "logic_terminal":
            return ["任务：确认伦理委员会记录", "目标：读取终端并准备撤离"]
        if self.quest_stage == "logic_exit":
            return ["任务：前往神经下层", "目标：乘坐北侧电梯离开逻辑中心"]
        if self.quest_stage == "resonator_intro":
            return ["任务：稳定情感共鸣器", "目标：接近中央共鸣场"]
        if self.quest_stage == "resonator_talk":
            return ["任务：聆听情绪回声", "目标：与六位回声对话"]
        if self.quest_stage == "resonator_boss":
            return ["任务：击溃情绪污染源", "提示：注意情绪切换的攻击方式"]
        if self.quest_stage == "resonator_log":
            return ["任务：收集音频日志", "目标：读取共鸣器核心记录"]
        if self.quest_stage == "resonator_exit":
            return ["任务：前往下一层", "目标：乘坐北侧电梯离开共鸣器"]
        return []

    def _draw_player_health_hud(self) -> pygame.Rect:
        max_hp = max(1.0, float(self.player_health_max))
        current = max(0.0, float(self.player_health))
        margin = settings.PLAYER_HEALTH_BAR_MARGIN
        width, height = settings.PLAYER_HEALTH_BAR_SIZE
        x = settings.WINDOW_WIDTH - margin - width
        y = margin
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, settings.PLAYER_HEALTH_BAR_BG, bg_rect)
        ratio = max(0.0, min(1.0, current / max_hp))
        if ratio > 0:
            fill_rect = bg_rect.copy()
            fill_rect.width = int(width * ratio)
            pygame.draw.rect(self.screen, settings.PLAYER_HEALTH_BAR_COLOR, fill_rect)
        pygame.draw.rect(self.screen, settings.PLAYER_HEALTH_BAR_BORDER, bg_rect, 1)
        hp_text = f"HP {int(math.ceil(current))}/{int(max_hp)}"
        label = self.font_prompt.render(hp_text, True, settings.QUEST_TEXT)
        label_x = max(8, x - label.get_width() - 12)
        label_y = y + (height - label.get_height()) // 2
        self.screen.blit(label, (label_x, label_y))
        return bg_rect

    def _draw_ammo_hud(self, avoid_rect: pygame.Rect | None = None) -> pygame.Rect:
        total = settings.GUN_CLIP_SIZE
        filled = max(0, min(total, self.ammo_in_clip))
        size = 12
        gap = 4
        margin = 12
        color_on = settings.GUN_BULLET_COLOR
        color_off = (70, 80, 90)
        x = settings.WINDOW_WIDTH - margin - total * (size + gap) + gap
        y = margin
        if avoid_rect and y < avoid_rect.bottom + 6:
            shift = (avoid_rect.bottom + 6) - y
            y += shift
        last_rect = pygame.Rect(x, y, 0, 0)
        for i in range(total):
            rect = pygame.Rect(x + i * (size + gap), y, size, size * 2)
            if i < filled:
                pygame.draw.rect(self.screen, color_on, rect, border_radius=3)
            else:
                pygame.draw.rect(self.screen, color_off, rect, width=1, border_radius=3)
            last_rect = rect
        return last_rect

    def _draw_reload_bar(self, ammo_rect: pygame.Rect | None = None) -> None:
        if self.reload_timer <= 0:
            return
        margin = 12
        width = 180
        height = 10
        x = settings.WINDOW_WIDTH - margin - width
        y = margin + 32  # below ammo icons
        if ammo_rect:
            y = max(y, ammo_rect.bottom + 6)
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.screen, (50, 60, 70), bg_rect, border_radius=3)
        progress = 1.0 - min(1.0, self.reload_timer / settings.GUN_RELOAD_TIME)
        if progress > 0:
            fill_rect = pygame.Rect(x, y, int(width * progress), height)
            pygame.draw.rect(self.screen, settings.GUN_BULLET_COLOR, fill_rect, border_radius=3)
        pygame.draw.rect(self.screen, (150, 160, 180), bg_rect, width=1, border_radius=3)

    def _start_click_feedback(self, map_x: int, map_y: int) -> None:
        self.click_fx_pos = (map_x, map_y)
        self.click_fx_timer = settings.CLICK_FEEDBACK_DURATION

    def _draw_click_feedback(self) -> None:
        if not self.click_fx_pos or self.click_fx_timer <= 0:
            return
        # screen-space position of the click on the map
        sx = int(self.click_fx_pos[0] + self.map_offset[0])
        sy = int(self.click_fx_pos[1] + self.map_offset[1])
        # simple shrinking circle effect
        t = self.click_fx_timer / settings.CLICK_FEEDBACK_DURATION
        radius = int(settings.CLICK_FEEDBACK_RADIUS * settings.MAP_SCALE * t)
        if radius <= 0:
            return
        pygame.draw.circle(self.screen, settings.CLICK_FEEDBACK_COLOR, (sx, sy), radius, width=2)
        # decay timer
        dt = self.clock.get_time() / 1000.0
        self.click_fx_timer = max(0.0, self.click_fx_timer - dt)

    # --- Intro sequence ---
    def _start_intro(self) -> None:
        self.intro_active = True
        self.intro_phase = "glitch"
        self.intro_timer = 0.5
        self.reveal_progress = 0.0
        self.player_fade = 0.0
        if self.boot_sound:
            try:
                self.boot_sound.play()
            except Exception:
                pass

    def _update_intro(self, dt: float) -> None:
        if not self.intro_active:
            return
        self.intro_timer -= dt
        if self.intro_phase == "glitch":
            if self.intro_timer <= 0:
                self.intro_phase = "text"
                self.intro_timer = 0.9
        elif self.intro_phase == "text":
            if self.intro_timer <= 0:
                self.intro_phase = "reveal"
                self.intro_timer = 1.8
        elif self.intro_phase == "reveal":
            dur = 1.8
            t = max(0.0, min(1.0, 1.0 - self.intro_timer / dur))
            self.reveal_progress = t
            self.player_fade = min(1.0, t * 1.2)
            if self.intro_timer <= 0:
                self.intro_active = False
                self.reveal_progress = 1.0
                self.player_fade = 1.0
                if not self.cutscene_started:
                    self._start_guidance_cutscene()

    def _render_intro(self) -> None:
        if self.intro_phase == "glitch":
            self._render_glitch()
        elif self.intro_phase == "text":
            self._render_glitch(fade_text=True)
        elif self.intro_phase == "reveal":
            self._render_map_reveal(self.reveal_progress, self.player_fade)

    def _render_glitch(self, fade_text: bool = False) -> None:
        self.screen.fill((8, 10, 18))
        # draw random blocks as pixel noise
        for _ in range(220):
            rw = random.randint(4, 24)
            rh = random.randint(4, 24)
            x = random.randint(0, settings.WINDOW_WIDTH)
            y = random.randint(0, settings.WINDOW_HEIGHT)
            col = (random.randint(80, 255), random.randint(80, 255), random.randint(80, 255))
            pygame.draw.rect(self.screen, col, (x, y, rw, rh))
        if fade_text:
            text = "//BOOT_SEQUENCE_INITIATED..."
            surf = self.font_prompt.render(text, True, settings.TITLE_GLOW_COLOR)
            surf.set_alpha(255)
            rect = surf.get_rect(center=(settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2))
            self.screen.blit(surf, rect)

    def _render_map_reveal(self, progress: float, player_alpha: float) -> None:
        # Mosaic-based reveal
        self.screen.fill(settings.BACKGROUND_COLOR)
        # keep player centered during reveal
        offset = (
            settings.WINDOW_WIDTH // 2 - self.player_rect.centerx,
            settings.WINDOW_HEIGHT // 2 - self.player_rect.centery,
        )
        if self.map_surface:
            base = self.map_surface
            w, h = base.get_size()
            block = max(3, int(32 * (1.0 - progress) + 2))
            small_w = max(1, w // block)
            small_h = max(1, h // block)
            mosaic = pygame.transform.scale(base, (small_w, small_h))
            mosaic = pygame.transform.scale(mosaic, (w, h))
            self.screen.blit(mosaic, offset)
        # draw player faded
        player_screen_pos = (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2)
        alpha = int(max(0, min(1.0, player_alpha)) * 255)
        if self.player_sprite:
            sprite_rect = self.player_sprite.get_rect(center=player_screen_pos)
            sprite = self.player_sprite.copy()
            sprite.set_alpha(alpha)
            self.screen.blit(sprite, sprite_rect)
        else:
            rect = pygame.Surface(settings.PLAYER_SIZE, pygame.SRCALPHA)
            rect.fill((*settings.PLAYER_COLOR, alpha))
            self.screen.blit(rect, (player_screen_pos[0] - settings.PLAYER_SIZE[0] // 2, player_screen_pos[1] - settings.PLAYER_SIZE[1] // 2))

    # --- Cutscene / Guided dialog ---
    def _start_guidance_cutscene(self) -> None:
        self.cutscene_started = True
        self.cutscene_lines = [
            {"speaker": "指引者", "text": "系统上线。欢迎回来，清除异常。正在初始化环境扫描..."},
            {"speaker": "指引者", "text": "检测到数据冗余，已清理。"},
            {"speaker": "指引者", "text": "起身校准体感：WASD/方向键移动，鼠标左键或空格射击，F 交互，R 装填。"},
            {"speaker": "指引者", "text": "需要导航时，右键点击地面会自动规划路径，按方向键随时打断并手动控制。"},
            {"speaker": "指引者", "text": "靠近终端或电梯按 F 交互，准星指向目标即可自动锁定射击。"},
            {"speaker": "指引者", "text": "别忘了切换到英文输入法，否则快捷键会失效。准备好了就开始行动。"},
        ]
        self.cutscene_idx = 0
        self.cutscene_char_progress = 0.0
        self.cutscene_done_line = False
        self.cutscene_active = True

    def _current_cutscene_line(self) -> dict | None:
        if 0 <= self.cutscene_idx < len(self.cutscene_lines):
            return self.cutscene_lines[self.cutscene_idx]
        return None

    def _advance_cutscene(self) -> None:
        if not self.cutscene_active:
            return
        line = self._current_cutscene_line()
        if not line:
            self.cutscene_active = False
            return
        text = line.get("text", "")
        if not self.cutscene_done_line:
            # skip typing to full
            self.cutscene_char_progress = len(text)
            self.cutscene_done_line = True
            return
        # move to next line
        self.cutscene_idx += 1
        if self.cutscene_idx >= len(self.cutscene_lines):
            self.cutscene_active = False
            # unlock exploration task
            self._set_quest_stage("explore")
            return
        self.cutscene_char_progress = 0.0
        self.cutscene_done_line = False

    def _update_cutscene(self, dt: float) -> None:
        line = self._current_cutscene_line()
        if not line:
            self.cutscene_active = False
            return
        text = line.get("text", "")
        length = max(1, len(text))
        cps = max(settings.DIALOG_TYPE_SPEED_MIN, length / settings.DIALOG_TYPE_MAX_DURATION)
        if not self.cutscene_done_line:
            self.cutscene_char_progress += cps * dt
            if self.cutscene_char_progress >= len(text):
                self.cutscene_char_progress = len(text)
                self.cutscene_done_line = True

    def _set_quest_stage(self, stage: str) -> None:
        self.quest_stage = stage
        if stage in {"elevator", "lab_exit", "resonator_log", "resonator_exit"}:
            self.elevator_locked = False
        if stage in {"intro", "explore", "combat", "log", "lab_intro", "lab_path", "lab_choice", "lab_bypass", "lab_switch",
                     "resonator_intro", "resonator_talk", "resonator_boss"}:
            self.elevator_locked = True

    def _draw_cutscene_dialog(self) -> None:
        line = self._current_cutscene_line()
        if not line:
            return
        speaker = line.get("speaker", "")
        text = line.get("text", "")
        shown_len = int(self.cutscene_char_progress) if not self.cutscene_done_line else len(text)
        shown_text = text[:shown_len]
        overlay_h = int(settings.WINDOW_HEIGHT * settings.DIALOG_OVERLAY_HEIGHT_RATIO)
        overlay = pygame.Surface((settings.WINDOW_WIDTH, overlay_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, settings.DIALOG_OVERLAY_ALPHA))
        self.screen.blit(overlay, (0, settings.WINDOW_HEIGHT - overlay_h))

        pad = settings.DIALOG_PADDING + 8
        y_base = settings.WINDOW_HEIGHT - overlay_h + pad
        # speaker
        speaker_surf = self.font_dialog.render(speaker, True, settings.TITLE_GLOW_COLOR)
        self.screen.blit(speaker_surf, (pad, y_base))
        # text (wrap simple by splitting) but single line for now
        text_surf = self.font_dialog.render(shown_text, True, settings.DIALOG_TEXT)
        self.screen.blit(text_surf, (pad, y_base + speaker_surf.get_height() + 8))
        if self.cutscene_done_line:
            hint = "点击任意键继续"
            hint_surf = self.font_prompt.render(hint, True, settings.DIALOG_TEXT)
            hint_x = settings.WINDOW_WIDTH - hint_surf.get_width() - pad
            hint_y = settings.WINDOW_HEIGHT - overlay_h + overlay_h - hint_surf.get_height() - settings.DIALOG_PADDING
            self.screen.blit(hint_surf, (hint_x, hint_y))
