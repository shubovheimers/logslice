"""Tests for logslice.rate_counter."""

from datetime import datetime, timezone
from typing import List

import pytest

from logslice.parser import LogLine
from logslice.rate_counter import (
    RateCounter,
    RateOptions,
    apply_rate_filter,
)


def _dt(second: int) -> datetime:
    return datetime(2024, 1, 1, 0, 0, second, tzinfo=timezone.utc)


def make_line(second: int, text: str = "msg") -> LogLine:
    return LogLine(raw=text, timestamp=_dt(second), level=None, message=text)


# ---------------------------------------------------------------------------
# RateOptions validation
# ---------------------------------------------------------------------------

class TestRateOptions:
    def test_defaults_disabled(self):
        opts = RateOptions()
        assert opts.enabled is False

    def test_bucket_seconds_zero_raises(self):
        with pytest.raises(ValueError, match="bucket_seconds"):
            RateOptions(enabled=True, bucket_seconds=0)

    def test_window_smaller_than_bucket_raises(self):
        with pytest.raises(ValueError, match="window_seconds"):
            RateOptions(enabled=True, window_seconds=1, bucket_seconds=5)


# ---------------------------------------------------------------------------
# RateCounter.record / rate_at
# ---------------------------------------------------------------------------

class TestRateCounter:
    def _counter(self, window: int = 60, bucket: int = 1) -> RateCounter:
        return RateCounter(options=RateOptions(enabled=True, window_seconds=window, bucket_seconds=bucket))

    def test_rate_zero_before_any_record(self):
        c = self._counter()
        assert c.rate_at(_dt(0)) == 0.0

    def test_rate_after_single_record(self):
        c = self._counter()
        c.record(_dt(5))
        assert c.rate_at(_dt(5)) == 1.0

    def test_multiple_records_same_bucket(self):
        c = self._counter()
        for _ in range(4):
            c.record(_dt(10))
        assert c.rate_at(_dt(10)) == 4.0

    def test_old_buckets_evicted(self):
        c = self._counter(window=5, bucket=1)
        c.record(_dt(0))
        c.record(_dt(10))  # _dt(0) should be evicted
        assert c.rate_at(_dt(0)) == 0.0

    def test_window_rate_averages_over_window(self):
        c = self._counter(window=10, bucket=1)
        for s in range(10):
            c.record(_dt(s))
        rate = c.window_rate()
        assert rate == pytest.approx(10 / 10)

    def test_window_rate_empty(self):
        c = self._counter()
        assert c.window_rate() == 0.0


# ---------------------------------------------------------------------------
# apply_rate_filter
# ---------------------------------------------------------------------------

class TestApplyRateFilter:
    def test_passthrough_when_disabled(self):
        opts = RateOptions(enabled=False)
        lines = [make_line(i) for i in range(5)]
        assert list(apply_rate_filter(lines, opts)) == lines

    def test_no_min_rate_yields_all(self):
        opts = RateOptions(enabled=True, min_rate=None)
        lines = [make_line(i) for i in range(5)]
        assert list(apply_rate_filter(lines, opts)) == lines

    def test_min_rate_filters_low_rate_lines(self):
        opts = RateOptions(enabled=True, bucket_seconds=1, window_seconds=60, min_rate=3.0)
        # 4 events in second=0, 1 event in second=5
        lines = [make_line(0)] * 4 + [make_line(5)]
        result = list(apply_rate_filter(lines, opts))
        # second=0 bucket rate == 4.0 >= 3.0 → kept; second=5 rate == 1.0 < 3.0 → dropped
        assert len(result) == 4
        assert all(ln.timestamp == _dt(0) for ln in result)

    def test_lines_without_timestamp_always_yielded(self):
        opts = RateOptions(enabled=True, min_rate=999.0)
        no_ts = LogLine(raw="bare", timestamp=None, level=None, message="bare")
        result = list(apply_rate_filter([no_ts], opts))
        assert result == [no_ts]
