"""Tests for logslice.paginator."""

import pytest
from datetime import datetime
from logslice.parser import LogLine
from logslice.paginator import (
    PaginateOptions,
    paginate_lines,
    build_paginate_options,
)


def make_line(n: int) -> LogLine:
    return LogLine(
        raw=f"line {n}",
        timestamp=datetime(2024, 1, 1, 0, 0, n),
        level="INFO",
        message=f"message {n}",
    )


LINES = [make_line(i) for i in range(10)]


# ---------------------------------------------------------------------------
# PaginateOptions validation
# ---------------------------------------------------------------------------

class TestPaginateOptions:
    def test_defaults_not_enabled(self):
        opts = PaginateOptions()
        assert not opts.enabled

    def test_limit_enables(self):
        opts = PaginateOptions(limit=5)
        assert opts.enabled

    def test_offset_enables(self):
        opts = PaginateOptions(offset=3)
        assert opts.enabled

    def test_negative_offset_raises(self):
        with pytest.raises(ValueError, match="offset"):
            PaginateOptions(offset=-1)

    def test_negative_limit_raises(self):
        with pytest.raises(ValueError, match="limit"):
            PaginateOptions(limit=-1)

    def test_zero_limit_allowed(self):
        opts = PaginateOptions(limit=0)
        assert opts.enabled


# ---------------------------------------------------------------------------
# paginate_lines
# ---------------------------------------------------------------------------

class TestPaginateLines:
    def test_none_opts_yields_all(self):
        result = list(paginate_lines(iter(LINES), opts=None))
        assert result == LINES

    def test_disabled_opts_yields_all(self):
        opts = PaginateOptions()
        result = list(paginate_lines(iter(LINES), opts=opts))
        assert result == LINES

    def test_limit_only(self):
        opts = PaginateOptions(limit=3)
        result = list(paginate_lines(iter(LINES), opts=opts))
        assert result == LINES[:3]

    def test_offset_only(self):
        opts = PaginateOptions(offset=4)
        result = list(paginate_lines(iter(LINES), opts=opts))
        assert result == LINES[4:]

    def test_offset_and_limit(self):
        opts = PaginateOptions(offset=2, limit=3)
        result = list(paginate_lines(iter(LINES), opts=opts))
        assert result == LINES[2:5]

    def test_limit_zero_yields_nothing(self):
        opts = PaginateOptions(limit=0)
        result = list(paginate_lines(iter(LINES), opts=opts))
        assert result == []

    def test_offset_beyond_length_yields_nothing(self):
        opts = PaginateOptions(offset=100)
        result = list(paginate_lines(iter(LINES), opts=opts))
        assert result == []

    def test_limit_larger_than_remaining(self):
        opts = PaginateOptions(offset=8, limit=50)
        result = list(paginate_lines(iter(LINES), opts=opts))
        assert result == LINES[8:]

    def test_empty_input(self):
        opts = PaginateOptions(limit=5, offset=2)
        result = list(paginate_lines(iter([]), opts=opts))
        assert result == []


# ---------------------------------------------------------------------------
# build_paginate_options
# ---------------------------------------------------------------------------

def test_build_paginate_options_defaults():
    opts = build_paginate_options()
    assert opts.limit is None
    assert opts.offset == 0


def test_build_paginate_options_values():
    opts = build_paginate_options(limit=10, offset=5)
    assert opts.limit == 10
    assert opts.offset == 5
