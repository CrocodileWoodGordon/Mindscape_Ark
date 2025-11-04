import pygame
import os
class Config:
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    TILE_SIZE = 32
    FPS = 60
    COLORS = {
        'background': (26, 43, 60),
        'text': (255, 255, 255),
        'highlight': (0, 255, 255),
        'error': (255, 0, 0),
        'ui_bg': (0, 0, 0, 180),
        'debug': (255, 0, 255)
    }
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSETS_PATH = os.path.join(BASE_DIR, 'assets')
    DEBUG_MODE = True
    @classmethod
    def get_asset_path(cls, *paths):
        return os.path.join(cls.ASSETS_PATH, *paths)