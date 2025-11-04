import pygame
from config import Config

class BaseScene:
    def __init__(self, game):
        self.game = game
        self.entities = []
        self.player = None
        self.background = None
        self.collision_map = None
        self.name = "未知场景"
        
    def setup(self):
        pass
    
    def cleanup(self):
        self.entities.clear()
    
    def handle_event(self, event):
        if self.player:
            self.player.handle_event(event)
        
        if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
            self.check_interactions()
    
    def update(self, dt):
        for entity in self.entities:
            entity.update(dt)
    
    def render(self, screen):
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill(Config.COLORS['background'])
        
        for entity in self.entities:
            entity.render(screen)
    
    def check_interactions(self):
        if not self.player:
            return
        
        for entity in self.entities:
            if entity.interactable and entity.is_near(self.player):
                entity.interact(self.player)
                break
    
    def add_entity(self, entity):
        entity.scene = self
        self.entities.append(entity)
    
    def remove_entity(self, entity):
        if entity in self.entities:
            self.entities.remove(entity)
    
    def check_collision(self, x, y):
        if not self.collision_map:
            return False
        
        map_x, map_y = int(x), int(y)
        if 0 <= map_x < len(self.collision_map[0]) and 0 <= map_y < len(self.collision_map):
            return self.collision_map[map_y][map_x] == 1
        return True
