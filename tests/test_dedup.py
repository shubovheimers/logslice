"""Tests for logslice.dedup."""

from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogLine
from logslice.dedup import DedupOptions, count_duplicates, dedup_lines


def make_line(message: str, raw: str | None = None) -> LogLine:
    return LogLine(
        raw=raw or message,
        timestamp=datetime(2024, 6, 1, 12, 0, 0),
        level="INFO",
        message=message,
    )


class TestDedupDisabled:
    def test_passthrough_when_disabled(self):
        lines = [make_line("a"), make_line("a"), make_line("b")]
        opts = DedupOptions(enabled=False)
        assert list(dedup_lines(lines, opts)) == lines

    def test_passthrough_when_opts_none(self):
        lines = [make_line("x"), make_line("x")]
        assert list(dedup_lines(lines, None)) == lines


class TestDedupEnabled:
    def test_removes_exact_duplicates(self):
        lines = [make_line("hello"), make_line("hello"), make_line("world")]
        opts = DedupOptions(enabled=True)
        result = list(dedup_lines(lines, opts))
        assert len(result) == 2
        assert result[0].message == "hello"
        assert result[1].message == "world"

    def test_preserves_order(self):
        lines = [make_line("a"), make_line("b"), make_line("a"), make_line("c")]
        opts = DedupOptions(enabled=True)
        result = list(dedup_lines(lines, opts))
        assert [r.message for r in result] == ["a", "b", "c"]

    def test_all_unique_unchanged(self):
        lines = [make_line(str(i)) for i in range(10)]
        opts = DedupOptions(enabled=True)
        assert list(dedup_lines(lines, opts)) == lines

    def test_custom_key_fn(self):
        # Deduplicate by first character only
        lines = [make_line("apple"), make_line("avocado"), make_line("banana")]
        opts = DedupOptions(enabled=True, key_fn=lambda l: l.message[0])
        result = list(dedup_lines(lines, opts))
        assert len(result) == 2
        assert result[0].message == "apple"
        assert result[1].message == "banana"

    def test_empty_stream(self):
        opts = DedupOptions(enabled=True)
        assert list(dedup_lines([], opts)) == []


class TestCountDuplicates:
    def test_no_dupes(self):
        lines = [make_line("a"), make_line("b"), make_line("c")]
        assert count_duplicates(lines) == 0

    def test_some_dupes(self):
        lines = [make_line("x"), make_line("x"), make_line("y"), make_line("x")]
        assert count_duplicates(lines) == 2

    def test_all_same(self):
        lines = [make_line("z")] * 5
        assert count_duplicates(lines) == 4

    def test_custom_key_fn(self):
        lines = [make_line("foo1"), make_line("foo2"), make_line("bar")]
        # key = first 3 chars → "foo" appears twice
        assert count_duplicates(lines, key_fn=lambda l: l.message[:3]) == 1
