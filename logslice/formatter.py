"""Output formatting utilities for logslice."""

from dataclasses import dataclass
from typing import Optional, List
from logslice.parser import LogLine


LEVEL_COLORS = {
    "DEBUG": "\033[36m",    # Cyan
    "INFO": "\033[32m",     # Green
    "WARNING": "\033[33m",  # Yellow
    "WARN": "\033[33m",     # Yellow
    "ERROR": "\033[31m",    # Red
    "CRITICAL": "\033[35m", # Magenta
    "FATAL": "\033[35m",    # Magenta
}
RESET = "\033[0m"


@dataclass
class FormatOptions:
    colorize: bool = False
    show_line_numbers: bool = False
    timestamp_format: Optional[str] = None
    fields: Optional[List[str]] = None  # e.g. ["timestamp", "level", "message"]


def format_line(line: LogLine, opts: FormatOptions, line_number: Optional[int] = None) -> str:
    """Format a single LogLine according to FormatOptions."""
    parts = []

    if opts.show_line_numbers and line_number is not None:
        parts.append(f"{line_number:>6}:")

    if opts.fields:
        selected = []
        for field in opts.fields:
            if field == "timestamp" and line.timestamp:
                ts = (
                    line.timestamp.strftime(opts.timestamp_format)
                    if opts.timestamp_format
                    else line.timestamp.isoformat()
                )
                selected.append(ts)
            elif field == "level" and line.level:
                selected.append(line.level)
            elif field == "message":
                selected.append(line.message)
        text = " | ".join(selected)
    else:
        text = line.raw.rstrip()

    if opts.colorize and line.level:
        color = LEVEL_COLORS.get(line.level.upper(), "")
        if color:
            text = f"{color}{text}{RESET}"

    parts.append(text)
    return " ".join(parts)


def format_lines(
    lines: List[LogLine],
    opts: FormatOptions,
    start_number: int = 1,
) -> List[str]:
    """Format a list of LogLines, optionally with line numbers."""
    result = []
    for i, line in enumerate(lines):
        number = start_number + i if opts.show_line_numbers else None
        result.append(format_line(line, opts, line_number=number))
    return result
