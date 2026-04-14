"""Tests for logslice.rotator."""
from __future__ import annotations

import gzip
from pathlib import Path

import pytest

from logslice.rotator import (
    RotateOptions,
    find_rotated_files,
    iter_rotated_paths,
    _rotation_sort_key,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    base = tmp_path / "app.log"
    base.write_text("current\n")
    (tmp_path / "app.log.1").write_text("rotated 1\n")
    (tmp_path / "app.log.2").write_text("rotated 2\n")
    (tmp_path / "app.log.3").write_text("rotated 3\n")
    gz = tmp_path / "app.log.4.gz"
    gz.write_bytes(gzip.compress(b"rotated 4\n"))
    # unrelated file — must not be picked up
    (tmp_path / "other.log").write_text("other\n")
    return tmp_path


# ---------------------------------------------------------------------------
# RotateOptions
# ---------------------------------------------------------------------------

class TestRotateOptions:
    def test_disabled_by_default(self):
        opts = RotateOptions()
        assert opts.enabled() is False

    def test_enabled_when_follow_rotated_true(self):
        opts = RotateOptions(follow_rotated=True)
        assert opts.enabled() is True

    def test_default_max_rotated(self):
        assert RotateOptions().max_rotated == 10


# ---------------------------------------------------------------------------
# find_rotated_files
# ---------------------------------------------------------------------------

class TestFindRotatedFiles:
    def test_returns_empty_when_disabled(self, log_dir: Path):
        opts = RotateOptions(follow_rotated=False)
        result = find_rotated_files(log_dir / "app.log", opts)
        assert result == []

    def test_finds_numeric_rotated_files(self, log_dir: Path):
        opts = RotateOptions(follow_rotated=True)
        result = find_rotated_files(log_dir / "app.log", opts)
        names = {p.name for p in result}
        assert "app.log.1" in names
        assert "app.log.2" in names
        assert "app.log.3" in names

    def test_finds_gz_rotated_file(self, log_dir: Path):
        opts = RotateOptions(follow_rotated=True)
        result = find_rotated_files(log_dir / "app.log", opts)
        names = {p.name for p in result}
        assert "app.log.4.gz" in names

    def test_does_not_include_base_file(self, log_dir: Path):
        opts = RotateOptions(follow_rotated=True)
        result = find_rotated_files(log_dir / "app.log", opts)
        assert log_dir / "app.log" not in result

    def test_does_not_include_unrelated_files(self, log_dir: Path):
        opts = RotateOptions(follow_rotated=True)
        result = find_rotated_files(log_dir / "app.log", opts)
        names = {p.name for p in result}
        assert "other.log" not in names

    def test_max_rotated_limits_results(self, log_dir: Path):
        opts = RotateOptions(follow_rotated=True, max_rotated=2)
        result = find_rotated_files(log_dir / "app.log", opts)
        assert len(result) <= 2

    def test_bad_directory_returns_empty(self, tmp_path: Path):
        opts = RotateOptions(follow_rotated=True)
        result = find_rotated_files(tmp_path / "missing" / "app.log", opts)
        assert result == []


# ---------------------------------------------------------------------------
# iter_rotated_paths
# ---------------------------------------------------------------------------

class TestIterRotatedPaths:
    def test_base_last_when_include_base(self, log_dir: Path):
        opts = RotateOptions(follow_rotated=True)
        paths = list(iter_rotated_paths(log_dir / "app.log", opts))
        assert paths[-1] == log_dir / "app.log"

    def test_base_excluded_when_flag_false(self, log_dir: Path):
        opts = RotateOptions(follow_rotated=True)
        paths = list(iter_rotated_paths(log_dir / "app.log", opts, include_base=False))
        assert log_dir / "app.log" not in paths

    def test_only_base_when_disabled(self, log_dir: Path):
        opts = RotateOptions(follow_rotated=False)
        paths = list(iter_rotated_paths(log_dir / "app.log", opts))
        assert paths == [log_dir / "app.log"]


# ---------------------------------------------------------------------------
# _rotation_sort_key
# ---------------------------------------------------------------------------

def test_sort_key_numeric():
    p = Path("app.log.3")
    assert _rotation_sort_key(p) == (1, 3)


def test_sort_key_date():
    p = Path("app.log.2023-06-15")
    assert _rotation_sort_key(p) == (0, "2023-06-15")


def test_sort_key_fallback():
    p = Path("app.log.bak")
    assert _rotation_sort_key(p)[0] == 2
