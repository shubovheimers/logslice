"""Classify log lines into named categories based on pattern rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from logslice.parser import LogLine


@dataclass
class ClassifyRule:
    """A single named pattern rule."""
    name: str
    pattern: str
    _compiled: re.Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._compiled = re.compile(self.pattern, re.IGNORECASE)

    def matches(self, text: str) -> bool:
        return bool(self._compiled.search(text))


@dataclass
class ClassifyOptions:
    """Options controlling line classification."""
    rules: List[ClassifyRule] = field(default_factory=list)
    default_category: str = "uncategorised"
    tag_field: str = "category"

    @property
    def enabled(self) -> bool:
        return len(self.rules) > 0


def classify_line(line: LogLine, opts: ClassifyOptions) -> Tuple[LogLine, str]:
    """Return *(line, category)* for a single log line."""
    for rule in opts.rules:
        if rule.matches(line.raw):
            return line, rule.name
    return line, opts.default_category


def classify_lines(
    lines: Iterable[LogLine],
    opts: Optional[ClassifyOptions],
) -> Iterator[Tuple[LogLine, str]]:
    """Yield *(line, category)* pairs for every line in *lines*.

    If *opts* is ``None`` or disabled every line is yielded with the
    default category so downstream consumers always receive a uniform
    stream.
    """
    if opts is None or not opts.enabled:
        default = (opts.default_category if opts else "uncategorised")
        for line in lines:
            yield line, default
        return

    for line in lines:
        yield classify_line(line, opts)


def group_by_category(
    lines: Iterable[LogLine],
    opts: ClassifyOptions,
) -> Dict[str, List[LogLine]]:
    """Consume *lines* and return a dict mapping category → list of lines."""
    groups: Dict[str, List[LogLine]] = {}
    for line, cat in classify_lines(lines, opts):
        groups.setdefault(cat, []).append(line)
    return groups
