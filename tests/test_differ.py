"""Tests for logslice.differ."""
from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogLine
from logslice.differ import DiffOptions, DiffResult, diff_log_sequences, _line_key


def make_line(raw: str, level: str | None = None, ts: datetime | None = None) -> LogLine:
    return LogLine(raw=raw, timestamp=ts, level=level, message=raw)


DT = datetime(2024, 1, 1, 12, 0, 0)


class TestDiffOptions:
    def test_defaults(self):
        opts = DiffOptions()
        assert opts.mode == "added"
        assert opts.key == "raw"
        assert opts.ignore_timestamps is True

    def test_custom_mode(self):
        opts = DiffOptions(mode="removed")
        assert opts.mode == "removed"


class TestLineKey:
    def test_no_timestamp(self):
        ln = make_line("hello world")
        key = _line_key(ln, DiffOptions())
        assert key == "hello world"

    def test_timestamp_stripped_when_ignore_true(self):
        ts = datetime(2024, 1, 1, 12, 0, 0)
        raw = f"{ts.isoformat()} ERROR something went wrong"
        ln = make_line(raw, ts=ts)
        key = _line_key(ln, DiffOptions(ignore_timestamps=True))
        assert "2024-01-01" not in key
        assert "something went wrong" in key

    def test_timestamp_kept_when_ignore_false(self):
        ts = datetime(2024, 1, 1, 12, 0, 0)
        raw = f"{ts.isoformat()} INFO msg"
        ln = make_line(raw, ts=ts)
        key = _line_key(ln, DiffOptions(ignore_timestamps=False))
        assert ts.isoformat() in key


class TestDiffAdded:
    def _run(self, left, right, **kw):
        opts = DiffOptions(mode="added", **kw)
        return list(diff_log_sequences(left, right, opts))

    def test_all_new_lines_returned(self):
        left = [make_line("alpha"), make_line("beta")]
        right = [make_line("beta"), make_line("gamma")]
        results = self._run(left, right)
        assert len(results) == 1
        assert results[0].line.raw == "gamma"
        assert results[0].tag == ">"

    def test_empty_left_returns_all_right(self):
        right = [make_line("a"), make_line("b")]
        results = self._run([], right)
        assert len(results) == 2

    def test_identical_streams_returns_nothing(self):
        lines = [make_line("same")]
        assert self._run(lines, lines) == []


class TestDiffRemoved:
    def _run(self, left, right, **kw):
        opts = DiffOptions(mode="removed", **kw)
        return list(diff_log_sequences(left, right, opts))

    def test_missing_from_right(self):
        left = [make_line("alpha"), make_line("beta")]
        right = [make_line("beta")]
        results = self._run(left, right)
        assert len(results) == 1
        assert results[0].line.raw == "alpha"
        assert results[0].tag == "<"

    def test_empty_right_returns_all_left(self):
        left = [make_line("x"), make_line("y")]
        results = self._run(left, [])
        assert len(results) == 2


class TestDiffCommon:
    def _run(self, left, right, **kw):
        opts = DiffOptions(mode="common", **kw)
        return list(diff_log_sequences(left, right, opts))

    def test_shared_lines_returned(self):
        left = [make_line("alpha"), make_line("beta")]
        right = [make_line("beta"), make_line("gamma")]
        results = self._run(left, right)
        assert len(results) == 1
        assert results[0].line.raw == "beta"
        assert results[0].tag == "="

    def test_no_overlap_returns_empty(self):
        left = [make_line("a")]
        right = [make_line("b")]
        assert self._run(left, right) == []

    def test_all_overlap(self):
        lines = [make_line("x"), make_line("y")]
        results = self._run(lines, lines)
        assert len(results) == 2
