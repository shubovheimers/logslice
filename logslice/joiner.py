"""joiner.py – merge multi-line log entries into single logical lines.

Some log formats (e.g. Java stack traces, Python tracebacks) spread a single
logical event across several physical lines.  JoinerOptions controls how
continuation lines are detected and folded into the preceding anchor line.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class JoinOptions:
    """Configuration for multi-line joining."""

    # Regex that marks a line as a *continuation* of the previous one.
    # Default matches lines that start with whitespace (indented) or a bare
    # 'at ' / 'Caused by:' prefix common in JVM stack traces.
    continuation_pattern: str = r"^(\s+|Caused by:|\.\.\. \d+ more)"

    # Maximum number of continuation lines to fold into one anchor.
    max_continuation: int = 50

    # Separator inserted between folded lines in the combined raw text.
    separator: str = " \\ "

    # When False the joiner is a no-op passthrough.
    enabled: bool = True

    _compiled: Optional[re.Pattern] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.enabled and self.continuation_pattern:
            self._compiled = re.compile(self.continuation_pattern)

    def is_continuation(self, raw: str) -> bool:
        """Return True when *raw* looks like a continuation line."""
        if self._compiled is None:
            return False
        return bool(self._compiled.match(raw))


def join_lines(
    lines: Iterable[LogLine],
    opts: Optional[JoinOptions] = None,
) -> Iterator[LogLine]:
    """Yield LogLines with continuation lines folded into their anchor.

    When *opts* is None or disabled every line is yielded unchanged.
    """
    if opts is None or not opts.enabled:
        yield from lines
        return

    pending: Optional[LogLine] = None
    count = 0

    for line in lines:
        if pending is None:
            pending = line
            count = 0
            continue

        if opts.is_continuation(line.raw) and count < opts.max_continuation:
            # Fold this continuation into the pending anchor.
            pending = LogLine(
                raw=pending.raw + opts.separator + line.raw.strip(),
                timestamp=pending.timestamp,
                level=pending.level,
                message=pending.message,
                extra=pending.extra,
            )
            count += 1
        else:
            yield pending
            pending = line
            count = 0

    if pending is not None:
        yield pending
