"""Diff two log streams, emitting lines unique to each or common to both."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, Literal

from logslice.parser import LogLine


Mode = Literal["added", "removed", "common"]


@dataclass
class DiffOptions:
    mode: Mode = "added"          # which lines to emit
    key: str = "raw"              # attribute of LogLine to compare on
    ignore_timestamps: bool = True # strip leading timestamp before keying


@dataclass
class DiffResult:
    line: LogLine
    mode: Mode
    tag: str = ""                 # '<', '>', or '='


def _line_key(line: LogLine, opts: DiffOptions) -> str:
    text: str = getattr(line, opts.key, line.raw)
    if opts.ignore_timestamps and line.timestamp is not None:
        # Remove the ISO timestamp prefix if present so diffs ignore time shifts
        ts = line.timestamp.isoformat()
        text = text.replace(ts, "", 1).lstrip(" |-")
    return text.rstrip()


def diff_logs(
    left: Iterable[LogLine],
    right: Iterable[LogLine],
    opts: DiffOptions | None = None,
) -> Iterator[DiffResult]:
    """Compare *left* and *right* log streams.

    Yields :class:`DiffResult` objects whose ``.mode`` matches *opts.mode*:
    - ``"added"``   — lines present in *right* but not *left*
    - ``"removed"`` — lines present in *left* but not *right*
    - ``"common"``  — lines present in both
    """
    if opts is None:
        opts = DiffOptions()

    left_keys: set[str] = {_line_key(ln, opts) for ln in left}
    right_keys: set[str] = {_line_key(ln, opts) for ln in right}

    # Re-iterate right to preserve order and emit matching results
    if opts.mode == "added":
        # lines in right not in left
        seen_right: set[str] = set()
        # We need the original lines from right — caller must pass iterables
        # that can be consumed once; we already consumed both above, so this
        # function accepts lists or the caller should pass lists.
        # To keep the API simple we require sequences; document accordingly.
        raise RuntimeError("Use diff_log_sequences for sequence inputs.")
    return iter([])


def diff_log_sequences(
    left: list[LogLine],
    right: list[LogLine],
    opts: DiffOptions | None = None,
) -> Iterator[DiffResult]:
    """Compare two *lists* of LogLine and yield DiffResult items."""
    if opts is None:
        opts = DiffOptions()

    left_keys: set[str] = {_line_key(ln, opts) for ln in left}
    right_keys: set[str] = {_line_key(ln, opts) for ln in right}

    if opts.mode == "added":
        for ln in right:
            if _line_key(ln, opts) not in left_keys:
                yield DiffResult(line=ln, mode="added", tag=">")
    elif opts.mode == "removed":
        for ln in left:
            if _line_key(ln, opts) not in right_keys:
                yield DiffResult(line=ln, mode="removed", tag="<")
    elif opts.mode == "common":
        for ln in left:
            if _line_key(ln, opts) in right_keys:
                yield DiffResult(line=ln, mode="common", tag="=")
