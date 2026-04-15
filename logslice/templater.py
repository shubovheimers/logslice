"""Output line formatting via user-defined templates."""
from __future__ import annotations

import re
import string
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine

_FIELD_RE = re.compile(r"\{(\w+)(?::(.*?))?\}")


@dataclass
class TemplateOptions:
    """Configuration for the templater."""

    template: Optional[str] = None
    missing: str = "-"

    def enabled(self) -> bool:
        return bool(self.template)


def _safe_format(template: str, line: LogLine, missing: str) -> str:
    """Render *template* against *line*, substituting *missing* for absent fields."""
    result = []
    last = 0
    for m in _FIELD_RE.finditer(template):
        result.append(template[last : m.start()])
        key = m.group(1)
        fmt_spec = m.group(2) or ""
        value = _resolve(line, key, missing)
        if fmt_spec:
            try:
                value = format(value, fmt_spec)
            except (ValueError, TypeError):
                value = str(value)
        else:
            value = str(value)
        result.append(value)
        last = m.end()
    result.append(template[last:])
    return "".join(result)


def _resolve(line: LogLine, key: str, missing: str) -> object:
    """Return the value for *key* from *line*, falling back to extra dict or *missing*."""
    direct = {
        "timestamp": line.timestamp,
        "level": line.level,
        "message": line.message,
        "raw": line.raw,
        "source": line.source,
        "lineno": line.lineno,
    }
    if key in direct:
        v = direct[key]
        return v if v is not None else missing
    if line.extra and key in line.extra:
        return line.extra[key]
    return missing


def apply_template(line: LogLine, opts: TemplateOptions) -> str:
    """Return the formatted string for *line* using *opts.template*."""
    if not opts.enabled():
        return line.raw
    return _safe_format(opts.template, line, opts.missing)  # type: ignore[arg-type]


def template_lines(
    lines: Iterable[LogLine], opts: Optional[TemplateOptions]
) -> Iterator[str]:
    """Yield formatted strings for each line in *lines*."""
    if opts is None or not opts.enabled():
        for ln in lines:
            yield ln.raw
        return
    for ln in lines:
        yield apply_template(ln, opts)
