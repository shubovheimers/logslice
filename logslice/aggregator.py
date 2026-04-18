"""Aggregate log lines into bucketed counts over time windows."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterator, Iterable, Dict, List
from logslice.parser import LogLine


@dataclass
class AggregateOptions:
    bucket_seconds: int = 60
    by_level: bool = False
    by_pattern: str = ""
    enabled: bool = False

    def __post_init__(self) -> None:
        if self.bucket_seconds <= 0:
            raise ValueError("bucket_seconds must be positive")


@dataclass
class AggregateBucket:
    start: datetime
    end: datetime
    count: int = 0
    breakdown: Dict[str, int] = field(default_factory=dict)

    def label(self) -> str:
        return self.start.strftime("%Y-%m-%dT%H:%M:%S")


def _bucket_start(ts: datetime, seconds: int) -> datetime:
    epoch = datetime(1970, 1, 1, tzinfo=ts.tzinfo)
    total = int((ts - epoch).total_seconds())
    snapped = (total // seconds) * seconds
    return epoch + timedelta(seconds=snapped)


def aggregate_lines(
    lines: Iterable[LogLine],
    opts: AggregateOptions,
) -> Iterator[AggregateBucket]:
    import re
    buckets: Dict[datetime, AggregateBucket] = {}
    pat = re.compile(opts.by_pattern, re.IGNORECASE) if opts.by_pattern else None
    delta = timedelta(seconds=opts.bucket_seconds)

    for line in lines:
        if line.timestamp is None:
            continue
        start = _bucket_start(line.timestamp, opts.bucket_seconds)
        if start not in buckets:
            buckets[start] = AggregateBucket(start=start, end=start + delta)
        bucket = buckets[start]
        bucket.count += 1
        if opts.by_level and line.level:
            bucket.breakdown[line.level] = bucket.breakdown.get(line.level, 0) + 1
        if pat and pat.search(line.raw):
            key = opts.by_pattern
            bucket.breakdown[key] = bucket.breakdown.get(key, 0) + 1

    for start in sorted(buckets):
        yield buckets[start]
