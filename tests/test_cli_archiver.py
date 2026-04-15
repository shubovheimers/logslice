"""Tests for logslice.cli_archiver."""
from __future__ import annotations

import argparse
import gzip
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from logslice.cli_archiver import add_archive_subparser, run_archive


def _make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_archive_subparser(sub)
    return parser


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = dict(
        input="app.log",
        output="app.log.gz",
        compression="gz",
        overwrite=False,
        level=None,
        pattern=None,
        func=run_archive,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


class TestAddArchiveSubparser:
    def test_subparser_registered(self):
        parser = _make_parser()
        args = parser.parse_args(["archive", "app.log", "-o", "out.log.gz"])
        assert args.func is run_archive

    def test_default_compression_gz(self):
        parser = _make_parser()
        args = parser.parse_args(["archive", "app.log", "-o", "out.log.gz"])
        assert args.compression == "gz"

    def test_custom_compression(self):
        parser = _make_parser()
        args = parser.parse_args(["archive", "app.log", "-o", "out.log.bz2", "--compression", "bz2"])
        assert args.compression == "bz2"

    def test_overwrite_defaults_false(self):
        parser = _make_parser()
        args = parser.parse_args(["archive", "app.log", "-o", "out.log.gz"])
        assert args.overwrite is False

    def test_overwrite_flag(self):
        parser = _make_parser()
        args = parser.parse_args(["archive", "app.log", "-o", "out.log.gz", "--overwrite"])
        assert args.overwrite is True

    def test_level_defaults_none(self):
        parser = _make_parser()
        args = parser.parse_args(["archive", "app.log", "-o", "out.log.gz"])
        assert args.level is None

    def test_pattern_defaults_none(self):
        parser = _make_parser()
        args = parser.parse_args(["archive", "app.log", "-o", "out.log.gz"])
        assert args.pattern is None


class TestRunArchive:
    def test_returns_zero_on_success(self, tmp_path, capsys):
        log_file = tmp_path / "app.log"
        log_file.write_text("2024-01-01T12:00:00 INFO hello\n")
        dest = tmp_path / "out.log.gz"
        args = _make_args(input=str(log_file), output=str(dest), overwrite=True)
        result = run_archive(args)
        assert result == 0

    def test_prints_summary(self, tmp_path, capsys):
        log_file = tmp_path / "app.log"
        log_file.write_text("2024-01-01T12:00:00 INFO hello\n")
        dest = tmp_path / "out.log.gz"
        args = _make_args(input=str(log_file), output=str(dest), overwrite=True)
        run_archive(args)
        out = capsys.readouterr().out
        assert "Archived" in out
        assert "1 line" in out

    def test_archive_file_created(self, tmp_path):
        log_file = tmp_path / "app.log"
        log_file.write_text("2024-01-01T12:00:00 INFO hello\n")
        dest = tmp_path / "out.log.gz"
        args = _make_args(input=str(log_file), output=str(dest), overwrite=True)
        run_archive(args)
        assert dest.exists()
        with gzip.open(dest, "rt") as fh:
            lines = fh.readlines()
        assert len(lines) == 1
