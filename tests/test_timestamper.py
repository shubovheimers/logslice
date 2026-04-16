"""Tests for logslice.timestamper."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.parser import LogLine
from logslice.timestamper import TimestampOptions, stamp_line, stamp_lines


def make_line(raw="hello world", timestamp=None, level=None, message="hello world"):
    return LogLine(raw=raw, timestamp=timestamp, level=level, message=message, extra={})


class TestTimestampOptions:
    def test_disabled_by_default(self):
        opts = TimestampOptions()
        assert not opts.enabled()

    def test_inject_enables(self):
        opts = TimestampOptions(inject=True)
        assert opts.enabled()

    def test_overwrite_enables(self):
        opts = TimestampOptions(overwrite=True)
        assert opts.enabled()


class TestStampLine:
    def test_no_op_when_disabled(self):
        line = make_line()
        opts = TimestampOptions()
        assert stamp_line(line, opts) is line

    def test_inject_adds_timestamp_when_missing(self):
        line = make_line(timestamp=None)
        opts = TimestampOptions(inject=True, utc=True)
        result = stamp_line(line, opts)
        assert result.timestamp is not None
        assert isinstance(result.timestamp, datetime)

    def test_inject_skips_when_timestamp_present(self):
        existing = datetime(2024, 1, 1, tzinfo=timezone.utc)
        line = make_line(timestamp=existing)
        opts = TimestampOptions(inject=True, utc=True)
        result = stamp_line(line, opts)
        assert result.timestamp == existing

    def test_overwrite_replaces_existing_timestamp(self):
        existing = datetime(2020, 6, 15, tzinfo=timezone.utc)
        line = make_line(timestamp=existing)
        opts = TimestampOptions(overwrite=True, utc=True)
        result = stamp_line(line, opts)
        assert result.timestamp != existing

    def test_injected_raw_prefixed_when_no_original_timestamp(self):
        line = make_line(raw="plain message", timestamp=None)
        opts = TimestampOptions(inject=True, utc=True)
        result = stamp_line(line, opts)
        assert "plain message" in result.raw
        assert len(result.raw) > len(line.raw)

    def test_raw_unchanged_when_timestamp_already_present(self):
        existing = datetime(2024, 3, 1, tzinfo=timezone.utc)
        line = make_line(raw="2024-03-01 msg", timestamp=existing)
        opts = TimestampOptions(inject=True)
        result = stamp_line(line, opts)
        assert result.raw == line.raw


class TestStampLines:
    def _collect(self, lines, opts):
        return list(stamp_lines(lines, opts))

    def test_passthrough_when_opts_none(self):
        lines = [make_line(), make_line()]
        result = self._collect(lines, None)
        assert result == lines

    def test_passthrough_when_disabled(self):
        lines = [make_line(), make_line()]
        result = self._collect(lines, TimestampOptions())
        assert result == lines

    def test_stamps_all_lines(self):
        lines = [make_line(timestamp=None) for _ in range(4)]
        opts = TimestampOptions(inject=True, utc=True)
        result = self._collect(lines, opts)
        assert all(r.timestamp is not None for r in result)
        assert len(result) == 4
