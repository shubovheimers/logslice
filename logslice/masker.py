"""Field-level masking for sensitive log data beyond simple regex redaction."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine

_BUILTIN_MASKS: dict[str, str] = {
    "token": r"(?i)(token|api[_-]?key|secret)[=:\s]+\S+",
    "password": r"(?i)(password|passwd|pwd)[=:\s]+\S+",
    "jwt": r"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
    "credit_card": r"\b(?:\d[ -]?){13,16}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
}


@dataclass
class MaskOptions:
    """Options controlling which built-in and custom masks to apply."""

    enabled: bool = False
    builtins: list[str] = field(default_factory=list)
    custom_patterns: list[str] = field(default_factory=list)
    placeholder: str = "[MASKED]"

    def __post_init__(self) -> None:
        unknown = set(self.builtins) - set(_BUILTIN_MASKS)
        if unknown:
            raise ValueError(f"Unknown built-in mask(s): {', '.join(sorted(unknown))}")

    def is_active(self) -> bool:
        return self.enabled and bool(self.builtins or self.custom_patterns)


def _compile(opts: MaskOptions):
    import re

    patterns = [_BUILTIN_MASKS[b] for b in opts.builtins]
    patterns.extend(opts.custom_patterns)
    return [re.compile(p) for p in patterns]


def mask_text(text: str, opts: MaskOptions) -> str:
    """Return *text* with all matching patterns replaced by the placeholder."""
    if not opts.is_active():
        return text
    for rx in _compile(opts):
        text = rx.sub(opts.placeholder, text)
    return text


def mask_line(line: LogLine, opts: MaskOptions) -> LogLine:
    """Return a new *LogLine* with its raw text masked."""
    if not opts.is_active():
        return line
    new_raw = mask_text(line.raw, opts)
    return LogLine(
        raw=new_raw,
        timestamp=line.timestamp,
        level=line.level,
        message=mask_text(line.message, opts) if line.message else line.message,
        extra=line.extra,
    )


def apply_masking(
    lines: Iterable[LogLine],
    opts: Optional[MaskOptions],
) -> Iterator[LogLine]:
    """Yield lines with masking applied when *opts* is active."""
    if opts is None or not opts.is_active():
        yield from lines
        return
    for line in lines:
        yield mask_line(line, opts)
