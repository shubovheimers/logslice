"""Tests for logslice.aggregator."""
from __future__ import annotations
import pytest
from datetime import datetime, timezone
from logslice.parser import LogLine
from logslice.aggregator import (
    AggregateOptions,
    AggregateBucket,
    aggregate_lines,
    _bucket_start,
)


def make_line(raw: str, ts: datetime | None = None, level: str = "") -> LogLine:
    return LogLine(raw=raw, timestamp=ts, level=level or None, extra={})


def dt(minute: int, second: int = 0) -> datetime:
    return datetime(2024, 1, 1, 12, minute, second, tzinfo=timezone.utc)


class TestAggregateOptions:
    def test_defaults(self):
        opts = AggregateOptions()
        assert opts.bucket_seconds == 60
        assert opts.by_level is False
        assert opts.by_pattern == ""
        assert opts.enabled is False

    def test_invalid_bucket_seconds_raises(self):
        with pytest.raises(ValueError):
            AggregateOptions(bucket_seconds=0)

    def test_negative_bucket_seconds_raises(self):
        with pytest.raises(ValueError):
            AggregateOptions(bucket_seconds=-10)


class TestAggregateLines:
    def test_empty_yields_nothing(self):
        opts = AggregateOptions()
        assert list(aggregate_lines([], opts)) == []

    def test_no_timestamp_skipped(self):
        opts = AggregateOptions()
        lines = [make_line("no ts", ts=None)]
        assert list(aggregate_lines(lines, opts)) == []

    def test_single_bucket(self):
        opts = AggregateOptions(bucket_seconds=60)
        lines = [
            make_line("a", dt(0, 5)),
            make_line("b", dt(0, 30)),
            make_line("c", dt(0, 59)),
        ]
        buckets = list(aggregate_lines(lines, opts))
        assert len(buckets) == 1
        assert buckets[0].count == 3

    def test_two_buckets(self):
        opts = AggregateOptions(bucket_seconds=60)
        lines = [
            make_line("a", dt(0, 10)),
            make_line("b", dt(1, 10)),
        ]
        buckets = list(aggregate_lines(lines, opts))
        assert len(buckets) == 2
        assert all(b.count == 1 for b in buckets)

    def test_by_level_breakdown(self):
        opts = AggregateOptions(bucket_seconds=60, by_level=True)
        lines = [
            make_line("err", dt(0, 1), level="ERROR"),
            make_line("warn", dt(0, 2), level="WARN"),
            make_line("err2", dt(0, 3), level="ERROR"),
        ]
        buckets = list(aggregate_lines(lines, opts))
        assert buckets[0].breakdown["ERROR"] == 2
        assert buckets[0].breakdown["WARN"] == 1

    def test_by_pattern_breakdown(self):
        opts = AggregateOptions(bucket_seconds=60, by_pattern="timeout")
        lines = [
            make_line("connection timeout", dt(0, 1)),
            make_line("all good", dt(0, 2)),
            make_line("timeout again", dt(0, 3)),
        ]
        buckets = list(aggregate_lines(lines, opts))
        assert buckets[0].breakdown["timeout"] == 2

    def test_buckets_sorted_by_start(self):
        opts = AggregateOptions(bucket_seconds=60)
        lines = [
            make_line("late", dt(5, 0)),
            make_line("early", dt(0, 0)),
            make_line("mid", dt(2, 0)),
        ]
        buckets = list(aggregate_lines(lines, opts))
        starts = [b.start for b in buckets]
        assert starts == sorted(starts)

    def test_bucket_label_format(self):
        opts = AggregateOptions(bucket_seconds=60)
        lines = [make_line("x", dt(3, 15))]
        bucket = list(aggregate_lines(lines, opts))[0]
        assert "2024-01-01T" in bucket.label()
