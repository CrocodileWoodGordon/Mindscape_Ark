import pygame
from scenes.base_scene import BaseScene
from entities.player import Player
from entities.item import Item

class Floor30Scene(BaseScene):
    def setup(self):
        self.name = "逻辑中心 (Floor 30)"
        self.player = Player(7, 1)
        self.add_entity(self.player)
        
        self.load_puzzle()
        self.show_floor_intro()
        self.setup_ui_glitch()
    
    def load_puzzle(self):
        # 三个电源继电器
        self.relays = [
            Item(4, 7, "relay", "左继电器"),
            Item(7, 7, "relay", "中继电器"), 
            Item(10, 7, "relay", "右继电器")
        ]
        
        for relay in self.relays:
            relay.interactable = True
            relay.interact_callback = self.on_relay_interact
            self.add_entity(relay)
        
        self.correct_sequence = [0, 2, 1]  # 左-右-中
        self.current_sequence = []
        self.puzzle_solved = False
    
    def setup_ui_glitch(self):
        # 设置UI故障效果
        self.ui_glitch_timer = 0
        self.ui_glitch_interval = 8.0
    
    def show_floor_intro(self):
        self.game.ui_manager.show_dialog({
            "speaker": "指引者系统",
            "text": "逻辑核心。不稳定的故障即将发生。你必须按正确顺序激活三个主要继电器来恢复电力。"
        })
    
    def update(self, dt):
        super().update(dt)
        
        # UI故障效果
        self.ui_glitch_timer += dt
        if self.ui_glitch_timer >= self.ui_glitch_interval:
            self.trigger_ui_glitch()
            self.ui_glitch_timer = 0
    
    def trigger_ui_glitch(self):
        self.game.ui_manager.show_glitch_effect(2.0)
        
        # 短暂显示真实系统信息
        self.game.ui_manager.show_system_message("[认知屏障完整性: 64%]", 1.5)
    
    def on_relay_interact(self, player):
        if self.puzzle_solved:
            return
        
        relay_index = self.relays.index(player.last_interacted)
        self.current_sequence.append(relay_index)
        
        # 检查序列
        if len(self.current_sequence) <= len(self.correct_sequence):
            if self.current_sequence[-1] != self.correct_sequence[len(self.current_sequence)-1]:
                # 错误序列
                self.current_sequence = []
                self.game.ui_manager.show_dialog({
                    "speaker": "系统",
                    "text": "序列错误。继电器已重置。"
                })
                # 对玩家造成伤害
                player.take_damage(10)
            elif len(self.current_sequence) == len(self.correct_sequence):
                # 正确序列
                self.puzzle_solved = True
                self.on_puzzle_solved()
    
    def on_puzzle_solved(self):
        self.game.ui_manager.show_dialog({
            "speaker": "系统", 
            "text": "电力恢复。逻辑核心稳定。"
        })
        
        # 解锁电梯
        elevator = Item(7, 15, "elevator")
        elevator.interactable = True
        elevator.interact_callback = lambda player: self.game.change_scene("floor_25")
        self.add_entity(elevator)
        
        self.game.unlock_achievement("logic_puzzle_solved")
