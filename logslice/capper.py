"""capper.py – cap (truncate) a stream to at most N matching lines per level."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class CapOptions:
    """Options controlling per-level line capping."""

    max_per_level: int = 0          # 0 = disabled
    max_total: int = 0              # 0 = no total cap
    fallback_level: str = "UNKNOWN"

    def __post_init__(self) -> None:
        if self.max_per_level < 0:
            raise ValueError("max_per_level must be >= 0")
        if self.max_total < 0:
            raise ValueError("max_total must be >= 0")

    @property
    def enabled(self) -> bool:
        return self.max_per_level > 0 or self.max_total > 0


@dataclass
class _State:
    counts: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    total: int = 0


def cap_lines(
    lines: Iterable[LogLine],
    opts: Optional[CapOptions] = None,
) -> Iterator[LogLine]:
    """Yield lines, dropping any that exceed per-level or total caps."""
    if opts is None or not opts.enabled:
        yield from lines
        return

    state = _State()

    for line in lines:
        level = (line.level or opts.fallback_level).upper()

        if opts.max_total > 0 and state.total >= opts.max_total:
            break

        if opts.max_per_level > 0 and state.counts[level] >= opts.max_per_level:
            continue

        state.counts[level] += 1
        state.total += 1
        yield line
