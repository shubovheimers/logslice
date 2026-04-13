"""Statistics and summary reporting for log slices."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Optional
import datetime

from logslice.parser import LogLine


@dataclass
class LogStats:
    """Aggregated statistics over a collection of log lines."""

    total_lines: int = 0
    matched_lines: int = 0
    level_counts: Counter = field(default_factory=Counter)
    first_timestamp: Optional[datetime.datetime] = None
    last_timestamp: Optional[datetime.datetime] = None
    skipped_lines: int = 0

    @property
    def time_span(self) -> Optional[datetime.timedelta]:
        """Return the duration between the first and last timestamp, if available."""
        if self.first_timestamp and self.last_timestamp:
            return self.last_timestamp - self.first_timestamp
        return None

    def as_dict(self) -> dict:
        return {
            "total_lines": self.total_lines,
            "matched_lines": self.matched_lines,
            "skipped_lines": self.skipped_lines,
            "level_counts": dict(self.level_counts),
            "first_timestamp": self.first_timestamp.isoformat() if self.first_timestamp else None,
            "last_timestamp": self.last_timestamp.isoformat() if self.last_timestamp else None,
            "time_span_seconds": self.time_span.total_seconds() if self.time_span else None,
        }


def collect_stats(lines: Iterable[LogLine], total_lines: int = 0) -> LogStats:
    """Collect statistics from an iterable of matched LogLine objects."""
    stats = LogStats(total_lines=total_lines)

    for line in lines:
        stats.matched_lines += 1

        if line.level:
            stats.level_counts[line.level.upper()] += 1
        else:
            stats.skipped_lines += 1

        if line.timestamp:
            if stats.first_timestamp is None:
                stats.first_timestamp = line.timestamp
            stats.last_timestamp = line.timestamp

    return stats


def format_stats(stats: LogStats) -> str:
    """Return a human-readable summary string for the given LogStats."""
    lines = [
        f"Total lines scanned : {stats.total_lines}",
        f"Matched lines       : {stats.matched_lines}",
        f"Skipped (no level)  : {stats.skipped_lines}",
    ]

    if stats.level_counts:
        level_summary = ", ".join(
            f"{lvl}={cnt}" for lvl, cnt in sorted(stats.level_counts.items())
        )
        lines.append(f"By level            : {level_summary}")

    if stats.first_timestamp:
        lines.append(f"First timestamp     : {stats.first_timestamp.isoformat()}")
    if stats.last_timestamp:
        lines.append(f"Last timestamp      : {stats.last_timestamp.isoformat()}")
    if stats.time_span is(f"Time span           : {stats.time_span}")

    return "\n".join(lines)
