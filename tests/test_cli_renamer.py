"""Tests for logslice.cli_renamer."""
from __future__ import annotations

import argparse
import pytest

from logslice.cli_renamer import add_rename_args, rename_opts_from_args, _parse_mapping


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_rename_args(p)
    return p


def _make_args(argv=None):
    return _make_parser().parse_args(argv or [])


class TestAddRenameArgs:
    def test_rename_fields_default_empty(self):
        args = _make_args()
        assert args.rename_fields == []

    def test_rename_level_default_none(self):
        assert _make_args().rename_level is None

    def test_rename_source_default_none(self):
        assert _make_args().rename_source is None

    def test_strip_prefix_default_none(self):
        assert _make_args().strip_prefix is None

    def test_strip_suffix_default_none(self):
        assert _make_args().strip_suffix is None

    def test_rename_field_parsed(self):
        args = _make_args(["--rename-field", "old=new"])
        assert args.rename_fields == ["old=new"]

    def test_rename_field_multiple(self):
        args = _make_args(["--rename-field", "a=b", "--rename-field", "c=d"])
        assert len(args.rename_fields) == 2

    def test_rename_level_parsed(self):
        args = _make_args(["--rename-level", "severity"])
        assert args.rename_level == "severity"

    def test_strip_prefix_parsed(self):
        args = _make_args(["--strip-prefix", "log_"])
        assert args.strip_prefix == "log_"

    def test_strip_suffix_parsed(self):
        args = _make_args(["--strip-suffix", "_tag"])
        assert args.strip_suffix == "_tag"


class TestParseMappingHelper:
    def test_single_pair(self):
        assert _parse_mapping(["old=new"]) == {"old": "new"}

    def test_multiple_pairs(self):
        result = _parse_mapping(["a=b", "c=d"])
        assert result == {"a": "b", "c": "d"}

    def test_invalid_pair_raises(self):
        with pytest.raises(argparse.ArgumentTypeError):
            _parse_mapping(["noequalssign"])

    def test_empty_list(self):
        assert _parse_mapping([]) == {}


class TestRenameOptsFromArgs:
    def test_defaults_produce_disabled_opts(self):
        opts = rename_opts_from_args(_make_args())
        assert not opts.enabled()

    def test_mapping_populated(self):
        args = _make_args(["--rename-field", "req=request"])
        opts = rename_opts_from_args(args)
        assert opts.mapping == {"req": "request"}

    def test_rename_level_forwarded(self):
        args = _make_args(["--rename-level", "severity"])
        opts = rename_opts_from_args(args)
        assert opts.rename_level == "severity"
