"""Entrypoint for MindscapeArk."""

from __future__ import annotations

from pathlib import Path
import sys


def _ensure_project_root_on_path() -> None:
    """Allow running as a script while still resolving package imports."""
    if __package__:
        return
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))


_ensure_project_root_on_path()

from src.core.game import Game


def main() -> None:
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
