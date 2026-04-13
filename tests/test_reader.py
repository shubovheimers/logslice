"""Tests for logslice.reader module."""

import gzip
import os
import tempfile
import textwrap
from datetime import datetime

import pytest

from logslice.reader import iter_lines, iter_lines_raw, count_lines, open_log_file


SAMPLE_LOG = textwrap.dedent("""\
    2024-01-15T10:00:00 INFO  Starting application
    2024-01-15T10:00:01 DEBUG Loaded config
    2024-01-15T10:00:02 ERROR Something went wrong
    not a valid log line
    2024-01-15T10:00:03 WARN  Retrying connection
""")


@pytest.fixture()
def plain_log(tmp_path):
    p = tmp_path / "app.log"
    p.write_text(SAMPLE_LOG, encoding="utf-8")
    return str(p)


@pytest.fixture()
def gz_log(tmp_path):
    p = tmp_path / "app.log.gz"
    with gzip.open(str(p), "wt", encoding="utf-8") as fh:
        fh.write(SAMPLE_LOG)
    return str(p)


class TestIterLines:
    def test_yields_parsed_lines(self, plain_log):
        lines = list(iter_lines(plain_log))
        assert len(lines) == 4  # unparseable line skipped

    def test_timestamps_are_datetime(self, plain_log):
        for line in iter_lines(plain_log):
            assert isinstance(line.timestamp, datetime)

    def test_skip_unparseable_false(self, plain_log):
        lines = list(iter_lines(plain_log, skip_unparseable=False))
        assert len(lines) == 5
        none_ts = [l for l in lines if l.timestamp is None]
        assert len(none_ts) == 1

    def test_reads_gz_file(self, gz_log):
        lines = list(iter_lines(gz_log))
        assert len(lines) == 4

    def test_levels_parsed(self, plain_log):
        lines = list(iter_lines(plain_log))
        levels = [l.level for l in lines]
        assert "ERROR" in levels
        assert "DEBUG" in levels


class TestIterLinesRaw:
    def test_yields_all_raw_lines(self, plain_log):
        raw = list(iter_lines_raw(plain_log))
        # SAMPLE_LOG has 5 non-empty lines + trailing newline yields 5 lines
        assert len(raw) == 5

    def test_no_trailing_newline(self, plain_log):
        for line in iter_lines_raw(plain_log):
            assert not line.endswith("\n")


class TestCountLines:
    def test_count_plain(self, plain_log):
        assert count_lines(plain_log) == 5

    def test_count_gz(self, gz_log):
        assert count_lines(gz_log) == 5
