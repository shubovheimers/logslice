"""fence.py – extract log lines between two boundary patterns."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator

from logslice.parser import LogLine


@dataclass
class FenceOptions:
    start_pattern: str = ""
    end_pattern: str = ""
    inclusive: bool = True          # include the boundary lines themselves
    repeat: bool = False            # capture multiple fenced regions
    ignore_case: bool = True

    def __post_init__(self) -> None:
        if not self.start_pattern:
            raise ValueError("start_pattern is required")
        if not self.end_pattern:
            raise ValueError("end_pattern is required")

    def enabled(self) -> bool:
        return bool(self.start_pattern and self.end_pattern)


def _compile(pattern: str, ignore_case: bool) -> re.Pattern:
    flags = re.IGNORECASE if ignore_case else 0
    return re.compile(pattern, flags)


def fence_lines(
    lines: Iterable[LogLine],
    opts: FenceOptions,
) -> Iterator[LogLine]:
    """Yield lines that fall inside fenced regions."""
    if not opts.enabled():
        yield from lines
        return

    start_re = _compile(opts.start_pattern, opts.ignore_case)
    end_re = _compile(opts.end_pattern, opts.ignore_case)

    inside = False

    for line in lines:
        text = line.raw

        if not inside:
            if start_re.search(text):
                inside = True
                if opts.inclusive:
                    yield line
            continue

        # inside a region
        if end_re.search(text):
            if opts.inclusive:
                yield line
            inside = False
            if not opts.repeat:
                return
        else:
            yield line
