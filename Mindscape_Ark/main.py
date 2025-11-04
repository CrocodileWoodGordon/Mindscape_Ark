import pygame
import sys
from config import Config
from engine.game import Game

def main():
    pygame.init()
    pygame.mixer.init()
    
    screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
    pygame.display.set_caption("MINDSCAPE: ARK")
    
    game = Game(screen)
    
    try:
        game.run()
    except Exception as e:
        print(f"游戏运行错误: {e}")
        if Config.DEBUG_MODE:
            import traceback
            traceback.print_exc()
    finally:
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    main()