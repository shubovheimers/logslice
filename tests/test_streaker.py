"""Tests for logslice.streaker."""
from __future__ import annotations

import pytest
from logslice.parser import LogLine
from logslice.streaker import StreakOptions, Streak, find_streaks, iter_streak_lines


def make_line(text: str) -> LogLine:
    return LogLine(raw=text, timestamp=None, level=None, message=text)


def collect(lines, opts):
    return list(find_streaks(lines, opts))


class TestStreakOptions:
    def test_defaults_not_enabled(self):
        assert not StreakOptions().enabled()

    def test_enabled_with_pattern(self):
        assert StreakOptions(pattern="ERROR").enabled()

    def test_invalid_min_length_raises(self):
        with pytest.raises(ValueError):
            StreakOptions(pattern="x", min_length=0)


class TestFindStreaks:
    def test_empty_input_yields_nothing(self):
        assert collect([], StreakOptions(pattern="ERR")) == []

    def test_no_pattern_yields_nothing(self):
        lines = [make_line("ERROR foo"), make_line("ERROR bar")]
        assert collect(lines, StreakOptions()) == []

    def test_single_run_qualifies(self):
        lines = [make_line("ERROR a"), make_line("ERROR b"), make_line("OK")]
        streaks = collect(lines, StreakOptions(pattern="ERROR", min_length=2))
        assert len(streaks) == 1
        assert len(streaks[0]) == 2

    def test_run_too_short_excluded(self):
        lines = [make_line("ERROR a"), make_line("OK")]
        assert collect(lines, StreakOptions(pattern="ERROR", min_length=2)) == []

    def test_multiple_runs(self):
        lines = [
            make_line("ERROR a"), make_line("ERROR b"),
            make_line("INFO x"),
            make_line("ERROR c"), make_line("ERROR d"), make_line("ERROR e"),
        ]
        streaks = collect(lines, StreakOptions(pattern="ERROR", min_length=2))
        assert len(streaks) == 2
        assert len(streaks[1]) == 3

    def test_run_at_end_of_input(self):
        lines = [make_line("INFO ok"), make_line("ERROR x"), make_line("ERROR y")]
        streaks = collect(lines, StreakOptions(pattern="ERROR", min_length=2))
        assert len(streaks) == 1

    def test_case_insensitive_by_default(self):
        lines = [make_line("error a"), make_line("ERROR b")]
        streaks = collect(lines, StreakOptions(pattern="error", min_length=2))
        assert len(streaks) == 1

    def test_case_sensitive_misses_mixed(self):
        lines = [make_line("error a"), make_line("ERROR b")]
        streaks = collect(lines, StreakOptions(pattern="error", min_length=2, case_sensitive=True))
        assert len(streaks) == 0


class TestIterStreakLines:
    def test_yields_only_streak_lines(self):
        lines = [
            make_line("ERROR a"), make_line("ERROR b"),
            make_line("INFO ok"),
            make_line("ERROR c"),
        ]
        result = list(iter_streak_lines(lines, StreakOptions(pattern="ERROR", min_length=2)))
        assert len(result) == 2
        assert all("ERROR" in ln.raw for ln in result)
