"""collapser.py – collapse consecutive repeated log lines into a single
summary line, similar to how syslog shows "last message repeated N times".
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class CollapseOptions:
    enabled: bool = False
    # Minimum consecutive repeats before collapsing (>=2 means at least a pair)
    min_repeats: int = 2
    # Label template; {n} is replaced with the repeat count
    label: str = "[repeated {n}x]"

    def __post_init__(self) -> None:
        if self.min_repeats < 2:
            raise ValueError("min_repeats must be >= 2")
        if "{n}" not in self.label:
            raise ValueError("label template must contain '{n}' placeholder")


def _message_key(line: LogLine) -> str:
    """Return the text used to decide whether two lines are 'the same'."""
    return line.raw.rstrip()


def collapse_lines(
    lines: Iterable[LogLine],
    opts: Optional[CollapseOptions] = None,
) -> Iterator[LogLine]:
    """Yield lines, collapsing runs of identical messages.

    When *opts* is None or disabled every line is passed through unchanged.
    """
    if opts is None or not opts.enabled:
        yield from lines
        return

    pending: Optional[LogLine] = None
    run: int = 0

    for line in lines:
        if pending is None:
            pending = line
            run = 1
            continue

        if _message_key(line) == _message_key(pending):
            run += 1
        else:
            # Emit the buffered line (possibly annotated)
            yield _maybe_annotate(pending, run, opts)
            pending = line
            run = 1

    if pending is not None:
        yield _maybe_annotate(pending, run, opts)


def _maybe_annotate(line: LogLine, run: int, opts: CollapseOptions) -> LogLine:
    """Return *line* unchanged, or a new LogLine with a repeat label appended."""
    if run < opts.min_repeats:
        return line
    label = opts.label.format(n=run)
    new_raw = f"{line.raw.rstrip()} {label}"
    return LogLine(
        raw=new_raw,
        timestamp=line.timestamp,
        level=line.level,
        message=f"{line.message} {label}" if line.message else new_raw,
    )
