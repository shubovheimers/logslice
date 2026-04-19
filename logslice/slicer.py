"""Line-range slicer: extract a contiguous slice of log lines by index."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator

from logslice.parser import LogLine


@dataclass
class SliceOptions:
    start_line: int = 0   # 0-based, inclusive
    end_line: int | None = None  # 0-based, exclusive; None = until EOF
    step: int = 1

    def __post_init__(self) -> None:
        if self.start_line < 0:
            raise ValueError("start_line must be >= 0")
        if self.end_line is not None and self.end_line < self.start_line:
            raise ValueError("end_line must be >= start_line")
        if self.step < 1:
            raise ValueError("step must be >= 1")

    @property
    def enabled(self) -> bool:
        return self.end_line is not None or self.start_line > 0 or self.step > 1


def slice_lines(
    lines: Iterable[LogLine],
    opts: SliceOptions | None = None,
) -> Iterator[LogLine]:
    """Yield lines within [start_line, end_line) with optional step."""
    if opts is None or not opts.enabled:
        yield from lines
        return

    for idx, line in enumerate(lines):
        if opts.end_line is not None and idx >= opts.end_line:
            break
        if idx < opts.start_line:
            continue
        if (idx - opts.start_line) % opts.step == 0:
            yield line
