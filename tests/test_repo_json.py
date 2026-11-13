from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


def test_read_repo_json_events_disk_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NORTHSTAR_READ_JSON_FROM_DISK", "1")
    try:
        from repo_json import read_repo_json

        text = read_repo_json("events.json")
    finally:
        monkeypatch.delenv("NORTHSTAR_READ_JSON_FROM_DISK", raising=False)
    assert text.strip().startswith("[")


def test_build_raw_github_url() -> None:
    from repo_json import build_raw_github_url

    url = build_raw_github_url("acme", "northstar", "abc123def", "events.json")
    assert url == "https://raw.githubusercontent.com/acme/northstar/abc123def/events.json"


def test_fetch_branch_head_sha_parses_response() -> None:
    from repo_json import fetch_branch_head_sha

    payload = json.dumps({"object": {"sha": "deadbeef" * 5}}).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = payload
    mock_resp.__enter__ = MagicMock(return_value=mock_resp)
    mock_resp.__exit__ = MagicMock(return_value=False)

    with patch("repo_json.urllib.request.urlopen", return_value=mock_resp):
        sha = fetch_branch_head_sha("acme", "northstar", "main", token="test-token")

    assert sha == "deadbeef" * 5


def test_sha_check_interval_minimum(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NORTHSTAR_SHA_CHECK_INTERVAL_SEC", "10")
    from repo_json import _sha_check_interval_sec

    assert _sha_check_interval_sec() == 60
