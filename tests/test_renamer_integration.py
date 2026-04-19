"""Integration tests for renamer + cli_renamer working together."""
from __future__ import annotations

from datetime import datetime

from logslice.parser import LogLine
from logslice.renamer import rename_lines
from logslice.cli_renamer import _make_parser, rename_opts_from_args


def _make_parser():
    import argparse
    from logslice.cli_renamer import add_rename_args
    p = argparse.ArgumentParser()
    add_rename_args(p)
    return p


def _line(message="msg", level="INFO", source="svc", **extra):
    return LogLine(
        raw=message,
        timestamp=datetime(2024, 6, 1),
        level=level,
        message=message,
        source=source,
        extra=extra,
    )


class TestRenamerIntegration:
    def test_field_rename_end_to_end(self):
        args = _make_parser().parse_args(["--rename-field", "req_id=request_id"])
        opts = rename_opts_from_args(args)
        lines = [_line(req_id="abc123")]
        result = list(rename_lines(lines, opts))
        assert result[0].extra.get("request_id") == "abc123"
        assert "req_id" not in result[0].extra

    def test_strip_prefix_end_to_end(self):
        args = _make_parser().parse_args(["--strip-prefix", "log_"])
        opts = rename_opts_from_args(args)
        lines = [_line(log_env="prod", log_host="web1")]
        result = list(rename_lines(lines, opts))
        assert "env" in result[0].extra
        assert "host" in result[0].extra

    def test_combined_mapping_and_strip(self):
        args = _make_parser().parse_args(
            ["--rename-field", "x=log_x", "--strip-prefix", "log_"]
        )
        opts = rename_opts_from_args(args)
        lines = [_line(x="val")]
        result = list(rename_lines(lines, opts))
        assert result[0].extra.get("x") == "val"

    def test_no_args_passthrough(self):
        args = _make_parser().parse_args([])
        opts = rename_opts_from_args(args)
        lines = [_line(foo="bar")]
        result = list(rename_lines(lines, opts))
        assert result == lines
