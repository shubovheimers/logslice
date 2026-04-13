"""Bookmark support: save and restore named positions (byte offsets) in log files."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


DEFAULT_BOOKMARK_DIR = Path.home() / ".logslice" / "bookmarks"


@dataclass
class Bookmark:
    name: str
    filepath: str
    offset: int
    line_number: int
    timestamp: Optional[str] = None

    def as_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "Bookmark":
        return Bookmark(
            name=data["name"],
            filepath=data["filepath"],
            offset=data["offset"],
            line_number=data["line_number"],
            timestamp=data.get("timestamp"),
        )


def _bookmark_path(name: str, bookmark_dir: Path) -> Path:
    safe_name = name.replace(os.sep, "_").replace(" ", "_")
    return bookmark_dir / f"{safe_name}.json"


def save_bookmark(bookmark: Bookmark, bookmark_dir: Path = DEFAULT_BOOKMARK_DIR) -> Path:
    """Persist a bookmark to disk. Returns the path written."""
    bookmark_dir.mkdir(parents=True, exist_ok=True)
    path = _bookmark_path(bookmark.name, bookmark_dir)
    path.write_text(json.dumps(bookmark.as_dict(), indent=2))
    return path


def load_bookmark(name: str, bookmark_dir: Path = DEFAULT_BOOKMARK_DIR) -> Optional[Bookmark]:
    """Load a bookmark by name. Returns None if not found."""
    path = _bookmark_path(name, bookmark_dir)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return Bookmark.from_dict(data)


def delete_bookmark(name: str, bookmark_dir: Path = DEFAULT_BOOKMARK_DIR) -> bool:
    """Remove a bookmark by name. Returns True if deleted, False if not found."""
    path = _bookmark_path(name, bookmark_dir)
    if path.exists():
        path.unlink()
        return True
    return False


def list_bookmarks(bookmark_dir: Path = DEFAULT_BOOKMARK_DIR) -> list[Bookmark]:
    """Return all saved bookmarks sorted by name."""
    if not bookmark_dir.exists():
        return []
    bookmarks = []
    for p in sorted(bookmark_dir.glob("*.json")):
        try:
            data = json.loads(p.read_text())
            bookmarks.append(Bookmark.from_dict(data))
        except (json.JSONDecodeError, KeyError):
            continue
    return bookmarks
