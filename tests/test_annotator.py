"""Tests for logslice.annotator."""
from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.annotator import AnnotateOptions, annotate_lines
from logslice.parser import LogLine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_line(text: str = "some log message", level: str = "INFO") -> LogLine:
    return LogLine(
        raw=text,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=text,
    )


def collect(lines, opts) -> List[LogLine]:
    return list(annotate_lines(lines, opts))


# ---------------------------------------------------------------------------
# AnnotateOptions.enabled
# ---------------------------------------------------------------------------

class TestAnnotateOptions:
    def test_defaults_not_enabled(self):
        assert not AnnotateOptions().enabled()

    def test_sequence_enables(self):
        assert AnnotateOptions(sequence=True).enabled()

    def test_source_tag_enables(self):
        assert AnnotateOptions(source_tag="app").enabled()

    def test_labels_enables(self):
        assert AnnotateOptions(labels={"env": "prod"}).enabled()


# ---------------------------------------------------------------------------
# annotate_lines – passthrough
# ---------------------------------------------------------------------------

class TestAnnotateLinesPassthrough:
    def test_none_opts_yields_unchanged(self):
        lines = [make_line("a"), make_line("b")]
        result = collect(lines, None)
        assert [l.raw for l in result] == ["a", "b"]

    def test_disabled_opts_yields_unchanged(self):
        lines = [make_line("x")]
        result = collect(lines, AnnotateOptions())
        assert result[0].raw == "x"


# ---------------------------------------------------------------------------
# annotate_lines – sequence numbers
# ---------------------------------------------------------------------------

class TestSequenceAnnotation:
    def test_sequence_prepended(self):
        lines = [make_line("msg")]
        result = collect(lines, AnnotateOptions(sequence=True))
        assert result[0].raw == "[1] msg"

    def test_sequence_increments(self):
        lines = [make_line("a"), make_line("b"), make_line("c")]
        result = collect(lines, AnnotateOptions(sequence=True))
        assert result[0].raw.startswith("[1]")
        assert result[1].raw.startswith("[2]")
        assert result[2].raw.startswith("[3]")

    def test_original_fields_preserved(self):
        line = make_line("hello", level="ERROR")
        result = collect([line], AnnotateOptions(sequence=True))
        assert result[0].level == "ERROR"
        assert result[0].timestamp == line.timestamp


# ---------------------------------------------------------------------------
# annotate_lines – source tag
# ---------------------------------------------------------------------------

class TestSourceTagAnnotation:
    def test_tag_prepended(self):
        lines = [make_line("msg")]
        result = collect(lines, AnnotateOptions(source_tag="svc-a"))
        assert result[0].raw == "[svc-a] msg"

    def test_multiple_lines_all_tagged(self):
        lines = [make_line("x"), make_line("y")]
        result = collect(lines, AnnotateOptions(source_tag="node1"))
        assert all(l.raw.startswith("[node1]") for l in result)


# ---------------------------------------------------------------------------
# annotate_lines – labels
# ---------------------------------------------------------------------------

class TestLabelAnnotation:
    def test_single_label_appended(self):
        lines = [make_line("msg")]
        result = collect(lines, AnnotateOptions(labels={"env": "prod"}))
        assert "env=prod" in result[0].raw

    def test_multiple_labels_sorted(self):
        lines = [make_line("msg")]
        result = collect(lines, AnnotateOptions(labels={"z": "1", "a": "2"}))
        raw = result[0].raw
        assert raw.index("a=2") < raw.index("z=1")


# ---------------------------------------------------------------------------
# annotate_lines – combined options
# ---------------------------------------------------------------------------

class TestCombinedAnnotation:
    def test_sequence_and_tag(self):
        lines = [make_line("msg")]
        opts = AnnotateOptions(sequence=True, source_tag="svc")
        result = collect(lines, opts)
        # source tag applied first, then sequence wraps it
        assert result[0].raw == "[1] [svc] msg"

    def test_empty_lines_yields_nothing(self):
        result = collect([], AnnotateOptions(sequence=True, source_tag="x"))
        assert result == []
