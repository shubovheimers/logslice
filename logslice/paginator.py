"""Pagination support for logslice output — limit and offset line controls."""

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class PaginateOptions:
    """Options controlling pagination of log output."""

    limit: Optional[int] = None   # maximum number of lines to yield
    offset: int = 0               # number of lines to skip before yielding

    def __post_init__(self) -> None:
        if self.offset < 0:
            raise ValueError(f"offset must be >= 0, got {self.offset}")
        if self.limit is not None and self.limit < 0:
            raise ValueError(f"limit must be >= 0, got {self.limit}")

    @property
    def enabled(self) -> bool:
        return self.offset > 0 or self.limit is not None


def paginate_lines(
    lines: Iterable[LogLine],
    opts: Optional[PaginateOptions] = None,
) -> Iterator[LogLine]:
    """Yield lines from *lines* respecting offset and limit in *opts*.

    If *opts* is None or pagination is not enabled, all lines are yielded
    unchanged.
    """
    if opts is None or not opts.enabled:
        yield from lines
        return

    skipped = 0
    emitted = 0

    for line in lines:
        if skipped < opts.offset:
            skipped += 1
            continue

        if opts.limit is not None and emitted >= opts.limit:
            break

        yield line
        emitted += 1


def build_paginate_options(
    limit: Optional[int] = None,
    offset: int = 0,
) -> PaginateOptions:
    """Convenience constructor used by CLI layer."""
    return PaginateOptions(limit=limit, offset=offset)
