import pygame
from config import Config

class UIManager:
    def __init__(self, game):
        self.game = game
        self.active_dialog = None
        self.active_hint = None
        self.hint_timer = 0
        self.show_menu = False
        self.show_log = False
        self.show_glitch = False
        self.glitch_timer = 0
        self.system_message = None
        self.system_message_timer = 0
        
        self.fonts = self.load_fonts()
        self.dialog_callback = None
        self.log_entries = []
        self.achievements = {
            "first_contact": "初识异常",
            "memory_unlocked": "记忆解锁", 
            "logic_puzzle_solved": "逻辑解谜者",
            "truth_seeker": "真相探求者",
            "efficiency_expert": "效率至上",
            "humanitarian": "人道主义抉择",
            "cogito_ergo_sum": "缸中之脑？"
        }
    
    def load_fonts(self):
        fonts = {}
        try:
            fonts['small'] = pygame.font.Font(Config.get_asset_path('fonts', 'pixel_font.ttf'), 16)
            fonts['medium'] = pygame.font.Font(Config.get_asset_path('fonts', 'pixel_font.ttf'), 24)
            fonts['large'] = pygame.font.Font(Config.get_asset_path('fonts', 'pixel_font.ttf'), 32)
        except:
            fonts['small'] = pygame.font.SysFont('courier', 16)
            fonts['medium'] = pygame.font.SysFont('courier', 24)
            fonts['large'] = pygame.font.SysFont('courier', 32)
        
        return fonts
    
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and self.active_dialog:
                self.hide_dialog()
            elif event.key == pygame.K_1 and self.show_choice:
                self.choice_callback(0)
                self.show_choice = False
            elif event.key == pygame.K_2 and self.show_choice:
                self.choice_callback(1)
                self.show_choice = False
    
    def update(self, dt):
        if self.active_hint:
            self.hint_timer += dt
            if self.hint_timer >= 3.0:
                self.active_hint = None
                self.hint_timer = 0
        
        if self.show_glitch:
            self.glitch_timer += dt
            if self.glitch_timer >= self.glitch_duration:
                self.show_glitch = False
        
        if self.system_message:
            self.system_message_timer += dt
            if self.system_message_timer >= self.system_message_duration:
                self.system_message = None
    
    def render(self, screen):
        if self.active_dialog:
            self.render_dialog(screen)
        
        if self.active_hint:
            self.render_hint(screen)
        
        if self.show_glitch:
            self.render_glitch_effect(screen)
        
        if self.system_message:
            self.render_system_message(screen)
        
        if self.show_choice:
            self.render_choice(screen)
        
        self.render_interaction_prompt(screen)
        
        if self.show_achievement:
            self.render_achievement(screen)
    
    def show_dialog(self, dialog_data):
        self.active_dialog = dialog_data
        if 'callback' in dialog_data:
            self.dialog_callback = dialog_data['callback']
    
    def hide_dialog(self):
        if self.dialog_callback:
            self.dialog_callback()
            self.dialog_callback = None
        self.active_dialog = None
    
    def show_hint(self, text, duration=3.0):
        self.active_hint = text
        self.hint_timer = 0
    
    def show_log(self, title, content):
        self.log_entries.append({'title': title, 'content': content})
        self.show_log = True
    
    def show_glitch_effect(self, duration=2.0):
        self.show_glitch = True
        self.glitch_timer = 0
        self.glitch_duration = duration
    
    def show_system_message(self, message, duration=1.5):
        self.system_message = message
        self.system_message_timer = 0
        self.system_message_duration = duration
    
    def show_moral_choice(self, title, question, options, callback):
        self.choice_title = title
        self.choice_question = question
        self.choice_options = options
        self.choice_callback = callback
        self.show_choice = True
    
    def show_system_reveal(self, messages, callback):
        self.system_reveal_messages = messages
        self.system_reveal_index = 0
        self.system_reveal_callback = callback
        self.show_next_system_reveal()
    
    def show_next_system_reveal(self):
        if self.system_reveal_index < len(self.system_reveal_messages):
            self.show_dialog({
                "speaker": "系统核心",
                "text": self.system_reveal_messages[self.system_reveal_index],
                "callback": self.show_next_system_reveal
            })
            self.system_reveal_index += 1
        else:
            self.system_reveal_callback()
    
    def show_brain_reveal(self, line1, line2, line3, callback):
        # 实现缸中之脑揭示场景
        self.brain_reveal_callback = callback
        self.showing_brain_reveal = True
        # 这里可以添加具体的渲染逻辑
    
    def show_final_reveal(self, line1, line2, callback):
        # 实现最终揭示场景
        self.final_reveal_callback = callback
        self.showing_final_reveal = True
    
    def show_final_choice(self, options, callback):
        self.final_choice_options = options
        self.final_choice_callback = callback
        self.showing_final_choice = True
    
    def show_ending_cutscene(self, messages, callback):
        self.ending_messages = messages
        self.ending_index = 0
        self.ending_callback = callback
        self.show_next_ending_message()
    
    def show_next_ending_message(self):
        if self.ending_index < len(self.ending_messages):
            self.show_dialog({
                "speaker": "系统",
                "text": self.ending_messages[self.ending_index],
                "callback": self.show_next_ending_message
            })
            self.ending_index += 1
        else:
            self.ending_callback()
    
    def show_achievement(self, achievement_id):
        if achievement_id in self.achievements:
            self.showing_achievement = self.achievements[achievement_id]
            self.achievement_timer = 0
    
    def render_dialog(self, screen):
        if not self.active_dialog:
            return
        
        dialog_width = Config.SCREEN_WIDTH - 100
        dialog_height = 150
        dialog_x = 50
        dialog_y = Config.SCREEN_HEIGHT - dialog_height - 50
        
        dialog_bg = pygame.Surface((dialog_width, dialog_height), pygame.SRCALPHA)
        dialog_bg.fill(Config.COLORS['ui_bg'])
        screen.blit(dialog_bg, (dialog_x, dialog_y))
        
        pygame.draw.rect(screen, Config.COLORS['highlight'], 
                        (dialog_x, dialog_y, dialog_width, dialog_height), 2)
        
        speaker_text = self.fonts['medium'].render(
            self.active_dialog.get('speaker', '未知'), 
            True, Config.COLORS['highlight']
        )
        screen.blit(speaker_text, (dialog_x + 10, dialog_y + 10))
        
        dialog_text = self.active_dialog['text']
        text_surface = self.fonts['small'].render(dialog_text, True, Config.COLORS['text'])
        screen.blit(text_surface, (dialog_x + 10, dialog_y + 50))
        
        continue_text = self.fonts['small'].render("按回车键继续...", True, Config.COLORS['text'])
        screen.blit(continue_text, (dialog_x + dialog_width - 120, dialog_y + dialog_height - 30))
    
    def render_hint(self, screen):
        if not self.active_hint:
            return
        
        hint_surface = self.fonts['small'].render(self.active_hint, True, Config.COLORS['text'])
        hint_rect = hint_surface.get_rect(center=(Config.SCREEN_WIDTH // 2, 50))
        
        bg_rect = hint_rect.inflate(20, 10)
        bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg_surface.fill(Config.COLORS['ui_bg'])
        screen.blit(bg_surface, bg_rect)
        
        screen.blit(hint_surface, hint_rect)
    
    def render_glitch_effect(self, screen):
        # 实现屏幕故障效果
        glitch_surface = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT), pygame.SRCALPHA)
        glitch_surface.fill((255, 0, 0, 30))  # 红色覆盖层
        
        # 添加随机线条和噪点
        for i in range(20):
            x = pygame.time.get_ticks() % Config.SCREEN_WIDTH
            pygame.draw.line(glitch_surface, (0, 255, 255, 100), 
                           (x, 0), (x, Config.SCREEN_HEIGHT), 2)
        
        screen.blit(glitch_surface, (0, 0))
    
    def render_system_message(self, screen):
        if not self.system_message:
            return
        
        msg_surface = self.fonts['small'].render(self.system_message, True, Config.COLORS['error'])
        msg_rect = msg_surface.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT // 2))
        screen.blit(msg_surface, msg_rect)
    
    def render_choice(self, screen):
        choice_width = 400
        choice_height = 200
        choice_x = (Config.SCREEN_WIDTH - choice_width) // 2
        choice_y = (Config.SCREEN_HEIGHT - choice_height) // 2
        
        choice_bg = pygame.Surface((choice_width, choice_height), pygame.SRCALPHA)
        choice_bg.fill(Config.COLORS['ui_bg'])
        screen.blit(choice_bg, (choice_x, choice_y))
        
        pygame.draw.rect(screen, Config.COLORS['highlight'], 
                        (choice_x, choice_y, choice_width, choice_height), 2)
        
        title_text = self.fonts['medium'].render(self.choice_title, True, Config.COLORS['highlight'])
        screen.blit(title_text, (choice_x + 20, choice_y + 20))
        
        question_text = self.fonts['small'].render(self.choice_question, True, Config.COLORS['text'])
        screen.blit(question_text, (choice_x + 20, choice_y + 60))
        
        for i, option in enumerate(self.choice_options):
            option_text = self.fonts['small'].render(f"{i+1}. {option}", True, Config.COLORS['text'])
            screen.blit(option_text, (choice_x + 40, choice_y + 100 + i * 30))
    
    def render_interaction_prompt(self, screen):
        if not self.game.scene_manager.current_scene or not self.game.scene_manager.current_scene.player:
            return
        
        player = self.game.scene_manager.current_scene.player
        near_interactable = False
        
        for entity in self.game.scene_manager.current_scene.entities:
            if entity.interactable and entity.is_near(player):
                near_interactable = True
                break
        
        if near_interactable:
            prompt_text = self.fonts['small'].render("按 F 键交互", True, Config.COLORS['highlight'])
            prompt_rect = prompt_text.get_rect(center=(Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT - 30))
            screen.blit(prompt_text, prompt_rect)
    
    def render_achievement(self, screen):
        if not hasattr(self, 'showing_achievement') or not self.showing_achievement:
            return
        
        self.achievement_timer += self.game.dt
        if self.achievement_timer >= 3.0:
            self.showing_achievement = None
            return
        
        achievement_text = self.fonts['medium'].render(
            f"成就解锁: {self.showing_achievement}", 
            True, Config.COLORS['highlight']
        )
        achievement_rect = achievement_text.get_rect(center=(Config.SCREEN_WIDTH // 2, 100))
        
        bg_rect = achievement_rect.inflate(40, 20)
        bg_surface = pygame.Surface(bg_rect.size, pygame.SRCALPHA)
        bg_surface.fill(Config.COLORS['ui_bg'])
        screen.blit(bg_surface, bg_rect)
        
        screen.blit(achievement_text, achievement_rect)
    
    def toggle_menu(self):
        self.show_menu = not self.show_menu
    
    def toggle_log(self):
        self.show_log = not self.show_log
