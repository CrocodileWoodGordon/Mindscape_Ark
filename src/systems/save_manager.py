"""Save file I/O helpers."""

from pathlib import Path
import json
from datetime import datetime

SAVE_VERSION = 1


def ensure_save_dir(save_dir: Path) -> None:
    save_dir.mkdir(parents=True, exist_ok=True)


def list_save_files(save_dir: Path) -> list[Path]:
    if not save_dir.exists():
        return []
    return sorted(
        [p for p in save_dir.iterdir() if p.is_file() and p.suffix == ".json"],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )


def latest_save_file(save_dir: Path) -> Path | None:
    files = list_save_files(save_dir)
    return files[0] if files else None


def write_save(save_dir: Path, payload: dict) -> Path:
    ensure_save_dir(save_dir)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"save_{stamp}.json"
    path = save_dir / filename
    counter = 1
    while path.exists():
        path = save_dir / f"save_{stamp}_{counter}.json"
        counter += 1
    data = dict(payload)
    data["version"] = SAVE_VERSION
    data["saved_at"] = datetime.now().isoformat(timespec="seconds")
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=True, indent=2)
    return path


def load_save(path: Path) -> dict | None:
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    return data
