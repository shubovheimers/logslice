"""Field mapping/transformation for log lines."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, Iterator, List, Optional

from logslice.parser import LogLine


@dataclass
class MapRule:
    target_field: str
    expression: str
    _compiled: Optional[re.Pattern] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.target_field:
            raise ValueError("target_field must not be empty")
        if not self.expression:
            raise ValueError("expression must not be empty")

    def apply(self, line: LogLine) -> Optional[str]:
        text = line.raw
        m = re.search(self.expression, text)
        if m:
            try:
                return m.group(1)
            except IndexError:
                return m.group(0)
        return None


@dataclass
class MapOptions:
    rules: List[MapRule] = field(default_factory=list)
    prefix: str = "map_"
    overwrite: bool = False

    def enabled(self) -> bool:
        return bool(self.rules)


def map_lines(
    lines: Iterable[LogLine],
    opts: Optional[MapOptions],
) -> Iterator[LogLine]:
    if opts is None or not opts.enabled():
        yield from lines
        return
    for line in lines:
        extra = dict(line.extra) if line.extra else {}
        for rule in opts.rules:
            key = f"{opts.prefix}{rule.target_field}" if opts.prefix else rule.target_field
            if key in extra and not opts.overwrite:
                continue
            value = rule.apply(line)
            if value is not None:
                extra[key] = value
        yield LogLine(
            raw=line.raw,
            timestamp=line.timestamp,
            level=line.level,
            message=line.message,
            extra=extra,
        )
