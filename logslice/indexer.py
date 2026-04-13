"""Byte-offset index for fast seeking within large log files."""

from __future__ import annotations

import gzip
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from logslice.parser import parse_line


@dataclass
class IndexEntry:
    offset: int
    timestamp: Optional[datetime]
    line_number: int


@dataclass
class LogIndex:
    source_path: str
    source_mtime: float
    entries: List[IndexEntry] = field(default_factory=list)

    def is_valid_for(self, path: str) -> bool:
        """Return True if the index matches the current file mtime."""
        try:
            return os.path.getmtime(path) == self.source_mtime
        except OSError:
            return False

    def find_offset(self, target: datetime) -> int:
        """Binary search for the first offset whose timestamp >= target."""
        lo, hi = 0, len(self.entries) - 1
        result = 0
        while lo <= hi:
            mid = (lo + hi) // 2
            ts = self.entries[mid].timestamp
            if ts is None or ts < target:
                lo = mid + 1
            else:
                result = self.entries[mid].offset
                hi = mid - 1
        return result


def build_index(path: str, sample_every: int = 100) -> LogIndex:
    """Build a byte-offset index by sampling every Nth line."""
    mtime = os.path.getmtime(path)
    entries: List[IndexEntry] = []
    opener = gzip.open if path.endswith(".gz") else open
    line_number = 0
    with opener(path, "rb") as fh:  # type: ignore[call-overload]
        while True:
            offset = fh.tell()
            raw = fh.readline()
            if not raw:
                break
            if line_number % sample_every == 0:
                parsed = parse_line(raw.decode("utf-8", errors="replace"))
                entries.append(IndexEntry(offset=offset, timestamp=parsed.timestamp, line_number=line_number))
            line_number += 1
    return LogIndex(source_path=path, source_mtime=mtime, entries=entries)


def save_index(index: LogIndex, index_path: str) -> None:
    """Persist a LogIndex to a JSON file."""
    data = {
        "source_path": index.source_path,
        "source_mtime": index.source_mtime,
        "entries": [
            {
                "offset": e.offset,
                "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                "line_number": e.line_number,
            }
            for e in index.entries
        ],
    }
    Path(index_path).write_text(json.dumps(data, indent=2))


def load_index(index_path: str) -> LogIndex:
    """Load a LogIndex from a JSON file."""
    data = json.loads(Path(index_path).read_text())
    entries = [
        IndexEntry(
            offset=e["offset"],
            timestamp=datetime.fromisoformat(e["timestamp"]) if e["timestamp"] else None,
            line_number=e["line_number"],
        )
        for e in data["entries"]
    ]
    return LogIndex(source_path=data["source_path"], source_mtime=data["source_mtime"], entries=entries)
