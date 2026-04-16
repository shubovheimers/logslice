"""Zip two log streams together, interleaving lines by timestamp."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogLine


@dataclass
class ZipOptions:
    """Options for zipping two log streams."""
    fill_missing: bool = False          # emit a placeholder when one stream is exhausted
    fill_text: str = "<no entry>"
    tag_a: str = "A"                    # label injected into extra['_zip_source']
    tag_b: str = "B"
    strict_order: bool = True           # sort by timestamp when both available

    def enabled(self) -> bool:
        return True  # always meaningful once instantiated


def _ts_key(line: LogLine):
    """Sort key: lines without a timestamp sort last."""
    return (0, line.timestamp) if line.timestamp is not None else (1, None)


def _tag(line: LogLine, tag: str) -> LogLine:
    extra = dict(line.extra or {})
    extra["_zip_source"] = tag
    return LogLine(
        raw=line.raw,
        timestamp=line.timestamp,
        level=line.level,
        message=line.message,
        extra=extra,
    )


def _placeholder(tag: str, fill_text: str) -> LogLine:
    return LogLine(raw=fill_text, timestamp=None, level=None, message=fill_text,
                   extra={"_zip_source": tag})


def zip_logs(
    stream_a: Iterable[LogLine],
    stream_b: Iterable[LogLine],
    opts: Optional[ZipOptions] = None,
) -> Iterator[LogLine]:
    """Interleave two log streams, optionally ordered by timestamp."""
    if opts is None:
        opts = ZipOptions()

    iter_a = iter(stream_a)
    iter_b = iter(stream_b)

    sentinel = object()
    buf_a: object = sentinel
    buf_b: object = sentinel

    def _advance_a():
        nonlocal buf_a
        buf_a = next(iter_a, sentinel)

    def _advance_b():
        nonlocal buf_b
        buf_b = next(iter_b, sentinel)

    _advance_a()
    _advance_b()

    while buf_a is not sentinel or buf_b is not sentinel:
        a_done = buf_a is sentinel
        b_done = buf_b is sentinel

        if a_done and b_done:
            break
        elif a_done:
            if opts.fill_missing:
                yield _tag(_placeholder(opts.tag_a, opts.fill_text), opts.tag_a)
            yield _tag(buf_b, opts.tag_b)  # type: ignore[arg-type]
            _advance_b()
        elif b_done:
            yield _tag(buf_a, opts.tag_a)  # type: ignore[arg-type]
            if opts.fill_missing:
                yield _tag(_placeholder(opts.tag_b, opts.fill_text), opts.tag_b)
            _advance_a()
        else:
            a_line: LogLine = buf_a  # type: ignore[assignment]
            b_line: LogLine = buf_b  # type: ignore[assignment]
            if opts.strict_order and _ts_key(a_line) <= _ts_key(b_line):
                yield _tag(a_line, opts.tag_a)
                _advance_a()
            else:
                yield _tag(b_line, opts.tag_b)
                _advance_b()
