"""Output sink abstraction for writing filtered log lines."""

from __future__ import annotations

import gzip
import sys
from pathlib import Path
from typing import Iterable, Optional, TextIO

from logslice.formatter import FormatOptions, format_line
from logslice.highlighter import HighlightOptions, apply_highlighting
from logslice.parser import LogLine


def _open_output(path: Optional[Path]) -> TextIO:
    """Return a writable text stream for *path*, or stdout when None."""
    if path is None:
        return sys.stdout
    if path.suffix == ".gz":
        # gzip.open returns a binary stream; wrap it
        import io
        return io.TextIOWrapper(gzip.open(path, "wb"))  # type: ignore[return-value]
    return path.open("w", encoding="utf-8")


def write_lines(
    lines: Iterable[LogLine],
    dest: Optional[Path] = None,
    fmt_opts: Optional[FormatOptions] = None,
    hl_opts: Optional[HighlightOptions] = None,
    count_only: bool = False,
) -> int:
    """Write *lines* to *dest* (or stdout) and return the number of lines written.

    Parameters
    ----------
    lines:      iterable of parsed log lines.
    dest:       output file path; ``None`` means stdout.
    fmt_opts:   formatting options passed to :func:`format_line`.
    hl_opts:    highlighting options; only applied when writing to a TTY.
    count_only: if ``True`` consume the iterable and return the count without
                writing anything.
    """
    fmt_opts = fmt_opts or FormatOptions()
    hl_opts = hl_opts or HighlightOptions()

    total = 0
    if count_only:
        for _ in lines:
            total += 1
        return total

    stream = _open_output(dest)
    try:
        use_color = hl_opts.colorize_levels and getattr(stream, "isatty", lambda: False)()
        for line in lines:
            text = format_line(line, fmt_opts)
            if use_color or hl_opts.highlight_patterns:
                text = apply_highlighting(text, line.level, hl_opts)
            stream.write(text + "\n")
            total += 1
    finally:
        if stream is not sys.stdout:
            stream.close()

    return total
