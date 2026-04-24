"""Tests for logslice.censor."""
from __future__ import annotations

import pytest

from logslice.parser import LogLine
from logslice.censor import CensorOptions, censor_line, censor_lines


def make_line(extra: dict | None = None) -> LogLine:
    return LogLine(
        raw="2024-01-01 00:00:00 INFO msg",
        timestamp=None,
        level="INFO",
        message="msg",
        extra=extra or {},
    )


# ---------------------------------------------------------------------------
# CensorOptions
# ---------------------------------------------------------------------------

class TestCensorOptions:
    def test_defaults_not_active(self):
        opts = CensorOptions()
        assert not opts.is_active

    def test_fields_activates(self):
        opts = CensorOptions(fields=["password"])
        assert opts.is_active

    def test_patterns_activates(self):
        opts = CensorOptions(patterns=[r"secret"])
        assert opts.is_active

    def test_invalid_replacement_raises(self):
        with pytest.raises(TypeError):
            CensorOptions(replacement=123)  # type: ignore

    def test_default_replacement_sentinel(self):
        opts = CensorOptions()
        assert opts.replacement == "[CENSORED]"


# ---------------------------------------------------------------------------
# censor_line – field list
# ---------------------------------------------------------------------------

class TestCensorLineByField:
    def test_named_field_replaced(self):
        opts = CensorOptions(fields=["password"])
        line = make_line({"user": "alice", "password": "s3cr3t"})
        result = censor_line(line, opts)
        assert result.extra["password"] == "[CENSORED]"
        assert result.extra["user"] == "alice"

    def test_named_field_dropped(self):
        opts = CensorOptions(fields=["token"], drop=True)
        line = make_line({"token": "abc", "level": "INFO"})
        result = censor_line(line, opts)
        assert "token" not in result.extra
        assert result.extra["level"] == "INFO"

    def test_custom_replacement(self):
        opts = CensorOptions(fields=["key"], replacement="***")
        line = make_line({"key": "value"})
        result = censor_line(line, opts)
        assert result.extra["key"] == "***"

    def test_no_match_unchanged(self):
        opts = CensorOptions(fields=["password"])
        line = make_line({"user": "bob"})
        result = censor_line(line, opts)
        assert result.extra == {"user": "bob"}

    def test_empty_extra_unchanged(self):
        opts = CensorOptions(fields=["password"])
        line = make_line({})
        result = censor_line(line, opts)
        assert result.extra == {}


# ---------------------------------------------------------------------------
# censor_line – pattern matching
# ---------------------------------------------------------------------------

class TestCensorLineByPattern:
    def test_pattern_matches_field(self):
        opts = CensorOptions(patterns=[r"secret|token"])
        line = make_line({"api_token": "xyz", "host": "localhost"})
        result = censor_line(line, opts)
        assert result.extra["api_token"] == "[CENSORED]"
        assert result.extra["host"] == "localhost"

    def test_pattern_drop(self):
        opts = CensorOptions(patterns=[r"pass"], drop=True)
        line = make_line({"password": "x", "passphrase": "y", "user": "z"})
        result = censor_line(line, opts)
        assert "password" not in result.extra
        assert "passphrase" not in result.extra
        assert result.extra["user"] == "z"


# ---------------------------------------------------------------------------
# censor_lines – generator
# ---------------------------------------------------------------------------

class TestCensorLines:
    def test_none_opts_passthrough(self):
        lines = [make_line({"pw": "secret"})]
        result = list(censor_lines(lines, None))
        assert result[0].extra["pw"] == "secret"

    def test_inactive_opts_passthrough(self):
        opts = CensorOptions()
        lines = [make_line({"pw": "secret"})]
        result = list(censor_lines(lines, opts))
        assert result[0].extra["pw"] == "secret"

    def test_multiple_lines_all_censored(self):
        opts = CensorOptions(fields=["pw"])
        lines = [make_line({"pw": str(i)}) for i in range(5)]
        result = list(censor_lines(lines, opts))
        assert all(r.extra["pw"] == "[CENSORED]" for r in result)

    def test_returns_iterator(self):
        opts = CensorOptions(fields=["x"])
        result = censor_lines([], opts)
        assert hasattr(result, "__iter__")
