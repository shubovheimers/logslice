"""Tests for logslice.stacker."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from logslice.parser import LogLine
from logslice.stacker import Stack, StackOptions, stack_lines


def make_line(text: str = "msg", ts: datetime | None = None) -> LogLine:
    return LogLine(raw=text, text=text, timestamp=ts, level=None, extra={})


def _dt(second: int) -> datetime:
    return datetime(2024, 1, 1, 0, 0, second, tzinfo=timezone.utc)


def collect(lines, opts):
    return list(stack_lines(iter(lines), opts))


class TestStackOptions:
    def test_defaults_not_enabled(self):
        assert StackOptions().enabled is False

    def test_max_lines_enables(self):
        assert StackOptions(max_lines=5).enabled is True

    def test_seconds_enables(self):
        assert StackOptions(seconds=10.0).enabled is True

    def test_negative_max_lines_raises(self):
        with pytest.raises(ValueError):
            StackOptions(max_lines=-1)

    def test_negative_seconds_raises(self):
        with pytest.raises(ValueError):
            StackOptions(seconds=-0.1)

    def test_zero_min_lines_raises(self):
        with pytest.raises(ValueError):
            StackOptions(min_lines=0)


class TestStackLen:
    def test_len_reflects_lines(self):
        s = Stack(lines=[make_line(), make_line()], index=0)
        assert len(s) == 2

    def test_empty_stack(self):
        assert len(Stack()) == 0


class TestStackLines:
    def test_disabled_yields_one_stack_per_line(self):
        lines = [make_line(f"l{i}") for i in range(4)]
        stacks = collect(lines, StackOptions())
        assert len(stacks) == 4
        for i, s in enumerate(stacks):
            assert s.index == i
            assert len(s) == 1

    def test_max_lines_groups_evenly(self):
        lines = [make_line(f"l{i}") for i in range(6)]
        stacks = collect(lines, StackOptions(max_lines=2))
        assert len(stacks) == 3
        assert all(len(s) == 2 for s in stacks)

    def test_max_lines_remainder_emitted(self):
        lines = [make_line(f"l{i}") for i in range(5)]
        stacks = collect(lines, StackOptions(max_lines=2))
        sizes = [len(s) for s in stacks]
        assert sizes == [2, 2, 1]

    def test_stack_index_increments(self):
        lines = [make_line(f"l{i}") for i in range(4)]
        stacks = collect(lines, StackOptions(max_lines=2))
        assert [s.index for s in stacks] == [0, 1]

    def test_time_window_groups_by_seconds(self):
        lines = [
            make_line("a", _dt(0)),
            make_line("b", _dt(1)),
            make_line("c", _dt(5)),
            make_line("d", _dt(6)),
        ]
        stacks = collect(lines, StackOptions(seconds=3.0))
        assert len(stacks) == 2
        assert len(stacks[0]) == 2
        assert len(stacks[1]) == 2

    def test_min_lines_filters_small_stacks(self):
        lines = [make_line(f"l{i}") for i in range(5)]
        stacks = collect(lines, StackOptions(max_lines=2, min_lines=2))
        # last remainder stack has 1 line — should be suppressed
        assert all(len(s) == 2 for s in stacks)

    def test_empty_input_yields_nothing(self):
        assert collect([], StackOptions(max_lines=3)) == []

    def test_lines_without_timestamps_use_max_lines_only(self):
        lines = [make_line(f"l{i}") for i in range(4)]
        stacks = collect(lines, StackOptions(max_lines=2, seconds=5.0))
        assert len(stacks) == 2
