"""Collision detection/resolution with explicit cell size."""

from typing import Iterable, Tuple
import pygame

Vec2 = Tuple[int, int]


def rect_collides_with_grid(rect: pygame.Rect, collision_grid: Iterable[Iterable[int]], cell_size: int) -> bool:
    rows = list(collision_grid)
    max_y = len(rows)
    max_x = len(rows[0]) if max_y else 0
    left = max(rect.left // cell_size, 0)
    right = min((rect.right - 1) // cell_size, max_x - 1)
    top = max(rect.top // cell_size, 0)
    bottom = min((rect.bottom - 1) // cell_size, max_y - 1)
    for ty in range(top, bottom + 1):
        row = rows[ty]
        for tx in range(left, right + 1):
            if row[tx] == 1:
                return True
    return False


def move_with_collision(rect: pygame.Rect, velocity: Vec2, collision_grid: Iterable[Iterable[int]], *, cell_size: int, substep: int) -> pygame.Rect:
    vx, vy = velocity
    steps = max(abs(vx), abs(vy)) // max(1, substep)
    steps = max(1, steps)
    dx = vx / steps
    dy = vy / steps
    new_rect = rect.copy()
    for _ in range(int(steps)):
        new_rect.x += int(dx)
        if rect_collides_with_grid(new_rect, collision_grid, cell_size):
            new_rect.x -= int(dx)
            vx = 0
        new_rect.y += int(dy)
        if rect_collides_with_grid(new_rect, collision_grid, cell_size):
            new_rect.y -= int(dy)
            vy = 0
    return new_rect
