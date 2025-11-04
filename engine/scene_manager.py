import importlib
from config import Config

class SceneManager:
    def __init__(self, game):
        self.game = game
        self.current_scene = None
        self.scenes = {}
        self.load_scenes()
        self.change_scene("floor_50")
    
    def load_scenes(self):
        scene_modules = [
            'floor_50', 'floor_40', 'floor_35', 'floor_30',
            'floor_25', 'floor_15', 'floor_10', 'basement'
        ]
        
        for scene_name in scene_modules:
            try:
                module = importlib.import_module(f'scenes.{scene_name}')
                scene_class = getattr(module, f'{scene_name.capitalize()}Scene')
                self.scenes[scene_name] = scene_class
            except Exception as e:
                print(f"加载场景 {scene_name} 失败: {e}")
    
    def change_scene(self, scene_name):
        if scene_name in self.scenes:
            if self.current_scene:
                self.current_scene.cleanup()
            
            self.current_scene = self.scenes[scene_name](self.game)
            self.current_scene.setup()
            self.game.player_data['current_floor'] = int(scene_name.split('_')[1])
            print(f"切换到场景: {scene_name}")
        else:
            print(f"场景不存在: {scene_name}")
    
    def handle_event(self, event):
        if self.current_scene:
            self.current_scene.handle_event(event)
    
    def update(self, dt):
        if self.current_scene:
            self.current_scene.update(dt)
    
    def render(self, screen):
        if self.current_scene:
            self.current_scene.render(screen)
