"""Tag log lines with user-defined labels based on pattern matching."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional

from logslice.parser import LogLine


@dataclass
class TagRule:
    tag: str
    pattern: str
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._regex = re.compile(self.pattern, flags)

    def matches(self, line: LogLine) -> bool:
        return bool(self._regex.search(line.raw))


@dataclass
class TaggerOptions:
    rules: List[TagRule] = field(default_factory=list)
    tag_field: str = "tags"
    multi: bool = True  # allow multiple tags per line

    def enabled(self) -> bool:
        return len(self.rules) > 0


def tag_lines(
    lines: Iterable[LogLine],
    opts: Optional[TaggerOptions],
) -> Iterator[LogLine]:
    """Yield lines annotated with matched tags in their extra dict."""
    if opts is None or not opts.enabled():
        yield from lines
        return

    for line in lines:
        matched: List[str] = []
        for rule in opts.rules:
            if rule.matches(line):
                matched.append(rule.tag)
                if not opts.multi:
                    break

        if matched:
            extra = dict(line.extra) if line.extra else {}
            existing = extra.get(opts.tag_field, [])
            if isinstanceextra[opts.tag_field] = existing + matched
            else:
                extra[opts.tag_field] = [existing] + matched
            line = LogLine(
                raw=line.raw,
                timestamp=line.timestamp,
                level=line.level,
                message=line.message,
                extra=extra,
            )
        yield line


def build_tagger_options(
    rules: Optional[List[Dict]] = None,
    multi: bool = True,
) -> TaggerOptions:
    """Build TaggerOptions from a list of rule dicts with 'tag' and 'pattern' keys."""
    tag_rules: List[TagRule] = []
    for r in (rules or []):
        tag_rules.append(
            TagRule(
                tag=r["tag"],
                pattern=r["pattern"],
                case_sensitive=r.get("case_sensitive", False),
            )
        )
    return TaggerOptions(rules=tag_rules, multi=multi)
