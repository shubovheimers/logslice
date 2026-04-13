"""Duplicate-line detection and removal for log streams."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class DedupOptions:
    """Options controlling deduplication behaviour."""

    enabled: bool = False
    # How to derive a comparison key from a line.
    # Defaults to the stripped raw text if None.
    key_fn: Optional[Callable[[LogLine], str]] = None
    # Maximum number of distinct keys to track (prevents unbounded memory).
    max_seen: int = 100_000


def _default_key(line: LogLine) -> str:
    return line.message.strip() if line.message else line.raw.strip()


def dedup_lines(
    lines: Iterable[LogLine],
    opts: Optional[DedupOptions] = None,
) -> Iterator[LogLine]:
    """Yield lines that have not been seen before according to *opts*.

    When *opts* is None or ``opts.enabled`` is False the stream is passed
    through unchanged.
    """
    if opts is None or not opts.enabled:
        yield from lines
        return

    key_fn: Callable[[LogLine], str] = opts.key_fn or _default_key
    seen: set[str] = set()

    for line in lines:
        key = key_fn(line)
        if key in seen:
            continue
        seen.add(key)
        # Evict oldest entries once we exceed the cap to avoid memory blow-up.
        # Simple strategy: clear half the set when the limit is hit.
        if len(seen) > opts.max_seen:
            items = list(seen)
            seen = set(items[len(items) // 2 :])
        yield line


def count_duplicates(lines: Iterable[LogLine], key_fn: Optional[Callable[[LogLine], str]] = None) -> int:
    """Return the number of duplicate lines in *lines* (does not stream)."""
    fn = key_fn or _default_key
    seen: set[str] = set()
    dupes = 0
    for line in lines:
        key = fn(line)
        if key in seen:
            dupes += 1
        else:
            seen.add(key)
    return dupes
