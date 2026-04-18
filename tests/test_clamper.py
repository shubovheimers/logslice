"""Tests for logslice.clamper."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from logslice.clamper import ClampOptions, clamp_lines
from logslice.parser import LogLine


def make_line(ts: datetime, msg: str = "hello") -> LogLine:
    return LogLine(raw=msg, timestamp=ts, level="INFO", message=msg, extra={})


def dt(hour: int) -> datetime:
    return datetime(2024, 1, 1, hour, 0, 0, tzinfo=timezone.utc)


def collect(lines) -> List[LogLine]:
    return list(clamp_lines(lines, lines if isinstance(lines, ClampOptions) else None))


class TestClampOptions:
    def test_defaults_not_active(self):
        assert not ClampOptions().is_active()

    def test_active_with_floor(self):
        assert ClampOptions(enabled=True, floor=dt(6)).is_active()

    def test_active_with_ceiling(self):
        assert ClampOptions(enabled=True, ceiling=dt(22)).is_active()

    def test_floor_after_ceiling_raises(self):
        with pytest.raises(ValueError):
            ClampOptions(enabled=True, floor=dt(12), ceiling=dt(6))


class TestClampLines:
    def _run(self, lines, opts):
        return list(clamp_lines(lines, opts))

    def test_passthrough_when_opts_none(self):
        src = [make_line(dt(8)), make_line(dt(10))]
        assert self._run(src, None) == src

    def test_passthrough_when_not_active(self):
        src = [make_line(dt(8))]
        opts = ClampOptions(enabled=False, floor=dt(9))
        assert self._run(src, opts) == src

    def test_floor_replaces_early_timestamp(self):
        src = [make_line(dt(5))]
        opts = ClampOptions(enabled=True, floor=dt(8))
        result = self._run(src, opts)
        assert result[0].timestamp == dt(8)

    def test_ceiling_replaces_late_timestamp(self):
        src = [make_line(dt(23))]
        opts = ClampOptions(enabled=True, ceiling=dt(20))
        result = self._run(src, opts)
        assert result[0].timestamp == dt(20)

    def test_in_range_timestamp_unchanged(self):
        src = [make_line(dt(12))]
        opts = ClampOptions(enabled=True, floor=dt(8), ceiling=dt(20))
        result = self._run(src, opts)
        assert result[0].timestamp == dt(12)

    def test_drop_mode_removes_out_of_range(self):
        src = [make_line(dt(3)), make_line(dt(12)), make_line(dt(23))]
        opts = ClampOptions(enabled=True, floor=dt(8), ceiling=dt(20), replace_with_bound=False)
        result = self._run(src, opts)
        assert len(result) == 1
        assert result[0].timestamp == dt(12)

    def test_none_timestamp_passes_through(self):
        line = LogLine(raw="x", timestamp=None, level=None, message="x", extra={})
        opts = ClampOptions(enabled=True, floor=dt(8))
        result = self._run([line], opts)
        assert result[0].timestamp is None

    def test_raw_and_message_preserved_after_clamp(self):
        src = [make_line(dt(2), msg="important")]
        opts = ClampOptions(enabled=True, floor=dt(6))
        result = self._run(src, opts)
        assert result[0].message == "important"
        assert result[0].raw == "important"
