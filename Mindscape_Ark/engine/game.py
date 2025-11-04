import pygame
from config import Config
from engine.scene_manager import SceneManager
from engine.ui import UIManager
from engine.audio import AudioManager

class Game:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = 0
        
        # 初始化子系统
        self.scene_manager = SceneManager(self)
        self.ui_manager = UIManager(self)
        self.audio_manager = AudioManager(self)
        
        # 游戏状态
        self.player_data = {
            'current_floor': 50,
            'inventory': [],
            'dialog_history': [],
            'moral_choice': None,
            'achievements': set()
        }
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.dt = self.clock.tick(Config.FPS) / 1000.0
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            self.scene_manager.handle_event(event)
            self.ui_manager.handle_event(event)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.ui_manager.toggle_menu()
                elif event.key == pygame.K_j:
                    self.ui_manager.toggle_log()
                elif event.key == pygame.K_f and Config.DEBUG_MODE:
                    print("调试信息:", self.player_data)
    
    def update(self):
        self.scene_manager.update(self.dt)
        self.ui_manager.update(self.dt)
    
    def render(self):
        self.screen.fill(Config.COLORS['background'])
        self.scene_manager.render(self.screen)
        self.ui_manager.render(self.screen)
        pygame.display.flip()
    
    def change_scene(self, scene_name):
        self.scene_manager.change_scene(scene_name)
    
    def unlock_achievement(self, achievement_id):
        if achievement_id not in self.player_data['achievements']:
            self.player_data['achievements'].add(achievement_id)
            self.ui_manager.show_achievement(achievement_id)
    
    def save_game(self):
        import json
        try:
            with open('save_data.json', 'w') as f:
                json.dump(self.player_data, f)
            print("游戏已保存")
        except Exception as e:
            print(f"保存失败: {e}")
    
    def load_game(self):
        import json
        try:
            with open('save_data.json', 'r') as f:
                self.player_data = json.load(f)
            print("游戏已加载")
        except Exception as e:
            print(f"加载失败: {e}")
