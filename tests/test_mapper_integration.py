"""Integration tests for mapper end-to-end."""
from __future__ import annotations

from datetime import datetime

from logslice.mapper import MapOptions, MapRule, map_lines
from logslice.parser import LogLine


def _line(text: str, extra=None) -> LogLine:
    return LogLine(
        raw=text,
        timestamp=datetime(2024, 6, 1, 10, 0, 0),
        level="INFO",
        message=text,
        extra=extra or {},
    )


class TestMapperIntegration:
    def test_extract_ip_address(self):
        opts = MapOptions(rules=[MapRule("ip", r"(\d{1,3}(?:\.\d{1,3}){3})")])
        lines = [_line("request from 192.168.1.1 accepted")]
        result = list(map_lines(lines, opts))
        assert result[0].extra["map_ip"] == "192.168.1.1"

    def test_multiple_lines_all_mapped(self):
        opts = MapOptions(rules=[MapRule("code", r"code=(\d+)")])
        lines = [_line(f"code={i}") for i in range(5)]
        result = list(map_lines(lines, opts))
        assert [r.extra["map_code"] for r in result] == [str(i) for i in range(5)]

    def test_mixed_match_and_no_match(self):
        opts = MapOptions(rules=[MapRule("code", r"code=(\d+)")])
        lines = [_line("code=10"), _line("no code here"), _line("code=20")]
        result = list(map_lines(lines, opts))
        assert result[0].extra.get("map_code") == "10"
        assert "map_code" not in result[1].extra
        assert result[2].extra.get("map_code") == "20"

    def test_original_raw_preserved(self):
        opts = MapOptions(rules=[MapRule("val", r"val=(\w+)")])
        line = _line("val=hello world")
        result = list(map_lines([line], opts))
        assert result[0].raw == "val=hello world"
