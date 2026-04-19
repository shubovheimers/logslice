"""Tests for logslice.capper."""
from __future__ import annotations

import pytest

from logslice.parser import LogLine
from logslice.capper import CapOptions, cap_lines


def make_line(level: str, text: str = "msg") -> LogLine:
    return LogLine(raw=text, timestamp=None, level=level, message=text, extra={})


def collect(lines, opts):
    return list(cap_lines(lines, opts))


class TestCapOptions:
    def test_defaults_not_enabled(self):
        assert not CapOptions().enabled

    def test_max_per_level_enables(self):
        assert CapOptions(max_per_level=3).enabled

    def test_max_total_enables(self):
        assert CapOptions(max_total=5).enabled

    def test_negative_max_per_level_raises(self):
        with pytest.raises(ValueError):
            CapOptions(max_per_level=-1)

    def test_negative_max_total_raises(self):
        with pytest.raises(ValueError):
            CapOptions(max_total=-1)


class TestCapLines:
    def test_passthrough_when_disabled(self):
        lines = [make_line("ERROR")] * 10
        assert collect(lines, CapOptions()) == lines

    def test_passthrough_when_opts_none(self):
        lines = [make_line("INFO")] * 5
        assert collect(lines, None) == lines

    def test_per_level_cap(self):
        lines = [make_line("ERROR")] * 6 + [make_line("INFO")] * 4
        result = collect(lines, CapOptions(max_per_level=2))
        error_count = sum(1 for l in result if l.level == "ERROR")
        info_count = sum(1 for l in result if l.level == "INFO")
        assert error_count == 2
        assert info_count == 2

    def test_total_cap(self):
        lines = [make_line("INFO")] * 20
        result = collect(lines, CapOptions(max_total=7))
        assert len(result) == 7

    def test_per_level_and_total_combined(self):
        lines = [make_line("ERROR")] * 5 + [make_line("WARN")] * 5
        result = collect(lines, CapOptions(max_per_level=3, max_total=4))
        assert len(result) == 4

    def test_fallback_level_used_when_none(self):
        lines = [make_line(None, "no level")] * 5  # type: ignore[arg-type]
        result = collect(lines, CapOptions(max_per_level=2, fallback_level="UNKNOWN"))
        assert len(result) == 2

    def test_mixed_levels_independent_caps(self):
        lines = (
            [make_line("DEBUG")] * 4
            + [make_line("INFO")] * 4
            + [make_line("ERROR")] * 4
        )
        result = collect(lines, CapOptions(max_per_level=2))
        assert len(result) == 6
