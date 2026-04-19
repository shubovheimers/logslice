"""Tests for logslice.cli_pruner."""
from __future__ import annotations

import argparse

from logslice.cli_pruner import add_prune_args, prune_opts_from_args


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_prune_args(p)
    return p


def _make_args(argv: list[str]):
    return _make_parser().parse_args(argv)


class TestAddPruneArgs:
    def test_prune_defaults_false(self):
        args = _make_args([])
        assert args.prune is False

    def test_prune_flag_sets_true(self):
        args = _make_args(["--prune"])
        assert args.prune is True

    def test_prune_min_length_default(self):
        args = _make_args([])
        assert args.prune_min_length == 1

    def test_prune_min_length_custom(self):
        args = _make_args(["--prune-min-length", "20"])
        assert args.prune_min_length == 20

    def test_keep_whitespace_default_false(self):
        args = _make_args([])
        assert args.prune_keep_whitespace is False

    def test_keep_whitespace_flag(self):
        args = _make_args(["--prune-keep-whitespace"])
        assert args.prune_keep_whitespace is True


class TestPruneOptsFromArgs:
    def test_disabled_by_default(self):
        opts = prune_opts_from_args(_make_args([]))
        assert not opts.enabled

    def test_enabled_via_flag(self):
        opts = prune_opts_from_args(_make_args(["--prune"]))
        assert opts.enabled

    def test_min_length_propagated(self):
        opts = prune_opts_from_args(_make_args(["--prune-min-length", "10"]))
        assert opts.min_length == 10

    def test_strip_whitespace_default_true(self):
        opts = prune_opts_from_args(_make_args([]))
        assert opts.strip_whitespace is True

    def test_strip_whitespace_disabled_by_flag(self):
        opts = prune_opts_from_args(_make_args(["--prune-keep-whitespace"]))
        assert opts.strip_whitespace is False
