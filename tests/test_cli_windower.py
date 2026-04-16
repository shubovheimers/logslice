"""Tests for logslice.cli_windower."""
from __future__ import annotations

import argparse
import pytest
from logslice.cli_windower import add_window_args, window_opts_from_args


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_window_args(p)
    return p


def _make_args(extra: list[str] | None = None) -> argparse.Namespace:
    return _make_parser().parse_args(extra or [])


class TestAddWindowArgs:
    def test_window_size_default_zero(self):
        args = _make_args()
        assert args.window_size == 0

    def test_window_step_default_none(self):
        args = _make_args()
        assert args.window_step is None

    def test_window_min_lines_default_one(self):
        args = _make_args()
        assert args.window_min_lines == 1

    def test_window_size_parsed(self):
        args = _make_args(["--window", "120"])
        assert args.window_size == 120

    def test_window_step_parsed(self):
        args = _make_args(["--window", "60", "--window-step", "30"])
        assert args.window_step == 30

    def test_window_min_lines_parsed(self):
        args = _make_args(["--window", "60", "--window-min-lines", "5"])
        assert args.window_min_lines == 5


class TestWindowOptsFromArgs:
    def test_returns_none_when_disabled(self):
        args = _make_args()
        assert window_opts_from_args(args) is None

    def test_returns_options_when_size_set(self):
        args = _make_args(["--window", "60"])
        opts = window_opts_from_args(args)
        assert opts is not None
        assert opts.enabled
        assert opts.size_seconds == 60

    def test_step_propagated(self):
        args = _make_args(["--window", "60", "--window-step", "15"])
        opts = window_opts_from_args(args)
        assert opts is not None
        assert opts.step_seconds == 15

    def test_min_lines_propagated(self):
        args = _make_args(["--window", "60", "--window-min-lines", "10"])
        opts = window_opts_from_args(args)
        assert opts is not None
        assert opts.min_lines == 10
