import pygame
import random
from scenes.base_scene import BaseScene
from entities.player import Player
from entities.npc import NPC
from entities.item import Item

class Floor40Scene(BaseScene):
    def setup(self):
        self.name = "感官实验室 (Floor 40)"
        self.player = Player(1, 1)
        self.add_entity(self.player)
        
        self.load_entities()
        self.setup_dynamic_paths()
        self.show_floor_intro()
    
    def setup_dynamic_paths(self):
        self.dynamic_paths = [
            {'rect': pygame.Rect(5, 1, 3, 1), 'active': False, 'timer': 0},
            {'rect': pygame.Rect(1, 5, 1, 3), 'active': False, 'timer': 0},
            {'rect': pygame.Rect(5, 10, 3, 1), 'active': False, 'timer': 0}
        ]
        self.path_toggle_interval = 5.0
    
    def load_entities(self):
        # 逻辑错误实体
        logic_entity = NPC(3, 3, "logic_error")
        logic_entity.dialogs = [
            "呃...又来了...",
            "为什么...总是这里疼？",
            "地板！地板在呼吸！你感觉不到吗？！"
        ]
        logic_entity.interactable = True
        logic_entity.interact_callback = self.on_logic_entity_interact
        self.add_entity(logic_entity)
        
        # 电梯开关
        elevator_switch = Item(10, 10, "elevator_switch")
        elevator_switch.interactable = True
        elevator_switch.interact_callback = self.on_elevator_switch_interact
        self.add_entity(elevator_switch)
    
    def show_floor_intro(self):
        self.game.ui_manager.show_dialog({
            "speaker": "指引者系统", 
            "text": "感官实验室。环境数据极不稳定。请谨慎行事。"
        })
    
    def update(self, dt):
        super().update(dt)
        self.update_dynamic_paths(dt)
        self.check_player_on_path()
    
    def update_dynamic_paths(self, dt):
        for path in self.dynamic_paths:
            path['timer'] += dt
            if path['timer'] >= self.path_toggle_interval:
                path['active'] = not path['active']
                path['timer'] = 0
    
    def check_player_on_path(self):
        if not self.player:
            return
        
        player_rect = self.player.rect
        for path in self.dynamic_paths:
            if not path['active'] and path['rect'].colliderect(player_rect):
                self.player.x = 1
                self.player.y = 1
                self.game.ui_manager.show_dialog({
                    "speaker": "指引者系统",
                    "text": "空间数据损坏。重新计算最安全路径。"
                })
                break
    
    def on_logic_entity_interact(self, player):
        entity = next(e for e in self.entities if hasattr(e, 'name') and e.name == "logic_error")
        
        if not hasattr(entity, 'interact_count'):
            entity.interact_count = 0
        
        entity.interact_count += 1
        
        if entity.interact_count <= len(entity.dialogs):
            self.game.ui_manager.show_dialog({
                "speaker": "逻辑错误实体",
                "text": entity.dialogs[entity.interact_count - 1]
            })
            
            if entity.interact_count == len(entity.dialogs):
                self.game.ui_manager.show_dialog({
                    "speaker": "指引者系统",
                    "text": "检测到逻辑错误实体。其不稳定性对环境构成威胁。建议清除。"
                })
    
    def on_elevator_switch_interact(self, player):
        self.game.change_scene("floor_35")
