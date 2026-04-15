"""Tests for logslice.grouper."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import pytest

from logslice.grouper import GroupOptions, group_lines, iter_groups
from logslice.parser import LogLine


def make_line(
    raw: str = "log line",
    level: Optional[str] = None,
    ts: Optional[datetime] = None,
    extra: Optional[dict] = None,
) -> LogLine:
    return LogLine(raw=raw, timestamp=ts, level=level, message=raw, extra=extra)


def _dt(epoch: float) -> datetime:
    return datetime.fromtimestamp(epoch, tz=timezone.utc)


# ---------------------------------------------------------------------------
# GroupOptions validation
# ---------------------------------------------------------------------------

class TestGroupOptions:
    def test_defaults_not_enabled(self):
        opts = GroupOptions()
        assert not opts.enabled

    def test_by_level_enables(self):
        opts = GroupOptions(by_level=True)
        assert opts.enabled

    def test_by_field_enables(self):
        opts = GroupOptions(by_field="service")
        assert opts.enabled

    def test_window_enables(self):
        opts = GroupOptions(window_seconds=60)
        assert opts.enabled

    def test_multiple_options_raises(self):
        with pytest.raises(ValueError):
            GroupOptions(by_level=True, by_field="service")

    def test_window_and_level_raises(self):
        with pytest.raises(ValueError):
            GroupOptions(by_level=True, window_seconds=60)


# ---------------------------------------------------------------------------
# group_lines
# ---------------------------------------------------------------------------

class TestGroupLines:
    def test_empty_input_returns_empty(self):
        result = group_lines([], GroupOptions(by_level=True))
        assert result == {}

    def test_group_by_level(self):
        lines = [
            make_line("a", level="ERROR"),
            make_line("b", level="INFO"),
            make_line("c", level="ERROR"),
        ]
        result = group_lines(lines, GroupOptions(by_level=True))
        assert set(result.keys()) == {"ERROR", "INFO"}
        assert len(result["ERROR"]) == 2
        assert len(result["INFO"]) == 1

    def test_group_by_field(self):
        lines = [
            make_line("x", extra={"svc": "auth"}),
            make_line("y", extra={"svc": "db"}),
            make_line("z", extra={"svc": "auth"}),
        ]
        result = group_lines(lines, GroupOptions(by_field="svc"))
        assert set(result.keys()) == {"auth", "db"}
        assert len(result["auth"]) == 2

    def test_missing_field_uses_sentinel(self):
        lines = [make_line("no extra", extra={})]
        result = group_lines(lines, GroupOptions(by_field="svc"))
        assert "__missing__" in result

    def test_group_by_time_window(self):
        lines = [
            make_line("a", ts=_dt(0)),
            make_line("b", ts=_dt(30)),
            make_line("c", ts=_dt(61)),
        ]
        result = group_lines(lines, GroupOptions(window_seconds=60))
        assert len(result) == 2

    def test_none_timestamp_with_window_uses_all_bucket(self):
        lines = [make_line("no ts", ts=None)]
        result = group_lines(lines, GroupOptions(window_seconds=60))
        assert "__all__" in result


# ---------------------------------------------------------------------------
# iter_groups
# ---------------------------------------------------------------------------

class TestIterGroups:
    def test_yields_key_and_list(self):
        lines = [
            make_line("a", level="INFO"),
            make_line("b", level="WARN"),
        ]
        pairs = list(iter_groups(lines, GroupOptions(by_level=True)))
        keys = [k for k, _ in pairs]
        assert "INFO" in keys
        assert "WARN" in keys

    def test_insertion_order_preserved(self):
        lines = [
            make_line("first", level="DEBUG"),
            make_line("second", level="ERROR"),
            make_line("third", level="DEBUG"),
        ]
        pairs = list(iter_groups(lines, GroupOptions(by_level=True)))
        assert pairs[0][0] == "DEBUG"
        assert pairs[1][0] == "ERROR"
