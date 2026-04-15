"""Tests for logslice.cli_watch."""

from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from logslice.cli_watch import add_watch_subparser, run_watch


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_parser() -> tuple[argparse.ArgumentParser, argparse._SubParsersAction]:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command")
    add_watch_subparser(subparsers)
    return parser, subparsers


def _make_args(extra: list[str] | None = None, file: str = "app.log") -> argparse.Namespace:
    parser, _ = _make_parser()
    argv = ["watch", file] + (extra or [])
    return parser.parse_args(argv)


# ---------------------------------------------------------------------------
# Subparser registration
# ---------------------------------------------------------------------------

class TestAddWatchSubparser:
    def test_subparser_registered(self):
        _, subparsers = _make_parser()
        assert "watch" in subparsers.choices

    def test_default_interval(self):
        args = _make_args()
        assert args.interval == 0.5

    def test_custom_interval(self):
        args = _make_args(["--interval", "2.0"])
        assert args.interval == 2.0

    def test_max_idle_default_none(self):
        args = _make_args()
        assert args.max_idle is None

    def test_max_idle_parsed(self):
        args = _make_args(["--max-idle", "10"])
        assert args.max_idle == 10.0

    def test_follow_rotated_default_false(self):
        args = _make_args()
        assert args.follow_rotated is False

    def test_follow_rotated_flag(self):
        args = _make_args(["--follow-rotated"])
        assert args.follow_rotated is True

    def test_color_default_false(self):
        args = _make_args()
        assert args.color is False

    def test_color_flag(self):
        args = _make_args(["--color"])
        assert args.color is True

    def test_func_set_to_run_watch(self):
        args = _make_args()
        assert args.func is run_watch


# ---------------------------------------------------------------------------
# run_watch
# ---------------------------------------------------------------------------

class TestRunWatch:
    def test_missing_file_returns_1(self, tmp_path: Path):
        args = _make_args(file=str(tmp_path / "no_such.log"))
        result = run_watch(args)
        assert result == 1

    def test_empty_file_exits_cleanly(self, tmp_path: Path):
        log = tmp_path / "app.log"
        log.write_text("")
        args = _make_args(file=str(log), extra=["--max-idle", "0.15", "--interval", "0.05"])
        result = run_watch(args)
        assert result == 0
