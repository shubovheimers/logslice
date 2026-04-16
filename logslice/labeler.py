"""Attach static or pattern-derived labels to log lines."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from logslice.parser import LogLine


@dataclass
class LabelRule:
    pattern: str
    label: str
    value: str = "true"
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._re = re.compile(self.pattern, flags)

    def matches(self, line: LogLine) -> bool:
        return bool(self._re.search(line.raw))


@dataclass
class LabelerOptions:
    rules: List[LabelRule] = field(default_factory=list)
    static_labels: Dict[str, str] = field(default_factory=dict)

    def enabled(self) -> bool:
        return bool(self.rules or self.static_labels)


def label_lines(
    lines: Iterable[LogLine],
    opts: Optional[LabelerOptions],
) -> Iterator[LogLine]:
    """Yield lines with labels added to their extra dict."""
    if opts is None or not opts.enabled():
        yield from lines
        return

    for line in lines:
        extra = dict(line.extra) if line.extra else {}
        for k, v in opts.static_labels.items():
            extra[k] = v
        for rule in opts.rules:
            if rule.matches(line):
                extra[rule.label] = rule.value
        yield LogLine(
            raw=line.raw,
            timestamp=line.timestamp,
            level=line.level,
            message=line.message,
            extra=extra,
        )
