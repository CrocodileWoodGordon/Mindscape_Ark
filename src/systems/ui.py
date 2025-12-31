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
        self.confirm_rect = pygame.Rect(0, 0, 420, 240)
        self.confirm_rect.center = (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2)
        self.confirm_option_rects: list[pygame.Rect] = []
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
        total_h = len(self.confirm_options) * button_h + (len(self.confirm_options) - 1) * gap
        start_y = self.confirm_rect.centery + 20 - total_h // 2
        rects: list[pygame.Rect] = []
        for idx in range(len(self.confirm_options)):
            rect = pygame.Rect(0, 0, button_w, button_h)
            rect.center = (self.confirm_rect.centerx, start_y + idx * (button_h + gap))
            rects.append(rect)
        return rects

    def handle_event(self, event: pygame.event.Event) -> str | None:
        if self.confirm_action:
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
            for idx, rect in enumerate(self.option_rects):
                if rect.collidepoint(event.pos):
                    self.selected_index = idx
                    return self.options[idx][1]
        return None

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

        title_surf = self.font_title.render(self.title, True, settings.TITLE_COLOR)
        title_rect = title_surf.get_rect(center=(self.panel_rect.centerx, self.panel_rect.top + 50))
        self.screen.blit(title_surf, title_rect)

        mouse_pos = pygame.mouse.get_pos()
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

            title = self.font_title.render("未存档", True, settings.TITLE_COLOR)
            title_rect = title.get_rect(center=(self.confirm_rect.centerx, self.confirm_rect.top + 46))
            self.screen.blit(title, title_rect)

            hint = self.font_hint.render("当前进度尚未存档，请选择操作", True, settings.TITLE_GLOW_COLOR)
            hint_rect = hint.get_rect(center=(self.confirm_rect.centerx, self.confirm_rect.top + 88))
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
