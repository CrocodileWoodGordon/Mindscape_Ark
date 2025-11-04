from engine.entity import Entity

class Enemy(Entity):
    def __init__(self, x, y, enemy_type):
        super().__init__(x, y, 1, 1)
        self.enemy_type = enemy_type
        self.is_enemy = True
        self.health = 100
        self.max_health = 100
        self.death_callback = None
        
        self.load_sprite(f"sprites/enemy_{enemy_type}.png")
    
    def take_damage(self, amount):
        self.health -= amount
        if self.health <= 0:
            self.die()
    
    def die(self):
        if self.death_callback:
            self.death_callback()
        self.scene.remove_entity(self)

class DataGlitch(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, "data_glitch")
        self.health = 30
        self.max_health = 30

class MemoryDevourer(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, "memory_devourer")
        self.width = 2
        self.height = 2
        self.health = 200
        self.max_health = 200
        self.attack_timer = 0

class EmotionalCore(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, "emotional_core")
        self.health = 150
        self.max_health = 150
        self.current_emotion = "anger"

class MirrorImage(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, "mirror_image")
        self.health = 120
        self.max_health = 120

class SystemPurifier(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y, "system_purifier")
        self.health = 80
        self.max_health = 80
