"""Field extractor — pull named fields from log line text via regex."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, List, Optional

from logslice.parser import LogLine


@dataclass
class ExtractOptions:
    """Configuration for field extraction."""
    patterns: List[str] = field(default_factory=list)
    prefix: str = "field_"
    overwrite: bool = False

    def __post_init__(self) -> None:
        if self.prefix is None:
            raise ValueError("prefix must not be None")

    def enabled(self) -> bool:
        return bool(self.patterns)

    def _compile(self) -> List[re.Pattern]:
        compiled = []
        for p in self.patterns:
            try:
                compiled.append(re.compile(p))
            except re.error as exc:
                raise ValueError(f"Invalid extraction pattern {p!r}: {exc}") from exc
        return compiled


def extract_fields(text: str, patterns: List[re.Pattern]) -> Dict[str, str]:
    """Return a dict of named groups captured from *text* by any of *patterns*."""
    result: Dict[str, str] = {}
    for pat in patterns:
        m = pat.search(text)
        if m:
            result.update(m.groupdict())
    return result


def extract_lines(
    lines: Iterable[LogLine],
    opts: Optional[ExtractOptions],
) -> Iterator[LogLine]:
    """Yield lines, annotating each with extracted fields in ``extra``."""
    if opts is None or not opts.enabled():
        yield from lines
        return

    compiled = opts._compile()
    for line in lines:
        extracted = extract_fields(line.raw, compiled)
        if extracted:
            extra = dict(line.extra) if line.extra else {}
            for k, v in extracted.items():
                key = f"{opts.prefix}{k}" if opts.prefix else k
                if overwrite_ok(opts, key, extra):
                    extra[key] = v
            yield LogLine(
                raw=line.raw,
                timestamp=line.timestamp,
                level=line.level,
                message=line.message,
                extra=extra,
            )
        else:
            yield line


def overwrite_ok(opts: ExtractOptions, key: str, extra: dict) -> bool:
    return opts.overwrite or key not in extra
