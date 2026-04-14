"""Export filtered log lines to various output formats (JSON, CSV, NDJSON)."""

from __future__ import annotations

import csv
import io
import json
from dataclasses import dataclass, field
from typing import Iterable, Iterator, Literal, Optional

from logslice.parser import LogLine

ExportFormat = Literal["raw", "json", "ndjson", "csv"]

_CSV_FIELDS = ["timestamp", "level", "text"]


@dataclass
class ExportOptions:
    """Configuration for the log exporter."""

    format: ExportFormat = "raw"
    # For JSON array output: pretty-print with indentation
    pretty: bool = False
    # Extra static fields to inject into every exported record
    extra_fields: dict = field(default_factory=dict)

    def is_structured(self) -> bool:
        """Return True when the format produces structured (non-raw) output."""
        return self.format in ("json", "ndjson", "csv")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _line_to_record(line: LogLine, extra: dict) -> dict:
    """Convert a LogLine to a plain dict suitable for serialisation."""
    record: dict = {
        "timestamp": line.timestamp.isoformat() if line.timestamp else None,
        "level": line.level,
        "text": line.text,
    }
    if extra:
        record.update(extra)
    return record


# ---------------------------------------------------------------------------
# Per-format serialisers
# ---------------------------------------------------------------------------

def export_raw(lines: Iterable[LogLine]) -> Iterator[str]:
    """Yield the original raw text for each log line."""
    for line in lines:
        yield line.raw


def export_ndjson(lines: Iterable[LogLine], extra: dict) -> Iterator[str]:
    """Yield one JSON object per line (newline-delimited JSON)."""
    for line in lines:
        record = _line_to_record(line, extra)
        yield json.dumps(record, ensure_ascii=False)


def export_json(lines: Iterable[LogLine], extra: dict, pretty: bool) -> Iterator[str]:
    """Yield a single JSON array containing all records.

    The array is streamed in chunks so that the caller can write it
    incrementally without buffering the entire input.
    """
    indent = 2 if pretty else None
    separator = ",\n" if pretty else ", "
    first = True
    yield "[\n" if pretty else "["
    for line in lines:
        record = _line_to_record(line, extra)
        serialised = json.dumps(record, ensure_ascii=False, indent=indent)
        if first:
            first = False
        else:
            yield separator
        yield serialised
    yield "\n]" if pretty else "]"


def export_csv(lines: Iterable[LogLine], extra: dict) -> Iterator[str]:
    """Yield CSV rows (including a header row) for each log line."""
    all_fields = _CSV_FIELDS + [k for k in extra if k not in _CSV_FIELDS]
    buf = io.StringIO()
    writer = csv.DictWriter(
        buf,
        fieldnames=all_fields,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    yield buf.getvalue()

    for line in lines:
        buf = io.StringIO()
        writer = csv.DictWriter(
            buf,
            fieldnames=all_fields,
            extrasaction="ignore",
            lineterminator="\n",
        )
        record = _line_to_record(line, extra)
        writer.writerow(record)
        yield buf.getvalue()


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def export_lines(
    lines: Iterable[LogLine],
    opts: Optional[ExportOptions] = None,
) -> Iterator[str]:
    """Serialise *lines* according to *opts* and yield output strings.

    Each yielded string is a complete unit (row, object, or chunk) that the
    caller can write directly to a file or stdout.  A trailing newline is
    **not** added here — callers should use ``'\\n'.join(...)`` or write
    each chunk followed by a newline as appropriate for the format.
    """
    if opts is None:
        opts = ExportOptions()

    fmt = opts.format
    extra = opts.extra_fields or {}

    if fmt == "raw":
        yield from export_raw(lines)
    elif fmt == "ndjson":
        yield from export_ndjson(lines, extra)
    elif fmt == "json":
        yield from export_json(lines, extra, opts.pretty)
    elif fmt == "csv":
        yield from export_csv(lines, extra)
    else:
        raise ValueError(f"Unsupported export format: {fmt!r}")
