"""Pipeline integration for scoring and ranking log lines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogLine
from logslice.scorer import ScorerOptions, score_lines


@dataclass
class RankedLine:
    """A log line paired with its computed score."""

    line: LogLine
    score: float

    def __lt__(self, other: "RankedLine") -> bool:
        return self.score < other.score


@dataclass
class RankOptions:
    """Options for ranking a stream of log lines by score."""

    scorer: ScorerOptions = field(default_factory=ScorerOptions)
    top_n: int = 0          # 0 means return all
    threshold: float = 0.0  # exclude lines scoring below this
    descending: bool = True  # highest score first

    def __post_init__(self) -> None:
        if self.top_n < 0:
            raise ValueError("top_n must be >= 0")
        if self.threshold < 0.0:
            raise ValueError("threshold must be >= 0")


def rank_lines(
    lines: Iterable[LogLine],
    opts: RankOptions,
) -> Iterator[RankedLine]:
    """Score every line, filter by threshold, sort, and yield top-n."""
    scored: List[RankedLine] = []
    for line, s in score_lines(lines, opts.scorer):
        if s >= opts.threshold:
            scored.append(RankedLine(line=line, score=s))

    scored.sort(key=lambda r: r.score, reverse=opts.descending)

    top = scored[: opts.top_n] if opts.top_n else scored
    yield from top
