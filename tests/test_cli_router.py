"""Tests for logslice.cli_router."""
from __future__ import annotations

import argparse
import pytest
from logslice.cli_router import add_router_subparser, _parse_rules
from logslice.router import RouteRule


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command")
    add_router_subparser(sub)
    return p


def _make_args(extra: list[str] | None = None) -> argparse.Namespace:
    p = _make_parser()
    return p.parse_args(["route", "logfile.log"] + (extra or []))


class TestAddRouterSubparser:
    def test_subparser_registered(self):
        p = _make_parser()
        ns = p.parse_args(["route", "app.log"])
        assert ns.command == "route"

    def test_default_channel_default(self):
        ns = _make_args()
        assert ns.default_channel == "default"

    def test_custom_default_channel(self):
        ns = _make_args(["--default-channel", "fallback"])
        assert ns.default_channel == "fallback"

    def test_stop_on_first_match_default_true(self):
        ns = _make_args()
        assert ns.stop_on_first_match is True

    def test_no_stop_flag(self):
        ns = _make_args(["--no-stop"])
        assert ns.stop_on_first_match is False

    def test_rules_default_empty(self):
        ns = _make_args()
        assert ns.rules == []

    def test_single_rule_appended(self):
        ns = _make_args(["--rule", "errors:error"])
        assert ns.rules == ["errors:error"]

    def test_multiple_rules(self):
        ns = _make_args(["--rule", "errors:error", "--rule", "warns@WARNING"])
        assert len(ns.rules) == 2

    def test_func_set(self):
        ns = _make_args()
        assert callable(ns.func)


class TestParseRules:
    def test_pattern_rule(self):
        rules = _parse_rules(["errors:error"])
        assert len(rules) == 1
        assert rules[0].channel == "errors"
        assert rules[0].pattern == "error"
        assert rules[0].level is None

    def test_level_rule(self):
        rules = _parse_rules(["warns@WARNING"])
        assert len(rules) == 1
        assert rules[0].channel == "warns"
        assert rules[0].level == "WARNING"
        assert rules[0].pattern is None

    def test_multiple_rules_parsed(self):
        rules = _parse_rules(["a:foo", "b@ERROR"])
        assert len(rules) == 2

    def test_invalid_spec_raises(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _parse_rules(["badspec"])

    def test_empty_list_returns_empty(self):
        assert _parse_rules([]) == []
