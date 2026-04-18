"""Trimmer: strip leading/trailing blank lines and whitespace from log output."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator

from logslice.parser import LogLine


@dataclass
class TrimOptions:
    enabled: bool = False
    strip_blank_lines: bool = True
    strip_inline_whitespace: bool = True
    max_consecutive_blanks: int = 1

    def __post_init__(self) -> None:
        if self.max_consecutive_blanks < 0:
            raise ValueError("max_consecutive_blanks must be >= 0")

    def is_active(self) -> bool:
        return self.enabled and (
            self.strip_blank_lines or self.strip_inline_whitespace
        )


def _is_blank(line: LogLine) -> bool:
    return line.raw.strip() == ""


def trim_lines(
    lines: Iterable[LogLine],
    opts: TrimOptions | None = None,
) -> Iterator[LogLine]:
    if opts is None or not opts.is_active():
        yield from lines
        return

    consecutive_blanks = 0
    buffer: list[LogLine] = []

    for line in lines:
        if opts.strip_inline_whitespace:
            stripped = line.raw.strip()
            if stripped != line.raw:
                line = LogLine(
                    raw=stripped,
                    timestamp=line.timestamp,
                    level=line.level,
                    message=line.message.strip() if line.message else line.message,
                    extra=line.extra,
                )

        if _is_blank(line):
            if opts.strip_blank_lines:
                consecutive_blanks += 1
                if consecutive_blanks <= opts.max_consecutive_blanks:
                    buffer.append(line)
            else:
                consecutive_blanks += 1
                if consecutive_blanks <= opts.max_consecutive_blanks:
                    yield line
        else:
            if buffer:
                yield from buffer
                buffer.clear()
            consecutive_blanks = 0
            yield line
