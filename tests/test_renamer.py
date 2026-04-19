"""Tests for logslice.renamer."""
from __future__ import annotations

import pytest
from datetime import datetime

from logslice.parser import LogLine
from logslice.renamer import RenameOptions, rename_lines, _rename_key


def make_line(message: str = "hello", level: str = "INFO", source: str = "app",
              **extra) -> LogLine:
    return LogLine(
        raw=message,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        level=level,
        message=message,
        source=source,
        extra=extra,
    )


def collect(lines):
    return list(lines)


class TestRenameOptions:
    def test_defaults_not_enabled(self):
        assert not RenameOptions().enabled()

    def test_mapping_enables(self):
        assert RenameOptions(mapping={"a": "b"}).enabled()

    def test_rename_level_enables(self):
        assert RenameOptions(rename_level="severity").enabled()

    def test_rename_source_enables(self):
        assert RenameOptions(rename_source="host").enabled()

    def test_strip_prefix_enables(self):
        assert RenameOptions(strip_prefix="log_").enabled()

    def test_strip_suffix_enables(self):
        assert RenameOptions(strip_suffix="_field").enabled()

    def test_invalid_mapping_raises(self):
        with pytest.raises(TypeError):
            RenameOptions(mapping="bad")  # type: ignore


class TestRenameKey:
    def test_mapping_applied(self):
        opts = RenameOptions(mapping={"old": "new"})
        assert _rename_key("old", opts) == "new"

    def test_unknown_key_unchanged(self):
        opts = RenameOptions(mapping={"old": "new"})
        assert _rename_key("other", opts) == "other"

    def test_strip_prefix(self):
        opts = RenameOptions(strip_prefix="log_")
        assert _rename_key("log_level", opts) == "level"

    def test_strip_suffix(self):
        opts = RenameOptions(strip_suffix="_tag")
        assert _rename_key("env_tag", opts) == "env"

    def test_mapping_then_strip(self):
        opts = RenameOptions(mapping={"old": "log_new"}, strip_prefix="log_")
        assert _rename_key("old", opts) == "new"


class TestRenameLines:
    def test_passthrough_when_none(self):
        lines = [make_line()]
        assert collect(rename_lines(lines, None)) == lines

    def test_passthrough_when_disabled(self):
        lines = [make_line()]
        assert collect(rename_lines(lines, RenameOptions())) == lines

    def test_extra_keys_renamed(self):
        ln = make_line(request_id="abc")
        opts = RenameOptions(mapping={"request_id": "rid"})
        result = collect(rename_lines([ln], opts))
        assert "rid" in result[0].extra
        assert "request_id" not in result[0].extra

    def test_level_renamed(self):
        ln = make_line(level="ERROR")
        opts = RenameOptions(rename_level="CRITICAL")
        result = collect(rename_lines([ln], opts))
        assert result[0].level == "CRITICAL"

    def test_source_renamed(self):
        ln = make_line(source="svc-a")
        opts = RenameOptions(rename_source="service-a")
        result = collect(rename_lines([ln], opts))
        assert result[0].source == "service-a"

    def test_strip_prefix_on_extras(self):
        ln = make_line(log_env="prod", log_region="us")
        opts = RenameOptions(strip_prefix="log_")
        result = collect(rename_lines([ln], opts))
        assert "env" in result[0].extra
        assert "region" in result[0].extra

    def test_raw_preserved(self):
        ln = make_line(message="keep me")
        opts = RenameOptions(mapping={"x": "y"})
        result = collect(rename_lines([ln], opts))
        assert result[0].raw == ln.raw
