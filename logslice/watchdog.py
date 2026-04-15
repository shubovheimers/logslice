"""Live file watching: tail a log file and yield new lines as they appear."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Generator, Optional

from logslice.parser import LogLine, parse_line


@dataclass
class WatchOptions:
    enabled: bool = False
    poll_interval: float = 0.5   # seconds between polls
    max_idle: Optional[float] = None  # stop after N seconds with no new data
    follow_rotated: bool = False
    encoding: str = "utf-8"
    errors: str = "replace"

    def __post_init__(self) -> None:
        if self.poll_interval <= 0:
            raise ValueError("poll_interval must be positive")


def _open_text(path: Path, encoding: str, errors: str):
    """Open a plain text file for reading."""
    return open(path, "r", encoding=encoding, errors=errors)


def tail_file(
    path: Path,
    opts: WatchOptions,
) -> Generator[LogLine, None, None]:
    """Yield LogLine objects as new lines are appended to *path*.

    Starts from the current end-of-file so only *new* content is emitted.
    Stops when *max_idle* seconds elapse with no new data (or runs forever).
    """
    path = Path(path)
    idle_elapsed = 0.0

    with _open_text(path, opts.encoding, opts.errors) as fh:
        fh.seek(0, 2)  # jump to EOF
        while True:
            raw = fh.readline()
            if raw:
                idle_elapsed = 0.0
                line = parse_line(raw.rstrip("\n"))
                yield line
            else:
                time.sleep(opts.poll_interval)
                idle_elapsed += opts.poll_interval
                if opts.max_idle is not None and idle_elapsed >= opts.max_idle:
                    return
                # Re-open if file was rotated (inode changed / truncated)
                if opts.follow_rotated and _was_rotated(path, fh):
                    fh.close()
                    fh = _open_text(path, opts.encoding, opts.errors)


def _was_rotated(path: Path, fh) -> bool:
    """Return True if the file on disk is a different inode or smaller."""
    try:
        disk_stat = path.stat()
        fd_stat = Path(f"/proc/self/fd/{fh.fileno()}").stat()
        return disk_stat.st_ino != fd_stat.st_ino
    except Exception:
        # Fallback: check if current position > file size (truncated)
        try:
            pos = fh.tell()
            size = path.stat().st_size
            return pos > size
        except Exception:
            return False
