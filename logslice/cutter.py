"""cutter.py – split a line's raw text into named fields using a delimiter or regex."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional

from logslice.parser import LogLine


@dataclass
class CutOptions:
    enabled: bool = False
    delimiter: Optional[str] = None          # simple string split
    pattern: Optional[str] = None            # regex with named groups
    fields: List[str] = field(default_factory=list)  # names for delimiter columns
    keep_raw: bool = True

    def __post_init__(self) -> None:
        if self.delimiter is not None and self.pattern is not None:
            raise ValueError("Specify delimiter or pattern, not both.")
        if self.pattern is not None:
            # validate the regex early
            re.compile(self.pattern)

    def is_active(self) -> bool:
        return self.enabled and (self.delimiter is not None or self.pattern is not None)


def _cut_with_delimiter(text: str, delimiter: str, names: List[str]) -> Dict[str, str]:
    parts = text.split(delimiter)
    result: Dict[str, str] = {}
    for i, part in enumerate(parts):
        name = names[i] if i < len(names) else f"field{i}"
        result[name] = part
    return result


def _cut_with_pattern(text: str, compiled: re.Pattern) -> Dict[str, str]:  # type: ignore[type-arg]
    m = compiled.search(text)
    if m is None:
        return {}
    return {k: v or "" for k, v in m.groupdict().items()}


def cut_line(line: LogLine, opts: CutOptions) -> LogLine:
    """Return a new LogLine with extra fields populated from cutting raw text."""
    if not opts.is_active():
        return line

    extra = dict(line.extra) if line.extra else {}

    if opts.delimiter is not None:
        extracted = _cut_with_delimiter(line.raw, opts.delimiter, opts.fields)
    else:
        compiled = re.compile(opts.pattern)  # type: ignore[arg-type]
        extracted = _cut_with_pattern(line.raw, compiled)

    extra.update(extracted)
    if not opts.keep_raw:
        extra.pop("raw", None)

    return LogLine(
        raw=line.raw,
        timestamp=line.timestamp,
        level=line.level,
        message=line.message,
        extra=extra,
    )


def cut_lines(lines: Iterable[LogLine], opts: CutOptions) -> Iterator[LogLine]:
    for line in lines:
        yield cut_line(line, opts)
