from __future__ import annotations

import datetime as dt
import json

import pytest

import events
import expedition_tokens as et

URL = (
    "https://signup.snowflake.com/?trial=student&cloud=aws&region=us-east-2"
    "&utm_source=workshop&utm_campaign=northstar-2026"
    "&utm_content=expedition-d2-noam&t=oldtoken"
)
TOKENS = [(dt.date(2026, 11, 7), "tokA"), (dt.date(2026, 11, 11), "tokB")]


def test_current_token_window_edges() -> None:
    assert et.current_token(TOKENS, dt.date(2026, 11, 4)) is None
    assert et.current_token(TOKENS, dt.date(2026, 11, 5)) == "tokA"
    assert et.current_token(TOKENS, dt.date(2026, 11, 8)) == "tokA"
    # Overlap day: the later event date wins.
    assert et.current_token(TOKENS, dt.date(2026, 11, 9)) == "tokB"
    assert et.current_token(TOKENS, dt.date(2026, 11, 13)) == "tokB"
    assert et.current_token(TOKENS, dt.date(2026, 11, 14)) is None


def test_rotate_url_swaps_only_t() -> None:
    out = et.rotate_url(URL, "newtoken")
    assert out == URL.replace("t=oldtoken", "t=newtoken")


def test_rotate_url_ignores_non_expedition_and_missing_token() -> None:
    other = URL.replace("expedition-d2-noam", "london-1126")
    assert et.rotate_url(other, "newtoken") == other
    assert et.rotate_url(URL, None) == URL


def test_parse_tokens_skips_bad_rows() -> None:
    raw = [
        {"event_date": "2026-11-07", "t": "tokA"},
        {"event_date": "not-a-date", "t": "x"},
        {"event_date": "2026-11-11"},
    ]
    assert et._parse_tokens(raw) == [(dt.date(2026, 11, 7), "tokA")]


def test_load_event_records_rotates_expedition(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps(
        [
            {"Event Name": "Expedition Day 2 (NOAM)", "Final URL": URL},
            {"Event Name": "London", "Final URL": "https://example.com/?t=keep"},
        ]
    )
    monkeypatch.setattr(events, "read_repo_json", lambda _path: payload)
    monkeypatch.setattr(events, "load_tokens", lambda: TOKENS)
    monkeypatch.setattr(events, "current_token", lambda toks: "tokA")
    recs = events.load_event_records()
    assert recs["Expedition Day 2 (NOAM)"]["final_url"].endswith("t=tokA")
    assert recs["London"]["final_url"] == "https://example.com/?t=keep"
