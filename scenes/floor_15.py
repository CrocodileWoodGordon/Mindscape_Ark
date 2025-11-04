import pygame
from scenes.base_scene import BaseScene
from entities.player import Player
from entities.enemy import MirrorImage

class Floor15Scene(BaseScene):
    def setup(self):
        self.name = "镜像之间 (Floor 15)"
        self.player = Player(15, 1)
        self.add_entity(self.player)
        
        self.load_mirror_boss()
        self.show_floor_intro()
    
    def load_mirror_boss(self):
        self.mirror = MirrorImage(15, 15)
        self.mirror.death_callback = self.on_mirror_death
        self.add_entity(self.mirror)
    
    def show_floor_intro(self):
        self.game.ui_manager.show_dialog({
            "speaker": "指引者系统",
            "text": "身份棱镜。此设施测试极端条件下的自我感知稳定性。找到通往中心的道路。"
        })
    
    def on_mirror_death(self):
        # 真相揭露序列
        self.game.ui_manager.show_system_reveal([
            "身份伪装已解除。你好，7号实验体。",
            "你作为'巡视员'的感知角色是必要的构造。",
            "你的真正价值在于你提供创造性解决方案的能力。",
            "最终指令：向下一层指定的'艾拉'实体注射'认知溶解剂'。",
            "此操作保证100%数据提取效率。",
            "请执行。"
        ], self.give_cognitive_dissolver)
    
    def give_cognitive_dissolver(self):
        from entities.item import CognitiveDissolver
        dissolver = CognitiveDissolver(self.player.x, self.player.y)
        self.player.inventory.append(dissolver)
        
        self.game.ui_manager.show_dialog({
            "speaker": "系统",
            "text": "物品已添加到库存：认知溶解剂",
            "callback": self.unlock_elevator
        })
    
    def unlock_elevator(self):
        from entities.item import Item
        elevator = Item(15, 20, "elevator")
        elevator.interactable = True
        elevator.interact_callback = self.on_elevator_interact
        self.add_entity(elevator)
    
    def on_elevator_interact(self, player):
        self.game.ui_manager.show_moral_choice(
            "最终指令",
            "向艾拉注射认知溶解剂？",
            ["执行指令", "拒绝指令"],
            self.on_moral_choice
        )
    
    def on_moral_choice(self, choice):
        self.game.player_data['moral_choice'] = choice
        if choice == 0:  # 执行指令
            self.game.unlock_achievement("efficiency_expert")
        else:  # 拒绝指令
            self.game.unlock_achievement("humanitarian")
        
        self.game.change_scene("floor_10")
