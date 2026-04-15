"""Tests for logslice.templater."""
from __future__ import annotations

from datetime import datetime

import pytest

from logslice.parser import LogLine
from logslice.templater import TemplateOptions, apply_template, template_lines


def make_line(
    message: str = "hello world",
    level: str = "INFO",
    ts: datetime | None = None,
    source: str | None = None,
    lineno: int | None = None,
    extra: dict | None = None,
) -> LogLine:
    return LogLine(
        raw=f"{level} {message}",
        timestamp=ts or datetime(2024, 1, 15, 10, 30, 0),
        level=level,
        message=message,
        source=source,
        lineno=lineno,
        extra=extra or {},
    )


# ---------------------------------------------------------------------------
# TemplateOptions
# ---------------------------------------------------------------------------

class TestTemplateOptions:
    def test_disabled_by_default(self):
        opts = TemplateOptions()
        assert not opts.enabled()

    def test_enabled_with_template(self):
        opts = TemplateOptions(template="{level}: {message}")
        assert opts.enabled()

    def test_missing_default(self):
        opts = TemplateOptions()
        assert opts.missing == "-"


# ---------------------------------------------------------------------------
# apply_template
# ---------------------------------------------------------------------------

class TestApplyTemplate:
    def test_level_and_message(self):
        line = make_line(message="disk full", level="ERROR")
        opts = TemplateOptions(template="[{level}] {message}")
        assert apply_template(line, opts) == "[ERROR] disk full"

    def test_timestamp_rendered(self):
        line = make_line(ts=datetime(2024, 6, 1, 12, 0, 0))
        opts = TemplateOptions(template="{timestamp} {message}")
        result = apply_template(line, opts)
        assert "2024-06-01" in result

    def test_missing_field_uses_placeholder(self):
        line = make_line(source=None)
        opts = TemplateOptions(template="{source}: {message}", missing="N/A")
        assert apply_template(line, opts).startswith("N/A:")

    def test_extra_field_resolved(self):
        line = make_line(extra={"request_id": "abc123"})
        opts = TemplateOptions(template="rid={request_id}")
        assert apply_template(line, opts) == "rid=abc123"

    def test_unknown_field_uses_missing(self):
        line = make_line()
        opts = TemplateOptions(template="{nonexistent}", missing="?")
        assert apply_template(line, opts) == "?"

    def test_no_template_returns_raw(self):
        line = make_line()
        opts = TemplateOptions()
        assert apply_template(line, opts) == line.raw

    def test_lineno_rendered(self):
        line = make_line(lineno=42)
        opts = TemplateOptions(template="L{lineno}: {message}")
        assert apply_template(line, opts) == "L42: hello world"


# ---------------------------------------------------------------------------
# template_lines
# ---------------------------------------------------------------------------

class TestTemplateLines:
    def test_yields_raw_when_opts_none(self):
        lines = [make_line(message=f"msg{i}") for i in range(3)]
        result = list(template_lines(lines, None))
        assert result == [ln.raw for ln in lines]

    def test_yields_raw_when_disabled(self):
        lines = [make_line()]
        opts = TemplateOptions()
        result = list(template_lines(lines, opts))
        assert result == [lines[0].raw]

    def test_applies_template_to_all_lines(self):
        lines = [make_line(message=f"m{i}", level="DEBUG") for i in range(4)]
        opts = TemplateOptions(template="{level}|{message}")
        result = list(template_lines(lines, opts))
        assert result == [f"DEBUG|m{i}" for i in range(4)]

    def test_empty_input(self):
        assert list(template_lines([], TemplateOptions(template="{level}"))) == []
