"""Map loading helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List


@dataclass
class MapData:
    collision_grid: List[List[int]]
    cell_size: int
    grid_size: tuple[int, int]
    tile_size: int
    size_pixels: tuple[int, int]
    spawn_player: tuple[int, int]
    triggers: list[Any]
    metadata: dict[str, Any]
    image_path: Path | None


def load_map(path: str | Path, *, base_dir: Path | None = None) -> MapData:
    p = Path(path)
    if not p.is_absolute():
        base = base_dir or Path(__file__).resolve().parents[2]
        p = base / p
    with p.open("r", encoding="utf-8") as f:
        data = json.load(f)

    grid = data["collision_grid"]
    cell_size = int(data.get("cell_size", data.get("tile_size", 64)))
    width = len(grid[0]) if grid else 0
    height = len(grid) if grid else 0

    size_pixels = data.get("size_pixels") or {"width": width * cell_size, "height": height * cell_size}
    spawn = data.get("spawn", {}).get("player", [0, 0])
    triggers = data.get("triggers", [])
    metadata = data.get("metadata", {})
    image_path = data.get("image")
    image_path = Path(image_path) if image_path else None
    if image_path and not image_path.is_absolute():
        base = base_dir or Path(__file__).resolve().parents[2]
        image_path = base / image_path

    return MapData(
        collision_grid=grid,
        cell_size=cell_size,
        grid_size=(width, height),
        tile_size=int(data.get("tile_size", 64)),
        size_pixels=(size_pixels.get("width", 0), size_pixels.get("height", 0)),
        spawn_player=(int(spawn[0]), int(spawn[1])),
        triggers=triggers,
        metadata=metadata,
        image_path=image_path,
    )
