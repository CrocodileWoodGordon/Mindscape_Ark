import pygame
from config import Config

class AudioManager:
    def __init__(self, game):
        self.game = game
        self.sounds = {}
        self.music = {}
        self.current_music = None
        
        self.load_audio()
    
    def load_audio(self):
        try:
            # 加载音效
            sound_files = {
                'ui_click': 'ui_click.wav',
                'attack': 'attack.wav',
                'enemy_hit': 'enemy_hit.wav',
                'glitch': 'glitch.wav'
            }
            
            for name, file in sound_files.items():
                self.sounds[name] = pygame.mixer.Sound(Config.get_asset_path('audio', file))
            
            # 加载音乐
            music_files = {
                'guide_theme': 'guide_theme.ogg',
                'truth_theme': 'truth_theme.ogg',
                'ending_theme': 'ending_theme.ogg'
            }
            
            for name, file in music_files.items():
                self.music[name] = Config.get_asset_path('audio', file)
                
        except pygame.error as e:
            print(f"音频加载失败: {e}")
    
    def play_sound(self, sound_name):
        if sound_name in self.sounds:
            self.sounds[sound_name].play()
    
    def play_music(self, music_name, loops=-1):
        if music_name in self.music and self.current_music != music_name:
            try:
                pygame.mixer.music.load(self.music[music_name])
                pygame.mixer.music.play(loops)
                self.current_music = music_name
            except pygame.error as e:
                print(f"音乐播放失败: {e}")
    
    def stop_music(self):
        pygame.mixer.music.stop()
        self.current_music = None
    
    def set_volume(self, volume):
        pygame.mixer.music.set_volume(volume)
        for sound in self.sounds.values():
            sound.set_volume(volume)
