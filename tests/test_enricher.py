"""Tests for logslice.enricher."""
from __future__ import annotations

from datetime import datetime

import pytest

from logslice.enricher import EnrichOptions, enrich_lines
from logslice.parser import LogLine


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_line(raw: str = "hello world", level: str = "INFO") -> LogLine:
    return LogLine(
        raw=raw,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=raw,
        extra={},
    )


def collect(lines, opts):
    return list(enrich_lines(lines, opts))


# ---------------------------------------------------------------------------
# EnrichOptions
# ---------------------------------------------------------------------------

class TestEnrichOptions:
    def test_defaults_not_enabled(self):
        assert EnrichOptions().enabled() is False

    def test_add_sequence_enables(self):
        assert EnrichOptions(add_sequence=True).enabled() is True

    def test_extract_patterns_enables(self):
        assert EnrichOptions(extract_patterns=[r"(?P<id>\d+)"]).enabled() is True

    def test_source_tag_enables(self):
        assert EnrichOptions(source_tag="app.log").enabled() is True


# ---------------------------------------------------------------------------
# enrich_lines — passthrough
# ---------------------------------------------------------------------------

class TestEnrichPassthrough:
    def test_none_opts_yields_unchanged(self):
        lines = [make_line()]
        result = collect(lines, None)
        assert result == lines

    def test_disabled_opts_yields_unchanged(self):
        lines = [make_line()]
        result = collect(lines, EnrichOptions())
        assert result == lines


# ---------------------------------------------------------------------------
# Sequence numbers
# ---------------------------------------------------------------------------

class TestSequenceNumbers:
    def test_seq_starts_at_zero(self):
        lines = [make_line(), make_line(), make_line()]
        opts = EnrichOptions(add_sequence=True)
        result = collect(lines, opts)
        assert [r.extra["seq"] for r in result] == [0, 1, 2]

    def test_original_not_mutated(self):
        original = make_line()
        opts = EnrichOptions(add_sequence=True)
        collect([original], opts)
        assert "seq" not in original.extra


# ---------------------------------------------------------------------------
# Source tag
# ---------------------------------------------------------------------------

class TestSourceTag:
    def test_source_stored_in_extra(self):
        opts = EnrichOptions(source_tag="server.log")
        result = collect([make_line()], opts)
        assert result[0].extra["source"] == "server.log"


# ---------------------------------------------------------------------------
# Pattern extraction
# ---------------------------------------------------------------------------

class TestExtractPatterns:
    def test_named_group_captured(self):
        line = make_line(raw="request_id=abc-123 status=200")
        opts = EnrichOptions(extract_patterns=[r"request_id=(?P<request_id>[\w-]+)"])
        result = collect([line], opts)
        assert result[0].extra["request_id"] == "abc-123"

    def test_no_match_leaves_extra_unchanged(self):
        line = make_line(raw="no special fields here")
        opts = EnrichOptions(extract_patterns=[r"request_id=(?P<request_id>[\w-]+)"])
        result = collect([line], opts)
        assert "request_id" not in result[0].extra

    def test_multiple_patterns_all_applied(self):
        line = make_line(raw="user=alice status=404")
        opts = EnrichOptions(
            extract_patterns=[
                r"user=(?P<user>\w+)",
                r"status=(?P<status>\d+)",
            ]
        )
        result = collect([line], opts)
        assert result[0].extra["user"] == "alice"
        assert result[0].extra["status"] == "404"
