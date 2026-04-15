"""Tests for logslice.cli_correlate."""
from __future__ import annotations

import argparse
import gzip
import os
from pathlib import Path

import pytest

from logslice.cli_correlate import add_correlate_subparser, run_correlate


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    add_correlate_subparser(sub)
    return parser


def _make_args(tmp_path: Path, extra: list | None = None) -> argparse.Namespace:
    log = tmp_path / "app.log"
    log.write_text(
        "2024-01-01 INFO req=abc GET /api\n"
        "2024-01-01 INFO req=xyz POST /login\n"
        "2024-01-01 ERROR req=abc timeout\n"
    )
    argv = ["correlate", str(log), "abc", "--pattern", r"req=(\w+)"]
    if extra:
        argv += extra
    parser = _make_parser()
    return parser.parse_args(argv)


class TestAddCorrelateSubparser:
    def test_subparser_registered(self):
        parser = _make_parser()
        args = parser.parse_args(["correlate", "dummy.log", "abc"])
        assert args.command == "correlate"

    def test_default_field(self):
        parser = _make_parser()
        args = parser.parse_args(["correlate", "dummy.log", "abc"])
        assert args.field == "request_id"

    def test_custom_field(self):
        parser = _make_parser()
        args = parser.parse_args(["correlate", "dummy.log", "abc", "--field", "trace"])
        assert args.field == "trace"

    def test_default_pattern_is_none(self):
        parser = _make_parser()
        args = parser.parse_args(["correlate", "dummy.log", "abc"])
        assert args.pattern is None

    def test_func_set(self):
        parser = _make_parser()
        args = parser.parse_args(["correlate", "dummy.log", "abc"])
        assert args.func is run_correlate


class TestRunCorrelate:
    def test_returns_zero_on_success(self, tmp_path, capsys):
        args = _make_args(tmp_path)
        rc = run_correlate(args)
        assert rc == 0

    def test_matched_lines_written_to_stdout(self, tmp_path, capsys):
        args = _make_args(tmp_path)
        run_correlate(args)
        out = capsys.readouterr().out
        assert "req=abc GET /api" in out
        assert "req=abc timeout" in out

    def test_unmatched_lines_not_in_stdout(self, tmp_path, capsys):
        args = _make_args(tmp_path)
        run_correlate(args)
        out = capsys.readouterr().out
        assert "req=xyz" not in out

    def test_count_reported_to_stderr(self, tmp_path, capsys):
        args = _make_args(tmp_path)
        run_correlate(args)
        err = capsys.readouterr().err
        assert "2 line(s) matched" in err

    def test_missing_file_returns_one(self, tmp_path, capsys):
        parser = _make_parser()
        args = parser.parse_args(["correlate", str(tmp_path / "nope.log"), "abc"])
        rc = run_correlate(args)
        assert rc == 1
        assert "file not found" in capsys.readouterr().err
