"""Timestamper: inject or rewrite timestamps on log lines."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class TimestampOptions:
    """Options controlling timestamp injection/rewriting."""
    inject: bool = False          # add now() when timestamp is missing
    overwrite: bool = False       # replace every timestamp with now()
    utc: bool = True              # use UTC; if False use local time
    format: str = "%Y-%m-%dT%H:%M:%S.%f"  # strftime format for injected value

    def enabled(self) -> bool:
        return self.inject or self.overwrite


def _now(utc: bool) -> datetime:
    return datetime.now(timezone.utc) if utc else datetime.now()


def _format(dt: datetime, fmt: str) -> str:
    return dt.strftime(fmt)


def stamp_line(line: LogLine, opts: TimestampOptions) -> LogLine:
    """Return a (possibly new) LogLine with timestamp applied."""
    if not opts.enabled():
        return line

    needs_stamp = opts.overwrite or (opts.inject and line.timestamp is None)
    if not needs_stamp:
        return line

    now = _now(opts.utc)
    new_raw = f"{_format(now, opts.format)} {line.raw}" if line.timestamp is None else line.raw

    return LogLine(
        raw=new_raw,
        timestamp=now,
        level=line.level,
        message=line.message,
        extra=line.extra,
    )


def stamp_lines(
    lines: Iterable[LogLine],
    opts: Optional[TimestampOptions] = None,
) -> Iterator[LogLine]:
    """Yield lines with timestamps injected/overwritten according to opts."""
    if opts is None or not opts.enabled():
        yield from lines
        return
    for line in lines:
        yield stamp_line(line, opts)
