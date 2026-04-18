"""Tests for logslice.cli_aggregator."""
from __future__ import annotations
import argparse
import pytest
from logslice.cli_aggregator import add_aggregate_args, aggregate_opts_from_args
from logslice.aggregator import AggregateOptions


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_aggregate_args(p)
    return p


def _make_args(argv: list[str]) -> argparse.Namespace:
    return _make_parser().parse_args(argv)


class TestAddAggregateArgs:
    def test_aggregate_defaults_false(self):
        args = _make_args([])
        assert args.aggregate is False

    def test_aggregate_flag_true(self):
        args = _make_args(["--aggregate"])
        assert args.aggregate is True

    def test_bucket_seconds_default(self):
        args = _make_args([])
        assert args.bucket_seconds == 60

    def test_bucket_seconds_custom(self):
        args = _make_args(["--bucket-seconds", "300"])
        assert args.bucket_seconds == 300

    def test_agg_by_level_default_false(self):
        args = _make_args([])
        assert args.agg_by_level is False

    def test_agg_by_level_flag(self):
        args = _make_args(["--agg-by-level"])
        assert args.agg_by_level is True

    def test_agg_pattern_default_empty(self):
        args = _make_args([])
        assert args.agg_pattern == ""

    def test_agg_pattern_custom(self):
        args = _make_args(["--agg-pattern", "error"])
        assert args.agg_pattern == "error"


class TestAggregateOptsFromArgs:
    def test_returns_aggregate_options(self):
        args = _make_args([])
        opts = aggregate_opts_from_args(args)
        assert isinstance(opts, AggregateOptions)

    def test_enabled_propagated(self):
        args = _make_args(["--aggregate"])
        opts = aggregate_opts_from_args(args)
        assert opts.enabled is True

    def test_bucket_seconds_propagated(self):
        args = _make_args(["--bucket-seconds", "120"])
        opts = aggregate_opts_from_args(args)
        assert opts.bucket_seconds == 120

    def test_by_level_propagated(self):
        args = _make_args(["--agg-by-level"])
        opts = aggregate_opts_from_args(args)
        assert opts.by_level is True

    def test_pattern_propagated(self):
        args = _make_args(["--agg-pattern", "timeout"])
        opts = aggregate_opts_from_args(args)
        assert opts.by_pattern == "timeout"
