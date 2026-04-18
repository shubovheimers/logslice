"""Tests for logslice.fuzzer."""
from __future__ import annotations

import pytest
from datetime import datetime

from logslice.parser import LogLine
from logslice.fuzzer import (
    FuzzOptions,
    dice_coefficient,
    fuzz_filter,
)


def make_line(raw: str, level: str = "INFO", message: str = "") -> LogLine:
    return LogLine(
        raw=raw,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=message or raw,
        extra={},
    )


# ---------------------------------------------------------------------------
# dice_coefficient
# ---------------------------------------------------------------------------

class TestDiceCoefficient:
    def test_identical_strings(self):
        assert dice_coefficient("hello", "hello") == 1.0

    def test_empty_string_returns_zero(self):
        assert dice_coefficient("", "hello") == 0.0
        assert dice_coefficient("hello", "") == 0.0

    def test_completely_different(self):
        score = dice_coefficient("abc", "xyz")
        assert score == 0.0

    def test_partial_overlap(self):
        score = dice_coefficient("night", "nacht")
        assert 0.0 < score < 1.0

    def test_case_insensitive(self):
        assert dice_coefficient("Hello", "hello") == 1.0


# ---------------------------------------------------------------------------
# FuzzOptions
# ---------------------------------------------------------------------------

class TestFuzzOptions:
    def test_defaults_not_active(self):
        opts = FuzzOptions()
        assert not opts.is_active()

    def test_enabled_with_query_is_active(self):
        opts = FuzzOptions(query="error", enabled=True)
        assert opts.is_active()

    def test_enabled_without_query_not_active(self):
        opts = FuzzOptions(query="", enabled=True)
        assert not opts.is_active()

    def test_invalid_threshold_raises(self):
        with pytest.raises(ValueError):
            FuzzOptions(query="x", threshold=1.5)

    def test_threshold_zero_valid(self):
        opts = FuzzOptions(query="x", threshold=0.0)
        assert opts.threshold == 0.0


# ---------------------------------------------------------------------------
# fuzz_filter
# ---------------------------------------------------------------------------

class TestFuzzFilter:
    def test_passthrough_when_disabled(self):
        lines = [make_line("error connecting to db")]
        opts = FuzzOptions(query="error", enabled=False)
        result = list(fuzz_filter(lines, opts))
        assert result == lines

    def test_passthrough_when_opts_none(self):
        lines = [make_line("hello world")]
        result = list(fuzz_filter(lines, None))
        assert result == lines

    def test_filters_below_threshold(self):
        lines = [
            make_line("database connection error"),
            make_line("zzzzzzzzzzzzzzzzzzzzzzzzz"),
        ]
        opts = FuzzOptions(query="database error", threshold=0.3, enabled=True)
        result = list(fuzz_filter(lines, opts))
        assert len(result) == 1
        assert result[0].raw == "database connection error"

    def test_scores_attached_when_requested(self):
        lines = [make_line("connection timeout error")]
        opts = FuzzOptions(query="connection error", enabled=True, scores=True, threshold=0.1)
        result = list(fuzz_filter(lines, opts))
        assert len(result) == 1
        assert "fuzz_score" in result[0].extra

    def test_scores_not_attached_by_default(self):
        lines = [make_line("connection timeout error")]
        opts = FuzzOptions(query="connection error", enabled=True, scores=False, threshold=0.1)
        result = list(fuzz_filter(lines, opts))
        assert "fuzz_score" not in result[0].extra

    def test_field_level(self):
        lines = [
            make_line("some message", level="ERROR"),
            make_line("some message", level="INFO"),
        ]
        opts = FuzzOptions(query="ERROR", field="level", threshold=0.8, enabled=True)
        result = list(fuzz_filter(lines, opts))
        assert len(result) == 1
        assert result[0].level == "ERROR"
