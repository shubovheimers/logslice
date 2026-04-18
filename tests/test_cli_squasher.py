"""Tests for logslice.cli_squasher."""
from __future__ import annotations

import argparse

from logslice.cli_squasher import add_squash_args, squash_opts_from_args
from logslice.squasher import SquashOptions


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_squash_args(p)
    return p


def _make_args(argv: list[str]) -> argparse.Namespace:
    return _make_parser().parse_args(argv)


class TestAddSquashArgs:
    def test_squash_defaults_false(self):
        args = _make_args([])
        assert args.squash is False

    def test_squash_flag_sets_true(self):
        args = _make_args(["--squash"])
        assert args.squash is True

    def test_default_separator(self):
        args = _make_args([])
        assert args.squash_separator == " | "

    def test_custom_separator(self):
        args = _make_args(["--squash-separator", "::"])
        assert args.squash_separator == "::"

    def test_default_max_group(self):
        args = _make_args([])
        assert args.squash_max_group == 50

    def test_custom_max_group(self):
        args = _make_args(["--squash-max-group", "10"])
        assert args.squash_max_group == 10


class TestSquashOptsFromArgs:
    def test_returns_squash_options(self):
        args = _make_args(["--squash"])
        opts = squash_opts_from_args(args)
        assert isinstance(opts, SquashOptions)

    def test_enabled_when_flag_set(self):
        args = _make_args(["--squash"])
        opts = squash_opts_from_args(args)
        assert opts.enabled is True

    def test_not_enabled_by_default(self):
        args = _make_args([])
        opts = squash_opts_from_args(args)
        assert opts.enabled is False

    def test_separator_propagated(self):
        args = _make_args(["--squash-separator", "---"])
        opts = squash_opts_from_args(args)
        assert opts.separator == "---"

    def test_max_group_propagated(self):
        args = _make_args(["--squash-max-group", "5"])
        opts = squash_opts_from_args(args)
        assert opts.max_group == 5
