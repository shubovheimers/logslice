"""Tests for logslice.cli_chunker."""
from __future__ import annotations

import argparse

import pytest

from logslice.cli_chunker import add_chunk_args, chunk_opts_from_args
from logslice.chunker import ChunkOptions


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_chunk_args(p)
    return p


def _make_args(argv: list[str]) -> argparse.Namespace:
    return _make_parser().parse_args(argv)


class TestAddChunkArgs:
    def test_chunk_lines_default_zero(self):
        args = _make_args([])
        assert args.chunk_lines == 0

    def test_chunk_seconds_default_zero(self):
        args = _make_args([])
        assert args.chunk_seconds == 0.0

    def test_no_partial_chunk_default_false(self):
        args = _make_args([])
        assert args.no_partial_chunk is False

    def test_chunk_lines_parsed(self):
        args = _make_args(["--chunk-lines", "100"])
        assert args.chunk_lines == 100

    def test_chunk_seconds_parsed(self):
        args = _make_args(["--chunk-seconds", "30.5"])
        assert args.chunk_seconds == 30.5

    def test_no_partial_chunk_flag(self):
        args = _make_args(["--no-partial-chunk"])
        assert args.no_partial_chunk is True


class TestChunkOptsFromArgs:
    def test_defaults_produce_disabled_opts(self):
        args = _make_args([])
        opts = chunk_opts_from_args(args)
        assert not opts.enabled

    def test_max_lines_forwarded(self):
        args = _make_args(["--chunk-lines", "50"])
        opts = chunk_opts_from_args(args)
        assert opts.max_lines == 50

    def test_time_window_forwarded(self):
        args = _make_args(["--chunk-seconds", "120"])
        opts = chunk_opts_from_args(args)
        assert opts.time_window_seconds == 120.0

    def test_include_partial_inverted(self):
        args = _make_args(["--no-partial-chunk"])
        opts = chunk_opts_from_args(args)
        assert opts.include_partial is False

    def test_include_partial_default_true(self):
        args = _make_args([])
        opts = chunk_opts_from_args(args)
        assert opts.include_partial is True
