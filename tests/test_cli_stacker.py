"""Tests for logslice.cli_stacker."""
from __future__ import annotations

import argparse

import pytest

from logslice.cli_stacker import add_stack_args, stack_opts_from_args
from logslice.stacker import StackOptions


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_stack_args(p)
    return p


def _make_args(extra: list[str] | None = None) -> argparse.Namespace:
    return _make_parser().parse_args(extra or [])


class TestAddStackArgs:
    def test_stack_lines_default_zero(self):
        assert _make_args().stack_lines == 0

    def test_stack_seconds_default_zero(self):
        assert _make_args().stack_seconds == 0.0

    def test_stack_min_lines_default_one(self):
        assert _make_args().stack_min_lines == 1

    def test_stack_lines_parsed(self):
        assert _make_args(["--stack-lines", "10"]).stack_lines == 10

    def test_stack_seconds_parsed(self):
        assert _make_args(["--stack-seconds", "30.5"]).stack_seconds == 30.5

    def test_stack_min_lines_parsed(self):
        assert _make_args(["--stack-min-lines", "3"]).stack_min_lines == 3


class TestStackOptsFromArgs:
    def test_returns_none_when_disabled(self):
        args = _make_args()
        assert stack_opts_from_args(args) is None

    def test_returns_opts_when_max_lines_set(self):
        args = _make_args(["--stack-lines", "5"])
        opts = stack_opts_from_args(args)
        assert isinstance(opts, StackOptions)
        assert opts.max_lines == 5

    def test_returns_opts_when_seconds_set(self):
        args = _make_args(["--stack-seconds", "60"])
        opts = stack_opts_from_args(args)
        assert isinstance(opts, StackOptions)
        assert opts.seconds == 60.0

    def test_min_lines_propagated(self):
        args = _make_args(["--stack-lines", "4", "--stack-min-lines", "2"])
        opts = stack_opts_from_args(args)
        assert opts is not None
        assert opts.min_lines == 2

    def test_both_max_lines_and_seconds(self):
        args = _make_args(["--stack-lines", "3", "--stack-seconds", "10"])
        opts = stack_opts_from_args(args)
        assert opts is not None
        assert opts.max_lines == 3
        assert opts.seconds == 10.0
