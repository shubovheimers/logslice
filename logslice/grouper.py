"""Group log lines by a time window or field value."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Dict, Iterable, Iterator, List, Optional

from logslice.parser import LogLine


@dataclass
class GroupOptions:
    by_field: Optional[str] = None          # group by a key in LogLine.extra
    by_level: bool = False                  # group by log level
    window_seconds: Optional[int] = None    # group by fixed time window

    def __post_init__(self) -> None:
        active = sum([
            self.by_field is not None,
            self.by_level,
            self.window_seconds is not None,
        ])
        if active > 1:
            raise ValueError(
                "Only one of by_field, by_level, or window_seconds may be set."
            )

    @property
    def enabled(self) -> bool:
        return (
            self.by_field is not None
            or self.by_level
            or self.window_seconds is not None
        )


def _group_key(line: LogLine, opts: GroupOptions) -> str:
    if opts.by_level:
        return (line.level or "UNKNOWN").upper()
    if opts.by_field is not None:
        return str((line.extra or {}).get(opts.by_field, "__missing__"))
    if opts.window_seconds is not None and line.timestamp is not None:
        epoch = line.timestamp.timestamp()
        bucket = int(epoch // opts.window_seconds) * opts.window_seconds
        return str(bucket)
    return "__all__"


def group_lines(
    lines: Iterable[LogLine],
    opts: GroupOptions,
) -> Dict[str, List[LogLine]]:
    """Collect *lines* into a dict keyed by group label."""
    groups: Dict[str, List[LogLine]] = {}
    for line in lines:
        key = _group_key(line, opts)
        groups.setdefault(key, []).append(line)
    return groups


def iter_groups(
    lines: Iterable[LogLine],
    opts: GroupOptions,
) -> Iterator[tuple[str, List[LogLine]]]:
    """Yield (group_key, [LogLine, ...]) pairs in insertion order."""
    groups = group_lines(lines, opts)
    for key, members in groups.items():
        yield key, members
