"""Game lifecycle: start menu -> floor view."""

import sys
from pathlib import Path
import random

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
        self.player_rect = pygame.Rect(0, 0, *settings.PLAYER_SIZE)  # map-space rect
        self.player_sprite: pygame.Surface | None = self._load_player_sprite()
        self.path: list[tuple[int, int]] = []  # list of map-cell nodes
        self.path_target: tuple[int, int] | None = None
        self.path_goal_cell: tuple[int, int] | None = None
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
        self.quest_stage = "intro"  # Ensure quest stage reset in _load_floor
        self.elevator_locked = True

        self.font_path = self._resolve_font()
        self.font_prompt = self._load_font(18)
        self.font_dialog = self._load_font(20)

        self.current_floor = settings.START_FLOOR
        self._load_floor(settings.MAP_FILES[self.current_floor])

    def _load_floor(self, path: Path) -> None:
        self.map_data = load_map(path)
        self.map_surface = self._build_map_surface(self.map_data)
        map_w, map_h = self.map_surface.get_size()
        self.map_offset = (
            (settings.WINDOW_WIDTH - map_w) // 2,
            (settings.WINDOW_HEIGHT - map_h) // 2,
        )
        spawn_x, spawn_y = self.map_data.spawn_player
        # spawn is in pixels relative to map; scale to render space
        self.player_rect.center = (int(spawn_x * settings.MAP_SCALE), int(spawn_y * settings.MAP_SCALE))
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
        self.quest_stage = "intro"
        self.elevator_locked = self.current_floor == "F50"
        self.font_path = self._resolve_font()
        self.font_prompt = self._load_font(18)
        self.font_dialog = self._load_font(20)
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
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
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
                    # Close current dialog instead of firing
                    self.dialog_lines = []
                    self.dialog_timer = 0.0
                    self.dialog_title = ""
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
        # Ensure key state is refreshed even if no new events arrived this frame
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        manual_dx, manual_dy = self._manual_axis(keys, dt)

        if manual_dx or manual_dy:
            self.path = []
            self.path_target = None
            self.path_goal_cell = None
            self._move_player(manual_dx, manual_dy)
        elif self.path:
            self._follow_path(dt)

        self._update_bullets(dt)

        self._update_interaction_prompt()

        self._update_camera()
        self._check_triggers()

    def _check_triggers(self) -> None:
        if not self.map_data:
            return
        px = self.player_rect.centerx
        py = self.player_rect.centery
        for trig in self.map_data.triggers:
            # exit interactions now handled via prompt + F key
            continue

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
        self._draw_bullets()
        player_screen_pos = (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2)
        if self.player_sprite:
            sprite_rect = self.player_sprite.get_rect(center=player_screen_pos)
            self.screen.blit(self.player_sprite, sprite_rect)
        else:
            pygame.draw.rect(self.screen, settings.PLAYER_COLOR, pygame.Rect(0, 0, *settings.PLAYER_SIZE).move(
                player_screen_pos[0] - settings.PLAYER_SIZE[0] // 2, player_screen_pos[1] - settings.PLAYER_SIZE[1] // 2))

        self._render_minimap()
        self._draw_quest_hud()
        self._draw_ammo_hud()
        self._draw_reload_bar()
        self._draw_prompt()
        self._draw_dialog()
        self._draw_debug_coords()
        self._draw_click_feedback()

    def _load_player_sprite(self) -> pygame.Surface | None:
        if settings.PLAYER_SPRITE.exists():
            sprite = pygame.image.load(str(settings.PLAYER_SPRITE)).convert_alpha()
            w, h = sprite.get_size()
            return pygame.transform.scale(sprite, (int(w * settings.PLAYER_SCALE), int(h * settings.PLAYER_SCALE)))
        return None

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

    def _move_player(self, dx: int, dy: int) -> None:
        if not self.map_data:
            return
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

    def _manual_axis(self, keys: pygame.key.ScancodeWrapper, dt: float) -> tuple[int, int]:
        # WASD/arrow with cancellation rules; speed matches auto-path (PLAYER_SPEED)
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

        speed = settings.PLAYER_SPEED * dt
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
        if not self.map_data:
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
            cx = int(b["x"] // cell_px)
            cy = int(b["y"] // cell_px)
            if cx < 0 or cy < 0 or cx >= max_x or cy >= max_y:
                continue
            if self.map_data.collision_grid[cy][cx] == 1:
                continue
            next_bullets.append(b)
        self.bullets = next_bullets

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

    def _follow_path(self, dt: float) -> None:
        if not self.map_data or not self.path:
            return
        cell_px = self.map_data.cell_size * settings.MAP_SCALE
        next_node = self.path[0]
        target_pos = (next_node[0] * cell_px + cell_px // 2, next_node[1] * cell_px + cell_px // 2)
        vx = target_pos[0] - self.player_rect.centerx
        vy = target_pos[1] - self.player_rect.centery
        dist = max(1, (vx * vx + vy * vy) ** 0.5)
        speed = settings.PLAYER_SPEED * dt
        dx = int(round(vx / dist * speed))
        dy = int(round(vy / dist * speed))
        before = self.player_rect.center
        self._move_player(dx, dy)
        after = self.player_rect.center
        # If we failed to get closer (collision), try skipping the node or replanning to goal
        prev_dist = abs(before[0] - target_pos[0]) + abs(before[1] - target_pos[1])
        new_dist = abs(after[0] - target_pos[0]) + abs(after[1] - target_pos[1])
        no_progress = new_dist >= prev_dist and after == before
        if no_progress:
            self.path.pop(0)
            if not self.path:
                self._replan_to_goal()
                return
            next_node = self.path[0]
            target_pos = (next_node[0] * cell_px + cell_px // 2, next_node[1] * cell_px + cell_px // 2)

        if abs(self.player_rect.centerx - target_pos[0]) <= cell_px // 3 and abs(self.player_rect.centery - target_pos[1]) <= cell_px // 3:
            self.path.pop(0)
            if not self.path:
                self.path_target = None
                self.path_goal_cell = None

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
    def _update_interaction_prompt(self) -> None:
        self.interaction_target = None
        if not self.map_data:
            return
        if not self._player_in_interact_zone():
            return
        px, py = self.player_rect.center
        radius = settings.INTERACT_RADIUS * settings.MAP_SCALE
        best = None
        best_dist = 1e9
        for trig in self.map_data.triggers:
            tx, ty = trig.get("at_pixel", [0, 0])
            tx = int(tx * settings.MAP_SCALE)
            ty = int(ty * settings.MAP_SCALE)
            dist = ((px - tx) ** 2 + (py - ty) ** 2) ** 0.5
            if dist <= radius and dist < best_dist:
                best = trig
                best_dist = dist
        self.interaction_target = best

    def _player_in_interact_zone(self) -> bool:
        if not self.interact_mask:
            return True
        px = int(self.player_rect.centerx / settings.MAP_SCALE)
        py = int(self.player_rect.centery / settings.MAP_SCALE)
        return self._mask_has_red(px, py, settings.INTERACT_MASK_RADIUS)

    def _mask_has_red(self, x: int, y: int, radius: int) -> bool:
        if not self.interact_mask:
            return True
        w, h = self.interact_mask.get_size()
        r = radius
        for yy in range(max(0, y - r), min(h - 1, y + r) + 1):
            for xx in range(max(0, x - r), min(w - 1, x + r) + 1):
                color = self.interact_mask.get_at((xx, yy))
                # Treat red if it is dominant and not dark; accept slight anti-aliased edges
                if color.r > 100 and color.r > color.g + 20 and color.r > color.b + 20:
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
        return "按F互动"

    def _activate_interaction(self, trig: dict) -> None:
        t = trig.get("type")
        if t == "exit" and "to_floor" in trig:
            if self.current_floor == "F50" and self.elevator_locked:
                self._show_dialog(["电梯未解锁。请先完成当前任务。"], title="指引者")
                return
            next_floor = trig["to_floor"]
            if next_floor in settings.MAP_FILES:
                self.current_floor = next_floor
                self._load_floor(settings.MAP_FILES[next_floor])
            return
        if t == "terminal":
            msg = self._terminal_message(trig.get("id", ""))
            self._show_dialog(msg, title="终端")
            self._maybe_complete_explore()
            return
        if t == "frame":
            msg = self._frame_message(trig.get("id", ""))
            self._show_dialog(msg, title="相框")
            self._maybe_complete_explore()
            return
        # fallback
        self._show_dialog(["没有可以操作的反应。"], title="提示")

    def _terminal_message(self, term_id: str) -> list[str]:
        if term_id == "log_kaines_001":
            return [
                "终端：安全日志片段", "", "Kaines：", "· 第50层宿舍，电源仍稳定。", "· 收容间有三处异常活动记录。", "· 如果你读到这行，尽快下行。"
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

    def _update_dialog(self, dt: float) -> None:
        if self.dialog_timer > 0:
            self.dialog_timer -= dt
            if self.dialog_timer <= 0:
                self.dialog_lines = []
                self.dialog_timer = 0.0
                self.dialog_title = ""

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
        if self.quest_stage == "intro":
            return ["任务：等待系统初始化"]
        if self.quest_stage == "explore":
            return ["任务：探索房间", "目标：查看桌上日志"]
        if self.quest_stage == "elevator":
            return ["任务：乘坐电梯前往F40"]
        return []

    def _draw_ammo_hud(self) -> None:
        total = settings.GUN_CLIP_SIZE
        filled = max(0, min(total, self.ammo_in_clip))
        size = 12
        gap = 4
        margin = 12
        color_on = settings.GUN_BULLET_COLOR
        color_off = (70, 80, 90)
        x = settings.WINDOW_WIDTH - margin - total * (size + gap) + gap
        y = margin
        for i in range(total):
            rect = pygame.Rect(x + i * (size + gap), y, size, size * 2)
            if i < filled:
                pygame.draw.rect(self.screen, color_on, rect, border_radius=3)
            else:
                pygame.draw.rect(self.screen, color_off, rect, width=1, border_radius=3)

    def _draw_reload_bar(self) -> None:
        if self.reload_timer <= 0:
            return
        margin = 12
        width = 180
        height = 10
        x = settings.WINDOW_WIDTH - margin - width
        y = margin + 32  # below ammo icons
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
            {"speaker": "指引者", "text": "系统上线。欢迎回来，巡视员。正在初始化环境扫描..."},
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
        if stage == "elevator":
            self.elevator_locked = False
        if stage == "intro":
            self.elevator_locked = True
        if stage == "explore":
            self.elevator_locked = True

    def _maybe_complete_explore(self) -> None:
        if self.quest_stage == "explore":
            self._set_quest_stage("elevator")

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
