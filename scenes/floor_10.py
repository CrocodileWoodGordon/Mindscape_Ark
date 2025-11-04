import pygame
from scenes.base_scene import BaseScene
from entities.player import Player
from entities.npc import Aera
from entities.enemy import SystemPurifier

class Floor10Scene(BaseScene):
    def setup(self):
        self.name = "避难所 (Floor 10)"
        self.player = Player(12, 1)
        self.add_entity(self.player)
        
        self.load_sanctuary()
        self.show_floor_intro()
    
    def load_sanctuary(self):
        # 艾拉NPC
        self.aera = Aera(12, 12)
        self.aera.interactable = True
        self.aera.interact_callback = self.on_aera_interact
        self.add_entity(self.aera)
        
        # 数据核心
        from entities.item import DataCore
        self.data_core = DataCore(12, 14)
        self.add_entity(self.data_core)
    
    def show_floor_intro(self):
        if self.game.player_data['moral_choice'] == 0:  # 牺牲路线
            self.execute_sacrifice_route()
        else:  # 保护路线
            self.execute_protect_route()
    
    def execute_sacrifice_route(self):
        # 牺牲艾拉
        self.game.ui_manager.show_dialog({
            "speaker": "艾拉",
            "text": "巡视员！你终于来了！我们找到了一些证据，系统它——",
            "callback": self.perform_sacrifice
        })
    
    def perform_sacrifice(self):
        # 找到认知溶解剂
        dissolver = next(item for item in self.player.inventory if hasattr(item, 'is_cognitive_dissolver'))
        
        self.game.ui_manager.show_cutscene([
            "你从背后接近艾拉……",
            "举起认知溶解剂……",
            "注射！",
            "艾拉惊愕地回头，身体开始化为像素尘埃……",
            "只留下一声戛然而止的悲鸣……"
        ], self.after_sacrifice)
    
    def after_sacrifice(self):
        self.remove_entity(self.aera)
        self.game.ui_manager.show_dialog({
            "speaker": "系统",
            "text": "高效的选择。数据完整性98%。前往神喻之间进行上传。"
        })
        
        self.unlock_elevator()
    
    def execute_protect_route(self):
        self.game.ui_manager.show_dialog({
            "speaker": "艾拉", 
            "text": "巡视员！你终于来了！我们找到了一些证据，系统它——",
            "callback": self.start_defense_battle
        })
    
    def start_defense_battle(self):
        self.game.ui_manager.show_dialog({
            "speaker": "艾拉",
            "text": "我就知道……我一直在怀疑。我们必须保护这个数据核心，它包含了所有证据！"
        })
        
        # 生成系统净化者
        self.wave_count = 0
        self.start_next_wave()
    
    def start_next_wave(self):
        self.wave_count += 1
        enemy_positions = [(10, 5), (14, 5), (8, 7), (16, 7)]
        
        for pos in enemy_positions:
            purifier = SystemPurifier(pos[0], pos[1])
            purifier.death_callback = self.on_enemy_death
            self.add_entity(purifier)
        
        self.enemies_remaining = len(enemy_positions)
        self.game.ui_manager.show_hint(f"防御波次 {self.wave_count}/5 - 保护数据核心和艾拉！")
    
    def on_enemy_death(self):
        self.enemies_remaining -= 1
        if self.enemies_remaining <= 0:
            if self.wave_count < 5:
                self.start_next_wave()
            else:
                self.defense_victory()
    
    def defense_victory(self):
        self.game.ui_manager.show_dialog({
            "speaker": "艾拉",
            "text": "我们做到了……谢谢你相信我们。现在，我们必须面对最终的真相。",
            "callback": self.unlock_elevator
        })
    
    def unlock_elevator(self):
        from entities.item import Item
        elevator = Item(12, 25, "elevator")
        elevator.interactable = True
        elevator.interact_callback = lambda player: self.game.change_scene("basement")
        self.add_entity(elevator)
    
    def on_aera_interact(self, player):
        # 在保护路线中与艾拉对话
        if self.game.player_data['moral_choice'] == 1:
            self.game.ui_manager.show_dialog({
                "speaker": "艾拉",
                "text": "我们一起面对这一切。系统不会得逞的。"
            })
