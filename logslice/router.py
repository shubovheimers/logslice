"""Route log lines to different outputs based on rules."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, Iterator, List, Optional, Tuple

from logslice.parser import LogLine


@dataclass
class RouteRule:
    """A single routing rule matching a pattern or level to a named channel."""
    channel: str
    pattern: Optional[str] = None
    level: Optional[str] = None
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        if not self.channel:
            raise ValueError("channel must not be empty")
        if self.pattern is None and self.level is None:
            raise ValueError("at least one of pattern or level must be set")
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._rx = re.compile(self.pattern, flags) if self.pattern else None

    def matches(self, line: LogLine) -> bool:
        if self.level is not None:
            if (line.level or "").upper() != self.level.upper():
                return False
        if self._rx is not None:
            if not self._rx.search(line.raw):
                return False
        return True


@dataclass
class RouterOptions:
    rules: List[RouteRule] = field(default_factory=list)
    default_channel: str = "default"
    stop_on_first_match: bool = True

    def enabled(self) -> bool:
        return bool(self.rules)


def route_lines(
    lines: Iterable[LogLine],
    opts: RouterOptions,
) -> Iterator[Tuple[str, LogLine]]:
    """Yield (channel, line) pairs according to routing rules."""
    for line in lines:
        matched = False
        for rule in opts.rules:
            if rule.matches(line):
                yield rule.channel, line
                matched = True
                if opts.stop_on_first_match:
                    break
        if not matched:
            yield opts.default_channel, line


def collect_routed(
    lines: Iterable[LogLine],
    opts: RouterOptions,
) -> Dict[str, List[LogLine]]:
    """Collect routed lines into a dict keyed by channel name."""
    result: Dict[str, List[LogLine]] = {}
    for channel, line in route_lines(lines, opts):
        result.setdefault(channel, []).append(line)
    return result
