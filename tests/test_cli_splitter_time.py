"""Tests for logslice.cli_splitter_time."""
from __future__ import annotations

import argparse

import pytest

from logslice.cli_splitter_time import add_time_slice_args, time_slice_opts_from_args
from logslice.splitter_time import TimeSliceOptions


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_time_slice_args(p)
    return p


def _make_args(argv: list[str]) -> argparse.Namespace:
    return _make_parser().parse_args(argv)


class TestAddTimeSliceArgs:
    def test_slice_window_default_zero(self):
        args = _make_args([])
        assert args.slice_window == 0

    def test_slice_window_parsed(self):
        args = _make_args(["--slice-window", "300"])
        assert args.slice_window == 300

    def test_keep_empty_default_false(self):
        args = _make_args([])
        assert args.slice_keep_empty is False

    def test_keep_empty_flag(self):
        args = _make_args(["--slice-keep-empty"])
        assert args.slice_keep_empty is True


class TestTimeSliceOptsFromArgs:
    def test_returns_none_when_window_zero(self):
        args = _make_args([])
        assert time_slice_opts_from_args(args) is None

    def test_returns_options_when_window_set(self):
        args = _make_args(["--slice-window", "120"])
        opts = time_slice_opts_from_args(args)
        assert isinstance(opts, TimeSliceOptions)
        assert opts.window_seconds == 120

    def test_drop_empty_default_true(self):
        args = _make_args(["--slice-window", "60"])
        opts = time_slice_opts_from_args(args)
        assert opts.drop_empty is True

    def test_keep_empty_inverts_drop_empty(self):
        args = _make_args(["--slice-window", "60", "--slice-keep-empty"])
        opts = time_slice_opts_from_args(args)
        assert opts.drop_empty is False
