"""A* pathfinding on grid."""

from __future__ import annotations

import heapq
import math
from collections import deque
from typing import Iterable, List, Tuple, Set

Grid = List[List[int]]
Node = Tuple[int, int]

ORTH_COST = 10
DIAG_COST = 14


def is_walkable(val: int, passable: Set[int]) -> bool:
    return val in passable


def has_clearance(x: int, y: int, grid: Grid, passable: Set[int], *, radius_x: int, radius_y: int) -> bool:
    max_y = len(grid)
    max_x = len(grid[0]) if max_y else 0
    if not (0 <= x < max_x and 0 <= y < max_y):
        return False
    for yy in range(y - radius_y, y + radius_y + 1):
        if yy < 0 or yy >= max_y:
            return False
        row = grid[yy]
        for xx in range(x - radius_x, x + radius_x + 1):
            if xx < 0 or xx >= max_x:
                return False
            if not is_walkable(row[xx], passable):
                return False
    return True


def neighbors(
    x: int,
    y: int,
    grid: Grid,
    passable: Set[int],
    *,
    radius_x: int,
    radius_y: int,
) -> Iterable[tuple[Node, int]]:
    max_y = len(grid)
    max_x = len(grid[0]) if max_y else 0
    directions = (
        (1, 0, ORTH_COST),
        (-1, 0, ORTH_COST),
        (0, 1, ORTH_COST),
        (0, -1, ORTH_COST),
        (1, 1, DIAG_COST),
        (-1, 1, DIAG_COST),
        (1, -1, DIAG_COST),
        (-1, -1, DIAG_COST),
    )
    for dx, dy, cost in directions:
        nx, ny = x + dx, y + dy
        if not (0 <= nx < max_x and 0 <= ny < max_y):
            continue
        if not is_walkable(grid[ny][nx], passable):
            continue
        if not has_clearance(nx, ny, grid, passable, radius_x=radius_x, radius_y=radius_y):
            continue
        if dx != 0 and dy != 0:
            # block diagonal corner cutting if either adjacent orthogonal cell is solid
            adj1 = grid[y][nx]
            adj2 = grid[ny][x]
            if not (is_walkable(adj1, passable) and is_walkable(adj2, passable)):
                continue
        yield (nx, ny), cost


def heuristic(a: Node, b: Node) -> int:
    dx = abs(a[0] - b[0])
    dy = abs(a[1] - b[1])
    # Octile distance scaled to match ORTH_COST/DIAG_COST units
    return DIAG_COST * min(dx, dy) + ORTH_COST * (max(dx, dy) - min(dx, dy))


def _clearance_radius(actor_size: tuple[int, int], cell_size: int) -> tuple[int, int]:
    actor_w, actor_h = actor_size
    cells_x = max(1, math.ceil(actor_w / cell_size))
    cells_y = max(1, math.ceil(actor_h / cell_size))
    radius_x = (cells_x - 1) // 2
    radius_y = (cells_y - 1) // 2
    return radius_x, radius_y


def astar(
    grid: Grid,
    start: Node,
    goal: Node,
    passable: Set[int],
    *,
    cell_size: int = 1,
    actor_size: tuple[int, int] = (1, 1),
) -> List[Node]:
    if not grid:
        return []
    if not is_walkable(grid[start[1]][start[0]], passable):
        return []
    if not is_walkable(grid[goal[1]][goal[0]], passable):
        return []

    # compute clearance in cells based on actor footprint
    radius_x, radius_y = _clearance_radius(actor_size, cell_size)

    if not has_clearance(start[0], start[1], grid, passable, radius_x=radius_x, radius_y=radius_y):
        return []
    if not has_clearance(goal[0], goal[1], grid, passable, radius_x=radius_x, radius_y=radius_y):
        return []

    open_heap: List[Tuple[int, Node]] = []
    heapq.heappush(open_heap, (0, start))
    came_from: dict[Node, Node] = {}
    g_score: dict[Node, int] = {start: 0}

    while open_heap:
        _, current = heapq.heappop(open_heap)
        if current == goal:
            # reconstruct
            path: List[Node] = [current]
            while current in came_from:
                current = came_from[current]
                path.append(current)
            path.reverse()
            return path
        for nxt, step_cost in neighbors(*current, grid, passable, radius_x=radius_x, radius_y=radius_y):
            tentative = g_score[current] + step_cost
            if tentative < g_score.get(nxt, 1_000_000_000):
                came_from[nxt] = current
                g_score[nxt] = tentative
                f = tentative + heuristic(nxt, goal)
                heapq.heappush(open_heap, (f, nxt))
    return []


def nearest_reachable(
    grid: Grid,
    start: Node,
    desired: Node,
    passable: Set[int],
    *,
    cell_size: int = 1,
    actor_size: tuple[int, int] = (1, 1),
    max_distance_px: int = 10,
) -> Node | None:
    if not grid:
        return None
    max_y = len(grid)
    max_x = len(grid[0]) if max_y else 0
    sx, sy = start
    if not (0 <= sx < max_x and 0 <= sy < max_y):
        return None

    radius_x, radius_y = _clearance_radius(actor_size, cell_size)
    if not has_clearance(sx, sy, grid, passable, radius_x=radius_x, radius_y=radius_y):
        return None

    visited: set[Node] = set()
    q = deque([(start, 0)])
    visited.add(start)
    best: Node | None = None
    best_dist = 1_000_000
    max_steps = max(0, max_distance_px // cell_size)

    while q:
        (cx, cy), depth = q.popleft()
        if depth > max_steps:
            continue
        dist = abs(cx - desired[0]) + abs(cy - desired[1])
        if dist < best_dist:
            best = (cx, cy)
            best_dist = dist
        if depth == max_steps:
            continue
        for (nx, ny), _ in neighbors(cx, cy, grid, passable, radius_x=radius_x, radius_y=radius_y):
            if (nx, ny) in visited:
                continue
            visited.add((nx, ny))
            q.append(((nx, ny), depth + 1))

    return best
