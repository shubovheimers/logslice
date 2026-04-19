"""Tests for logslice.cli_mapper."""
from __future__ import annotations

import argparse
import pytest

from logslice.cli_mapper import add_mapper_args, mapper_opts_from_args, _parse_rules
from logslice.mapper import MapOptions


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_mapper_args(p)
    return p


def _make_args(argv=None):
    return _make_parser().parse_args(argv or [])


class TestAddMapperArgs:
    def test_map_rules_default_empty(self):
        args = _make_args()
        assert args.map_rules == []

    def test_single_rule_parsed(self):
        args = _make_args(["--map", "code=code=(\\d+)"])
        assert args.map_rules == ["code=code=(\\d+)"]

    def test_multiple_rules(self):
        args = _make_args(["--map", "a=x", "--map", "b=y"])
        assert len(args.map_rules) == 2

    def test_prefix_default(self):
        args = _make_args()
        assert args.map_prefix == "map_"

    def test_custom_prefix(self):
        args = _make_args(["--map-prefix", "f_"])
        assert args.map_prefix == "f_"

    def test_overwrite_default_false(self):
        args = _make_args()
        assert args.map_overwrite is False

    def test_overwrite_flag_sets_true(self):
        args = _make_args(["--map-overwrite"])
        assert args.map_overwrite is True


class TestParseRules:
    def test_valid_rule(self):
        rules = _parse_rules(["user=user=(\\w+)"])
        assert rules[0].target_field == "user"
        assert rules[0].expression == "user=(\\w+)"

    def test_missing_equals_raises(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _parse_rules(["badformat"])

    def test_empty_list_returns_empty(self):
        assert _parse_rules([]) == []


class TestMapperOptsFromArgs:
    def test_no_rules_returns_disabled(self):
        args = _make_args()
        opts = mapper_opts_from_args(args)
        assert isinstance(opts, MapOptions)
        assert not opts.enabled()

    def test_rule_creates_enabled_opts(self):
        args = _make_args(["--map", "code=code=(\\d+)"])
        opts = mapper_opts_from_args(args)
        assert opts.enabled()
        assert opts.rules[0].target_field == "code"

    def test_prefix_propagated(self):
        args = _make_args(["--map-prefix", "x_"])
        opts = mapper_opts_from_args(args)
        assert opts.prefix == "x_"

    def test_overwrite_propagated(self):
        args = _make_args(["--map-overwrite"])
        opts = mapper_opts_from_args(args)
        assert opts.overwrite is True
