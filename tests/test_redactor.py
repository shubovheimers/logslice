"""Tests for logslice.redactor."""

from __future__ import annotations

from datetime import datetime

import pytest

from logslice.parser import LogLine
from logslice.redactor import (
    DEFAULT_MASK,
    RedactOptions,
    apply_redaction,
    redact_line,
    redact_text,
)


def make_line(raw: str, message: str = "") -> LogLine:
    return LogLine(raw=raw, timestamp=datetime(2024, 1, 1, 12, 0, 0), level="INFO", message=message or raw)


# ---------------------------------------------------------------------------
# redact_text
# ---------------------------------------------------------------------------

class TestRedactText:
    def test_no_patterns_returns_unchanged(self):
        assert redact_text("hello world", []) == "hello world"

    def test_ipv4_masked(self):
        import re
        from logslice.redactor import BUILTIN_PATTERNS
        pattern = re.compile(BUILTIN_PATTERNS["ipv4"])
        result = redact_text("connected from 192.168.1.1 ok", [pattern])
        assert "192.168.1.1" not in result
        assert DEFAULT_MASK in result

    def test_email_masked(self):
        import re
        from logslice.redactor import BUILTIN_PATTERNS
        pattern = re.compile(BUILTIN_PATTERNS["email"])
        result = redact_text("user admin@example.com logged in", [pattern])
        assert "admin@example.com" not in result
        assert DEFAULT_MASK in result

    def test_custom_mask(self):
        import re
        pattern = re.compile(r"secret")
        result = redact_text("my secret value", [pattern], mask="***")
        assert result == "my *** value"

    def test_multiple_patterns_all_replaced(self):
        import re
        p1 = re.compile(r"foo")
        p2 = re.compile(r"bar")
        result = redact_text("foo and bar", [p1, p2])
        assert "foo" not in result
        assert "bar" not in result


# ---------------------------------------------------------------------------
# redact_line
# ---------------------------------------------------------------------------

class TestRedactLine:
    def test_raw_is_redacted(self):
        import re
        pattern = re.compile(r"\d+\.\d+\.\d+\.\d+")
        line = make_line("request from 10.0.0.1")
        result = redact_line(line, [pattern])
        assert "10.0.0.1" not in result.raw

    def test_timestamp_and_level_preserved(self):
        import re
        pattern = re.compile(r"secret")
        line = make_line("secret data")
        result = redact_line(line, [pattern])
        assert result.timestamp == line.timestamp
        assert result.level == line.level


# ---------------------------------------------------------------------------
# apply_redaction
# ---------------------------------------------------------------------------

class TestApplyRedaction:
    def test_none_opts_passthrough(self):
        lines = [make_line("192.168.0.1 access")]
        result = list(apply_redaction(lines, None))
        assert result[0].raw == "192.168.0.1 access"

    def test_disabled_opts_passthrough(self):
        opts = RedactOptions(enabled=False, builtins=["ipv4"])
        lines = [make_line("192.168.0.1 access")]
        result = list(apply_redaction(lines, opts))
        assert "192.168.0.1" in result[0].raw

    def test_enabled_with_builtin(self):
        opts = RedactOptions(enabled=True, builtins=["ipv4"])
        lines = [make_line("request from 10.0.0.2")]
        result = list(apply_redaction(lines, opts))
        assert "10.0.0.2" not in result[0].raw

    def test_enabled_with_custom_pattern(self):
        opts = RedactOptions(enabled=True, patterns=[r"token=[^\s]+"])
        lines = [make_line("auth token=abc123 granted")]
        result = list(apply_redaction(lines, opts))
        assert "abc123" not in result[0].raw

    def test_empty_builtins_and_patterns_passthrough(self):
        opts = RedactOptions(enabled=True, builtins=[], patterns=[])
        lines = [make_line("192.168.1.1 data")]
        result = list(apply_redaction(lines, opts))
        assert "192.168.1.1" in result[0].raw
