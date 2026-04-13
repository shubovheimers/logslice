"""Tests for logslice.cli_summarize."""
from __future__ import annotations

import argparse
from unittest.mock import MagicMock, patch

import pytest

from logslice.cli_summarize import add_summarize_subparser, run_summarize
from logslice.summarizer import LogSummary


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "file": "app.log",
        "top_n": 10,
        "no_levels": False,
        "no_patterns": False,
        "func": run_summarize,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddSummarizeSubparser:
    def test_subparser_registered(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_summarize_subparser(sub)
        args = parser.parse_args(["summarize", "my.log"])
        assert args.file == "my.log"

    def test_default_top_n(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_summarize_subparser(sub)
        args = parser.parse_args(["summarize", "my.log"])
        assert args.top_n == 10

    def test_custom_top_n(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_summarize_subparser(sub)
        args = parser.parse_args(["summarize", "my.log", "--top-n", "5"])
        assert args.top_n == 5

    def test_no_levels_flag(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_summarize_subparser(sub)
        args = parser.parse_args(["summarize", "my.log", "--no-levels"])
        assert args.no_levels is True

    def test_no_patterns_flag(self):
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        add_summarize_subparser(sub)
        args = parser.parse_args(["summarize", "my.log", "--no-patterns"])
        assert args.no_patterns is True


class TestRunSummarize:
    def _run(self, args, fake_lines=None, summary=None):
        if fake_lines is None:
            fake_lines = []
        if summary is None:
            summary = LogSummary(total_lines=0)
        with patch("logslice.cli_summarize.iter_lines", return_value=fake_lines), \
             patch("logslice.cli_summarize.summarize_lines", return_value=summary), \
             patch("logslice.cli_summarize.format_summary", return_value="SUMMARY") as fmt, \
             patch("builtins.print") as mock_print:
            code = run_summarize(args)
        return code, mock_print

    def test_returns_zero_on_success(self):
        code, _ = self._run(_make_args())
        assert code == 0

    def test_prints_summary(self):
        code, mock_print = self._run(_make_args())
        mock_print.assert_called_once_with("SUMMARY")

    def test_returns_one_on_file_not_found(self):
        args = _make_args(file="missing.log")
        with patch("logslice.cli_summarize.iter_lines", side_effect=FileNotFoundError), \
             patch("builtins.print"):
            code = run_summarize(args)
        assert code == 1

    def test_returns_one_on_os_error(self):
        args = _make_args()
        with patch("logslice.cli_summarize.iter_lines", side_effect=OSError("boom")), \
             patch("builtins.print"):
            code = run_summarize(args)
        assert code == 1
