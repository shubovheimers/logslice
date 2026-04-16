"""Interactive line-range scroller: yield a sliding window of LogLines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogLine


@dataclass
class ScrollOptions:
    """Configuration for the scroller."""

    window_size: int = 50
    step: int = 1
    start_line: int = 0  # 0-based index into the source
    max_windows: Optional[int] = None  # None → no limit

    def __post_init__(self) -> None:
        if self.window_size < 1:
            raise ValueError("window_size must be >= 1")
        if self.step < 1:
            raise ValueError("step must be >= 1")
        if self.start_line < 0:
            raise ValueError("start_line must be >= 0")
        if self.max_windows is not None and self.max_windows < 1:
            raise ValueError("max_windows must be >= 1 when set")

    @property
    def enabled(self) -> bool:
        return self.window_size > 0


def _buffer_lines(source: Iterable[LogLine], skip: int) -> List[LogLine]:
    """Materialise source into a list, skipping the first *skip* entries."""
    lines: List[LogLine] = []
    for i, line in enumerate(source):
        if i >= skip:
            lines.append(line)
    return lines


def scroll_lines(
    source: Iterable[LogLine],
    opts: Optional[ScrollOptions] = None,
) -> Iterator[List[LogLine]]:
    """Yield successive windows of *window_size* lines, advancing by *step*.

    Each yielded value is a list of :class:`LogLine` objects representing one
    screen-worth of content.  The iterator stops when the window would start
    beyond the available lines, or when *max_windows* has been reached.
    """
    if opts is None:
        opts = ScrollOptions()

    lines = _buffer_lines(source, opts.start_line)
    total = len(lines)
    windows_emitted = 0
    pos = 0

    while pos < total:
        window = lines[pos : pos + opts.window_size]
        yield window
        windows_emitted += 1
        if opts.max_windows is not None and windows_emitted >= opts.max_windows:
            break
        pos += opts.step
