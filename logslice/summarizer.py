"""Summarize log files: count lines, levels, time range, and top patterns."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Optional

from logslice.parser import LogLine


@dataclass
class SummaryOptions:
    top_n: int = 10
    count_levels: bool = True
    count_patterns: bool = True


@dataclass
class LogSummary:
    total_lines: int = 0
    level_counts: Counter = field(default_factory=Counter)
    top_messages: list[tuple[str, int]] = field(default_factory=list)
    first_timestamp: Optional[object] = None
    last_timestamp: Optional[object] = None

    def time_range(self) -> Optional[tuple]:
        if self.first_timestamp and self.last_timestamp:
            return (self.first_timestamp, self.last_timestamp)
        return None


def _normalise_message(raw: str, max_len: int = 60) -> str:
    """Trim and normalise a message for pattern grouping."""
    return raw.strip()[:max_len]


def summarize_lines(
    lines: Iterable[LogLine],
    opts: Optional[SummaryOptions] = None,
) -> LogSummary:
    """Consume *lines* and return a :class:`LogSummary`."""
    if opts is None:
        opts = SummaryOptions()

    summary = LogSummary()
    message_counter: Counter = Counter()

    for line in lines:
        summary.total_lines += 1

        if line.timestamp is not None:
            if summary.first_timestamp is None:
                summary.first_timestamp = line.timestamp
            summary.last_timestamp = line.timestamp

        if opts.count_levels and line.level:
            summary.level_counts[line.level.upper()] += 1

        if opts.count_patterns:
            key = _normalise_message(line.raw)
            message_counter[key] += 1

    if opts.count_patterns:
        summary.top_messages = message_counter.most_common(opts.top_n)

    return summary


def format_summary(summary: LogSummary) -> str:
    """Return a human-readable multi-line string for *summary*."""
    lines = []
    lines.append(f"Total lines : {summary.total_lines}")

    tr = summary.time_range()
    if tr:
        lines.append(f"First entry : {tr[0]}")
        lines.append(f"Last entry  : {tr[1]}")

    if summary.level_counts:
        lines.append("Levels:")
        for lvl, cnt in sorted(summary.level_counts.items()):
            lines.append(f"  {lvl:<10} {cnt}")

    if summary.top_messages:
        lines.append("Top messages:")
        for msg, cnt in summary.top_messages:
            lines.append(f"  ({cnt:>5}x) {msg}")

    return "\n".join(lines)
