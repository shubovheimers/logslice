"""Integration tests for chunker: realistic multi-option scenarios."""
from __future__ import annotations

from datetime import datetime, timezone

from logslice.chunker import ChunkOptions, chunk_lines
from logslice.parser import LogLine


def _line(text: str, seconds: int) -> LogLine:
    ts = datetime(2024, 6, 1, 12, 0, seconds, tzinfo=timezone.utc)
    return LogLine(raw=text, timestamp=ts, level=None, message=text, extra={})


class TestChunkerIntegration:
    def test_max_lines_total_preserved(self):
        lines = [_line(str(i), i) for i in range(10)]
        chunks = list(chunk_lines(iter(lines), ChunkOptions(max_lines=3)))
        total = sum(len(c) for c in chunks)
        assert total == 10

    def test_time_window_total_preserved(self):
        lines = [_line(str(i), i * 10) for i in range(9)]
        chunks = list(chunk_lines(iter(lines), ChunkOptions(time_window_seconds=25)))
        total = sum(len(c) for c in chunks)
        assert total == 9

    def test_combined_max_lines_and_time_window(self):
        # 6 lines, each 5 s apart; window=20s, max_lines=2
        lines = [_line(str(i), i * 5) for i in range(6)]
        opts = ChunkOptions(max_lines=2, time_window_seconds=20)
        chunks = list(chunk_lines(iter(lines), opts))
        total = sum(len(c) for c in chunks)
        assert total == 6

    def test_chunk_indices_are_sequential(self):
        lines = [_line(str(i), i) for i in range(9)]
        chunks = list(chunk_lines(iter(lines), ChunkOptions(max_lines=3)))
        assert [c.index for c in chunks] == list(range(len(chunks)))

    def test_single_line_input_one_chunk(self):
        lines = [_line("only", 0)]
        chunks = list(chunk_lines(iter(lines), ChunkOptions(max_lines=10)))
        assert len(chunks) == 1
        assert chunks[0].lines[0].message == "only"
