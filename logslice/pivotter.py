"""Pivot log lines into a frequency table by a field or pattern group."""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Iterator

from logslice.parser import LogLine


@dataclass
class PivotOptions:
    by: str = "level"          # 'level', 'source', or a regex group name
    pattern: str | None = None  # if set, extract named group 'key' from raw text
    top_n: int = 0              # 0 = all
    min_count: int = 1

    def __post_init__(self) -> None:
        if self.top_n < 0:
            raise ValueError("top_n must be >= 0")
        if self.min_count < 1:
            raise ValueError("min_count must be >= 1")

    def enabled(self) -> bool:
        return bool(self.by or self.pattern)


def _extract_key(line: LogLine, opts: PivotOptions) -> str | None:
    if opts.pattern:
        m = re.search(opts.pattern, line.raw)
        if m:
            try:
                return m.group("key")
            except IndexError:
                return m.group(0)
        return None
    if opts.by == "level":
        return line.level or "UNKNOWN"
    if opts.by == "source":
        return line.source or "UNKNOWN"
    extra = line.extra or {}
    return str(extra.get(opts.by, "UNKNOWN"))


def pivot_lines(
    lines: Iterable[LogLine],
    opts: PivotOptions,
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for line in lines:
        key = _extract_key(line, opts)
        if key is not None:
            counts[key] += 1
    result = {k: v for k, v in counts.items() if v >= opts.min_count}
    if opts.top_n:
        result = dict(counts.most_common(opts.top_n))
        result = {k: v for k, v in result.items() if v >= opts.min_count}
    return result


def format_pivot(table: dict[str, int], total: int | None = None) -> Iterator[str]:
    if not table:
        yield "(no results)"
        return
    width = max(len(k) for k in table)
    grand = total or sum(table.values())
    for key, count in sorted(table.items(), key=lambda kv: -kv[1]):
        pct = 100.0 * count / grand if grand else 0.0
        yield f"{key:<{width}}  {count:>6}  {pct:5.1f}%"
