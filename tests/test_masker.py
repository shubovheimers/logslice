"""Tests for logslice.masker."""
from __future__ import annotations

import pytest

from logslice.masker import MaskOptions, apply_masking, mask_line, mask_text
from logslice.parser import LogLine


def make_line(text: str) -> LogLine:
    return LogLine(raw=text, timestamp=None, level=None, message=text, extra={})


# ---------------------------------------------------------------------------
# MaskOptions
# ---------------------------------------------------------------------------

class TestMaskOptions:
    def test_defaults_not_active(self):
        opts = MaskOptions()
        assert not opts.is_active()

    def test_enabled_without_patterns_not_active(self):
        opts = MaskOptions(enabled=True)
        assert not opts.is_active()

    def test_enabled_with_builtin_is_active(self):
        opts = MaskOptions(enabled=True, builtins=["token"])
        assert opts.is_active()

    def test_enabled_with_custom_is_active(self):
        opts = MaskOptions(enabled=True, custom_patterns=[r"\d{4}"])
        assert opts.is_active()

    def test_unknown_builtin_raises(self):
        with pytest.raises(ValueError, match="Unknown built-in"):
            MaskOptions(enabled=True, builtins=["nonexistent"])


# ---------------------------------------------------------------------------
# mask_text
# ---------------------------------------------------------------------------

class TestMaskText:
    def test_inactive_returns_unchanged(self):
        opts = MaskOptions()
        assert mask_text("secret=abc123", opts) == "secret=abc123"

    def test_token_masked(self):
        opts = MaskOptions(enabled=True, builtins=["token"])
        result = mask_text("api_key=supersecret", opts)
        assert "supersecret" not in result
        assert "[MASKED]" in result

    def test_password_masked(self):
        opts, builtins=["password"])
        result = mask_text("password=hunter2", opts)
        assert "hunter2" not in result

    def test_jwt_masked(self):
        opts = builtins=["jwt"])
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        result = mask_text(f"Authorization: Bearer {jwt}", opts)
        assert jwt[MASKED]" in result

    def test_custom_placeholder(self):
        opts = MaskOptions(enabled=True, builtins=["ssn"], placeholder="***")
        result = mask_text("ssn: 123-45-6789", opts)
        assert "123-45-6789" not in result
        assert "***" in result

    def test_custom_pattern(self):
        opts = MaskOptions(enabled=True, custom_patterns=[r"ORDER-\d+"])
        result = mask_text("Processing ORDER-99182", opts)
        assert "
        assert "[MASKED]" in result


# ---------------------------------------------------------------------------
# mask_line / apply_masking
# ---------------------------------------------------------------------------

class TestMaskLine:
    def test_raw_and_message_masked(self):
        opts = MaskOptions(enabled=True, builtins=["password"])
        line = make_line("Login failed password=topsecret")
        result = mask_line(line, opts)
        assert "topsecret" not in result.raw
        assert "topsecret" not in (result.message or "")

    def test_timestamp_and_level_preserved(self):
        from datetime import datetime
        opts = MaskOptions(enabled=True, builtins=["token"])
        line = LogLine(
            raw="token=abc",
            timestamp=datetime(2024, 1, 1),
            level="INFO",
            message="token=abc",
            extra={},
        )
        result = mask_line(line, opts)
        assert result.timestamp == datetime(2024, 1, 1)
        assert result.level == "INFO"


class TestApplyMasking:
    def test_none_opts_passthrough(self):
        lines = [make_line("password=secret")]
        result = list(apply_masking(lines, None))
        assert result[0].raw == "password=secret"

    def test_inactive_opts_passthrough(self):
        opts = MaskOptions()
        lines = [make_line("password=secret")]
        result = list(apply_masking(lines, opts))
        assert result[0].raw == "password=secret"

    def test_masks_all_lines(self):
        opts = MaskOptions(enabled=True, builtins=["password"])
        lines = [make_line(f"password=secret{i}") for i in range(3)]
        results = list(apply_masking(lines, opts))
        assert all("secret" not in r.raw for r in results)
        assert len(results) == 3
