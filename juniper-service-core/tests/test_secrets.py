"""Tests for :func:`juniper_service_core.secrets.get_secret`."""

from __future__ import annotations

from juniper_service_core.secrets import get_secret


def test_reads_from_file_env_var_when_present(tmp_path, monkeypatch):
    secret_file = tmp_path / "api_key.txt"
    secret_file.write_text("super-secret-value")
    monkeypatch.setenv("MY_SECRET_FILE", str(secret_file))
    # A plain env var is also set, but the file takes precedence.
    monkeypatch.setenv("MY_SECRET", "plain-env-value")
    assert get_secret("MY_SECRET") == "super-secret-value"


def test_strips_surrounding_whitespace_from_file(tmp_path, monkeypatch):
    secret_file = tmp_path / "api_key.txt"
    secret_file.write_text("  trailing-and-leading \n")
    monkeypatch.setenv("MY_SECRET_FILE", str(secret_file))
    assert get_secret("MY_SECRET") == "trailing-and-leading"


def test_explicit_file_env_var_name_is_honored(tmp_path, monkeypatch):
    secret_file = tmp_path / "creds.txt"
    secret_file.write_text("from-custom-file-var")
    monkeypatch.setenv("CUSTOM_PATH_VAR", str(secret_file))
    assert get_secret("MY_SECRET", file_env_var="CUSTOM_PATH_VAR") == "from-custom-file-var"


def test_falls_back_to_plain_env_var_when_no_file(monkeypatch):
    monkeypatch.delenv("MY_SECRET_FILE", raising=False)
    monkeypatch.setenv("MY_SECRET", "plain-env-value")
    assert get_secret("MY_SECRET") == "plain-env-value"


def test_falls_back_to_plain_env_var_when_file_path_missing(tmp_path, monkeypatch):
    # _FILE points at a non-existent path -> fall back to the plain env var.
    monkeypatch.setenv("MY_SECRET_FILE", str(tmp_path / "does-not-exist.txt"))
    monkeypatch.setenv("MY_SECRET", "plain-env-value")
    assert get_secret("MY_SECRET") == "plain-env-value"


def test_returns_none_when_neither_set(monkeypatch):
    monkeypatch.delenv("MY_SECRET_FILE", raising=False)
    monkeypatch.delenv("MY_SECRET", raising=False)
    assert get_secret("MY_SECRET") is None


def test_falls_back_when_file_env_points_at_directory(tmp_path, monkeypatch):
    # A directory is not ``is_file()`` — must fall back to the plain env var (never
    # attempt ``read_text`` on a directory / treat the path as a secret value).
    monkeypatch.setenv("MY_SECRET_FILE", str(tmp_path))
    monkeypatch.setenv("MY_SECRET", "plain-env-value")
    assert get_secret("MY_SECRET") == "plain-env-value"


def test_non_utf8_secret_file_raises_unicode_decode_error(tmp_path, monkeypatch):
    # Current contract: ``Path.read_text()`` is bare — a binary / non-UTF-8 Docker
    # secret aborts with ``UnicodeDecodeError`` rather than silently returning the
    # plain env fallback. Pin so a future fail-soft change is intentional.
    secret_file = tmp_path / "api_key.bin"
    secret_file.write_bytes(b"\xff\xfe\x00not-utf8")
    monkeypatch.setenv("MY_SECRET_FILE", str(secret_file))
    monkeypatch.setenv("MY_SECRET", "plain-env-value")
    try:
        get_secret("MY_SECRET")
    except UnicodeDecodeError:
        return
    raise AssertionError("expected UnicodeDecodeError for non-UTF-8 _FILE contents")
