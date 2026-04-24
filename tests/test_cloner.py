"""Tests for logslice.cloner."""
from __future__ import annotations

import pytest

from logslice.parser import LogLine
from logslice.cloner import CloneOptions, clone_lines


def make_line(raw: str = "hello", level: str = "INFO") -> LogLine:
    return LogLine(raw=raw, timestamp=None, level=level, message=raw, extra={})


def collect(lines):
    return list(clone_lines(lines, None))


# ---------------------------------------------------------------------------
# CloneOptions
# ---------------------------------------------------------------------------

class TestCloneOptions:
    def test_defaults_not_enabled(self):
        assert CloneOptions().enabled is False

    def test_positive_copies_enables(self):
        assert CloneOptions(copies=2).enabled is True

    def test_negative_copies_raises(self):
        with pytest.raises(ValueError):
            CloneOptions(copies=-1)

    def test_zero_copies_not_enabled(self):
        assert CloneOptions(copies=0).enabled is False


# ---------------------------------------------------------------------------
# clone_lines – disabled / passthrough
# ---------------------------------------------------------------------------

class TestCloneLinesDisabled:
    def test_none_opts_passthrough(self):
        lines = [make_line("a"), make_line("b")]
        assert collect(lines) == lines

    def test_zero_copies_passthrough(self):
        lines = [make_line("x")]
        result = list(clone_lines(lines, CloneOptions(copies=0)))
        assert result == lines


# ---------------------------------------------------------------------------
# clone_lines – basic cloning
# ---------------------------------------------------------------------------

class TestCloneLines:
    def test_one_copy_doubles_each_line(self):
        lines = [make_line("a"), make_line("b")]
        result = list(clone_lines(lines, CloneOptions(copies=1)))
        assert len(result) == 4

    def test_two_copies_triples_each_line(self):
        line = make_line("x")
        result = list(clone_lines([line], CloneOptions(copies=2)))
        assert len(result) == 3

    def test_original_is_first(self):
        line = make_line("original")
        result = list(clone_lines([line], CloneOptions(copies=1)))
        assert result[0] is line

    def test_empty_input_yields_nothing(self):
        result = list(clone_lines([], CloneOptions(copies=3)))
        assert result == []


# ---------------------------------------------------------------------------
# clone_lines – pattern filter
# ---------------------------------------------------------------------------

class TestCloneLinesPattern:
    def test_only_matching_lines_cloned(self):
        lines = [make_line("ERROR: disk full"), make_line("INFO: ok")]
        opts = CloneOptions(copies=1, pattern="ERROR")
        result = list(clone_lines(lines, opts))
        # first line cloned (×2), second not (×1)
        assert len(result) == 3

    def test_no_match_no_clone(self):
        lines = [make_line("INFO: all good")]
        opts = CloneOptions(copies=2, pattern="ERROR")
        result = list(clone_lines(lines, opts))
        assert len(result) == 1


# ---------------------------------------------------------------------------
# clone_lines – level filter
# ---------------------------------------------------------------------------

class TestCloneLinesLevel:
    def test_matching_level_cloned(self):
        lines = [make_line(level="ERROR"), make_line(level="DEBUG")]
        opts = CloneOptions(copies=1, levels=["ERROR"])
        result = list(clone_lines(lines, opts))
        assert len(result) == 3

    def test_case_insensitive_level(self):
        lines = [make_line(level="error")]
        opts = CloneOptions(copies=1, levels=["ERROR"])
        result = list(clone_lines(lines, opts))
        assert len(result) == 2


# ---------------------------------------------------------------------------
# clone_lines – tag_clones
# ---------------------------------------------------------------------------

class TestCloneLinesTagging:
    def test_clone_tagged_when_flag_set(self):
        line = make_line("msg")
        opts = CloneOptions(copies=1, tag_clones=True)
        result = list(clone_lines([line], opts))
        assert result[0].extra.get("_clone") is not True
        assert result[1].extra.get("_clone") is True

    def test_original_not_tagged(self):
        line = make_line("msg")
        opts = CloneOptions(copies=2, tag_clones=True)
        result = list(clone_lines([line], opts))
        assert "_clone" not in result[0].extra
