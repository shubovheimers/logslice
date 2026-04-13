"""Redaction support for masking sensitive patterns in log lines."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogLine

# Built-in patterns for common sensitive
BUILTIN_PATTERNS: dict[str, str] = {
    "ipv4": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    "email": r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    "jwt": r"eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+",
    "credit_card": r"\b(?:\d[ \-]?){13,16}\b",
    "uuid": r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
}

DEFAULT_MASK = "[REDACTED]"


@dataclass
class RedactOptions:
    """Configuration for the redaction step."""

    enabled: bool = False
    # Named built-in patterns to activate, eipv4", "email"]
    builtins: Listfactory=list)
    # Raw regex patterns supplied by the user
    patterns: Listfactory=list)
    mask: str = DEFAULT_MASK

    def is_active(self) -> bool:
        return self.enabled and bool(self.builtins or self.patterns)


def _compile_patterns(opts: RedactOptions) -> List[re.Pattern]:
    """Return compiled regex objects from options."""
    compiled: List[re.Pattern] = []
    for name in opts.builtins:
        if name in BUILTIN_PATTERNS:
            compiled.append(re.compile(BUILTIN_PATTERNS[name]))
    for raw in opts.patterns:
        compiled.append(re.compile(raw))
    return compiled


def redact_text(text: str, patterns: List[re.Pattern], mask: str = DEFAULT_MASK) -> str:
    """Replace all matches for every pattern in *text* with *mask*."""
    for pattern in patterns:
        text = pattern.sub(mask, text)
    return text


def redact_line(line: LogLine, patterns: List[re.Pattern], mask: str = DEFAULT_MASK) -> LogLine:
    """Return a new LogLine with sensitive data replaced in the raw text."""
    new_raw = redact_text(line.raw, patterns, mask)
    return LogLine(
        raw=new_raw,
        timestamp=line.timestamp,
        level=line.level,
        message=redact_text(line.message, patterns, mask) if line.message else line.message,
    )


def apply_redaction(
    lines: Iterable[LogLine],
    opts: Optional[RedactOptions],
) -> Iterator[LogLine]:
    """Yield lines, optionally redacting sensitive content."""
    if opts is None or not opts.is_active():
        yield from lines
        return

    patterns = _compile_patterns(opts)
    for line in lines:
        yield redact_line(line, patterns, opts.mask)
