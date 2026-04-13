"""Tests for logslice.output."""

from __future__ import annotations

import gzip
from datetime import datetime
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from logslice.formatter import FormatOptions
from logslice.highlighter import HighlightOptions, LEVEL_COLORS, RESET
from logslice.output import write_lines
from logslice.parser import LogLine


def make_line(raw: str = "INFO hello world", level: str = "INFO") -> LogLine:
    return LogLine(
        raw=raw,
        timestamp=datetime(2024, 1, 15, 10, 0, 0),
        level=level,
        message="hello world",
    )


class TestWriteLinesToStdout:
    def test_returns_line_count(self, capsys):
        lines = [make_line(), make_line()]
        count = write_lines(lines)
        assert count == 2

    def test_output_written_to_stdout(self, capsys):
        write_lines([make_line(raw="INFO hello world")])
        captured = capsys.readouterr()
        assert "INFO hello world" in captured.out

    def test_empty_iterable_returns_zero(self, capsys):
        count = write_lines([])
        assert count == 0


class TestCountOnly:
    def test_count_only_does_not_write(self, capsys):
        write_lines([make_line(), make_line(), make_line()], count_only=True)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_count_only_returns_correct_count(self):
        count = write_lines([make_line()] * 5, count_only=True)
        assert count == 5


class TestWriteLinesToFile:
    def test_writes_to_plain_file(self, tmp_path):
        dest = tmp_path / "out.log"
        write_lines([make_line(raw="ERROR oops")], dest=dest)
        assert "ERROR oops" in dest.read_text()

    def test_writes_multiple_lines(self, tmp_path):
        dest = tmp_path / "out.log"
        lines = [make_line(raw=f"INFO line {i}") for i in range(3)]
        count = write_lines(lines, dest=dest)
        assert count == 3
        text = dest.read_text()
        for i in range(3):
            assert f"INFO line {i}" in text

    def test_writes_to_gz_file(self, tmp_path):
        dest = tmp_path / "out.log.gz"
        write_lines([make_line(raw="DEBUG compressed")], dest=dest)
        with gzip.open(dest, "rt", encoding="utf-8") as fh:
            content = fh.read()
        assert "DEBUG compressed" in content


class TestHighlightingIntegration:
    def test_highlight_pattern_applied(self, capsys):
        hl = HighlightOptions(colorize_levels=False, highlight_patterns=["hello"])
        write_lines([make_line(raw="INFO hello world")], hl_opts=hl)
        captured = capsys.readouterr()
        assert RESET in captured.out
