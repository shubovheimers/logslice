"""censor.py – field-level censoring for LogLine extras.

Drops or blanks specific named fields from the LogLine.extra dict,
useful for stripping credentials or PII before output.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine

_SENTINEL = "[CENSORED]"


@dataclass
class CensorOptions:
    """Configuration for the censor stage."""

    fields: list[str] = field(default_factory=list)
    """Exact field names in LogLine.extra to censor."""

    patterns: list[str] = field(default_factory=list)
    """Regex patterns matched against field names."""

    drop: bool = False
    """When True, remove the field entirely; otherwise replace with sentinel."""

    replacement: str = _SENTINEL
    """Replacement value used when drop=False."""

    def __post_init__(self) -> None:
        if not isinstance(self.replacement, str):
            raise TypeError("replacement must be a str")
        self._compiled: list[re.Pattern[str]] = [
            re.compile(p) for p in self.patterns
        ]

    @property
    def is_active(self) -> bool:
        return bool(self.fields or self.patterns)

    def _should_censor(self, key: str) -> bool:
        if key in self.fields:
            return True
        return any(rx.search(key) for rx in self._compiled)


def censor_line(line: LogLine, opts: CensorOptions) -> LogLine:
    """Return a new LogLine with matching extra fields censored."""
    if not opts.is_active or not line.extra:
        return line

    new_extra: dict = {}
    for k, v in line.extra.items():
        if opts._should_censor(k):
            if not opts.drop:
                new_extra[k] = opts.replacement
            # drop: simply omit the key
        else:
            new_extra[k] = v

    return LogLine(
        raw=line.raw,
        timestamp=line.timestamp,
        level=line.level,
        message=line.message,
        extra=new_extra,
    )


def censor_lines(
    lines: Iterable[LogLine],
    opts: Optional[CensorOptions],
) -> Iterator[LogLine]:
    """Apply censoring to every line in *lines*."""
    if opts is None or not opts.is_active:
        yield from lines
        return
    for line in lines:
        yield censor_line(line, opts)
