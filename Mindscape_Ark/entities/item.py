from engine.entity import Entity

class Item(Entity):
    def __init__(self, x, y, item_type, display_name=None):
        super().__init__(x, y, 1, 1)
        self.item_type = item_type
        self.display_name = display_name or item_type
        self.interact_callback = None
        self.locked = False
        
        self.load_sprite(f"sprites/item_{item_type}.png")
    
    def interact(self, player):
        player.last_interacted = self
        
        if self.locked:
            player.scene.game.ui_manager.show_dialog({
                "speaker": "系统",
                "text": f"{self.display_name} 已锁定。"
            })
            return
        
        if self.interact_callback:
            self.interact_callback(player)

class CognitiveDissolver(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "cognitive_dissolver", "认知溶解剂")
        self.is_cognitive_dissolver = True

class DataCore(Item):
    def __init__(self, x, y):
        super().__init__(x, y, "data_core", "数据核心")
        self.health = 100
        self.max_health = 100
