"""Tests for logslice.cli_split."""

from __future__ import annotations

import argparse
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from logslice.cli_split import add_split_subparser, run_split
from logslice.parser import LogLine


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "file": "test.log",
        "lines": None,
        "time_window": None,
        "output_dir": ".",
        "prefix": "part",
        "suffix": ".log",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddSplitSubparser:
    def test_subparser_registered(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_split_subparser(sub)
        args = parser.parse_args(["split", "myfile.log", "--lines", "50"])
        assert args.file == "myfile.log"
        assert args.lines == 50

    def test_default_output_dir(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_split_subparser(sub)
        args = parser.parse_args(["split", "f.log", "--lines", "10"])
        assert args.output_dir == "."

    def test_time_window_parsed(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_split_subparser(sub)
        args = parser.parse_args(["split", "f.log", "--time-window", "300"])
        assert args.time_window == 300


class TestRunSplit:
    def _fake_lines(self, n: int):
        return [LogLine(raw=f"line {i}", timestamp=None, level=None, message=f"line {i}") for i in range(n)]

    def test_returns_1_when_no_strategy(self):
        args = _make_args(lines=None, time_window=None)
        assert run_split(args) == 1

    def test_split_by_lines_creates_parts(self, tmp_path):
        args = _make_args(lines=3, output_dir=str(tmp_path))
        with patch("logslice.cli_split.iter_lines", return_value=self._fake_lines(7)):
            result = run_split(args)
        assert result == 0
        parts = list(tmp_path.glob("part_*.log"))
        assert len(parts) == 3  # 3+3+1

    def test_split_by_time_window(self, tmp_path):
        from datetime import datetime, timedelta
        base = datetime(2024, 1, 1, 0, 0, 0)
        lines = [
            LogLine(raw=f"l{i}", timestamp=base + timedelta(seconds=i * 10), level=None, message=f"l{i}")
            for i in range(4)
        ] + [
            LogLine(raw="gap", timestamp=base + timedelta(seconds=500), level=None, message="gap"),
        ]
        args = _make_args(time_window=60, output_dir=str(tmp_path))
        with patch("logslice.cli_split.iter_lines", return_value=lines):
            result = run_split(args)
        assert result == 0
        parts = list(tmp_path.glob("part_*.log"))
        assert len(parts) == 2

    def test_output_files_contain_raw_text(self, tmp_path):
        args = _make_args(lines=10, output_dir=str(tmp_path))
        with patch("logslice.cli_split.iter_lines", return_value=self._fake_lines(3)):
            run_split(args)
        parts = sorted(tmp_path.glob("part_*.log"))
        content = parts[0].read_text()
        assert "line 0" in content
