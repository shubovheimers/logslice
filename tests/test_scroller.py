"""Tests for logslice.scroller and logslice.cli_scroller."""
from __future__ import annotations

import argparse
from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogLine
from logslice.scroller import ScrollOptions, scroll_lines
from logslice.cli_scroller import add_scroll_args, scroll_opts_from_args


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_line(n: int) -> LogLine:
    return LogLine(
        raw=f"line {n}",
        timestamp=datetime(2024, 1, 1, 0, 0, n % 60),
        level=None,
        message=f"line {n}",
    )


def make_lines(count: int) -> List[LogLine]:
    return [make_line(i) for i in range(count)]


# ---------------------------------------------------------------------------
# ScrollOptions validation
# ---------------------------------------------------------------------------

class TestScrollOptions:
    def test_defaults(self):
        o = ScrollOptions()
        assert o.window_size == 50
        assert o.step == 1
        assert o.start_line == 0
        assert o.max_windows is None
        assert o.enabled

    def test_invalid_window_size_raises(self):
        with pytest.raises(ValueError, match="window_size"):
            ScrollOptions(window_size=0)

    def test_invalid_step_raises(self):
        with pytest.raises(ValueError, match="step"):
            ScrollOptions(step=0)

    def test_negative_start_raises(self):
        with pytest.raises(ValueError, match="start_line"):
            ScrollOptions(start_line=-1)

    def test_invalid_max_windows_raises(self):
        with pytest.raises(ValueError, match="max_windows"):
            ScrollOptions(max_windows=0)


# ---------------------------------------------------------------------------
# scroll_lines
# ---------------------------------------------------------------------------

class TestScrollLines:
    def test_single_window_when_lines_lt_window(self):
        lines = make_lines(5)
        windows = list(scroll_lines(lines, ScrollOptions(window_size=10)))
        assert len(windows) == 1
        assert len(windows[0]) == 5

    def test_exact_fit_yields_one_window(self):
        lines = make_lines(10)
        windows = list(scroll_lines(lines, ScrollOptions(window_size=10)))
        assert len(windows) == 1

    def test_step_1_yields_sliding_windows(self):
        lines = make_lines(5)
        windows = list(scroll_lines(lines, ScrollOptions(window_size=3, step=1)))
        # positions 0,1,2 → 3 windows
        assert len(windows) == 3
        assert [l.message for l in windows[0]] == ["line 0", "line 1", "line 2"]
        assert [l.message for l in windows[2]] == ["line 2", "line 3", "line 4"]

    def test_step_equals_window_non_overlapping(self):
        lines = make_lines(6)
        windows = list(scroll_lines(lines, ScrollOptions(window_size=3, step=3)))
        assert len(windows) == 2

    def test_max_windows_limits_output(self):
        lines = make_lines(20)
        windows = list(scroll_lines(lines, ScrollOptions(window_size=5, step=1, max_windows=3)))
        assert len(windows) == 3

    def test_start_line_skips_prefix(self):
        lines = make_lines(10)
        windows = list(scroll_lines(lines, ScrollOptions(window_size=3, step=3, start_line=6)))
        # remaining after skip: lines 6,7,8,9 → one full window + one partial
        assert windows[0][0].message == "line 6"

    def test_empty_source_yields_nothing(self):
        windows = list(scroll_lines([], ScrollOptions()))
        assert windows == []

    def test_default_opts_used_when_none(self):
        lines = make_lines(3)
        windows = list(scroll_lines(lines))
        # default window_size=50, so one window with all 3 lines
        assert len(windows) == 1


# ---------------------------------------------------------------------------
# cli_scroller helpers
# ---------------------------------------------------------------------------

def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_scroll_args(p)
    return p


def _make_args(**kwargs):
    defaults = {
        "scroll_window": 50,
        "scroll_step": 1,
        "scroll_start": 0,
        "scroll_max_windows": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestScrollOptsFromArgs:
    def test_returns_none_for_all_defaults(self):
        assert scroll_opts_from_args(_make_args()) is None

    def test_custom_window_returns_opts(self):
        opts = scroll_opts_from_args(_make_args(scroll_window=10))
        assert opts is not None
        assert opts.window_size == 10

    def test_custom_step_returns_opts(self):
        opts = scroll_opts_from_args(_make_args(scroll_step=5))
        assert opts is not None
        assert opts.step == 5

    def test_max_windows_set_returns_opts(self):
        opts = scroll_opts_from_args(_make_args(scroll_max_windows=4))
        assert opts is not None
        assert opts.max_windows == 4

    def test_parser_registers_args(self):
        p = _make_parser()
        ns = p.parse_args(["--scroll-window", "20", "--scroll-step", "5"])
        assert ns.scroll_window == 20
        assert ns.scroll_step == 5
