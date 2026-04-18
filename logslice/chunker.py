"""Split a log stream into fixed-size or time-based chunks."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Iterator, List, Optional

from logslice.parser import LogLine


@dataclass
class ChunkOptions:
    max_lines: int = 0
    time_window_seconds: float = 0.0
    include_partial: bool = True

    def __post_init__(self) -> None:
        if self.max_lines < 0:
            raise ValueError("max_lines must be >= 0")
        if self.time_window_seconds < 0:
            raise ValueError("time_window_seconds must be >= 0")

    @property
    def enabled(self) -> bool:
        return self.max_lines > 0 or self.time_window_seconds > 0


@dataclass
class Chunk:
    lines: List[LogLine] = field(default_factory=list)
    index: int = 0

    def __len__(self) -> int:
        return len(self.lines)


def chunk_lines(
    lines: Iterator[LogLine],
    opts: ChunkOptions,
) -> Iterator[Chunk]:
    """Yield Chunk objects according to the given ChunkOptions."""
    if not opts.enabled:
        yield Chunk(lines=list(lines), index=0)
        return

    current: List[LogLine] = []
    chunk_index = 0
    window = timedelta(seconds=opts.time_window_seconds) if opts.time_window_seconds > 0 else None
    window_start = None

    for line in lines:
        if window is not None and line.timestamp is not None:
            if window_start is None:
                window_start = line.timestamp
            elif line.timestamp - window_start >= window:
                if current:
                    yield Chunk(lines=current, index=chunk_index)
                    chunk_index += 1
                current = []
                window_start = line.timestamp

        current.append(line)

        if opts.max_lines > 0 and len(current) >= opts.max_lines:
            yield Chunk(lines=current, index=chunk_index)
            chunk_index += 1
            current = []
            window_start = None

    if current and opts.include_partial:
        yield Chunk(lines=current, index=chunk_index)
