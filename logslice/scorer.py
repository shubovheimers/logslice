"""Relevance scoring for log lines based on weighted pattern matches."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional, Tuple

from logslice.parser import LogLine


@dataclass
class ScoreRule:
    pattern: str
    weight: float = 1.0
    case_sensitive: bool = False
    _compiled: re.Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._compiled = re.compile(self.pattern, flags)

    def score(self, text: str) -> float:
        matches = self._compiled.findall(text)
        return len(matches) * self.weight


@dataclass
class ScorerOptions:
    rules: List[ScoreRule] = field(default_factory=list)
    threshold: float = 0.0
    top_n: Optional[int] = None

    def enabled(self) -> bool:
        return bool(self.rules)


@dataclass
class ScoredLine:
    line: LogLine
    score: float


def score_line(line: LogLine, rules: List[ScoreRule]) -> float:
    text = line.raw
    return sum(rule.score(text) for rule in rules)


def score_lines(
    lines: Iterable[LogLine],
    opts: ScorerOptions,
) -> Iterator[ScoredLine]:
    if not opts.enabled():
        for line in lines:
            yield ScoredLine(line=line, score=0.0)
        return

    scored: List[ScoredLine] = []
    for line in lines:
        s = score_line(line, opts.rules)
        if s >= opts.threshold:
            scored.append(ScoredLine(line=line, score=s))

    scored.sort(key=lambda sl: sl.score, reverse=True)

    if opts.top_n is not None:
        scored = scored[: opts.top_n]

    yield from scored
