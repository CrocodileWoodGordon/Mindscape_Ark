import pygame
from scenes.base_scene import BaseScene
from entities.player import Player
from entities.item import Item
from entities.enemy import DataGlitch

class Floor50Scene(BaseScene):
    def setup(self):
        self.name = "休眠舱 (Floor 50)"
        self.player = Player(5, 5)
        self.add_entity(self.player)
        self.load_entities()
        self.start_initial_sequence()
    
    def load_entities(self):
        # 电子相框
        photo_frame = Item(8, 8, "electronic_frame")
        photo_frame.interactable = True
        photo_frame.interact_callback = self.on_photo_frame_interact
        self.add_entity(photo_frame)
        
        # 终端机
        terminal1 = Item(7, 8, "terminal")
        terminal1.interactable = True
        terminal1.interact_callback = self.on_terminal1_interact
        self.add_entity(terminal1)
        
        terminal2 = Item(17, 4, "terminal")
        terminal2.interactable = True
        terminal2.interact_callback = self.on_terminal2_interact
        self.add_entity(terminal2)
        
        # 电梯
        elevator = Item(19, 39, "elevator")
        elevator.interactable = True
        elevator.interact_callback = self.on_elevator_interact
        elevator.locked = True
        self.add_entity(elevator)
        
        # 敌人
        enemies = [
            DataGlitch(3, 3),
            DataGlitch(7, 3),
            DataGlitch(5, 7)
        ]
        for enemy in enemies:
            self.add_entity(enemy)
    
    def start_initial_sequence(self):
        self.game.ui_manager.show_dialog({
            "speaker": "系统",
            "text": "//BOOT_SEQUENCE_INITIATED.../SIMULATION_LOADING...",
            "callback": self.show_welcome_message
        })
    
    def show_welcome_message(self):
        self.game.ui_manager.show_dialog({
            "speaker": "指引者系统",
            "text": "系统上线。欢迎回来，巡视员。正在初始化环境扫描...",
            "callback": self.show_movement_tutorial
        })
    
    def show_movement_tutorial(self):
        self.game.ui_manager.show_hint("点击地面移动角色")
    
    def on_photo_frame_interact(self, player):
        self.game.ui_manager.show_dialog({
            "speaker": "指引者系统",
            "text": "警告：检测到局部数据冗余。已清理。"
        })
    
    def on_terminal1_interact(self, player):
        log_text = """[DR. KAINES LOG - ENTRY 001]
认知锚定成功。
目标"巡视员"相信主要任务是"拯救方舟"。
生命体征稳定。现实阻抗：0.2%。
开始第一阶段。"""
        
        self.game.ui_manager.show_log("研究日志", log_text)
        self.start_combat_tutorial()
    
    def on_terminal2_interact(self, player):
        log_text = """[方舟人员备忘录]
所有非必要人员必须在1800时前完成神经同步。
认知锚定程序无痛，确保您的注意力始终集中在我们的主要使命上：拯救方舟。"""
        
        self.game.ui_manager.show_log("人员备忘录", log_text)
    
    def on_elevator_interact(self, player):
        if hasattr(self, 'elevator_unlocked') and self.elevator_unlocked:
            self.game.change_scene("floor_40")
        else:
            self.game.ui_manager.show_dialog({
                "speaker": "系统",
                "text": "电梯访问被拒绝。请先清除该区域的数据异常。"
            })
    
    def start_combat_tutorial(self):
        self.game.ui_manager.show_hint("右键点击敌人进行攻击")
        self.player.teaching_mode = True
    
    def update(self, dt):
        super().update(dt)
        
        if not hasattr(self, 'elevator_unlocked'):
            enemies_remaining = any(isinstance(e, DataGlitch) for e in self.entities)
            if not enemies_remaining:
                self.elevator_unlocked = True
                self.game.unlock_achievement("first_contact")
                self.game.ui_manager.show_hint("电梯已解锁。可以前往下一层了。")
