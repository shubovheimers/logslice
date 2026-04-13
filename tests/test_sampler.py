"""Tests for logslice.sampler."""

from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogLine
from logslice.sampler import (
    SampleOptions,
    apply_sampling,
    sample_every_nth,
    sample_head,
    sample_tail,
)


def make_lines(n: int) -> List[LogLine]:
    return [
        LogLine(
            raw=f"line {i}",
            timestamp=datetime(2024, 1, 1, 0, i % 60),
            level="INFO",
            message=f"message {i}",
        )
        for i in range(n)
    ]


class TestSampleEveryNth:
    def test_every_1_returns_all(self):
        lines = make_lines(5)
        assert list(sample_every_nth(lines, 1)) == lines

    def test_every_2_returns_even_indexed(self):
        lines = make_lines(6)
        result = list(sample_every_nth(lines, 2))
        assert result == [lines[0], lines[2], lines[4]]

    def test_every_3(self):
        lines = make_lines(9)
        result = list(sample_every_nth(lines, 3))
        assert len(result) == 3
        assert result[0] is lines[0]

    def test_invalid_n_raises(self):
        with pytest.raises(ValueError):
            list(sample_every_nth(make_lines(3), 0))


class TestSampleHead:
    def test_head_fewer_than_available(self):
        lines = make_lines(10)
        assert list(sample_head(lines, 3)) == lines[:3]

    def test_head_more_than_available(self):
        lines = make_lines(4)
        assert list(sample_head(lines, 10)) == lines

    def test_head_zero(self):
        assert list(sample_head(make_lines(5), 0)) == []

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            list(sample_head(make_lines(3), -1))


class TestSampleTail:
    def test_tail_fewer_than_available(self):
        lines = make_lines(10)
        assert list(sample_tail(lines, 3)) == lines[-3:]

    def test_tail_more_than_available(self):
        lines = make_lines(4)
        assert list(sample_tail(lines, 10)) == lines

    def test_tail_zero(self):
        assert list(sample_tail(make_lines(5), 0)) == []

    def test_negative_raises(self):
        with pytest.raises(ValueError):
            list(sample_tail(make_lines(3), -1))


class TestApplySampling:
    def test_defaults_pass_through_all(self):
        lines = make_lines(10)
        opts = SampleOptions()
        assert list(apply_sampling(lines, opts)) == lines

    def test_max_lines_caps_output(self):
        lines = make_lines(20)
        opts = SampleOptions(max_lines=5)
        assert len(list(apply_sampling(lines, opts))) == 5

    def test_head_applied(self):
        lines = make_lines(10)
        opts = SampleOptions(head=4)
        assert list(apply_sampling(lines, opts)) == lines[:4]

    def test_tail_applied(self):
        lines = make_lines(10)
        opts = SampleOptions(tail=3)
        assert list(apply_sampling(lines, opts)) == lines[-3:]

    def test_every_nth_and_max_lines(self):
        lines = make_lines(20)
        opts = SampleOptions(every_nth=2, max_lines=4)
        result = list(apply_sampling(lines, opts))
        assert len(result) == 4
        # every_nth=2 picks indices 0,2,4,6,...; max_lines then caps at 4
        assert result == [lines[0], lines[2], lines[4], lines[6]]
