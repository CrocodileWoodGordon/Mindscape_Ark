import pygame
from scenes.base_scene import BaseScene
from entities.player import Player
from entities.enemy import MemoryDevourer

class Floor35Scene(BaseScene):
    def setup(self):
        self.name = "记忆档案馆 (Floor 35)"
        self.player = Player(10, 1)
        self.add_entity(self.player)
        
        self.load_boss()
        self.show_floor_intro()
    
    def load_boss(self):
        self.boss = MemoryDevourer(10, 10)
        self.boss.death_callback = self.on_boss_death
        self.add_entity(self.boss)
    
    def show_floor_intro(self):
        self.game.ui_manager.show_dialog({
            "speaker": "指引者系统",
            "text": "记忆档案馆。损坏的数据已凝聚成防御性实体。请极其谨慎地前进。"
        })
    
    def on_boss_death(self):
        # 记忆闪回序列
        self.game.ui_manager.show_dialog({
            "speaker": "系统",
            "text": "检测到高密度数据冲击。正在稳定你的认知……忽略那些碎片。它们是来自前世生活的损坏记忆。",
            "callback": self.unlock_elevator
        })
        
        # 解锁成就
        self.game.unlock_achievement("memory_unlocked")
    
    def unlock_elevator(self):
        # 创建电梯入口
        from entities.item import Item
        elevator = Item(10, 20, "elevator")
        elevator.interactable = True
        elevator.interact_callback = lambda player: self.game.change_scene("floor_30")
        self.add_entity(elevator)
        
        self.game.ui_manager.show_hint("通往逻辑中心的电梯已解锁")
