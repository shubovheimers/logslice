"""Integration tests for summarizer using real LogLine streams."""
from __future__ import annotations

from datetime import datetime

import pytest

from logslice.parser import LogLine
from logslice.summarizer import SummaryOptions, format_summary, summarize_lines


def _line(raw: str, level: str | None = None, ts: datetime | None = None) -> LogLine:
    return LogLine(raw=raw, timestamp=ts, level=level, message=raw)


DT_A = datetime(2024, 3, 1, 8, 0, 0)
DT_B = datetime(2024, 3, 1, 9, 30, 0)
DT_C = datetime(2024, 3, 1, 11, 0, 0)

SAMPLE_LINES = [
    _line("Server started", level="INFO", ts=DT_A),
    _line("Request received", level="DEBUG", ts=DT_B),
    _line("Request received", level="DEBUG", ts=DT_B),
    _line("Disk full", level="ERROR", ts=DT_C),
    _line("Disk full", level="ERROR", ts=DT_C),
    _line("Disk full", level="ERROR", ts=DT_C),
]


class TestSummarizeIntegration:
    def test_total_line_count(self):
        s = summarize_lines(iter(SAMPLE_LINES))
        assert s.total_lines == 6

    def test_first_timestamp_is_earliest(self):
        s = summarize_lines(iter(SAMPLE_LINES))
        assert s.first_timestamp == DT_A

    def test_last_timestamp_is_latest(self):
        s = summarize_lines(iter(SAMPLE_LINES))
        assert s.last_timestamp == DT_C

    def test_error_count(self):
        s = summarize_lines(iter(SAMPLE_LINES))
        assert s.level_counts["ERROR"] == 3

    def test_debug_count(self):
        s = summarize_lines(iter(SAMPLE_LINES))
        assert s.level_counts["DEBUG"] == 2

    def test_top_message_is_disk_full(self):
        s = summarize_lines(iter(SAMPLE_LINES))
        assert s.top_messages[0] == ("Disk full", 3)

    def test_second_top_message_is_request(self):
        s = summarize_lines(iter(SAMPLE_LINES))
        assert s.top_messages[1] == ("Request received", 2)

    def test_format_output_is_string(self):
        s = summarize_lines(iter(SAMPLE_LINES))
        out = format_summary(s)
        assert isinstance(out, str)
        assert len(out) > 0

    def test_format_includes_error_level(self):
        s = summarize_lines(iter(SAMPLE_LINES))
        out = format_summary(s)
        assert "ERROR" in out

    def test_format_includes_top_message(self):
        s = summarize_lines(iter(SAMPLE_LINES))
        out = format_summary(s)
        assert "Disk full" in out

    def test_top_n_limits_output(self):
        opts = SummaryOptions(top_n=1)
        s = summarize_lines(iter(SAMPLE_LINES), opts)
        assert len(s.top_messages) == 1

    def test_generator_consumed_once(self):
        """Ensure summarize_lines works with a one-shot generator."""
        gen = (_line(f"msg{i}", level="INFO") for i in range(20))
        s = summarize_lines(gen)
        assert s.total_lines == 20
