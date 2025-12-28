"""UI elements including start menu."""

import pygame
from ..core import settings


class StartMenu:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.title = settings.WINDOW_TITLE
        self.font_path = self._resolve_font()
        self.font_title = self._load_font(74)
        self.font_sub = self._load_font(30)
        self.font_btn = self._load_font(36)
        w, h = settings.START_BUTTON_SIZE
        self.button_rect = pygame.Rect(0, 0, w, h)
        self.button_rect.center = (settings.WINDOW_WIDTH // 2, settings.WINDOW_HEIGHT // 2 + 120)
        self._start_requested = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_requested = True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.button_rect.collidepoint(event.pos):
                self._start_requested = True
        return self._start_requested

    def update(self, dt: float) -> None:  # noqa: ARG002
        pass

    def _resolve_font(self) -> str | None:
        if settings.FONTS_DIR.exists():
            candidates = [p for p in sorted(settings.FONTS_DIR.iterdir()) if p.is_file() and p.suffix.lower() in {".ttf", ".otf"}]
            preferred = [p for p in candidates if "notosanssc" in p.name.lower()]
            pick = preferred[0] if preferred else (candidates[0] if candidates else None)
            return str(pick) if pick else None
        return None

    def _load_font(self, size: int) -> pygame.font.Font:
        if self.font_path:
            try:
                return pygame.font.Font(self.font_path, size)
            except Exception:
                pass
        return pygame.font.SysFont(settings.UI_FONT_NAME, size)

    def draw(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        hover = self.button_rect.collidepoint(mouse_pos)
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

        # Button
        color = settings.BUTTON_HOVER_COLOR if hover else settings.BUTTON_COLOR
        pygame.draw.rect(self.screen, color, self.button_rect, border_radius=10)
        text = self.font_btn.render("开始游戏", True, settings.BUTTON_TEXT_COLOR)
        text_rect = text.get_rect(center=self.button_rect.center)
        self.screen.blit(text, text_rect)

    @property
    def start_requested(self) -> bool:
        return self._start_requested

    def reset(self) -> None:
        """Return menu to idle state so it can be shown again."""
        self._start_requested = False
