import pygame
from config import Config

class Entity:
    def __init__(self, x, y, width=1, height=1):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.sprite = None
        self.collidable = True
        self.interactable = False
        self.interact_range = 2.0
        self.scene = None
    
    @property
    def rect(self):
        return pygame.Rect(
            self.x * Config.TILE_SIZE,
            self.y * Config.TILE_SIZE,
            self.width * Config.TILE_SIZE,
            self.height * Config.TILE_SIZE
        )
    
    def load_sprite(self, sprite_path):
        try:
            self.sprite = pygame.image.load(sprite_path).convert_alpha()
            target_size = (self.width * Config.TILE_SIZE, self.height * Config.TILE_SIZE)
            self.sprite = pygame.transform.scale(self.sprite, target_size)
        except pygame.error as e:
            print(f"无法加载精灵图 {sprite_path}: {e}")
            self.sprite = pygame.Surface(target_size)
            self.sprite.fill(Config.COLORS['debug'])
    
    def update(self, dt):
        pass
    
    def render(self, screen):
        if self.sprite:
            screen.blit(self.sprite, self.rect)
        elif Config.DEBUG_MODE:
            pygame.draw.rect(screen, Config.COLORS['debug'], self.rect, 1)
    
    def interact(self, player):
        pass
    
    def is_near(self, other_entity):
        distance = ((self.x - other_entity.x) ** 2 + (self.y - other_entity.y) ** 2) ** 0.5
        return distance <= self.interact_range
