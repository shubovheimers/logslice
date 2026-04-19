"""pruner.py – drop log lines whose message falls below a minimum length."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator

from logslice.parser import LogLine


@dataclass
class PruneOptions:
    enabled: bool = False
    min_length: int = 1
    strip_whitespace: bool = True

    def __post_init__(self) -> None:
        if self.min_length < 0:
            raise ValueError("min_length must be >= 0")

    def is_active(self) -> bool:
        return self.enabled and self.min_length > 0


def _effective_text(line: LogLine, strip: bool) -> str:
    text = line.raw
    return text.strip() if strip else text


def prune_lines(
    lines: Iterable[LogLine],
    opts: PruneOptions | None = None,
) -> Iterator[LogLine]:
    """Yield only lines whose text meets the minimum length requirement."""
    if opts is None or not opts.is_active():
        yield from lines
        return

    for line in lines:
        if len(_effective_text(line, opts.strip_whitespace)) >= opts.min_length:
            yield line
