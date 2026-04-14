"""rotator.py — detect and handle rotated log file sequences."""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, List, Optional


@dataclass
class RotateOptions:
    """Options controlling rotated-log discovery."""
    follow_rotated: bool = False
    max_rotated: int = 10
    rotated_suffix_pattern: str = r"(\.\d+|\.\d{4}-\d{2}-\d{2})(\.gz)?$"

    def enabled(self) -> bool:
        return self.follow_rotated


def _rotation_sort_key(path: Path) -> tuple:
    """Sort rotated files so that .1 < .2, older dates first."""
    name = path.name
    # Extract numeric suffix if present
    m = re.search(r"\.(\d+)(\.gz)?$", name)
    if m:
        return (1, int(m.group(1)))
    # Extract date suffix
    m = re.search(r"\.(\d{4}-\d{2}-\d{2})(\.gz)?$", name)
    if m:
        return (0, m.group(1))
    return (2, name)


def find_rotated_files(
    base_path: Path,
    opts: RotateOptions,
) -> List[Path]:
    """Return rotated companions of *base_path*, oldest first.

    For a base path like ``/var/log/app.log`` this looks for siblings
    matching ``app.log.1``, ``app.log.2``, ``app.log.2023-01-01``, etc.
    """
    if not opts.enabled():
        return []

    directory = base_path.parent
    base_name = base_path.name
    pattern = re.compile(
        re.escape(base_name) + opts.rotated_suffix_pattern
    )

    candidates: List[Path] = []
    try:
        for entry in directory.iterdir():
            if pattern.search(entry.name):
                candidates.append(entry)
    except OSError:
        return []

    candidates.sort(key=_rotation_sort_key, reverse=True)  # oldest (highest .N) first
    return candidates[: opts.max_rotated]


def iter_rotated_paths(
    base_path: Path,
    opts: RotateOptions,
    include_base: bool = True,
) -> Iterator[Path]:
    """Yield rotated files (oldest first) then optionally the base file."""
    rotated = find_rotated_files(base_path, opts)
    yield from rotated
    if include_base:
        yield base_path
