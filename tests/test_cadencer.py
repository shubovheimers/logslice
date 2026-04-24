"""Tests for logslice.cadencer and logslice.cli_cadencer."""
from __future__ import annotations

import argparse
from datetime import datetime
from typing import List

import pytest

from logslice.cadencer import CadenceOptions, cadence_lines
from logslice.cli_cadencer import add_cadence_args, cadence_opts_from_args
from logslice.parser import LogLine


def make_line(text: str = "hello") -> LogLine:
    return LogLine(raw=text, timestamp=datetime(2024, 1, 1), level="INFO", text=text)


def make_lines(n: int) -> List[LogLine]:
    return [make_line(f"line {i}") for i in range(n)]


# ---------------------------------------------------------------------------
# CadenceOptions
# ---------------------------------------------------------------------------

class TestCadenceOptions:
    def test_defaults_not_enabled(self):
        opts = CadenceOptions()
        assert not opts.enabled

    def test_positive_lps_enables(self):
        opts = CadenceOptions(lines_per_second=10.0)
        assert opts.enabled

    def test_negative_lps_raises(self):
        with pytest.raises(ValueError):
            CadenceOptions(lines_per_second=-1.0)

    def test_zero_burst_raises(self):
        with pytest.raises(ValueError):
            CadenceOptions(lines_per_second=5.0, burst=0)

    def test_interval_disabled_is_zero(self):
        assert CadenceOptions().interval == 0.0

    def test_interval_calculation(self):
        opts = CadenceOptions(lines_per_second=10.0, burst=2)
        assert opts.interval == pytest.approx(0.2)


# ---------------------------------------------------------------------------
# cadence_lines
# ---------------------------------------------------------------------------

class TestCadenceLines:
    def test_none_opts_passthrough(self):
        lines = make_lines(5)
        result = list(cadence_lines(lines, None))
        assert result == lines

    def test_disabled_opts_passthrough(self):
        lines = make_lines(5)
        result = list(cadence_lines(lines, CadenceOptions()))
        assert result == lines

    def test_all_lines_yielded(self):
        slept: List[float] = []
        opts = CadenceOptions(lines_per_second=100.0, burst=1, _sleep=slept.append)
        lines = make_lines(4)
        result = list(cadence_lines(lines, opts))
        assert len(result) == 4

    def test_sleep_called_per_burst(self):
        slept: List[float] = []
        opts = CadenceOptions(lines_per_second=2.0, burst=2, _sleep=slept.append)
        list(cadence_lines(make_lines(6), opts))
        # 6 lines / burst of 2 => 3 sleeps
        assert len(slept) == 3

    def test_sleep_duration_matches_interval(self):
        slept: List[float] = []
        opts = CadenceOptions(lines_per_second=4.0, burst=2, _sleep=slept.append)
        list(cadence_lines(make_lines(4), opts))
        for duration in slept:
            assert duration == pytest.approx(0.5)

    def test_empty_input_no_sleep(self):
        slept: List[float] = []
        opts = CadenceOptions(lines_per_second=10.0, _sleep=slept.append)
        list(cadence_lines([], opts))
        assert slept == []


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_cadence_args(p)
    return p


def _make_args(**kwargs):
    defaults = {"cadence": 0.0, "cadence_burst": 1}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddCadenceArgs:
    def test_cadence_default_zero(self):
        p = _make_parser()
        args = p.parse_args([])
        assert args.cadence == 0.0

    def test_cadence_parsed(self):
        p = _make_parser()
        args = p.parse_args(["--cadence", "50"])
        assert args.cadence == pytest.approx(50.0)

    def test_burst_default_one(self):
        p = _make_parser()
        args = p.parse_args([])
        assert args.cadence_burst == 1

    def test_burst_parsed(self):
        p = _make_parser()
        args = p.parse_args(["--cadence-burst", "10"])
        assert args.cadence_burst == 10

    def test_opts_from_args_disabled(self):
        opts = cadence_opts_from_args(_make_args())
        assert not opts.enabled

    def test_opts_from_args_enabled(self):
        opts = cadence_opts_from_args(_make_args(cadence=20.0, cadence_burst=5))
        assert opts.enabled
        assert opts.lines_per_second == pytest.approx(20.0)
        assert opts.burst == 5
