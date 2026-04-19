"""Drop lines matching patterns or levels before further processing."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogLine


@dataclass
class DropOptions:
    patterns: List[str] = field(default_factory=list)
    levels: List[str] = field(default_factory=list)
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._compiled = [re.compile(p, flags) for p in self.patterns]
        self._levels_upper = {lv.upper() for lv in self.levels}

    def is_active(self) -> bool:
        return bool(self.patterns or self.levels)

    def should_drop(self, line: LogLine) -> bool:
        if self._levels_upper and line.level and line.level.upper() in self._levels_upper:
            return True
        for rx in self._compiled:
            if rx.search(line.raw):
                return True
        return False


def drop_lines(
    lines: Iterable[LogLine],
    opts: Optional[DropOptions],
) -> Iterator[LogLine]:
    """Yield lines that do NOT match any drop rule."""
    if opts is None or not opts.is_active():
        yield from lines
        return
    for line in lines:
        if not opts.should_drop(line):
            yield line
