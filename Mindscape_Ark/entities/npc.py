from engine.entity import Entity

class NPC(Entity):
    def __init__(self, x, y, npc_type, display_name=None):
        super().__init__(x, y, 1, 1)
        self.npc_type = npc_type
        self.display_name = display_name or self.get_speaker_name()
        self.interactable = True
        self.dialogs = []
        self.current_dialog_index = 0
        
        self.load_sprite(f"sprites/npc_{npc_type}.png")
    
    def interact(self, player):
        player.last_interacted = self
        
        if self.dialogs and self.current_dialog_index < len(self.dialogs):
            dialog = {
                "speaker": self.display_name,
                "text": self.dialogs[self.current_dialog_index]
            }
            player.scene.game.ui_manager.show_dialog(dialog)
            
            self.current_dialog_index += 1
            
            if self.current_dialog_index >= len(self.dialogs) and hasattr(self, 'final_callback'):
                self.final_callback(player)
        else:
            player.scene.game.ui_manager.show_dialog({
                "speaker": self.display_name,
                "text": "..."
            })
    
    def get_speaker_name(self):
        names = {
            "logic_error": "逻辑错误实体",
            "aera": "艾拉",
            "engineer": "工程师马克",
            "doctor": "医生莉娜",
            "technician": "技术员奇普"
        }
        return names.get(self.npc_type, "未知NPC")

class EmotionalNPC(NPC):
    def __init__(self, x, y, npc_type, display_name):
        super().__init__(x, y, npc_type, display_name)
        self.emotion_type = npc_type

class Aera(NPC):
    def __init__(self, x, y):
        super().__init__(x, y, "aera", "艾拉")
        self.dialogs = [
            "巡视员！你终于来了！我们找到了一些证据，系统它——"
        ]
