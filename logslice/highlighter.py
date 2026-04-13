"""Terminal color highlighting for log output."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ANSI escape codes
RESET = "\033[0m"
BOLD = "\033[1m"

LEVEL_COLORS: Dict[str, str] = {
    "DEBUG": "\033[36m",    # cyan
    "INFO": "\033[32m",     # green
    "WARNING": "\033[33m",  # yellow
    "WARN": "\033[33m",     # yellow
    "ERROR": "\033[31m",    # red
    "CRITICAL": "\033[35m", # magenta
    "FATAL": "\033[35m",    # magenta
}

PATTERN_COLOR = "\033[43m\033[30m"  # black on yellow background


@dataclass
class HighlightOptions:
    colorize_levels: bool = True
    highlight_patterns: List[str] = field(default_factory=list)
    bold_timestamps: bool = False


def colorize_level(text: str, level: Optional[str]) -> str:
    """Wrap the level token in the appropriate ANSI color."""
    if not level:
        return text
    color = LEVEL_COLORS.get(level.upper())
    if not color:
        return text
    return text.replace(level, f"{color}{BOLD}{level}{RESET}", 1)


def highlight_pattern(text: str, pattern: str) -> str:
    """Highlight all occurrences of *pattern* (regex) in *text*."""
    try:
        return re.sub(
            pattern,
            lambda m: f"{PATTERN_COLOR}{m.group()}{RESET}",
            text,
        )
    except re.error:
        return text


def apply_highlighting(text: str, level: Optional[str], opts: HighlightOptions) -> str:
    """Apply all requested highlighting to a single log line string."""
    if opts.colorize_levels and level:
        text = colorize_level(text, level)
    for pat in opts.highlight_patterns:
        text = highlight_pattern(text, pat)
    return text
