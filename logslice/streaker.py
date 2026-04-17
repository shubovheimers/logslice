"""Streak detection: find consecutive runs of matching log lines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List
import re

from logslice.parser import LogLine


@dataclass
class StreakOptions:
    pattern: str = ""
    min_length: int = 2
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        if self.min_length < 1:
            raise ValueError("min_length must be >= 1")

    def enabled(self) -> bool:
        return bool(self.pattern)


@dataclass
class Streak:
    lines: List[LogLine] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.lines)


def _compile(opts: StreakOptions) -> re.Pattern:
    flags = 0 if opts.case_sensitive else re.IGNORECASE
    return re.compile(opts.pattern, flags)


def find_streaks(lines: Iterable[LogLine], opts: StreakOptions) -> Iterator[Streak]:
    """Yield Streak objects for consecutive runs of lines matching *pattern*."""
    if not opts.enabled():
        return

    rx = _compile(opts)
    current: List[LogLine] = []

    for line in lines:
        if rx.search(line.raw):
            current.append(line)
        else:
            if len(current) >= opts.min_length:
                yield Streak(lines=list(current))
            current = []

    if len(current) >= opts.min_length:
        yield Streak(lines=list(current))


def iter_streak_lines(lines: Iterable[LogLine], opts: StreakOptions) -> Iterator[LogLine]:
    """Yield only lines that belong to a qualifying streak."""
    for streak in find_streaks(lines, opts):
        yield from streak.lines
