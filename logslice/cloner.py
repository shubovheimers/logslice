"""cloner.py – duplicate each matching log line N times.

Useful for stress-testing downstream pipeline stages or simulating
high-frequency bursts from a captured sample.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class CloneOptions:
    """Configuration for the line-cloner stage."""

    copies: int = 0
    """Total copies to emit per matched line (0 = disabled; 1 = emit twice, etc.)"""

    pattern: Optional[str] = None
    """If set, only lines whose raw text matches this pattern are cloned."""

    levels: list[str] = field(default_factory=list)
    """If non-empty, only lines whose level is in this list are cloned."""

    tag_clones: bool = False
    """When True, extra fields on clones carry ``_clone=True``."""

    def __post_init__(self) -> None:
        if self.copies < 0:
            raise ValueError("copies must be >= 0")

    @property
    def enabled(self) -> bool:
        return self.copies > 0

    def _compile(self):
        import re
        if self.pattern:
            return re.compile(self.pattern)
        return None

    def _matches(self, line: LogLine, compiled) -> bool:
        if compiled is not None and not compiled.search(line.raw):
            return False
        if self.levels:
            lvl = (line.level or "").upper()
            if lvl not in [l.upper() for l in self.levels]:
                return False
        return True


def clone_lines(
    lines: Iterable[LogLine],
    opts: Optional[CloneOptions] = None,
) -> Iterator[LogLine]:
    """Yield each line, followed by *opts.copies* duplicates when matched."""
    if opts is None or not opts.enabled:
        yield from lines
        return

    compiled = opts._compile()

    for line in lines:
        yield line
        if opts._matches(line, compiled):
            for _ in range(opts.copies):
                if opts.tag_clones:
                    extra = {**line.extra, "_clone": True}
                    yield LogLine(
                        raw=line.raw,
                        timestamp=line.timestamp,
                        level=line.level,
                        message=line.message,
                        extra=extra,
                    )
                else:
                    yield line
