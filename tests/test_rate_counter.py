"""Tests for logslice/rate_counter.py — RateOptions, RateBucket, RateCounter."""

import pytest
from datetime import datetime, timezone
from logslice.parser import LogLine
from logslice.rate_counter import (
    RateOptions,
    RateBucket,
    RateCounter,
    _bucket_key,
    count_rates,
    format_rate_report,
)


def _dt(hour: int, minute: int, second: int = 0) -> datetime:
    return datetime(2024, 1, 15, hour, minute, second, tzinfo=timezone.utc)


def make_line(
    raw: str = "INFO message",
    level: str = "INFO",
    timestamp: datetime | None = None,
) -> LogLine:
    return LogLine(
        raw=raw,
        timestamp=timestamp,
        level=level,
        message=raw,
    )


# ---------------------------------------------------------------------------
# RateOptions
# ---------------------------------------------------------------------------

class TestRateOptions:
    def test_defaults_disabled(self):
        opts = RateOptions()
        assert opts.enabled is False

    def test_bucket_seconds_zero_raises(self):
        with pytest.raises(ValueError, match="bucket_seconds"):
            RateOptions(bucket_seconds=0, enabled=True)

    def test_negative_bucket_raises(self):
        with pytest.raises(ValueError):
            RateOptions(bucket_seconds=-5, enabled=True)

    def test_enabled_when_bucket_set(self):
        opts = RateOptions(bucket_seconds=60, enabled=True)
        assert opts.enabled is True

    def test_default_bucket_is_sixty(self):
        opts = RateOptions()
        assert opts.bucket_seconds == 60


# ---------------------------------------------------------------------------
# _bucket_key helper
# ---------------------------------------------------------------------------

class TestBucketKey:
    def test_same_minute_same_key(self):
        dt1 = _dt(10, 5, 3)
        dt2 = _dt(10, 5, 57)
        assert _bucket_key(dt1, 60) == _bucket_key(dt2, 60)

    def test_different_minute_different_key(self):
        dt1 = _dt(10, 5, 0)
        dt2 = _dt(10, 6, 0)
        assert _bucket_key(dt1, 60) != _bucket_key(dt2, 60)

    def test_30s_bucket_splits_minute(self):
        dt1 = _dt(10, 5, 10)
        dt2 = _dt(10, 5, 40)
        assert _bucket_key(dt1, 30) != _bucket_key(dt2, 30)

    def test_30s_bucket_groups_within_window(self):
        dt1 = _dt(10, 5, 0)
        dt2 = _dt(10, 5, 29)
        assert _bucket_key(dt1, 30) == _bucket_key(dt2, 30)


# ---------------------------------------------------------------------------
# RateCounter
# ---------------------------------------------------------------------------

class TestRateCounter:
    def _make_counter(self, bucket_seconds: int = 60) -> RateCounter:
        opts = RateOptions(bucket_seconds=bucket_seconds, enabled=True)
        return RateCounter(opts)

    def test_empty_counter_has_no_buckets(self):
        rc = self._make_counter()
        assert rc.buckets == {}

    def test_feed_increments_bucket(self):
        rc = self._make_counter(60)
        line = make_line(timestamp=_dt(10, 5, 0))
        rc.feed(line)
        assert sum(rc.buckets.values()) == 1

    def test_same_bucket_accumulates(self):
        rc = self._make_counter(60)
        for sec in range(5):
            rc.feed(make_line(timestamp=_dt(10, 5, sec)))
        assert sum(rc.buckets.values()) == 5
        assert len(rc.buckets) == 1

    def test_two_buckets_created(self):
        rc = self._make_counter(60)
        rc.feed(make_line(timestamp=_dt(10, 5, 0)))
        rc.feed(make_line(timestamp=_dt(10, 6, 0)))
        assert len(rc.buckets) == 2

    def test_line_without_timestamp_skipped(self):
        rc = self._make_counter(60)
        rc.feed(make_line(timestamp=None))
        assert rc.buckets == {}

    def test_peak_bucket(self):
        rc = self._make_counter(60)
        for _ in range(3):
            rc.feed(make_line(timestamp=_dt(10, 5, 0)))
        rc.feed(make_line(timestamp=_dt(10, 6, 0)))
        peak_key, peak_count = rc.peak()
        assert peak_count == 3


# ---------------------------------------------------------------------------
# count_rates integration helper
# ---------------------------------------------------------------------------

class TestCountRates:
    def test_returns_rate_counter(self):
        opts = RateOptions(bucket_seconds=60, enabled=True)
        lines = [make_line(timestamp=_dt(10, i, 0)) for i in range(3)]
        rc = count_rates(iter(lines), opts)
        assert isinstance(rc, RateCounter)
        assert len(rc.buckets) == 3

    def test_disabled_opts_returns_empty_counter(self):
        opts = RateOptions(enabled=False)
        lines = [make_line(timestamp=_dt(10, 0, 0))]
        rc = count_rates(iter(lines), opts)
        assert rc.buckets == {}


# ---------------------------------------------------------------------------
# format_rate_report
# ---------------------------------------------------------------------------

class TestFormatRateReport:
    def test_empty_buckets_returns_empty_string(self):
        opts = RateOptions(bucket_seconds=60, enabled=True)
        rc = RateCounter(opts)
        assert format_rate_report(rc) == ""

    def test_output_contains_bucket_count(self):
        opts = RateOptions(bucket_seconds=60, enabled=True)
        rc = RateCounter(opts)
        rc.feed(make_line(timestamp=_dt(10, 5, 0)))
        rc.feed(make_line(timestamp=_dt(10, 5, 30)))
        report = format_rate_report(rc)
        assert "2" in report

    def test_output_is_multiline_for_multiple_buckets(self):
        opts = RateOptions(bucket_seconds=60, enabled=True)
        rc = RateCounter(opts)
        rc.feed(make_line(timestamp=_dt(10, 5, 0)))
        rc.feed(make_line(timestamp=_dt(10, 6, 0)))
        lines = format_rate_report(rc).strip().splitlines()
        assert len(lines) >= 2
