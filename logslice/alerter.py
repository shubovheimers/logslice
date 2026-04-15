"""Alert rules that fire when log lines match a threshold within a time window."""
from __future__ import annotations

import re
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogLine


@dataclass
class AlertRule:
    name: str
    pattern: str
    threshold: int = 1          # number of matches required to fire
    window_seconds: int = 60    # rolling time window in seconds
    level: Optional[str] = None # restrict to a specific log level

    _regex: re.Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._regex = re.compile(self.pattern, re.IGNORECASE)

    def matches(self, line: LogLine) -> bool:
        if self.level and (line.level or "").upper() != self.level.upper():
            return False
        return bool(self._regex.search(line.raw))


@dataclass
class AlertFired:
    rule_name: str
    count: int
    window_seconds: int
    first_seen: Optional[datetime]
    last_seen: Optional[datetime]
    sample_line: str

    def __str__(self) -> str:
        return (
            f"[ALERT] {self.rule_name}: {self.count} match(es) "
            f"in {self.window_seconds}s window "
            f"(first={self.first_seen}, last={self.last_seen})"
        )


@dataclass
class AlertOptions:
    rules: List[AlertRule] = field(default_factory=list)
    enabled: bool = False

    def __post_init__(self) -> None:
        if self.rules:
            self.enabled = True


def _check_window(
    timestamps: deque,
    window: timedelta,
    now: Optional[datetime],
) -> None:
    """Evict entries outside the rolling window."""
    if now is None:
        return
    cutoff = now - window
    while timestamps and timestamps[0] < cutoff:
        timestamps.popleft()


def evaluate_alerts(
    lines: Iterable[LogLine],
    opts: AlertOptions,
) -> Iterator[AlertFired]:
    """Yield AlertFired events whenever a rule's threshold is breached."""
    if not opts.enabled or not opts.rules:
        return

    windows: dict[str, deque] = {r.name: deque() for r in opts.rules}
    fired: set[str] = set()

    for line in lines:
        for rule in opts.rules:
            if not rule.matches(line):
                continue
            ts = line.timestamp
            _check_window(windows[rule.name], timedelta(seconds=rule.window_seconds), ts)
            windows[rule.name].append(ts)
            if len(windows[rule.name]) >= rule.threshold and rule.name not in fired:
                fired.add(rule.name)
                dq = windows[rule.name]
                yield AlertFired(
                    rule_name=rule.name,
                    count=len(dq),
                    window_seconds=rule.window_seconds,
                    first_seen=dq[0],
                    last_seen=dq[-1],
                    sample_line=line.raw,
                )
