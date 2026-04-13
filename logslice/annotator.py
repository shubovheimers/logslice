"""Line annotation: attach sequence numbers, source tags, or custom labels to log lines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Optional

from logslice.parser import LogLine


@dataclass
class AnnotateOptions:
    """Configuration for line annotation."""
    sequence: bool = False          # prepend a global sequence number
    source_tag: Optional[str] = None  # tag every line with a source label (e.g. filename)
    labels: dict[str, str] = field(default_factory=dict)  # arbitrary key→value metadata

    def enabled(self) -> bool:
        return self.sequence or bool(self.source_tag) or bool(self.labels)


def _apply_sequence(line: LogLine, n: int) -> LogLine:
    """Return a new LogLine whose raw text is prefixed with the sequence number."""
    annotated_raw = f"[{n}] {line.raw}"
    return LogLine(
        raw=annotated_raw,
        timestamp=line.timestamp,
        level=line.level,
        message=line.message,
    )


def _apply_source_tag(line: LogLine, tag: str) -> LogLine:
    """Return a new LogLine whose raw text is prefixed with a source tag."""
    annotated_raw = f"[{tag}] {line.raw}"
    return LogLine(
        raw=annotated_raw,
        timestamp=line.timestamp,
        level=line.level,
        message=line.message,
    )


def _apply_labels(line: LogLine, labels: dict[str, str]) -> LogLine:
    """Append key=value pairs to the raw text of a line."""
    suffix = " ".join(f"{k}={v}" for k, v in sorted(labels.items()))
    annotated_raw = f"{line.raw} {suffix}"
    return LogLine(
        raw=annotated_raw,
        timestamp=line.timestamp,
        level=line.level,
        message=line.message,
    )


def annotate_lines(
    lines: Iterable[LogLine],
    opts: Optional[AnnotateOptions] = None,
) -> Iterator[LogLine]:
    """Yield lines with annotations applied according to *opts*.

    Annotation order is: labels first, then source tag, then sequence number.
    This ensures the sequence number always appears as the outermost (leftmost)
    prefix, making it easy to identify line positions at a glance.

    If *opts* is ``None`` or not enabled, lines are yielded unchanged.
    """
    if opts is None or not opts.enabled():
        yield from lines
        return

    for seq, line in enumerate(lines, start=1):
        if opts.labels:
            line = _apply_labels(line, opts.labels)
        if opts.source_tag:
            line = _apply_source_tag(line, opts.source_tag)
        if opts.sequence:
            line = _apply_sequence(line, seq)
        yield line
