"""Integration tests for aggregate_lines end-to-end."""
from __future__ import annotations
from datetime import datetime, timezone
from logslice.parser import LogLine
from logslice.aggregator import AggregateOptions, aggregate_lines


def _line(raw: str, minute: int, level: str = "") -> LogLine:
    ts = datetime(2024, 6, 1, 10, minute, 0, tzinfo=timezone.utc)
    return LogLine(raw=raw, timestamp=ts, level=level or None, extra={})


class TestAggregatorIntegration:
    def test_mixed_levels_two_buckets(self):
        opts = AggregateOptions(bucket_seconds=60, by_level=True, enabled=True)
        lines = [
            _line("a", 0, "INFO"),
            _line("b", 0, "ERROR"),
            _line("c", 1, "INFO"),
        ]
        buckets = list(aggregate_lines(lines, opts))
        assert len(buckets) == 2
        assert buckets[0].breakdown.get("INFO") == 1
        assert buckets[0].breakdown.get("ERROR") == 1
        assert buckets[1].breakdown.get("INFO") == 1

    def test_total_count_matches_input(self):
        opts = AggregateOptions(bucket_seconds=300)
        lines = [_line(f"line {i}", i % 5) for i in range(20)]
        buckets = list(aggregate_lines(lines, opts))
        total = sum(b.count for b in buckets)
        assert total == 20

    def test_pattern_and_level_independent(self):
        opts = AggregateOptions(
            bucket_seconds=60, by_level=True, by_pattern="fail"
        )
        lines = [
            _line("fail hard", 0, "ERROR"),
            _line("ok", 0, "INFO"),
        ]
        bucket = list(aggregate_lines(lines, opts))[0]
        assert bucket.breakdown["ERROR"] == 1
        assert bucket.breakdown["fail"] == 1
        assert bucket.count == 2
