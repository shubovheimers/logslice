"""Tests for logslice.cli_profile."""

import argparse
import io
import sys
from pathlib import Path

import pytest

from logslice.cli_profile import (
    add_profile_args,
    profile_opts_from_args,
    emit_profile,
)
from logslice.profiler import PipelineProfile, ProfileOptions


def _make_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    add_profile_args(p)
    return p


class TestAddProfileArgs:
    def test_profile_flag_defaults_false(self):
        parser = _make_parser()
        args = parser.parse_args([])
        assert args.profile is False

    def test_profile_flag_true_when_set(self):
        parser = _make_parser()
        args = parser.parse_args(["--profile"])
        assert args.profile is True

    def test_profile_out_defaults_none(self):
        parser = _make_parser()
        args = parser.parse_args([])
        assert args.profile_out is None

    def test_profile_out_accepts_path(self):
        parser = _make_parser()
        args = parser.parse_args(["--profile-out", "/tmp/prof.txt"])
        assert args.profile_out == "/tmp/prof.txt"


class TestProfileOptsFromArgs:
    def test_disabled_by_default(self):
        parser = _make_parser()
        args = parser.parse_args([])
        opts = profile_opts_from_args(args)
        assert opts.enabled is False

    def test_enabled_with_flag(self):
        parser = _make_parser()
        args = parser.parse_args(["--profile"])
        opts = profile_opts_from_args(args)
        assert opts.enabled is True

    def test_output_file_forwarded(self):
        parser = _make_parser()
        args = parser.parse_args(["--profile-out", "out.txt"])
        opts = profile_opts_from_args(args)
        assert opts.output_file == "out.txt"

    def test_missing_attrs_give_defaults(self):
        args = argparse.Namespace()
        opts = profile_opts_from_args(args)
        assert opts.enabled is False
        assert opts.output_file is None


class TestEmitProfile:
    def _make_profile(self) -> PipelineProfile:
        p = PipelineProfile(line_count=50)
        p.start_stage("read")
        p.stop_stage("read")
        return p

    def test_no_output_when_disabled(self, capsys):
        p = self._make_profile()
        opts = ProfileOptions(enabled=False)
        emit_profile(p, opts)
        captured = capsys.readouterr()
        assert captured.err == ""

    def test_writes_to_stderr_when_enabled(self, capsys):
        p = self._make_profile()
        opts = ProfileOptions(enabled=True)
        emit_profile(p, opts)
        captured = capsys.readouterr()
        assert "Total time" in captured.err

    def test_writes_to_file_when_output_file_set(self, tmp_path):
        out = tmp_path / "profile.txt"
        p = self._make_profile()
        opts = ProfileOptions(enabled=True, output_file=str(out))
        emit_profile(p, opts)
        content = out.read_text()
        assert "Total time" in content

    def test_bad_output_file_does_not_raise(self, capsys):
        p = self._make_profile()
        opts = ProfileOptions(enabled=True, output_file="/no/such/dir/prof.txt")
        emit_profile(p, opts)  # should not raise
        captured = capsys.readouterr()
        assert "could not write profile" in captured.err
