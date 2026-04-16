"""On-the-fly line compression using run-length encoding for repeated log segments."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class CompressOptions:
    enabled: bool = False
    min_run: int = 3  # minimum consecutive identical messages before compressing
    placeholder: str = "... [{count} identical lines omitted] ..."

    def __post_init__(self) -> None:
        if self.min_run < 2:
            raise ValueError("min_run must be >= 2")

    def is_active(self) -> bool:
        return self.enabled and self.min_run >= 2


def _message_key(line: LogLine) -> str:
    """Return the normalised message used for equality comparison."""
    return (line.message or line.raw).strip()


def compress_lines(
    lines: Iterable[LogLine],
    opts: Optional[CompressOptions] = None,
) -> Iterator[LogLine]:
    """Yield lines, collapsing runs of identical messages when opts is active."""
    if opts is None or not opts.is_active():
        yield from lines
        return

    buffer: list[LogLine] = []

    def _flush() -> Iterator[LogLine]:
        if not buffer:
            return
        if len(buffer) >= opts.min_run:
            yield buffer[0]
            summary_raw = opts.placeholder.format(count=len(buffer) - 1)
            yield LogLine(raw=summary_raw, timestamp=None, level=None, message=summary_raw)
        else:
            yield from buffer
        buffer.clear()

    prev_key: Optional[str] = None

    for line in lines:
        key = _message_key(line)
        if key == prev_key:
            buffer.append(line)
        else:
            yield from _flush()
            buffer.append(line)
            prev_key = key

    yield from _flush()
