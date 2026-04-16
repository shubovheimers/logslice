"""Flatten multi-line log entries into single LogLine records."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class FlattenOptions:
    """Configuration for the log line flattener."""

    enabled: bool = False
    # Regex that marks the START of a new log record; continuation lines
    # are any lines that do NOT match this pattern.
    record_start_pattern: str = r"^\d{4}-\d{2}-\d{2}"
    # Separator inserted between joined continuation lines.
    join_separator: str = " "
    # Maximum number of continuation lines to absorb into one record.
    max_continuation: int = 50
    _compiled: Optional[re.Pattern] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.max_continuation < 1:
            raise ValueError("max_continuation must be >= 1")
        self._compiled = re.compile(self.record_start_pattern)

    def is_record_start(self, text: str) -> bool:
        assert self._compiled is not None
        return bool(self._compiled.match(text))


def flatten_lines(
    lines: Iterable[LogLine],
    opts: Optional[FlattenOptions] = None,
) -> Iterator[LogLine]:
    """Merge continuation lines into the preceding record.

    When *opts* is ``None`` or ``opts.enabled`` is ``False`` the input is
    yielded unchanged.
    """
    if opts is None or not opts.enabled:
        yield from lines
        return

    pending: Optional[LogLine] = None
    absorbed: int = 0

    for line in lines:
        if opts.is_record_start(line.raw):
            if pending is not None:
                yield pending
            pending = line
            absorbed = 0
        else:
            if pending is None:
                # No record started yet — emit as-is.
                yield line
            elif absorbed >= opts.max_continuation:
                # Cap reached: flush current record, start fresh.
                yield pending
                pending = line
                absorbed = 0
            else:
                merged_raw = pending.raw + opts.join_separator + line.raw.strip()
                pending = LogLine(
                    raw=merged_raw,
                    timestamp=pending.timestamp,
                    level=pending.level,
                    message=(
                        (pending.message or "")
                        + opts.join_separator
                        + (line.message or line.raw).strip()
                    ),
                    extra=pending.extra,
                )
                absorbed += 1

    if pending is not None:
        yield pending
