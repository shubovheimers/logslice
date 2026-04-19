"""Field renaming for log lines."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class RenameOptions:
    """Options for renaming fields in log line extras."""
    mapping: Dict[str, str] = field(default_factory=dict)
    rename_level: Optional[str] = None
    rename_source: Optional[str] = None
    strip_prefix: Optional[str] = None
    strip_suffix: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.mapping, dict):
            raise TypeError("mapping must be a dict")

    def enabled(self) -> bool:
        return bool(
            self.mapping
            or self.rename_level
            or self.rename_source
            or self.strip_prefix
            or self.strip_suffix
        )


def _rename_key(key: str, opts: RenameOptions) -> str:
    result = opts.mapping.get(key, key)
    if opts.strip_prefix and result.startswith(opts.strip_prefix):
        result = result[len(opts.strip_prefix):]
    if opts.strip_suffix and result.endswith(opts.strip_suffix):
        result = result[: -len(opts.strip_suffix)]
    return result


def rename_lines(
    lines: Iterable[LogLine], opts: Optional[RenameOptions]
) -> Iterator[LogLine]:
    if opts is None or not opts.enabled():
        yield from lines
        return

    for ln in lines:
        new_extra = {_rename_key(k, opts): v for k, v in ln.extra.items()}
        new_level = opts.rename_level if ln.level is not None else ln.level
        new_source = opts.rename_source if ln.source is not None else ln.source
        yield LogLine(
            raw=ln.raw,
            timestamp=ln.timestamp,
            level=new_level if opts.rename_level else ln.level,
            message=ln.message,
            source=new_source if opts.rename_source else ln.source,
            extra=new_extra,
        )
