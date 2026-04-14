"""Normalize log line text: strip whitespace, collapse runs, fix encoding."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, Iterator

from logslice.parser import LogLine


@dataclass
class NormalizeOptions:
    enabled: bool = False
    strip_ansi: bool = True
    collapse_whitespace: bool = False
    unicode_normalize: str = ""  # e.g. "NFC", "NFD", "NFKC", "NFKD"
    max_line_length: int = 0  # 0 = no limit


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[mGKHF]")
_WS_RE = re.compile(r"[ \t]+")


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from *text*."""
    return _ANSI_RE.sub("", text)


def collapse_whitespace(text: str) -> str:
    """Replace runs of spaces/tabs with a single space and strip edges."""
    return _WS_RE.sub(" ", text).strip()


def normalize_text(text: str, opts: NormalizeOptions) -> str:
    """Apply all enabled normalization steps to *text*."""
    if opts.strip_ansi:
        text = strip_ansi(text)
    if opts.unicode_normalize:
        text = unicodedata.normalize(opts.unicode_normalize, text)
    if opts.collapse_whitespace:
        text = collapse_whitespace(text)
    if opts.max_line_length and len(text) > opts.max_line_length:
        text = text[: opts.max_line_length]
    return text


def normalize_line(line: LogLine, opts: NormalizeOptions) -> LogLine:
    """Return a new *LogLine* with its raw text normalized."""
    new_raw = normalize_text(line.raw, opts)
    return LogLine(
        raw=new_raw,
        timestamp=line.timestamp,
        level=line.level,
        message=normalize_text(line.message, opts) if line.message else line.message,
        extra=line.extra,
    )


def apply_normalization(
    lines: Iterable[LogLine],
    opts: NormalizeOptions | None = None,
) -> Iterator[LogLine]:
    """Yield lines, applying normalization when *opts* is active."""
    if opts is None or not opts.enabled:
        yield from lines
        return
    for line in lines:
        yield normalize_line(line, opts)
