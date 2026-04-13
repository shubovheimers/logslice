"""Line truncation utilities for controlling output width."""

from dataclasses import dataclass, field
from typing import Optional

from logslice.parser import LogLine


_ELLIPSIS = "..."
_ELLIPSIS_LEN = len(_ELLIPSIS)


@dataclass
class TruncateOptions:
    enabled: bool = False
    max_width: int = 200
    ellipsis: str = _ELLIPSIS
    truncate_from: str = "end"  # "end" or "start"


def truncate_text(text: str, opts: TruncateOptions) -> str:
    """Truncate a single string to fit within opts.max_width characters."""
    if not opts.enabled:
        return text
    if len(text) <= opts.max_width:
        return text

    ell = opts.ellipsis
    ell_len = len(ell)
    keep = opts.max_width - ell_len
    if keep <= 0:
        return ell[: opts.max_width]

    if opts.truncate_from == "start":
        return ell + text[-keep:]
    return text[:keep] + ell


def truncate_line(line: LogLine, opts: Optional[TruncateOptions]) -> LogLine:
    """Return a new LogLine with raw text truncated according to opts."""
    if opts is None or not opts.enabled:
        return line
    new_raw = truncate_text(line.raw, opts)
    return LogLine(
        raw=new_raw,
        timestamp=line.timestamp,
        level=line.level,
        message=line.message,
        extra=line.extra,
    )


def apply_truncation(lines, opts: Optional[TruncateOptions]):
    """Yield LogLine objects with truncated raw text."""
    if opts is None or not opts.enabled:
        yield from lines
        return
    for line in lines:
        yield truncate_line(line, opts)
