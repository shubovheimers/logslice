"""Tests for logslice.archiver."""
from __future__ import annotations

import gzip
import bz2
import lzma
from pathlib import Path
from datetime import datetime

import pytest

from logslice.parser import LogLine
from logslice.archiver import ArchiveOptions, archive_lines, iter_archive


def make_line(text: str) -> LogLine:
    return LogLine(raw=text, timestamp=datetime(2024, 1, 1, 12, 0, 0), level="INFO", message=text)


LINES = [make_line(f"line {i}") for i in range(5)]


class TestArchiveOptions:
    def test_default_compression_is_gz(self):
        opts = ArchiveOptions(output_path="out.log")
        assert opts.compression == "gz"

    def test_invalid_compression_raises(self):
        with pytest.raises(ValueError, match="compression"):
            ArchiveOptions(output_path="out.log", compression="zip")

    def test_enabled_when_output_set(self):
        assert ArchiveOptions(output_path="out.log").enabled()

    def test_not_enabled_when_empty(self):
        assert not ArchiveOptions().enabled()

    def test_resolved_path_appends_extension(self):
        opts = ArchiveOptions(output_path="out.log", compression="gz")
        assert opts.resolved_path().name == "out.log.gz"

    def test_resolved_path_no_double_extension(self):
        opts = ArchiveOptions(output_path="out.log.gz", compression="gz")
        assert opts.resolved_path().suffix == ".gz"
        assert "gz.gz" not in opts.resolved_path().name

    def test_resolved_path_none_compression(self):
        opts = ArchiveOptions(output_path="out.log", compression="none")
        assert opts.resolved_path().name == "out.log"


class TestArchiveLines:
    def test_writes_gz_archive(self, tmp_path):
        dest = tmp_path / "archive.log.gz"
        opts = ArchiveOptions(output_path=str(dest), compression="gz", overwrite=True)
        count = archive_lines(iter(LINES), opts)
        assert count == 5
        with gzip.open(dest, "rt") as fh:
            written = fh.readlines()
        assert len(written) == 5

    def test_writes_bz2_archive(self, tmp_path):
        dest = tmp_path / "archive.log.bz2"
        opts = ArchiveOptions(output_path=str(dest), compression="bz2", overwrite=True)
        archive_lines(iter(LINES), opts)
        with bz2.open(dest, "rt") as fh:
            written = fh.readlines()
        assert len(written) == 5

    def test_writes_xz_archive(self, tmp_path):
        dest = tmp_path / "archive.log.xz"
        opts = ArchiveOptions(output_path=str(dest), compression="xz", overwrite=True)
        archive_lines(iter(LINES), opts)
        with lzma.open(dest, "rt") as fh:
            written = fh.readlines()
        assert len(written) == 5

    def test_no_overwrite_raises_if_exists(self, tmp_path):
        dest = tmp_path / "archive.log.gz"
        dest.touch()
        opts = ArchiveOptions(output_path=str(dest), compression="gz", overwrite=False)
        with pytest.raises(FileExistsError):
            archive_lines(iter(LINES), opts)

    def test_overwrite_replaces_file(self, tmp_path):
        dest = tmp_path / "archive.log.gz"
        dest.touch()
        opts = ArchiveOptions(output_path=str(dest), compression="gz", overwrite=True)
        archive_lines(iter(LINES), opts)
        with gzip.open(dest, "rt") as fh:
            assert len(fh.readlines()) == 5

    def test_no_output_path_raises(self):
        opts = ArchiveOptions()
        with pytest.raises(ValueError):
            archive_lines(iter(LINES), opts)

    def test_returns_line_count(self, tmp_path):
        dest = tmp_path / "out.log.gz"
        opts = ArchiveOptions(output_path=str(dest), compression="gz", overwrite=True)
        assert archive_lines(iter(LINES), opts) == 5


class TestIterArchive:
    def test_yields_all_lines(self, tmp_path):
        dest = tmp_path / "out.log.gz"
        opts = ArchiveOptions(output_path=str(dest), compression="gz", overwrite=True)
        result = list(iter_archive(iter(LINES), opts))
        assert result == LINES

    def test_passthrough_when_disabled(self):
        opts = ArchiveOptions()
        result = list(iter_archive(iter(LINES), opts))
        assert result == LINES
