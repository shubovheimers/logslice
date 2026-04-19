"""Tests for logslice.pruner."""
from __future__ import annotations

import pytest

from logslice.parser import LogLine
from logslice.pruner import PruneOptions, prune_lines


def make_line(text: str) -> LogLine:
    return LogLine(raw=text, timestamp=None, level=None, message=text, extra={})


class TestPruneOptions:
    def test_defaults_not_active(self):
        opts = PruneOptions()
        assert not opts.is_active()

    def test_enabled_with_positive_min_length_is_active(self):
        opts = PruneOptions(enabled=True, min_length=5)
        assert opts.is_active()

    def test_enabled_with_zero_min_length_not_active(self):
        opts = PruneOptions(enabled=True, min_length=0)
        assert not opts.is_active()

    def test_negative_min_length_raises(self):
        with pytest.raises(ValueError):
            PruneOptions(min_length=-1)


class TestPruneLines:
    def _collect(self, lines, opts):
        return list(prune_lines(lines, opts))

    def test_passthrough_when_disabled(self):
        lines = [make_line("hi"), make_line("")]
        result = self._collect(lines, PruneOptions(enabled=False, min_length=5))
        assert len(result) == 2

    def test_passthrough_when_opts_none(self):
        lines = [make_line(""), make_line("x")]
        result = self._collect(lines, None)
        assert len(result) == 2

    def test_drops_short_lines(self):
        lines = [make_line("hi"), make_line("hello world"), make_line("no")]
        opts = PruneOptions(enabled=True, min_length=5)
        result = self._collect(lines, opts)
        assert len(result) == 1
        assert result[0].raw == "hello world"

    def test_keeps_exact_length(self):
        lines = [make_line("exact")]
        opts = PruneOptions(enabled=True, min_length=5)
        result = self._collect(lines, opts)
        assert len(result) == 1

    def test_strip_whitespace_before_measuring(self):
        lines = [make_line("   hi   ")]
        opts = PruneOptions(enabled=True, min_length=5, strip_whitespace=True)
        result = self._collect(lines, opts)
        assert len(result) == 0

    def test_no_strip_counts_whitespace(self):
        lines = [make_line("   hi   ")]
        opts = PruneOptions(enabled=True, min_length=5, strip_whitespace=False)
        result = self._collect(lines, opts)
        assert len(result) == 1

    def test_empty_iterable(self):
        result = self._collect([], PruneOptions(enabled=True, min_length=1))
        assert result == []
