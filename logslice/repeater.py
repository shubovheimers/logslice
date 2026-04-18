"""repeater.py – detect and count repeated log lines within a sliding window."""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Iterator

from logslice.parser import LogLine


@dataclass
class RepeatOptions:
    enabled: bool = False
    window: int = 10  # number of lines to look back
    min_repeats: int = 2  # minimum occurrences to flag
    key_fields: tuple[str, ...] = ("level", "message")

    def __post_init__(self) -> None:
        if self.window < 1:
            raise ValueError("window must be >= 1")
        if self.min_repeats < 2:
            raise ValueError("min_repeats must be >= 2")

    def is_active(self) -> bool:
        return self.enabled


def _make_key(line: LogLine, key_fields: tuple[str, ...]) -> tuple:
    parts = []
    for f in key_fields:
        if f == "level":
            parts.append(line.level or "")
        elif f == "message":
            parts.append(line.message)
        else:
            parts.append(line.extra.get(f, "") if line.extra else "")
    return tuple(parts)


@dataclass
class RepeatMatch:
    line: LogLine
    count: int
    first_seen_index: int


def find_repeats(
    lines: Iterator[LogLine],
    opts: RepeatOptions,
) -> Iterator[RepeatMatch]:
    """Yield RepeatMatch for lines that repeat >= min_repeats times in window."""
    if not opts.is_active():
        return

    buf: deque[tuple[tuple, int]] = deque()  # (key, global_index)
    emitted: set[tuple] = set()
    idx = 0

    for line in lines:
        key = _make_key(line, opts.key_fields)
        # evict entries outside window
        while buf and buf[0][1] < idx - opts.window:
            old_key = buf.popleft()[0]
            # only remove from emitted if no longer in window
            if all(k != old_key for _, k2 in buf for k in [k2]):
                emitted.discard(old_key)

        buf.append((key, idx))
        count = sum(1 for k, _ in buf if k == key)

        if count >= opts.min_repeats and key not in emitted:
            first = next(i for k, i in buf if k == key)
            yield RepeatMatch(line=line, count=count, first_seen_index=first)
            emitted.add(key)

        idx += 1
