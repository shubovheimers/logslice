"""Tests for logslice.repeater."""
from __future__ import annotations

import pytest
from datetime import datetime

from logslice.parser import LogLine
from logslice.repeater import RepeatOptions, RepeatMatch, find_repeats


def make_line(msg: str, level: str = "INFO") -> LogLine:
    return LogLine(
        raw=f"{level} {msg}",
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=msg,
        extra={},
    )


def collect(lines, opts):
    return list(find_repeats(iter(lines), opts))


class TestRepeatOptions:
    def test_defaults_not_active(self):
        opts = RepeatOptions()
        assert not opts.is_active()

    def test_enabled_is_active(self):
        opts = RepeatOptions(enabled=True)
        assert opts.is_active()

    def test_invalid_window_raises(self):
        with pytest.raises(ValueError, match="window"):
            RepeatOptions(window=0)

    def test_invalid_min_repeats_raises(self):
        with pytest.raises(ValueError, match="min_repeats"):
            RepeatOptions(min_repeats=1)


class TestFindRepeats:
    def test_disabled_yields_nothing(self):
        lines = [make_line("hello")] * 5
        opts = RepeatOptions(enabled=False)
        assert collect(lines, opts) == []

    def test_no_repeats_yields_nothing(self):
        lines = [make_line(f"msg {i}") for i in range(5)]
        opts = RepeatOptions(enabled=True, min_repeats=2)
        assert collect(lines, opts) == []

    def test_exact_min_repeats_yields_match(self):
        lines = [make_line("dup"), make_line("dup")]
        opts = RepeatOptions(enabled=True, min_repeats=2, window=10)
        results = collect(lines, opts)
        assert len(results) == 1
        assert results[0].count == 2

    def test_repeat_count_reflects_window(self):
        lines = [make_line("x")] * 4
        opts = RepeatOptions(enabled=True, min_repeats=2, window=10)
        results = collect(lines, opts)
        assert len(results) == 1
        assert results[0].count >= 2

    def test_each_distinct_repeat_emitted_once(self):
        lines = [make_line("a"), make_line("a"), make_line("b"), make_line("b")]
        opts = RepeatOptions(enabled=True, min_repeats=2, window=10)
        results = collect(lines, opts)
        messages = [r.line.message for r in results]
        assert "a" in messages
        assert "b" in messages
        assert len(results) == 2

    def test_outside_window_not_counted(self):
        # window=2: only look back 2 lines
        lines = [make_line("z"), make_line("other"), make_line("other2"), make_line("z")]
        opts = RepeatOptions(enabled=True, min_repeats=2, window=2)
        results = collect(lines, opts)
        assert all(r.line.message != "z" for r in results)

    def test_level_included_in_key(self):
        lines = [make_line("msg", "ERROR"), make_line("msg", "INFO")]
        opts = RepeatOptions(enabled=True, min_repeats=2, window=10, key_fields=("level", "message"))
        results = collect(lines, opts)
        assert results == []
