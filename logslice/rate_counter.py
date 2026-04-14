"""Rate counter: compute per-second/minute log event rates over a sliding window."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class RateOptions:
    enabled: bool = False
    window_seconds: int = 60
    bucket_seconds: int = 1
    min_rate: Optional[float] = None  # only emit lines whose bucket rate >= this

    def __post_init__(self) -> None:
        if self.bucket_seconds < 1:
            raise ValueError("bucket_seconds must be >= 1")
        if self.window_seconds < self.bucket_seconds:
            raise ValueError("window_seconds must be >= bucket_seconds")


@dataclass
class RateBucket:
    ts: datetime
    count: int = 0


@dataclass
class RateCounter:
    options: RateOptions
    _buckets: deque = field(default_factory=deque, init=False, repr=False)

    def _bucket_key(self, ts: datetime) -> datetime:
        """Truncate timestamp to bucket boundary."""
        epoch = datetime(1970, 1, 1, tzinfo=ts.tzinfo)
        secs = int((ts - epoch).total_seconds())
        truncated = secs - (secs % self.options.bucket_seconds)
        return epoch + timedelta(seconds=truncated)

    def record(self, ts: datetime) -> None:
        key = self._bucket_key(ts)
        if self._buckets and self._buckets[-1].ts == key:
            self._buckets[-1].count += 1
        else:
            self._buckets.append(RateBucket(ts=key, count=1))
        cutoff = key - timedelta(seconds=self.options.window_seconds)
        while self._buckets and self._buckets[0].ts < cutoff:
            self._buckets.popleft()

    def rate_at(self, ts: datetime) -> float:
        """Return events-per-second rate for the bucket containing ts."""
        key = self._bucket_key(ts)
        for b in self._buckets:
            if b.ts == key:
                return b.count / self.options.bucket_seconds
        return 0.0

    def window_rate(self) -> float:
        """Return average events-per-second across the whole window."""
        if not self._buckets:
            return 0.0
        total = sum(b.count for b in self._buckets)
        span = self.options.window_seconds
        return total / span


def apply_rate_filter(
    lines: Iterable[LogLine], opts: RateOptions
) -> Iterator[LogLine]:
    """Yield lines whose per-bucket rate meets opts.min_rate (if set)."""
    if not opts.enabled:
        yield from lines
        return

    counter = RateCounter(options=opts)
    buffered: list[LogLine] = []

    for line in lines:
        if line.timestamp is not None:
            counter.record(line.timestamp)
        buffered.append(line)

    for line in buffered:
        if line.timestamp is None or opts.min_rate is None:
            yield line
        elif counter.rate_at(line.timestamp) >= opts.min_rate:
            yield line
