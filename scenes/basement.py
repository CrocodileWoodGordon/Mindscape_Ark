import pygame
from scenes.base_scene import BaseScene
from entities.player import Player
from entities.item import Item

class BasementScene(BaseScene):
    def setup(self):
        self.name = "神喻之间 (Basement)"
        self.player = Player(15, 5)
        self.add_entity(self.player)
        
        self.load_oracle_room()
        self.show_floor_intro()
    
    def load_oracle_room(self):
        # 控制核心
        self.control_core = Item(15, 15, "control_core")
        self.control_core.interactable = True
        self.control_core.interact_callback = self.on_control_core_interact
        self.add_entity(self.control_core)
    
    def show_floor_intro(self):
        if self.game.player_data['moral_choice'] == 0:
            speaker = "系统"
            text = "高效。数据完整性98%。前往控制核心进行上传。"
        else:
            speaker = "艾拉"
            text = "这就是一切的源头。方舟计划的控制核心。我们必须终止这个循环。"
        
        self.game.ui_manager.show_dialog({
            "speaker": speaker,
            "text": text
        })
    
    def on_control_core_interact(self, player):
        self.game.ui_manager.show_ending_sequence([
            "你触摸控制核心……",
            "系统开始崩溃……",
            "现实本身开始瓦解……"
        ], self.show_first_reveal)
    
    def show_first_reveal(self):
        # 第一层反转：缸中之脑
        self.game.ui_manager.show_brain_reveal(
            "巡视员，7号实验体已下线。",
            f"最终抉择记录: {'牺牲' if self.game.player_data['moral_choice'] == 0 else '保护'}模拟人格。",
            "数据已收录。",
            self.show_second_reveal
        )
    
    def show_second_reveal(self):
        # 第二层反转：巡视员身份
        self.game.ui_manager.show_final_reveal(
            "方舟计划第7次迭代失败。",
            "是否需要准备启动第8号实验体？",
            self.show_final_choice
        )
    
    def show_final_choice(self):
        self.game.ui_manager.show_final_choice(
            ["启动第8次迭代", "终止协议"],
            self.on_final_choice
        )
    
    def on_final_choice(self, choice):
        if choice == 0:  # 启动迭代
            self.game.ui_manager.show_ending_cutscene([
                "第8号实验体在50层休眠舱中醒来……",
                "系统提示：//BOOT_SEQUENCE_INITIATED...",
                "循环继续……"
            ], self.restart_game)
        else:  # 终止协议
            self.game.ui_manager.show_ending_cutscene([
                "所有监控屏幕变黑……",
                "系统完全关闭……",
                "方舟协议终止……",
                "模拟人格获得自由……"
            ], self.restart_game)
    
    def restart_game(self):
        self.game.unlock_achievement("cogito_ergo_sum")
        self.game.change_scene("floor_50")
