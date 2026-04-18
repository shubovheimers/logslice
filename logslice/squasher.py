"""Squasher: merge consecutive log lines that share the same level into a single entry."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class SquashOptions:
    enabled: bool = False
    by_level: bool = True
    separator: str = " | "
    max_group: int = 50

    def __post_init__(self) -> None:
        if self.max_group < 1:
            raise ValueError("max_group must be >= 1")

    def is_active(self) -> bool:
        return self.enabled and self.by_level


def squash_lines(
    lines: Iterable[LogLine],
    opts: Optional[SquashOptions] = None,
) -> Iterator[LogLine]:
    """Yield lines, merging consecutive same-level lines into one."""
    if opts is None or not opts.is_active():
        yield from lines
        return

    group: list[LogLine] = []

    def _flush(g: list[LogLine]) -> LogLine:
        if len(g) == 1:
            return g[0]
        merged_text = opts.separator.join(ln.raw_text for ln in g)
        base = g[0]
        return LogLine(
            raw_text=merged_text,
            timestamp=base.timestamp,
            level=base.level,
            message=opts.separator.join(ln.message or ln.raw_text for ln in g),
            extra=base.extra,
        )

    for line in lines:
        if not group:
            group.append(line)
            continue
        same_level = line.level == group[0].level
        if same_level and len(group) < opts.max_group:
            group.append(line)
        else:
            yield _flush(group)
            group = [line]

    if group:
        yield _flush(group)
