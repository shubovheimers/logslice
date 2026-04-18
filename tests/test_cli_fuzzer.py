"""Tests for logslice.cli_fuzzer."""
from __future__ import annotations

import argparse
import pytest

from logslice.cli_fuzzer import add_fuzz_args, fuzz_opts_from_args


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_fuzz_args(p)
    return p


def _make_args(**kwargs):
    defaults = {
        "fuzz": None,
        "fuzz_threshold": 0.3,
        "fuzz_field": "raw",
        "fuzz_scores": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddFuzzArgs:
    def test_fuzz_default_none(self):
        args = _make_parser().parse_args([])
        assert args.fuzz is None

    def test_fuzz_query_parsed(self):
        args = _make_parser().parse_args(["--fuzz", "timeout"])
        assert args.fuzz == "timeout"

    def test_threshold_default(self):
        args = _make_parser().parse_args([])
        assert args.fuzz_threshold == 0.3

    def test_threshold_custom(self):
        args = _make_parser().parse_args(["--fuzz-threshold", "0.6"])
        assert args.fuzz_threshold == pytest.approx(0.6)

    def test_field_default_raw(self):
        args = _make_parser().parse_args([])
        assert args.fuzz_field == "raw"

    def test_field_choices(self):
        for choice in ("raw", "level", "message"):
            args = _make_parser().parse_args(["--fuzz-field", choice])
            assert args.fuzz_field == choice

    def test_fuzz_scores_default_false(self):
        args = _make_parser().parse_args([])
        assert args.fuzz_scores is False

    def test_fuzz_scores_flag(self):
        args = _make_parser().parse_args(["--fuzz-scores"])
        assert args.fuzz_scores is True


class TestFuzzOptsFromArgs:
    def test_no_query_not_enabled(self):
        opts = fuzz_opts_from_args(_make_args())
        assert not opts.enabled
        assert not opts.is_active()

    def test_query_enables(self):
        opts = fuzz_opts_from_args(_make_args(fuzz="error"))
        assert opts.enabled
        assert opts.query == "error"

    def test_threshold_passed(self):
        opts = fuzz_opts_from_args(_make_args(fuzz_threshold=0.5))
        assert opts.threshold == pytest.approx(0.5)

    def test_field_passed(self):
        opts = fuzz_opts_from_args(_make_args(fuzz_field="level"))
        assert opts.field == "level"

    def test_scores_passed(self):
        opts = fuzz_opts_from_args(_make_args(fuzz_scores=True))
        assert opts.scores is True
