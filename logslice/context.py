"""Context lines: yield surrounding lines around matches (like grep -A/-B/-C)."""

from collections import deque
from dataclasses import dataclass, field
from typing import Callable, Iterable, Iterator

from logslice.parser import LogLine


@dataclass
class ContextOptions:
    before: int = 0
    after: int = 0

    @property
    def enabled(self) -> bool:
        return self.before > 0 or self.after > 0


def iter_with_context(
    lines: Iterable[LogLine],
    predicate: Callable[[LogLine], bool],
    opts: ContextOptions,
) -> Iterator[LogLine]:
    """Yield lines that match *predicate*, plus up to *before* lines before
    and *after* lines after each match.  Overlapping windows are merged."""
    if not opts.enabled:
        yield from (line for line in lines if predicate(line))
        return

    buf: deque[LogLine] = deque(maxlen=opts.before)
    pending_after: int = 0
    emitted_ids: set[int] = set()

    def _emit(line: LogLine) -> Iterator[LogLine]:
        lid = id(line)
        if lid not in emitted_ids:
            emitted_ids.add(lid)
            yield line

    for line in lines:
        if predicate(line):
            # flush buffered before-context
            for prev in buf:
                yield from _emit(prev)
            yield from _emit(line)
            pending_after = opts.after
            buf.clear()
        elif pending_after > 0:
            yield from _emit(line)
            pending_after -= 1
            buf.clear()
        else:
            buf.append(line)
