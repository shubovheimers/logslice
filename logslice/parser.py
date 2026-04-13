"""Log line parser for extracting timestamps and log levels."""

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

# Common log timestamp patterns
TIMESTAMP_PATTERNS = [
    # ISO 8601: 2024-01-15T13:45:00 or 2024-01-15 13:45:00
    r"(?P<ts>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)",
    # Common syslog: Jan 15 13:45:00
    r"(?P<ts>[A-Z][a-z]{2}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2})",
    # Apache/nginx: 15/Jan/2024:13:45:00
    r"(?P<ts>\d{2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2})",
]

LOG_LEVEL_PATTERN = re.compile(
    r"\b(?P<level>DEBUG|INFO|NOTICE|WARNING|WARN|ERROR|CRITICAL|FATAL|TRACE)\b",
    re.IGNORECASE,
)

COMPILED_TS_PATTERNS = [re.compile(p) for p in TIMESTAMP_PATTERNS]

TS_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M:%S.%f",
    "%b %d %H:%M:%S",
    "%d/%b/%Y:%H:%M:%S",
]


@dataclass
class LogLine:
    raw: str
    timestamp: Optional[datetime]
    level: Optional[str]
    message: str


def parse_timestamp(text: str) -> Optional[datetime]:
    """Attempt to parse a timestamp string into a datetime object."""
    clean = re.sub(r"Z$", "", text).strip()
    clean = re.sub(r"[+-]\d{2}:?\d{2}$", "", clean).strip()
    for fmt in TS_FORMATS:
        try:
            return datetime.strptime(clean, fmt)
        except ValueError:
            continue
    return None


def parse_line(line: str) -> LogLine:
    """Parse a single log line into a LogLine dataclass."""
    raw = line.rstrip("\n")
    timestamp: Optional[datetime] = None

    for pattern in COMPILED_TS_PATTERNS:
        match = pattern.search(raw)
        if match:
            timestamp = parse_timestamp(match.group("ts"))
            if timestamp:
                break

    level_match = LOG_LEVEL_PATTERN.search(raw)
    level = level_match.group("level").upper() if level_match else None

    return LogLine(raw=raw, timestamp=timestamp, level=level, message=raw)
