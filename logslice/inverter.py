"""Inverter: negate filter matches — keep lines that do NOT match a pattern."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogLine


@dataclass
class InvertOptions:
    patterns: List[str] = field(default_factory=list)
    case_sensitive: bool = False
    invert_level: Optional[str] = None  # exclude lines matching this level

    def __post_init__(self) -> None:
        if self.invert_level is not None:
            self.invert_level = self.invert_level.upper()

    @property
    def enabled(self) -> bool:
        return bool(self.patterns) or self.invert_level is not None

    def _compile(self) -> List[re.Pattern]:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        return [re.compile(p, flags) for p in self.patterns]


def invert_lines(
    lines: Iterable[LogLine],
    opts: Optional[InvertOptions],
) -> Iterator[LogLine]:
    """Yield lines that do NOT match any of the invert patterns or level."""
    if opts is None or not opts.enabled:
        yield from lines
        return

    compiled = opts._compile()

    for line in lines:
        # Check level exclusion
        if opts.invert_level and line.level and line.level.upper() == opts.invert_level:
            continue

        # Check pattern exclusion — skip line if ANY pattern matches
        text = line.raw
        if any(rx.search(text) for rx in compiled):
            continue

        yield line
