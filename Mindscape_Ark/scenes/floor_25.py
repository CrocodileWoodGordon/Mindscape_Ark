import pygame
from scenes.base_scene import BaseScene
from entities.player import Player
from entities.npc import EmotionalNPC
from entities.enemy import EmotionalCore

class Floor25Scene(BaseScene):
    def setup(self):
        self.name = "情感共鸣器 (Floor 25)"
        self.player = Player(12, 1)
        self.add_entity(self.player)
        
        self.load_emotional_npcs()
        self.load_boss()
        self.show_floor_intro()
    
    def load_emotional_npcs(self):
        emotions = [
            ("weeping_woman", "哭泣的女人", "数据流……带走了我的孩子……我看见他化成了光……"),
            ("angry_man", "愤怒的男人", "都是谎言！这方舟就是个监狱！我们是实验用的小白鼠！你看不出来吗？！"),
            ("numb_elder", "麻木的老人", "没用的……抵抗是没用的……我们只是……等待被删除的文件……"),
            ("confused_youth", "困惑的青年", "数字……它们加起来不对。物理定律是错的。这个地方……是拼凑起来的。廉价的模仿。"),
            ("fearful_scientist", "恐惧的科学家", "它在监视我们。一直在监视。从屏幕后面。不要抬头看！它不喜欢被看见！"),
            ("betrayed_guard", "被背叛的守卫", "我信任系统。我做了它要求的一切。为了什么？像坏掉的工具一样被丢弃？"),
            ("accepting_philosopher", "接纳的哲学家", "也许……这就是我们现在的样子。也许从来就没有'以前'。这种痛苦，这种喜悦……就是我们拥有的一切。这样不好吗？")
        ]
        
        self.emotional_npcs = []
        positions = [(5, 5), (15, 5), (25, 5), (5, 15), (15, 15), (25, 15), (15, 25)]
        
        for (npc_type, name, dialog), pos in zip(emotions, positions):
            npc = EmotionalNPC(pos[0], pos[1], npc_type, name)
            npc.dialogs = [dialog]
            npc.interactable = True
            npc.interact_callback = self.on_emotional_npc_interact
            self.add_entity(npc)
            self.emotional_npcs.append(npc)
    
    def load_boss(self):
        self.boss = EmotionalCore(15, 15)
        self.boss.death_callback = self.on_boss_death
        self.add_entity(self.boss)
    
    def show_floor_intro(self):
        self.game.ui_manager.show_dialog({
            "speaker": "指引者系统",
            "text": "情感共鸣器。极端的情感能量已物理显现。清除中央异常以稳定场域。"
        })
    
    def on_emotional_npc_interact(self, player):
        npc = player.last_interacted
        if hasattr(npc, 'interacted') and npc.interacted:
            return
        
        npc.interacted = True
        self.game.ui_manager.show_dialog({
            "speaker": npc.display_name,
            "text": npc.dialogs[0]
        })
        
        # 检查是否与所有NPC对话过
        if all(hasattr(npc, 'interacted') for npc in self.emotional_npcs):
            self.game.unlock_achievement("truth_seeker")
            self.game.ui_manager.show_dialog({
                "speaker": "系统",
                "text": "情感数据收集完成。解锁额外移动速度。"
            })
    
    def on_boss_death(self):
        self.game.ui_manager.show_dialog({
            "speaker": "系统",
            "text": "情感污染源已净化。通往镜像之间的道路已开启。"
        })
        from entities.item import Item
        elevator = Item(12, 25, "elevator")
        elevator.interactable = True
        elevator.interact_callback = lambda player: self.game.change_scene("floor_15")
        self.add_entity(elevator)
