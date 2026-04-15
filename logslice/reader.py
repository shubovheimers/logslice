"""Streaming log file reader with minimal memory overhead."""

import gzip
import bz2
import os
from typing import Iterator, Optional

from logslice.parser import LogLine, parse_line


SUPPORTED_EXTENSIONS = {
    ".gz": gzip.open,
    ".bz2": bz2.open,
}


def open_log_file(path: str, encoding: str = "utf-8"):
    """Open a log file, handling compressed formats transparently."""
    ext = os.path.splitext(path)[1].lower()
    opener = SUPPORTED_EXTENSIONS.get(ext, open)
    if opener is open:
        return opener(path, "r", encoding=encoding)
    return opener(path, "rt", encoding=encoding)


def iter_lines(
    path: str,
    encoding: str = "utf-8",
    skip_unparseable: bool = True,
) -> Iterator[LogLine]:
    """Yield parsed LogLine objects from a log file one at a time.

    Args:
        path: Path to the log file (plain, .gz, or .bz2).
        encoding: File encoding (default utf-8).
        skip_unparseable: If True, lines that cannot be parsed are silently
            skipped; if False, they are yielded with timestamp=None.
    """
    with open_log_file(path, encoding=encoding) as fh:
        for raw in fh:
            line = parse_line(raw.rstrip("\n"))
            if line is None:
                continue
            if line.timestamp is None and skip_unparseable:
                continue
            yield line


def iter_lines_raw(
    path: str,
    encoding: str = "utf-8",
) -> Iterator[str]:
    """Yield raw text lines from a log file without parsing."""
    with open_log_file(path, encoding=encoding) as fh:
        for raw in fh:
            yield raw.rstrip("\n")


def count_lines(path: str, encoding: str = "utf-8") -> int:
    """Return the total number of lines in a log file."""
    total = 0
    with open_log_file(path, encoding=encoding) as fh:
        for _ in fh:
            total += 1
    return total


def is_supported_file(path: str) -> bool:
    """Return True if the file extension is a supported log format.

    Accepts plain text files (no extension or any non-compressed extension)
    as well as explicitly supported compressed formats (.gz, .bz2).

    Args:
        path: Path to the file to check.
    """
    ext = os.path.splitext(path)[1].lower()
    # Compressed formats must be explicitly supported; plain text is always ok.
    if ext in (".gz", ".bz2"):
        return ext in SUPPORTED_EXTENSIONS
    return True
