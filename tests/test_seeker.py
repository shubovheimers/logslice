"""Tests for logslice.seeker."""

from __future__ import annotations

import gzip
from datetime import datetime
from pathlib import Path

import pytest

from logslice.indexer import build_index
from logslice.seeker import iter_from_offset, seek_and_iter


SAMPLE_LINES = [
    "2024-03-01T10:00:01 INFO  alpha\n",
    "2024-03-01T10:00:02 DEBUG beta\n",
    "2024-03-01T10:00:03 ERROR gamma\n",
    "2024-03-01T10:00:04 WARN  delta\n",
    "2024-03-01T10:00:05 INFO  epsilon\n",
]


@pytest.fixture()
def plain_log(tmp_path):
    p = tmp_path / "seek.log"
    p.write_text("".join(SAMPLE_LINES))
    return str(p)


@pytest.fixture()
def gz_log(tmp_path):
    p = tmp_path / "seek.log.gz"
    with gzip.open(str(p), "wt") as fh:
        fh.write("".join(SAMPLE_LINES))
    return str(p)


class TestIterFromOffset:
    def test_offset_zero_yields_all(self, plain_log):
        lines = list(iter_from_offset(plain_log, offset=0))
        assert len(lines) == len(SAMPLE_LINES)

    def test_nonzero_offset_skips_lines(self, plain_log):
        first_line_len = len(SAMPLE_LINES[0].encode())
        lines = list(iter_from_offset(plain_log, offset=first_line_len))
        assert len(lines) == len(SAMPLE_LINES) - 1

    def test_end_filter_stops_early(self, plain_log):
        end = datetime(2024, 3, 1, 10, 0, 3)
        lines = list(iter_from_offset(plain_log, offset=0, end=end))
        assert all(ln.timestamp is None or ln.timestamp <= end for ln in lines)

    def test_start_filter_skips_early_lines(self, plain_log):
        start = datetime(2024, 3, 1, 10, 0, 3)
        lines = list(iter_from_offset(plain_log, offset=0, start=start))
        assert all(ln.timestamp is None or ln.timestamp >= start for ln in lines)


class TestSeekAndIter:
    def test_no_bounds_yields_all(self, plain_log):
        lines = list(seek_and_iter(plain_log))
        assert len(lines) == len(SAMPLE_LINES)

    def test_start_bound_filters_results(self, plain_log):
        start = datetime(2024, 3, 1, 10, 0, 3)
        lines = list(seek_and_iter(plain_log, start=start))
        assert all(ln.timestamp is None or ln.timestamp >= start for ln in lines)

    def test_end_bound_filters_results(self, plain_log):
        end = datetime(2024, 3, 1, 10, 0, 3)
        lines = list(seek_and_iter(plain_log, end=end))
        assert all(ln.timestamp is None or ln.timestamp <= end for ln in lines)

    def test_prebuilt_index_accepted(self, plain_log):
        idx = build_index(plain_log, sample_every=1)
        lines = list(seek_and_iter(plain_log, index=idx))
        assert len(lines) == len(SAMPLE_LINES)

    def test_gz_file_works(self, gz_log):
        lines = list(seek_and_iter(gz_log))
        assert len(lines) == len(SAMPLE_LINES)

    def test_returns_log_line_objects(self, plain_log):
        from logslice.parser import LogLine
        lines = list(seek_and_iter(plain_log))
        assert all(isinstance(ln, LogLine) for ln in lines)
