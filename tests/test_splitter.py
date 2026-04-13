"""Tests for logslice.splitter."""

from __future__ import annotations

import os
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from logslice.parser import LogLine
from logslice.splitter import (
    SplitOptions,
    split_by_lines,
    split_by_time,
    write_chunks,
)


def make_line(raw: str, ts: datetime | None = None) -> LogLine:
    return LogLine(raw=raw, timestamp=ts, level=None, message=raw)


DT_BASE = datetime(2024, 1, 1, 12, 0, 0)


class TestSplitOptions:
    def test_enabled_with_max_lines(self):
        opts = SplitOptions(max_lines=100)
        assert opts.enabled() is True

    def test_enabled_with_time_window(self):
        opts = SplitOptions(time_window=timedelta(minutes=5))
        assert opts.enabled() is True

    def test_not_enabled_by_default(self):
        opts = SplitOptions()
        assert opts.enabled() is False


class TestSplitByLines:
    def _lines(self, n: int):
        return [make_line(f"line {i}") for i in range(n)]

    def test_exact_multiple(self):
        opts = SplitOptions(max_lines=3)
        chunks = list(split_by_lines(self._lines(6), opts))
        assert len(chunks) == 2
        assert all(len(c) == 3 for c in chunks)

    def test_remainder_in_last_chunk(self):
        opts = SplitOptions(max_lines=4)
        chunks = list(split_by_lines(self._lines(9), opts))
        assert len(chunks) == 3
        assert len(chunks[-1]) == 1

    def test_single_chunk_when_fewer_lines(self):
        opts = SplitOptions(max_lines=100)
        chunks = list(split_by_lines(self._lines(5), opts))
        assert len(chunks) == 1

    def test_empty_input(self):
        opts = SplitOptions(max_lines=10)
        chunks = list(split_by_lines([], opts))
        assert chunks == []

    def test_invalid_max_lines_raises(self):
        opts = SplitOptions(max_lines=0)
        with pytest.raises(ValueError):
            list(split_by_lines([], opts))


class TestSplitByTime:
    def _timed_lines(self, deltas_seconds):
        return [
            make_line(f"line {i}", DT_BASE + timedelta(seconds=s))
            for i, s in enumerate(deltas_seconds)
        ]

    def test_no_gap_single_chunk(self):
        opts = SplitOptions(time_window=timedelta(minutes=1))
        lines = self._timed_lines([0, 10, 20, 30])
        chunks = list(split_by_time(lines, opts))
        assert len(chunks) == 1

    def test_gap_creates_new_chunk(self):
        opts = SplitOptions(time_window=timedelta(minutes=1))
        lines = self._timed_lines([0, 10, 200, 210])
        chunks = list(split_by_time(lines, opts))
        assert len(chunks) == 2

    def test_lines_without_timestamps_stay_in_current_chunk(self):
        opts = SplitOptions(time_window=timedelta(seconds=5))
        lines = [
            make_line("a", DT_BASE),
            make_line("b", None),
            make_line("c", None),
        ]
        chunks = list(split_by_time(lines, opts))
        assert len(chunks) == 1
        assert len(chunks[0]) == 3

    def test_missing_time_window_raises(self):
        opts = SplitOptions()
        with pytest.raises(ValueError):
            list(split_by_time([], opts))


class TestWriteChunks:
    def test_creates_files(self, tmp_path):
        opts = SplitOptions(max_lines=2, output_dir=str(tmp_path))
        chunks = [
            [make_line("line 0"), make_line("line 1")],
            [make_line("line 2")],
        ]
        paths = write_chunks(chunks, opts)
        assert len(paths) == 2
        assert all(p.exists() for p in paths)

    def test_file_content_matches_raw(self, tmp_path):
        opts = SplitOptions(output_dir=str(tmp_path))
        chunks = [[make_line("hello world")]]
        paths = write_chunks(chunks, opts)
        content = paths[0].read_text()
        assert "hello world" in content

    def test_padding_in_filename(self, tmp_path):
        opts = SplitOptions(output_dir=str(tmp_path), pad_width=6)
        chunks = [[make_line("x")]]
        paths = write_chunks(chunks, opts)
        assert "000000" in paths[0].name
