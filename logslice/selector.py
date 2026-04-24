"""Field-based line selector: keep only lines whose extra fields match
a set of key/value criteria."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional, Pattern

from logslice.parser import LogLine


@dataclass
class SelectRule:
    """A single field-match rule."""
    key: str
    pattern: str
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._re: Pattern[str] = re.compile(self.pattern, flags)

    def matches(self, line: LogLine) -> bool:
        value = line.extra.get(self.key)
        if value is None:
            return False
        return bool(self._re.search(str(value)))


@dataclass
class SelectorOptions:
    rules: List[SelectRule] = field(default_factory=list)
    require_all: bool = True  # AND vs OR semantics

    def enabled(self) -> bool:
        return bool(self.rules)


def select_lines(
    lines: Iterable[LogLine],
    opts: Optional[SelectorOptions],
) -> Iterator[LogLine]:
    """Yield only lines that satisfy the selector rules.

    If *opts* is None or disabled every line passes through unchanged.
    """
    if opts is None or not opts.enabled():
        yield from lines
        return

    for line in lines:
        results = [rule.matches(line) for rule in opts.rules]
        if opts.require_all:
            keep = all(results)
        else:
            keep = any(results)
        if keep:
            yield line
