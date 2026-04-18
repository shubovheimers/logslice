"""Tests for logslice.chunker."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from logslice.chunker import Chunk, ChunkOptions, chunk_lines
from logslice.parser import LogLine


def make_line(text: str = "msg", ts: datetime | None = None) -> LogLine:
    return LogLine(raw=text, timestamp=ts, level=None, message=text, extra={})


def _dt(seconds: int) -> datetime:
    return datetime(2024, 1, 1, 0, 0, seconds, tzinfo=timezone.utc)


class TestChunkOptions:
    def test_defaults_not_enabled(self):
        assert not ChunkOptions().enabled

    def test_max_lines_enables(self):
        assert ChunkOptions(max_lines=10).enabled

    def test_time_window_enables(self):
        assert ChunkOptions(time_window_seconds=60).enabled

    def test_negative_max_lines_raises(self):
        with pytest.raises(ValueError):
            ChunkOptions(max_lines=-1)

    def test_negative_time_window_raises(self):
        with pytest.raises(ValueError):
            ChunkOptions(time_window_seconds=-1.0)


class TestChunkLines:
    def _collect(self, lines, opts) -> List[Chunk]:
        return list(chunk_lines(iter(lines), opts))

    def test_disabled_yields_single_chunk(self):
        lines = [make_line(str(i)) for i in range(5)]
        chunks = self._collect(lines, ChunkOptions())
        assert len(chunks) == 1
        assert len(chunks[0]) == 5

    def test_max_lines_splits_evenly(self):
        lines = [make_line(str(i)) for i in range(6)]
        chunks = self._collect(lines, ChunkOptions(max_lines=2))
        assert len(chunks) == 3
        assert all(len(c) == 2 for c in chunks)

    def test_max_lines_partial_chunk_included_by_default(self):
        lines = [make_line(str(i)) for i in range(5)]
        chunks = self._collect(lines, ChunkOptions(max_lines=2))
        assert len(chunks) == 3
        assert len(chunks[-1]) == 1

    def test_max_lines_partial_chunk_excluded(self):
        lines = [make_line(str(i)) for i in range(5)]
        chunks = self._collect(lines, ChunkOptions(max_lines=2, include_partial=False))
        assert len(chunks) == 2

    def test_chunk_index_increments(self):
        lines = [make_line(str(i)) for i in range(4)]
        chunks = self._collect(lines, ChunkOptions(max_lines=2))
        assert [c.index for c in chunks] == [0, 1]

    def test_time_window_splits_on_boundary(self):
        lines = [
            make_line("a", _dt(0)),
            make_line("b", _dt(30)),
            make_line("c", _dt(61)),
            make_line("d", _dt(90)),
        ]
        chunks = self._collect(lines, ChunkOptions(time_window_seconds=60))
        assert len(chunks) == 2
        assert len(chunks[0]) == 2
        assert len(chunks[1]) == 2

    def test_lines_without_timestamps_not_split_by_time(self):
        lines = [make_line(str(i)) for i in range(4)]
        chunks = self._collect(lines, ChunkOptions(time_window_seconds=10))
        assert len(chunks) == 1

    def test_empty_input_yields_nothing(self):
        opts = ChunkOptions(max_lines=5)
        chunks = self._collect([], opts)
        assert chunks == []
