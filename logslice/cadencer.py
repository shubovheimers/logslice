"""cadencer.py – emit lines at a controlled cadence (lines-per-second cap).

Useful when replaying or streaming log output to a downstream consumer that
cannot handle bursts.  Unlike the throttler (which drops lines), the cadencer
slows delivery by sleeping between emissions.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator

from logslice.parser import LogLine


@dataclass
class CadenceOptions:
    """Configuration for the cadencer."""

    lines_per_second: float = 0.0  # 0 means disabled
    burst: int = 1  # how many lines to emit before sleeping
    _sleep: Callable[[float], None] = field(default=time.sleep, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.lines_per_second < 0:
            raise ValueError("lines_per_second must be >= 0")
        if self.burst < 1:
            raise ValueError("burst must be >= 1")

    @property
    def enabled(self) -> bool:
        return self.lines_per_second > 0

    @property
    def interval(self) -> float:
        """Seconds to sleep after each burst."""
        if not self.enabled:
            return 0.0
        return self.burst / self.lines_per_second


def cadence_lines(
    lines: Iterable[LogLine],
    opts: CadenceOptions | None,
) -> Iterator[LogLine]:
    """Yield *lines* respecting the cadence defined in *opts*.

    If *opts* is ``None`` or disabled, lines are yielded without any delay.
    """
    if opts is None or not opts.enabled:
        yield from lines
        return

    interval = opts.interval
    bucket: int = 0

    for line in lines:
        yield line
        bucket += 1
        if bucket >= opts.burst:
            opts._sleep(interval)
            bucket = 0
