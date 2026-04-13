"""Tests for logslice.bookmarks."""

from __future__ import annotations

import pytest
from pathlib import Path

from logslice.bookmarks import (
    Bookmark,
    save_bookmark,
    load_bookmark,
    delete_bookmark,
    list_bookmarks,
)


@pytest.fixture
def bm_dir(tmp_path: Path) -> Path:
    return tmp_path / "bookmarks"


def make_bookmark(name: str = "test", offset: int = 0, line: int = 1) -> Bookmark:
    return Bookmark(name=name, filepath="/var/log/app.log", offset=offset, line_number=line)


class TestBookmarkRoundtrip:
    def test_save_creates_file(self, bm_dir):
        bm = make_bookmark("mymark")
        path = save_bookmark(bm, bm_dir)
        assert path.exists()

    def test_load_returns_bookmark(self, bm_dir):
        bm = make_bookmark("mymark", offset=1024, line=42)
        save_bookmark(bm, bm_dir)
        loaded = load_bookmark("mymark", bm_dir)
        assert loaded is not None
        assert loaded.name == "mymark"
        assert loaded.offset == 1024
        assert loaded.line_number == 42

    def test_load_missing_returns_none(self, bm_dir):
        result = load_bookmark("nonexistent", bm_dir)
        assert result is None

    def test_roundtrip_with_timestamp(self, bm_dir):
        bm = Bookmark(name="ts", filepath="/logs/x.log", offset=512, line_number=10, timestamp="2024-01-15T08:00:00")
        save_bookmark(bm, bm_dir)
        loaded = load_bookmark("ts", bm_dir)
        assert loaded.timestamp == "2024-01-15T08:00:00"

    def test_as_dict_contains_all_fields(self):
        bm = make_bookmark("x", offset=99, line=7)
        d = bm.as_dict()
        assert set(d.keys()) == {"name", "filepath", "offset", "line_number", "timestamp"}

    def test_from_dict_roundtrip(self):
        bm = make_bookmark("y", offset=200, line=5)
        restored = Bookmark.from_dict(bm.as_dict())
        assert restored == bm


class TestDeleteBookmark:
    def test_delete_existing_returns_true(self, bm_dir):
        bm = make_bookmark("del_me")
        save_bookmark(bm, bm_dir)
        assert delete_bookmark("del_me", bm_dir) is True

    def test_delete_missing_returns_false(self, bm_dir):
        assert delete_bookmark("ghost", bm_dir) is False

    def test_deleted_bookmark_not_loadable(self, bm_dir):
        bm = make_bookmark("gone")
        save_bookmark(bm, bm_dir)
        delete_bookmark("gone", bm_dir)
        assert load_bookmark("gone", bm_dir) is None


class TestListBookmarks:
    def test_empty_dir_returns_empty(self, bm_dir):
        assert list_bookmarks(bm_dir) == []

    def test_nonexistent_dir_returns_empty(self, tmp_path):
        assert list_bookmarks(tmp_path / "nope") == []

    def test_lists_all_saved(self, bm_dir):
        for name in ["alpha", "beta", "gamma"]:
            save_bookmark(make_bookmark(name), bm_dir)
        result = list_bookmarks(bm_dir)
        assert len(result) == 3
        assert [b.name for b in result] == ["alpha", "beta", "gamma"]

    def test_sorted_by_name(self, bm_dir):
        for name in ["zebra", "apple", "mango"]:
            save_bookmark(make_bookmark(name), bm_dir)
        names = [b.name for b in list_bookmarks(bm_dir)]
        assert names == sorted(names)
