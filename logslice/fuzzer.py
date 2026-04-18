"""Fuzzy matching filter for log lines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


def _char_bigrams(text: str) -> set[str]:
    t = text.lower()
    return {t[i:i+2] for i in range(len(t) - 1)}


def dice_coefficient(a: str, b: str) -> float:
    """Sorensen-Dice similarity between two strings (0.0 – 1.0)."""
    if not a or not b:
        return 0.0
    if a == b:
        return 1.0
    ba, bb = _char_bigrams(a), _char_bigrams(b)
    if not ba or not bb:
        return 0.0
    return 2 * len(ba & bb) / (len(ba) + len(bb))


@dataclass
class FuzzOptions:
    query: str = ""
    threshold: float = 0.3
    field: str = "raw"          # 'raw', 'level', or 'message'
    enabled: bool = False
    scores: bool = False         # attach score to extra dict

    def __post_init__(self) -> None:
        if not 0.0 <= self.threshold <= 1.0:
            raise ValueError("threshold must be between 0.0 and 1.0")

    def is_active(self) -> bool:
        return self.enabled and bool(self.query)


def _field_text(line: LogLine, field: str) -> str:
    if field == "level":
        return line.level or ""
    if field == "message":
        return line.message or line.raw
    return line.raw


def fuzz_filter(
    lines: Iterable[LogLine],
    opts: Optional[FuzzOptions] = None,
) -> Iterator[LogLine]:
    """Yield lines whose similarity to *query* meets *threshold*."""
    if opts is None or not opts.is_active():
        yield from lines
        return

    for line in lines:
        text = _field_text(line, opts.field)
        score = dice_coefficient(opts.query, text)
        if score >= opts.threshold:
            if opts.scores:
                line.extra["fuzz_score"] = round(score, 4)
            yield line
