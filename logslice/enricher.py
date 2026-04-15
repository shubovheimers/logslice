"""Enricher: attach derived metadata fields to LogLine objects."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class EnrichOptions:
    """Configuration for the log-line enricher."""

    # Add a monotonically increasing sequence number stored in extra['seq']
    add_sequence: bool = False

    # Extract a named capture group from raw text and store it in extra
    # e.g. r'request_id=(?P<request_id>[\w-]+)'
    extract_patterns: list[str] = field(default_factory=list)

    # Copy the source filename into extra['source'] when truthy
    source_tag: Optional[str] = None

    def enabled(self) -> bool:
        return self.add_sequence or bool(self.extract_patterns) or bool(self.source_tag)


def _compile(patterns: list[str]) -> list[re.Pattern]:
    return [re.compile(p) for p in patterns]


def enrich_lines(
    lines: Iterable[LogLine],
    opts: Optional[EnrichOptions] = None,
) -> Iterator[LogLine]:
    """Yield lines with extra metadata attached according to *opts*.

    The original LogLine objects are **not** mutated; a shallow copy with an
    updated *extra* dict is produced instead.
    """
    if opts is None or not opts.enabled():
        yield from lines
        return

    compiled = _compile(opts.extract_patterns)
    seq = 0

    for line in lines:
        extra = dict(line.extra) if line.extra else {}

        if opts.add_sequence:
            extra["seq"] = seq
            seq += 1

        if opts.source_tag:
            extra["source"] = opts.source_tag

        for pattern in compiled:
            m = pattern.search(line.raw)
            if m:
                extra.update(m.groupdict())

        yield LogLine(
            raw=line.raw,
            timestamp=line.timestamp,
            level=line.level,
            message=line.message,
            extra=extra,
        )
