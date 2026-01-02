"""A* pathfinding on grid."""

from __future__ import annotations

import heapq
import math
from collections import deque
from typing import Iterable, List, Tuple, Set, Optional, Dict, Any

Grid = List[List[int]]
Node = Tuple[int, int]
NavCache = Dict[str, Any]

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


def _neighbors_cached(
    x: int,
    y: int,
    walkable: list[list[bool]],
) -> Iterable[tuple[Node, int]]:
    max_y = len(walkable)
    max_x = len(walkable[0]) if max_y else 0
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
        if not walkable[ny][nx]:
            continue
        if dx != 0 and dy != 0:
            # block diagonal corner cutting if either adjacent orthogonal cell is blocked
            if not (walkable[y][nx] and walkable[ny][x]):
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


def build_nav_cache(
    grid: Grid,
    passable: Set[int],
    *,
    cell_size: int = 1,
    actor_size: tuple[int, int] = (1, 1),
) -> NavCache:
    if not grid:
        return {"walkable": [], "regions": []}
    max_y = len(grid)
    max_x = len(grid[0]) if max_y else 0
    radius_x, radius_y = _clearance_radius(actor_size, cell_size)
    walkable: list[list[bool]] = [[False] * max_x for _ in range(max_y)]
    for y in range(max_y):
        row = grid[y]
        for x in range(max_x):
            if not is_walkable(row[x], passable):
                continue
            if has_clearance(x, y, grid, passable, radius_x=radius_x, radius_y=radius_y):
                walkable[y][x] = True
    regions: list[list[int]] = [[-1] * max_x for _ in range(max_y)]
    region_id = 0
    for y in range(max_y):
        for x in range(max_x):
            if not walkable[y][x] or regions[y][x] != -1:
                continue
            queue = deque([(x, y)])
            regions[y][x] = region_id
            while queue:
                cx, cy = queue.popleft()
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < max_x and 0 <= ny < max_y:
                        if walkable[ny][nx] and regions[ny][nx] == -1:
                            regions[ny][nx] = region_id
                            queue.append((nx, ny))
            region_id += 1
    return {
        "walkable": walkable,
        "regions": regions,
        "cell_size": cell_size,
        "actor_size": actor_size,
    }


def astar(
    grid: Grid,
    start: Node,
    goal: Node,
    passable: Set[int],
    *,
    cell_size: int = 1,
    actor_size: tuple[int, int] = (1, 1),
    nav_cache: Optional[NavCache] = None,
) -> List[Node]:
    if not grid:
        return []
    if nav_cache:
        if nav_cache.get("cell_size") != cell_size or nav_cache.get("actor_size") != actor_size:
            nav_cache = None
    max_y = len(grid)
    max_x = len(grid[0]) if max_y else 0
    if not (0 <= start[0] < max_x and 0 <= start[1] < max_y):
        return []
    if not (0 <= goal[0] < max_x and 0 <= goal[1] < max_y):
        return []
    walkable: list[list[bool]] | None = None
    regions: list[list[int]] | None = None
    if nav_cache:
        walkable = nav_cache.get("walkable")
        regions = nav_cache.get("regions")
    if walkable:
        if not walkable[start[1]][start[0]]:
            return []
        if not walkable[goal[1]][goal[0]]:
            return []
        if regions and regions[start[1]][start[0]] != regions[goal[1]][goal[0]]:
            return []
    else:
        if not is_walkable(grid[start[1]][start[0]], passable):
            return []
        if not is_walkable(grid[goal[1]][goal[0]], passable):
            return []

    # compute clearance in cells based on actor footprint
    radius_x, radius_y = _clearance_radius(actor_size, cell_size)

    if not walkable:
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
        if walkable:
            neighbor_iter = _neighbors_cached(current[0], current[1], walkable)
        else:
            neighbor_iter = neighbors(*current, grid, passable, radius_x=radius_x, radius_y=radius_y)
        for nxt, step_cost in neighbor_iter:
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
    nav_cache: Optional[NavCache] = None,
) -> Node | None:
    if not grid:
        return None
    if nav_cache:
        if nav_cache.get("cell_size") != cell_size or nav_cache.get("actor_size") != actor_size:
            nav_cache = None
    max_y = len(grid)
    max_x = len(grid[0]) if max_y else 0
    sx, sy = start
    if not (0 <= sx < max_x and 0 <= sy < max_y):
        return None
    walkable: list[list[bool]] | None = None
    if nav_cache:
        walkable = nav_cache.get("walkable")
    radius_x, radius_y = _clearance_radius(actor_size, cell_size)
    if walkable:
        if not walkable[sy][sx]:
            return None
    else:
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
        if walkable:
            neighbor_iter = _neighbors_cached(cx, cy, walkable)
        else:
            neighbor_iter = neighbors(cx, cy, grid, passable, radius_x=radius_x, radius_y=radius_y)
        for (nx, ny), _ in neighbor_iter:
            if (nx, ny) in visited:
                continue
            visited.add((nx, ny))
            q.append(((nx, ny), depth + 1))

    return best
