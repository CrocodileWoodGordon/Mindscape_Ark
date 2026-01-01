"""UI elements including start menu."""

import pygame
from ..core import settings


def _resolve_font_path() -> str | None:
    if settings.FONTS_DIR.exists():
        candidates = [p for p in sorted(settings.FONTS_DIR.iterdir()) if p.is_file() and p.suffix.lower() in {".ttf", ".otf"}]
        preferred = [p for p in candidates if "notosanssc" in p.name.lower()]
        pick = preferred[0] if preferred else (candidates[0] if candidates else None)
        return str(pick) if pick else None
    return None


def _load_font(font_path: str | None, size: int) -> pygame.font.Font:
    if font_path:
        try:
            return pygame.font.Font(font_path, size)
        except Exception:
            pass
    return pygame.font.SysFont(settings.UI_FONT_NAME, size)


class StartMenu:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.title = settings.WINDOW_TITLE
        self.font_path = _resolve_font_path()
        self.font_title = _load_font(self.font_path, 74)
        self.font_sub = _load_font(self.font_path, 30)
        self.font_btn = _load_font(self.font_path, 36)
        self.font_notice = _load_font(self.font_path, 20)
        self.options = [
            ("开始游戏", "start"),
            ("读取存档", "load"),
        ]
        self.selected_index = 0
        self.save_available = False
        w, h = settings.START_BUTTON_SIZE
        self.button_rects = self._build_button_rects(w, h)
        self.notice_text = ""
        self.notice_timer = 0.0

    def _build_button_rects(self, width: int, height: int) -> list[pygame.Rect]:
        gap = 18
        total_h = len(self.options) * height + (len(self.options) - 1) * gap
        start_y = settings.WINDOW_HEIGHT // 2 + 120 - total_h // 2
        rects: list[pygame.Rect] = []
        for idx in range(len(self.options)):
            rect = pygame.Rect(0, 0, width, height)
            rect.center = (settings.WINDOW_WIDTH // 2, start_y + idx * (height + gap))
            rects.append(rect)
        return rects

    def set_save_available(self, available: bool) -> None:
        self.save_available = available

    def show_notice(self, text: str) -> None:
        self._set_notice(text)

    def _set_notice(self, text: str) -> None:
        self.notice_text = text
        self.notice_timer = 1.6

    def _activate_option(self, index: int) -> str | None:
        action = self.options[index][1]
        if action == "load" and not self.save_available:
            self._set_notice("暂无存档")
            return None
        return action

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self._activate_option(self.selected_index)
        if event.type == pygame.MOUSEMOTION:
            for idx, rect in enumerate(self.button_rects):
                if rect.collidepoint(event.pos):
                    self.selected_index = idx
                    break
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for idx, rect in enumerate(self.button_rects):
                if rect.collidepoint(event.pos):
                    self.selected_index = idx
                    return self._activate_option(idx)
        return None

    def update(self, dt: float) -> None:  # noqa: ARG002
        if self.notice_timer > 0:
            self.notice_timer = max(0.0, self.notice_timer - dt)
            if self.notice_timer == 0:
                self.notice_text = ""

    def draw(self) -> None:
        self.screen.fill(settings.BACKGROUND_COLOR)

        # Title layers
        center = (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 - 100)
        shadow = self.font_title.render(self.title, True, settings.TITLE_SHADOW_COLOR)
        glow = self.font_title.render(self.title, True, settings.TITLE_GLOW_COLOR)
        main = self.font_title.render(self.title, True, settings.TITLE_COLOR)
        for surf, offset in ((shadow, (6, 6)), (glow, (0, 2)), (main, (0, 0))):
            rect = surf.get_rect(center=(center[0] + offset[0], center[1] + offset[1]))
            self.screen.blit(surf, rect)

        sub_text = "心景：方舟"
        sub = self.font_sub.render(sub_text, True, settings.TITLE_GLOW_COLOR)
        sub_rect = sub.get_rect(center=(center[0], center[1] + 64))
        self.screen.blit(sub, sub_rect)

        # Buttons
        mouse_pos = pygame.mouse.get_pos()
        disabled_color = (50, 70, 90)
        for idx, (label, action) in enumerate(self.options):
            rect = self.button_rects[idx]
            hovered = rect.collidepoint(mouse_pos)
            selected = idx == self.selected_index
            disabled = action == "load" and not self.save_available
            if disabled:
                color = disabled_color
            else:
                color = settings.BUTTON_HOVER_COLOR if (hovered or selected) else settings.BUTTON_COLOR
            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            text_color = settings.BUTTON_TEXT_COLOR if not disabled else (190, 200, 210)
            text = self.font_btn.render(label, True, text_color)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

        if self.notice_text:
            notice = self.font_notice.render(self.notice_text, True, settings.TITLE_GLOW_COLOR)
            notice_rect = notice.get_rect(center=(settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT - 80))
            self.screen.blit(notice, notice_rect)

    def reset(self) -> None:
        """Return menu to idle state so it can be shown again."""
        self.selected_index = 0
        self.notice_text = ""
        self.notice_timer = 0.0


class PauseMenu:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.title = "暂停"
        self.options = [
            ("暂存进度", "save"),
            ("退出游戏", "quit"),
            ("返回首页", "home"),
            ("成就", "achievements"),
        ]
        self.font_path = _resolve_font_path()
        self.font_title = _load_font(self.font_path, 46)
        self.font_btn = _load_font(self.font_path, 32)
        self.font_hint = _load_font(self.font_path, 22)
        self.selected_index = 0
        self.panel_rect = pygame.Rect(0, 0, 420, 420)
        self.panel_rect.center = (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2)
        self.option_rects = self._build_option_rects()
        self.confirm_action: str | None = None
        self.confirm_options: list[tuple[str, str]] = []
        self.confirm_selected = 0
        self.confirm_rect = pygame.Rect(0, 0, 420, 260)
        self.confirm_rect.center = (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2)
        self.confirm_option_rects: list[pygame.Rect] = []
        self.close_size = 24
        self.close_padding = 12
        self.panel_close_rect = self._build_close_rect(self.panel_rect)
        self.confirm_close_rect = self._build_close_rect(self.confirm_rect)
        self.notice_text = ""
        self.notice_timer = 0.0

    def _build_option_rects(self) -> list[pygame.Rect]:
        button_w = 320
        button_h = 54
        gap = 14
        total_h = len(self.options) * button_h + (len(self.options) - 1) * gap
        start_y = self.panel_rect.centery - total_h // 2 + 20
        rects: list[pygame.Rect] = []
        for idx in range(len(self.options)):
            rect = pygame.Rect(0, 0, button_w, button_h)
            rect.center = (self.panel_rect.centerx, start_y + idx * (button_h + gap))
            rects.append(rect)
        return rects

    def _build_close_rect(self, base_rect: pygame.Rect) -> pygame.Rect:
        size = self.close_size
        return pygame.Rect(
            base_rect.right - self.close_padding - size,
            base_rect.top + self.close_padding,
            size,
            size,
        )

    def open_confirm(self, action: str) -> None:
        self.confirm_action = action
        if action == "quit":
            self.confirm_options = [
                ("确认退出", "confirm_quit"),
                ("存档后退出", "save_quit"),
            ]
        else:
            self.confirm_options = [
                ("确认返回", "confirm_home"),
                ("存档后返回", "save_home"),
            ]
        self.confirm_selected = 0
        self.confirm_option_rects = self._build_confirm_option_rects()

    def close_confirm(self) -> None:
        self.confirm_action = None
        self.confirm_options = []
        self.confirm_selected = 0
        self.confirm_option_rects = []

    def show_notice(self, text: str) -> None:
        self.notice_text = text
        self.notice_timer = 1.6

    def _build_confirm_option_rects(self) -> list[pygame.Rect]:
        button_w = 240
        button_h = 48
        gap = 14
        header_h = 120
        total_h = len(self.confirm_options) * button_h + (len(self.confirm_options) - 1) * gap
        start_y = self.confirm_rect.top + header_h + button_h // 2
        rects: list[pygame.Rect] = []
        for idx in range(len(self.confirm_options)):
            rect = pygame.Rect(0, 0, button_w, button_h)
            rect.center = (self.confirm_rect.centerx, start_y + idx * (button_h + gap))
            rects.append(rect)
        return rects

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if self.confirm_action:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self.confirm_close_rect.collidepoint(event.pos):
                    return "cancel_confirm"
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.confirm_selected = (self.confirm_selected - 1) % len(self.confirm_options)
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.confirm_selected = (self.confirm_selected + 1) % len(self.confirm_options)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    return self.confirm_options[self.confirm_selected][1]
                elif event.key == pygame.K_ESCAPE:
                    return "cancel_confirm"
            if event.type == pygame.MOUSEMOTION:
                for idx, rect in enumerate(self.confirm_option_rects):
                    if rect.collidepoint(event.pos):
                        self.confirm_selected = idx
                        break
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for idx, rect in enumerate(self.confirm_option_rects):
                    if rect.collidepoint(event.pos):
                        self.confirm_selected = idx
                        return self.confirm_options[idx][1]
            return None
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % len(self.options)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.options[self.selected_index][1]
        if event.type == pygame.MOUSEMOTION:
            for idx, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self.selected_index = idx
                    break
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.panel_close_rect.collidepoint(event.pos):
                return "close_menu"
            for idx, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self.selected_index = idx
                    return self.options[idx][1]
        return None

    def _draw_close_button(self, rect: pygame.Rect, mouse_pos: tuple[int, int]) -> None:
        hovered = rect.collidepoint(mouse_pos)
        color = settings.BUTTON_HOVER_COLOR if hovered else settings.BUTTON_COLOR
        pygame.draw.rect(self.screen, color, rect, border_radius=6)
        line_color = settings.BUTTON_TEXT_COLOR
        inset = 6
        pygame.draw.line(
            self.screen,
            line_color,
            (rect.left + inset, rect.top + inset),
            (rect.right - inset, rect.bottom - inset),
            2,
        )
        pygame.draw.line(
            self.screen,
            line_color,
            (rect.left + inset, rect.bottom - inset),
            (rect.right - inset, rect.top + inset),
            2,
        )

    def update(self, dt: float) -> None:  # noqa: ARG002
        if self.notice_timer > 0:
            self.notice_timer = max(0.0, self.notice_timer - dt)
            if self.notice_timer == 0:
                self.notice_text = ""

    def draw(self) -> None:
        overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        pygame.draw.rect(self.screen, (20, 26, 40), self.panel_rect, border_radius=14)
        pygame.draw.rect(self.screen, (80, 110, 150), self.panel_rect, 2, border_radius=14)

        mouse_pos = pygame.mouse.get_pos()
        self._draw_close_button(self.panel_close_rect, mouse_pos)

        title_surf = self.font_title.render(self.title, True, settings.TITLE_COLOR)
        title_rect = title_surf.get_rect(center=(self.panel_rect.centerx, self.panel_rect.top + 50))
        self.screen.blit(title_surf, title_rect)

        for idx, (label, _) in enumerate(self.options):
            rect = self.option_rects[idx]
            hovered = rect.collidepoint(mouse_pos)
            selected = idx == self.selected_index
            color = settings.BUTTON_HOVER_COLOR if (hovered or selected) else settings.BUTTON_COLOR
            pygame.draw.rect(self.screen, color, rect, border_radius=10)
            text = self.font_btn.render(label, True, settings.BUTTON_TEXT_COLOR)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

        if self.confirm_action:
            modal = pygame.Surface(self.confirm_rect.size, pygame.SRCALPHA)
            modal.fill((18, 22, 34, 235))
            self.screen.blit(modal, self.confirm_rect.topleft)
            pygame.draw.rect(self.screen, (100, 130, 170), self.confirm_rect, 2, border_radius=12)

            self._draw_close_button(self.confirm_close_rect, mouse_pos)

            title = self.font_title.render("未存档", True, settings.TITLE_COLOR)
            title_rect = title.get_rect(center=(self.confirm_rect.centerx, self.confirm_rect.top + 44))
            self.screen.blit(title, title_rect)

            hint = self.font_hint.render("当前进度尚未存档，请选择操作", True, settings.TITLE_GLOW_COLOR)
            hint_rect = hint.get_rect(center=(self.confirm_rect.centerx, self.confirm_rect.top + 86))
            self.screen.blit(hint, hint_rect)

            mouse_pos = pygame.mouse.get_pos()
            for idx, (label, _) in enumerate(self.confirm_options):
                rect = self.confirm_option_rects[idx]
                hovered = rect.collidepoint(mouse_pos)
                selected = idx == self.confirm_selected
                color = settings.BUTTON_HOVER_COLOR if (hovered or selected) else settings.BUTTON_COLOR
                pygame.draw.rect(self.screen, color, rect, border_radius=10)
                text = self.font_hint.render(label, True, settings.BUTTON_TEXT_COLOR)
                text_rect = text.get_rect(center=rect.center)
                self.screen.blit(text, text_rect)

        if self.notice_text and not self.confirm_action:
            notice = self.font_hint.render(self.notice_text, True, settings.TITLE_GLOW_COLOR)
            notice_rect = notice.get_rect(center=(self.panel_rect.centerx, self.panel_rect.bottom - 28))
            self.screen.blit(notice, notice_rect)

    def reset(self) -> None:
        self.selected_index = 0
        self.close_confirm()
        self.notice_text = ""
        self.notice_timer = 0.0


class AchievementsMenu:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.title = "成就"
        self.font_path = _resolve_font_path()
        self.font_title = _load_font(self.font_path, 40)
        self.font_body = _load_font(self.font_path, 22)
        self.font_small = _load_font(self.font_path, 18)
        self.panel_rect = pygame.Rect(0, 0, 720, 560)
        self.panel_rect.center = (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2)
        self.close_size = 24
        self.close_padding = 12
        self.close_rect = pygame.Rect(
            self.panel_rect.right - self.close_padding - self.close_size,
            self.panel_rect.top + self.close_padding,
            self.close_size,
            self.close_size,
        )
        self.scroll_offset = 0.0
        self.scroll_max = 0.0
        self.scroll_step = 28
        self.scroll_dragging = False
        self.scroll_drag_offset = 0
        self.scroll_track_rect = pygame.Rect(0, 0, 0, 0)
        self.scroll_handle_rect = pygame.Rect(0, 0, 0, 0)

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "close_achievements"
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.close_rect.collidepoint(event.pos):
                    return "close_achievements"
                if self.scroll_handle_rect.collidepoint(event.pos):
                    self.scroll_dragging = True
                    self.scroll_drag_offset = event.pos[1] - self.scroll_handle_rect.top
            elif event.button == 4:
                if self._mouse_in_list():
                    self._scroll_by(-self.scroll_step)
            elif event.button == 5:
                if self._mouse_in_list():
                    self._scroll_by(self.scroll_step)
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.scroll_dragging = False
        if event.type == pygame.MOUSEMOTION and self.scroll_dragging:
            self._drag_scroll(event.pos[1])
        if event.type == pygame.MOUSEWHEEL:
            if self._mouse_in_list():
                self._scroll_by(-event.y * self.scroll_step)
        return None

    def _mouse_in_list(self) -> bool:
        x, y = pygame.mouse.get_pos()
        return self.panel_rect.collidepoint((x, y))

    def _scroll_by(self, delta: float) -> None:
        if self.scroll_max <= 0:
            self.scroll_offset = 0.0
            return
        self.scroll_offset = max(0.0, min(self.scroll_max, self.scroll_offset + delta))

    def _drag_scroll(self, mouse_y: int) -> None:
        track = self.scroll_track_rect
        handle = self.scroll_handle_rect
        if self.scroll_max <= 0 or track.height <= handle.height:
            self.scroll_offset = 0.0
            return
        new_top = max(track.top, min(track.bottom - handle.height, mouse_y - self.scroll_drag_offset))
        ratio = (new_top - track.top) / max(1, track.height - handle.height)
        self.scroll_offset = max(0.0, min(self.scroll_max, ratio * self.scroll_max))

    def _draw_close_button(self, mouse_pos: tuple[int, int]) -> None:
        hovered = self.close_rect.collidepoint(mouse_pos)
        color = settings.BUTTON_HOVER_COLOR if hovered else settings.BUTTON_COLOR
        pygame.draw.rect(self.screen, color, self.close_rect, border_radius=6)
        line_color = settings.BUTTON_TEXT_COLOR
        inset = 6
        pygame.draw.line(
            self.screen,
            line_color,
            (self.close_rect.left + inset, self.close_rect.top + inset),
            (self.close_rect.right - inset, self.close_rect.bottom - inset),
            2,
        )
        pygame.draw.line(
            self.screen,
            line_color,
            (self.close_rect.left + inset, self.close_rect.bottom - inset),
            (self.close_rect.right - inset, self.close_rect.top + inset),
            2,
        )

    def update(self, dt: float) -> None:  # noqa: ARG002
        return

    def _update_scroll_metrics(self, total_rows: int, list_height: int, row_height: int) -> None:
        content_height = total_rows * row_height
        self.scroll_max = max(0.0, content_height - list_height)
        if self.scroll_offset > self.scroll_max:
            self.scroll_offset = self.scroll_max
        if self.scroll_offset < 0.0:
            self.scroll_offset = 0.0

    def draw(self, achievements: list[dict], unlocked: dict[str, bool]) -> None:
        overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        pygame.draw.rect(self.screen, (20, 26, 40), self.panel_rect, border_radius=14)
        pygame.draw.rect(self.screen, (80, 110, 150), self.panel_rect, 2, border_radius=14)

        mouse_pos = pygame.mouse.get_pos()
        self._draw_close_button(mouse_pos)

        title_surf = self.font_title.render(self.title, True, settings.TITLE_COLOR)
        title_rect = title_surf.get_rect(center=(self.panel_rect.centerx, self.panel_rect.top + 46))
        self.screen.blit(title_surf, title_rect)

        total = len(achievements)
        done = sum(1 for entry in achievements if unlocked.get(entry.get("id", ""), False))
        count_text = f"已完成 {done} / {total}"
        count_surf = self.font_small.render(count_text, True, settings.TITLE_GLOW_COLOR)
        count_rect = count_surf.get_rect(center=(self.panel_rect.centerx, self.panel_rect.top + 78))
        self.screen.blit(count_surf, count_rect)

        list_top = self.panel_rect.top + 108
        list_bottom = self.panel_rect.bottom - 18
        list_height = max(0, list_bottom - list_top)
        row_height = 54
        padding_x = 26
        scrollbar_w = 8
        row_width = self.panel_rect.width - padding_x * 2 - scrollbar_w - 8
        self._update_scroll_metrics(len(achievements), list_height, row_height)
        start_y = list_top - int(self.scroll_offset)
        track_x = self.panel_rect.right - padding_x - scrollbar_w
        self.scroll_track_rect = pygame.Rect(track_x, list_top, scrollbar_w, list_height)
        list_rect = pygame.Rect(self.panel_rect.left + padding_x, list_top, row_width, list_height)
        prev_clip = self.screen.get_clip()
        self.screen.set_clip(list_rect)
        for idx, entry in enumerate(achievements):
            y = start_y + idx * row_height
            row_rect = pygame.Rect(self.panel_rect.left + padding_x, y, row_width, row_height - 8)
            if row_rect.bottom < list_top or row_rect.top > list_bottom:
                continue
            if idx % 2 == 0:
                pygame.draw.rect(self.screen, (24, 32, 48), row_rect, border_radius=8)
            entry_id = entry.get("id", "")
            title_text = entry.get("title", "未命名成就")
            desc_text = entry.get("desc", "")
            is_done = bool(unlocked.get(entry_id, False))
            title_color = settings.TITLE_COLOR if is_done else (150, 165, 185)
            desc_color = settings.QUEST_TEXT if is_done else (120, 135, 150)
            status_text = "已完成" if is_done else "未完成"
            status_color = settings.TITLE_GLOW_COLOR if is_done else (120, 135, 150)

            title_surf = self.font_body.render(title_text, True, title_color)
            desc_surf = self.font_small.render(desc_text, True, desc_color)
            status_surf = self.font_small.render(status_text, True, status_color)

            title_pos = (row_rect.left + 10, row_rect.top + 6)
            desc_pos = (row_rect.left + 10, row_rect.top + 30)
            status_rect = status_surf.get_rect(midright=(row_rect.right - 10, row_rect.centery))

            self.screen.blit(title_surf, title_pos)
            self.screen.blit(desc_surf, desc_pos)
            self.screen.blit(status_surf, status_rect)
        self.screen.set_clip(prev_clip)

        if self.scroll_max > 0:
            handle_h = max(32, int(list_height * (list_height / max(1, len(achievements) * row_height))))
            handle_h = min(list_height, handle_h)
            handle_range = max(1, list_height - handle_h)
            handle_top = int(list_top + (self.scroll_offset / self.scroll_max) * handle_range)
            self.scroll_handle_rect = pygame.Rect(track_x, handle_top, scrollbar_w, handle_h)
            pygame.draw.rect(self.screen, (40, 50, 70), self.scroll_track_rect, border_radius=4)
            pygame.draw.rect(self.screen, (120, 170, 220), self.scroll_handle_rect, border_radius=4)
        else:
            self.scroll_handle_rect = pygame.Rect(0, 0, 0, 0)


class LoadMenu:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.title = "读取存档"
        self.font_path = _resolve_font_path()
        self.font_title = _load_font(self.font_path, 40)
        self.font_body = _load_font(self.font_path, 22)
        self.font_small = _load_font(self.font_path, 18)
        self.panel_rect = pygame.Rect(0, 0, 720, 520)
        self.panel_rect.center = (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2)
        self.close_size = 24
        self.close_padding = 12
        self.close_rect = pygame.Rect(
            self.panel_rect.right - self.close_padding - self.close_size,
            self.panel_rect.top + self.close_padding,
            self.close_size,
            self.close_size,
        )
        self.entries: list[dict] = []
        self.selected_index = 0
        self.scroll_offset = 0.0
        self.scroll_step = 28
        self.scroll_max = 0.0

    def set_entries(self, entries: list[dict]) -> None:
        self.entries = entries
        self.selected_index = 0
        self.scroll_offset = 0.0
        self.scroll_max = 0.0

    def handle_event(self, event: pygame.event.Event) -> str | tuple[str, int] | None:
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "close_load"
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = max(0, self.selected_index - 1)
                self._ensure_visible()
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = min(max(0, len(self.entries) - 1), self.selected_index + 1)
                self._ensure_visible()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return ("load_entry", self.selected_index)
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.close_rect.collidepoint(event.pos):
                    return "close_load"
                hit = self._hit_entry(event.pos)
                if hit is not None:
                    self.selected_index = hit
                    return ("load_entry", hit)
            elif event.button == 4:
                self._scroll_by(-self.scroll_step)
            elif event.button == 5:
                self._scroll_by(self.scroll_step)
        if event.type == pygame.MOUSEMOTION:
            hit = self._hit_entry(event.pos)
            if hit is not None:
                self.selected_index = hit
        if event.type == pygame.MOUSEWHEEL:
            self._scroll_by(-event.y * self.scroll_step)
        return None

    def _scroll_by(self, delta: float) -> None:
        if self.scroll_max <= 0:
            self.scroll_offset = 0.0
            return
        self.scroll_offset = max(0.0, min(self.scroll_max, self.scroll_offset + delta))

    def _ensure_visible(self) -> None:
        row_height = 52
        list_top = self.panel_rect.top + 96
        list_bottom = self.panel_rect.bottom - 18
        list_height = max(0, list_bottom - list_top)
        entry_y = self.selected_index * row_height
        if entry_y < self.scroll_offset:
            self.scroll_offset = max(0.0, entry_y)
        elif entry_y + row_height > self.scroll_offset + list_height:
            self.scroll_offset = max(0.0, entry_y + row_height - list_height)

    def _hit_entry(self, pos: tuple[int, int]) -> int | None:
        list_top = self.panel_rect.top + 96
        list_bottom = self.panel_rect.bottom - 18
        if not (self.panel_rect.left <= pos[0] <= self.panel_rect.right and list_top <= pos[1] <= list_bottom):
            return None
        row_height = 52
        index = int((pos[1] - list_top + self.scroll_offset) // row_height)
        if 0 <= index < len(self.entries):
            return index
        return None

    def _draw_close_button(self, mouse_pos: tuple[int, int]) -> None:
        hovered = self.close_rect.collidepoint(mouse_pos)
        color = settings.BUTTON_HOVER_COLOR if hovered else settings.BUTTON_COLOR
        pygame.draw.rect(self.screen, color, self.close_rect, border_radius=6)
        line_color = settings.BUTTON_TEXT_COLOR
        inset = 6
        pygame.draw.line(
            self.screen,
            line_color,
            (self.close_rect.left + inset, self.close_rect.top + inset),
            (self.close_rect.right - inset, self.close_rect.bottom - inset),
            2,
        )
        pygame.draw.line(
            self.screen,
            line_color,
            (self.close_rect.left + inset, self.close_rect.bottom - inset),
            (self.close_rect.right - inset, self.close_rect.top + inset),
            2,
        )

    def update(self, dt: float) -> None:  # noqa: ARG002
        return

    def draw(self) -> None:
        overlay = pygame.Surface((settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        pygame.draw.rect(self.screen, (20, 26, 40), self.panel_rect, border_radius=14)
        pygame.draw.rect(self.screen, (80, 110, 150), self.panel_rect, 2, border_radius=14)

        mouse_pos = pygame.mouse.get_pos()
        self._draw_close_button(mouse_pos)

        title_surf = self.font_title.render(self.title, True, settings.TITLE_COLOR)
        title_rect = title_surf.get_rect(center=(self.panel_rect.centerx, self.panel_rect.top + 44))
        self.screen.blit(title_surf, title_rect)

        list_top = self.panel_rect.top + 96
        list_bottom = self.panel_rect.bottom - 18
        list_height = max(0, list_bottom - list_top)
        row_height = 52
        padding_x = 26
        row_width = self.panel_rect.width - padding_x * 2
        content_height = len(self.entries) * row_height
        self.scroll_max = max(0.0, content_height - list_height)
        if self.scroll_offset > self.scroll_max:
            self.scroll_offset = self.scroll_max

        if not self.entries:
            notice = self.font_body.render("暂无存档", True, settings.TITLE_GLOW_COLOR)
            notice_rect = notice.get_rect(center=self.panel_rect.center)
            self.screen.blit(notice, notice_rect)
            return

        list_rect = pygame.Rect(self.panel_rect.left + padding_x, list_top, row_width, list_height)
        prev_clip = self.screen.get_clip()
        self.screen.set_clip(list_rect)
        start_y = list_top - int(self.scroll_offset)
        for idx, entry in enumerate(self.entries):
            y = start_y + idx * row_height
            row_rect = pygame.Rect(self.panel_rect.left + padding_x, y, row_width, row_height - 6)
            if row_rect.bottom < list_top or row_rect.top > list_bottom:
                continue
            selected = idx == self.selected_index
            if selected:
                pygame.draw.rect(self.screen, settings.BUTTON_HOVER_COLOR, row_rect, border_radius=8)
            elif idx % 2 == 0:
                pygame.draw.rect(self.screen, (24, 32, 48), row_rect, border_radius=8)
            time_text = entry.get("time", "未知时间")
            floor_text = entry.get("floor", "未知楼层")
            title_surf = self.font_body.render(time_text, True, settings.TITLE_COLOR if selected else settings.QUEST_TEXT)
            info_surf = self.font_small.render(f"楼层 {floor_text}", True, settings.TITLE_GLOW_COLOR if selected else (120, 135, 150))
            self.screen.blit(title_surf, (row_rect.left + 10, row_rect.top + 6))
            self.screen.blit(info_surf, (row_rect.left + 10, row_rect.top + 28))
        self.screen.set_clip(prev_clip)
