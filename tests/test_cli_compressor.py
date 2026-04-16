"""Tests for logslice.cli_compressor."""
from __future__ import annotations

import argparse
import pytest
from logslice.cli_compressor import add_compress_args, compress_opts_from_args
from logslice.compressor import CompressOptions


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_compress_args(p)
    return p


def _make_args(**kwargs):
    defaults = {
        "compress": False,
        "compress_min_run": 3,
        "compress_placeholder": "... [{count} identical lines omitted] ...",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddCompressArgs:
    def test_compress_flag_defaults_false(self):
        p = _make_parser()
        args = p.parse_args([])
        assert args.compress is False

    def test_compress_flag_true_when_set(self):
        p = _make_parser()
        args = p.parse_args(["--compress"])
        assert args.compress is True

    def test_min_run_default(self):
        p = _make_parser()
        args = p.parse_args([])
        assert args.compress_min_run == 3

    def test_min_run_custom(self):
        p = _make_parser()
        args = p.parse_args(["--compress-min-run", "5"])
        assert args.compress_min_run == 5

    def test_placeholder_default_contains_count(self):
        p = _make_parser()
        args = p.parse_args([])
        assert "{count}" in args.compress_placeholder

    def test_placeholder_custom(self):
        p = _make_parser()
        args = p.parse_args(["--compress-placeholder", "[{count} dupes]"])
        assert args.compress_placeholder == "[{count} dupes]"


class TestCompressOptsFromArgs:
    def test_disabled_by_default(self):
        opts = compress_opts_from_args(_make_args())
        assert isinstance(opts, CompressOptions)
        assert opts.enabled is False

    def test_enabled_flag_propagated(self):
        opts = compress_opts_from_args(_make_args(compress=True))
        assert opts.enabled is True

    def test_min_run_propagated(self):
        opts = compress_opts_from_args(_make_args(compress_min_run=7))
        assert opts.min_run == 7

    def test_placeholder_propagated(self):
        opts = compress_opts_from_args(
            _make_args(compress_placeholder="[{count} hidden]")
        )
        assert opts.placeholder == "[{count} hidden]"

    def test_invalid_min_run_raises(self):
        with pytest.raises(ValueError):
            compress_opts_from_args(_make_args(compress=True, compress_min_run=1))
