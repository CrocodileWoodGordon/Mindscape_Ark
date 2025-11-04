import pygame
from engine.entity import Entity
from config import Config

class Player(Entity):
    def __init__(self, x, y):
        super().__init__(x, y, 1, 1)
        self.speed = 3.0
        self.target_x = x
        self.target_y = y
        self.moving = False
        self.teaching_mode = False
        self.health = 100
        self.max_health = 100
        self.inventory = []
        self.last_interacted = None
        
        self.load_sprite(Config.get_asset_path('sprites', 'player.png'))
        
        self.direction = 'down'
        self.animation_frame = 0
        self.animation_timer = 0
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            grid_x = mouse_x // Config.TILE_SIZE
            grid_y = mouse_y // Config.TILE_SIZE
            
            if not self.scene.check_collision(grid_x, grid_y):
                self.set_target(grid_x, grid_y)
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            self.attack()
    
    def set_target(self, x, y):
        self.target_x = x
        self.target_y = y
        self.moving = True
        
        if abs(x - self.x) > abs(y - self.y):
            self.direction = 'right' if x > self.x else 'left'
        else:
            self.direction = 'down' if y > self.y else 'up'
    
    def attack(self):
        for entity in self.scene.entities:
            if hasattr(entity, 'is_enemy') and entity.is_enemy:
                if self.is_near(entity):
                    entity.take_damage(25)
                    break
    
    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.die()
    
    def die(self):
        print("玩家死亡")
        # 重新开始当前场景
        self.scene.setup()
    
    def update(self, dt):
        if self.moving:
            dx = self.target_x - self.x
            dy = self.target_y - self.y
            distance = (dx**2 + dy**2)**0.5
            
            if distance < 0.1:
                self.x = self.target_x
                self.y = self.target_y
                self.moving = False
            else:
                move_distance = self.speed * dt
                if move_distance > distance:
                    move_distance = distance
                
                self.x += (dx / distance) * move_distance
                self.y += (dy / distance) * move_distance
            
            self.animation_timer += dt
            if self.animation_timer >= 0.2:
                self.animation_frame = (self.animation_frame + 1) % 2
                self.animation_timer = 0
        else:
            self.animation_frame = 0
    
    def render(self, screen):
        super().render(screen)
        
        if Config.DEBUG_MODE and self.moving:
            target_rect = pygame.Rect(
                self.target_x * Config.TILE_SIZE,
                self.target_y * Config.TILE_SIZE,
                Config.TILE_SIZE, Config.TILE_SIZE
            )
            pygame.draw.rect(screen, (0, 255, 0), target_rect, 2)
