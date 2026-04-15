"""Tests for logslice.correlator."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import pytest

from logslice.parser import LogLine
from logslice.correlator import (
    CorrelateOptions,
    group_by_correlation,
    iter_correlated,
)


def make_line(
    raw: str = "log message",
    level: str = "INFO",
    extra: Optional[dict] = None,
) -> LogLine:
    return LogLine(
        raw=raw,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=raw,
        extra=extra or {},
    )


class TestCorrelateOptions:
    def test_enabled_with_field(self):
        opts = CorrelateOptions(field="req_id")
        assert opts.enabled()

    def test_enabled_with_pattern(self):
        opts = CorrelateOptions(field="", pattern=r"req=(\w+)")
        assert opts.enabled()

    def test_extract_id_from_extra(self):
        opts = CorrelateOptions(field="req_id")
        line = make_line(extra={"req_id": "abc123"})
        assert opts.extract_id(line) == "abc123"

    def test_extract_id_missing_key_returns_none(self):
        opts = CorrelateOptions(field="req_id")
        line = make_line(extra={})
        assert opts.extract_id(line) is None

    def test_extract_id_via_pattern(self):
        opts = CorrelateOptions(field="", pattern=r"txn=(\w+)")
        line = make_line(raw="2024-01-01 GET /api txn=xyz99 200")
        assert opts.extract_id(line) == "xyz99"

    def test_extract_id_pattern_no_match_returns_none(self):
        opts = CorrelateOptions(field="", pattern=r"txn=(\w+)")
        line = make_line(raw="no transaction here")
        assert opts.extract_id(line) is None

    def test_pattern_without_group_returns_full_match(self):
        opts = CorrelateOptions(field="", pattern=r"REQ-\d+")
        line = make_line(raw="handled REQ-42 successfully")
        assert opts.extract_id(line) == "REQ-42"


class TestGroupByCorrelation:
    def test_empty_input(self):
        opts = CorrelateOptions(field="req_id")
        assert group_by_correlation([], opts) == {}

    def test_groups_by_id(self):
        opts = CorrelateOptions(field="req_id")
        lines = [
            make_line(raw="a", extra={"req_id": "1"}),
            make_line(raw="b", extra={"req_id": "2"}),
            make_line(raw="c", extra={"req_id": "1"}),
        ]
        groups = group_by_correlation(lines, opts)
        assert len(groups["1"]) == 2
        assert len(groups["2"]) == 1

    def test_missing_id_goes_to_empty_key(self):
        opts = CorrelateOptions(field="req_id")
        line = make_line(raw="no id", extra={})
        groups = group_by_correlation([line], opts)
        assert "" in groups
        assert groups[""][0].raw == "no id"


class TestIterCorrelated:
    def test_yields_matching_lines_only(self):
        opts = CorrelateOptions(field="req_id")
        lines = [
            make_line(raw="match", extra={"req_id": "abc"}),
            make_line(raw="skip", extra={"req_id": "xyz"}),
            make_line(raw="match2", extra={"req_id": "abc"}),
        ]
        result = list(iter_correlated(lines, opts, "abc"))
        assert len(result) == 2
        assert all(l.extra["req_id"] == "abc" for l in result)

    def test_no_matches_yields_nothing(self):
        opts = CorrelateOptions(field="req_id")
        lines = [make_line(extra={"req_id": "other"})]
        assert list(iter_correlated(lines, opts, "missing")) == []
