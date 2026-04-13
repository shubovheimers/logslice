"""Split a large log file into smaller chunks by line count or time window."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogLine


@dataclass
class SplitOptions:
    max_lines: Optional[int] = None          # split every N lines
    time_window: Optional[timedelta] = None  # split on time-boundary gaps
    output_dir: str = "."
    prefix: str = "part"
    suffix: str = ".log"
    pad_width: int = 4                        # zero-padding for part numbers

    def enabled(self) -> bool:
        return self.max_lines is not None or self.time_window is not None


def _part_path(opts: SplitOptions, index: int) -> Path:
    name = f"{opts.prefix}_{str(index).zfill(opts.pad_width)}{opts.suffix}"
    return Path(opts.output_dir) / name


def split_by_lines(
    lines: Iterable[LogLine],
    opts: SplitOptions,
) -> Iterator[List[LogLine]]:
    """Yield successive chunks of at most *max_lines* lines."""
    if opts.max_lines is None or opts.max_lines < 1:
        raise ValueError("max_lines must be a positive integer")
    chunk: List[LogLine] = []
    for line in lines:
        chunk.append(line)
        if len(chunk) >= opts.max_lines:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def split_by_time(
    lines: Iterable[LogLine],
    opts: SplitOptions,
) -> Iterator[List[LogLine]]:
    """Yield chunks separated by gaps larger than *time_window*."""
    if opts.time_window is None:
        raise ValueError("time_window must be set")
    chunk: List[LogLine] = []
    prev_ts = None
    for line in lines:
        if prev_ts is not None and line.timestamp is not None:
            if line.timestamp - prev_ts > opts.time_window:
                if chunk:
                    yield chunk
                    chunk = []
        chunk.append(line)
        if line.timestamp is not None:
            prev_ts = line.timestamp
    if chunk:
        yield chunk


def write_chunks(
    chunks: Iterable[List[LogLine]],
    opts: SplitOptions,
) -> List[Path]:
    """Write each chunk to a separate file; return list of created paths."""
    os.makedirs(opts.output_dir, exist_ok=True)
    paths: List[Path] = []
    for idx, chunk in enumerate(chunks):
        path = _part_path(opts, idx)
        with open(path, "w", encoding="utf-8") as fh:
            for line in chunk:
                fh.write(line.raw + "\n")
        paths.append(path)
    return paths
