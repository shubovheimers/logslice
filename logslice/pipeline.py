"""High-level pipeline that wires reader → filter → output together."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from logslice.filter import apply_filters
from logslice.formatter import FormatOptions
from logslice.highlighter import HighlightOptions
from logslice.output import write_lines
from logslice.reader import iter_lines


@dataclass
class PipelineConfig:
    """All settings needed to execute a single logslice run."""

    input_path: Path
    output_path: Optional[Path] = None

    # time filters
    start: Optional[datetime] = None
    end: Optional[datetime] = None

    # content filters
    levels: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)

    # output
    fmt_opts: FormatOptions = field(default_factory=FormatOptions)
    hl_opts: HighlightOptions = field(default_factory=HighlightOptions)
    count_only: bool = False


def run_pipeline(cfg: PipelineConfig) -> int:
    """Execute the full read → filter → write pipeline.

    Returns the number of lines that passed all filters.
    """
    raw_lines = iter_lines(cfg.input_path)

    filtered = apply_filters(
        raw_lines,
        start=cfg.start,
        end=cfg.end,
        levels=cfg.levels or None,
        patterns=cfg.patterns or None,
    )

    return write_lines(
        filtered,
        dest=cfg.output_path,
        fmt_opts=cfg.fmt_opts,
        hl_opts=cfg.hl_opts,
        count_only=cfg.count_only,
    )
