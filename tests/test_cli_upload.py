"""CLI-level tests for `devpub upload`, focused on output modes."""

import json

import pytest
from click.testing import CliRunner

from devpub.cli import cli


@pytest.fixture(autouse=True)
def _fake_session(monkeypatch):
    """Bypass the real credential lookup so the command can run offline.

    Patched on the images module, where the name is actually resolved.
    """
    import devpub.cli.images as images_mod

    monkeypatch.setattr(
        images_mod, "ensure_session_credentials", lambda: ("session", "csrf")
    )


def _stub_uploads(monkeypatch, results):
    """Make ImageUploader.upload return a URL per filename, or raise for errors.

    `results` maps a filename to either a URL string or an Exception to raise.
    """
    from pathlib import Path

    def fake_upload(self, path):
        outcome = results[Path(path).name]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr("devpub.api.uploads.ImageUploader.upload", fake_upload)


def test_json_output_is_pure_json_on_stdout(monkeypatch):
    _stub_uploads(monkeypatch, {"a.png": "https://img/a.png", "b.png": "https://img/b.png"})
    runner = CliRunner()
    result = runner.invoke(cli, ["upload", "a.png", "b.png", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)  # must parse cleanly -> no rich noise
    assert [u["file"] for u in payload["uploaded"]] == ["a.png", "b.png"]
    assert payload["uploaded"][0]["url"] == "https://img/a.png"
    assert payload["failed"] == []


def test_json_reports_failures_and_exits_nonzero(monkeypatch):
    from devpub.api.devto import APIError

    _stub_uploads(
        monkeypatch,
        {"ok.png": "https://img/ok.png", "bad.png": APIError(422, "nope")},
    )
    runner = CliRunner()
    result = runner.invoke(cli, ["upload", "ok.png", "bad.png", "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert [u["file"] for u in payload["uploaded"]] == ["ok.png"]
    assert payload["failed"][0]["file"] == "bad.png"
    assert payload["failed"][0]["error"] == "nope"


def test_markdown_and_json_are_mutually_exclusive():
    runner = CliRunner()
    result = runner.invoke(cli, ["upload", "a.png", "--markdown", "--json"])
    assert result.exit_code != 0
    assert "mutually exclusive" in result.output


def test_all_success_exits_zero(monkeypatch):
    _stub_uploads(monkeypatch, {"a.png": "https://img/a.png"})
    runner = CliRunner()
    result = runner.invoke(cli, ["upload", "a.png", "--json"])
    assert result.exit_code == 0
