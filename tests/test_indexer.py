"""Tests for logslice.indexer."""

from __future__ import annotations

import gzip
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from logslice.indexer import (
    IndexEntry,
    LogIndex,
    build_index,
    load_index,
    save_index,
)


SAMPLE_LINES = [
    "2024-01-01T00:00:01 INFO  line one\n",
    "2024-01-01T00:00:02 DEBUG line two\n",
    "2024-01-01T00:00:03 ERROR line three\n",
    "2024-01-01T00:00:04 WARN  line four\n",
    "2024-01-01T00:00:05 INFO  line five\n",
]


@pytest.fixture()
def plain_log(tmp_path):
    p = tmp_path / "app.log"
    p.write_text("".join(SAMPLE_LINES))
    return str(p)


@pytest.fixture()
def gz_log(tmp_path):
    p = tmp_path / "app.log.gz"
    with gzip.open(str(p), "wt") as fh:
        fh.write("".join(SAMPLE_LINES))
    return str(p)


class TestBuildIndex:
    def test_returns_log_index(self, plain_log):
        idx = build_index(plain_log, sample_every=1)
        assert isinstance(idx, LogIndex)

    def test_entry_count_matches_sample_rate(self, plain_log):
        idx = build_index(plain_log, sample_every=2)
        # lines 0, 2, 4 → 3 entries
        assert len(idx.entries) == 3

    def test_all_lines_sampled_at_1(self, plain_log):
        idx = build_index(plain_log, sample_every=1)
        assert len(idx.entries) == len(SAMPLE_LINES)

    def test_mtime_recorded(self, plain_log):
        idx = build_index(plain_log)
        assert idx.source_mtime == os.path.getmtime(plain_log)

    def test_gz_file_indexed(self, gz_log):
        idx = build_index(gz_log, sample_every=1)
        assert len(idx.entries) == len(SAMPLE_LINES)

    def test_timestamps_parsed(self, plain_log):
        idx = build_index(plain_log, sample_every=1)
        assert all(e.timestamp is not None for e in idx.entries)


class TestLogIndexIsValid:
    def test_valid_for_unchanged_file(self, plain_log):
        idx = build_index(plain_log)
        assert idx.is_valid_for(plain_log) is True

    def test_invalid_after_modification(self, plain_log):
        idx = build_index(plain_log)
        Path(plain_log).write_text("new content\n")
        assert idx.is_valid_for(plain_log) is False

    def test_invalid_for_missing_file(self, plain_log):
        idx = build_index(plain_log)
        os.remove(plain_log)
        assert idx.is_valid_for(plain_log) is False


class TestFindOffset:
    def test_returns_zero_for_empty_entries(self):
        idx = LogIndex(source_path="x", source_mtime=0.0, entries=[])
        assert idx.find_offset(datetime(2024, 1, 1)) == 0

    def test_finds_correct_entry(self, plain_log):
        idx = build_index(plain_log, sample_every=1)
        target = datetime(2024, 1, 1, 0, 0, 3)
        offset = idx.find_offset(target)
        assert offset >= 0


class TestSaveLoadIndex:
    def test_round_trip(self, plain_log, tmp_path):
        idx = build_index(plain_log, sample_every=1)
        idx_path = str(tmp_path / "app.idx")
        save_index(idx, idx_path)
        loaded = load_index(idx_path)
        assert loaded.source_path == idx.source_path
        assert len(loaded.entries) == len(idx.entries)

    def test_timestamps_preserved(self, plain_log, tmp_path):
        idx = build_index(plain_log, sample_every=1)
        idx_path = str(tmp_path / "app.idx")
        save_index(idx, idx_path)
        loaded = load_index(idx_path)
        for orig, restored in zip(idx.entries, loaded.entries):
            assert orig.timestamp == restored.timestamp
