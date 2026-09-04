from __future__ import annotations

import json

import pytest

import event_hubs
import event_page


def test_load_event_hub_configs_parses_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps(
        [
            {
                "event_name": "Big Event 2026",
                "workshop": "My Workshop",
                "hub_title": "Welcome",
                "nav_title": "Welcome",
                "intro": "Hello room",
            }
        ]
    )

    monkeypatch.setattr(event_hubs, "_event_hubs_json_text", lambda: payload)
    rows = event_hubs.load_event_hub_configs()
    assert len(rows) == 1
    assert rows[0]["event_name"] == "Big Event 2026"
    assert rows[0]["workshop"] == "My Workshop"
    assert rows[0]["workshops"] == ["My Workshop"]
    assert rows[0]["trial_events"] == ["Big Event 2026"]
    assert rows[0]["hub_title"] == "Welcome"
    assert rows[0]["nav_title"] == "Welcome"
    assert rows[0]["intro"] == "Hello room"


def test_load_event_hub_configs_parses_multi_workshop(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps(
        [
            {
                "event_name": "APAC Virtual (7/15/2026)",
                "nav_title": "APAC Virtual — Day 1",
                "workshops": ["Lab A", "Lab B"],
                "trial_events": ["APAC Virtual (7/15/2026)", "APAC Virtual (7/16/2026)"],
            }
        ]
    )

    monkeypatch.setattr(event_hubs, "_event_hubs_json_text", lambda: payload)
    rows = event_hubs.load_event_hub_configs()
    assert rows[0]["workshops"] == ["Lab A", "Lab B"]
    assert rows[0]["trial_events"] == [
        "APAC Virtual (7/15/2026)",
        "APAC Virtual (7/16/2026)",
    ]


def test_load_event_hub_configs_allows_page_only_hub(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps(
        [
            {
                "event_name": "Chennai (9/5/2026)",
                "nav_title": "Chennai (9/5/2026)",
                "page": "pages/5_Chennai.py",
                "intro": "Hello Chennai",
            }
        ]
    )

    monkeypatch.setattr(event_hubs, "_event_hubs_json_text", lambda: payload)
    rows = event_hubs.load_event_hub_configs()
    assert len(rows) == 1
    assert rows[0]["event_name"] == "Chennai (9/5/2026)"
    assert rows[0]["workshops"] == []
    assert rows[0]["page"] == "pages/5_Chennai.py"


def test_hub_page_path_chennai_default() -> None:
    cfg = {"event_name": "Chennai (9/5/2026)", "page": ""}
    assert event_hubs.hub_page_path(cfg) == "pages/5_Chennai.py"


def test_hub_page_path_explicit_page() -> None:
    cfg_explicit = {
        "event_name": "Big Event 2026",
        "page": "pages/5_Big_Event.py",
    }
    assert event_hubs.hub_page_path(cfg_explicit) == "pages/5_Big_Event.py"


def test_hub_page_path_unknown_event() -> None:
    cfg = {"event_name": "Unknown Event", "page": ""}
    assert event_hubs.hub_page_path(cfg) is None


def test_hub_page_path_no_default_without_explicit_page() -> None:
    cfg = {"event_name": "Big Event 2026", "page": ""}
    assert event_hubs.hub_page_path(cfg) is None


def test_get_event_hub_match(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        event_hubs,
        "load_event_hub_configs",
        lambda: [
            {
                "event_name": "Summit Day",
                "workshop": "Lab A",
                "workshops": ["Lab A"],
                "trial_events": ["Summit Day"],
                "hub_title": "Summit Day",
                "intro": "",
            }
        ],
    )
    assert event_hubs.is_event_hub_event("Summit Day") is True
    assert event_hubs.get_event_hub("Summit Day")["workshop"] == "Lab A"
    assert event_hubs.is_event_hub_event("Other") is False


def test_resolve_event_config_uses_hub_overlay(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        event_page,
        "get_event_hub",
        lambda name: {
            "event_name": name,
            "nav_title": "Summit Day",
            "intro": "Hello summit",
            "workshops": ["Lab A", "Lab B"],
            "trial_events": [name],
        }
        if name == "Summit Day"
        else None,
    )
    cfg = event_page.resolve_event_config("Summit Day")
    assert cfg["title"] == "Summit Day"
    assert cfg["workshops"] == ["Lab A", "Lab B"]
    assert cfg["intro"] == "Hello summit"


def test_resolve_event_config_hub_falls_back_to_sheet_workshops(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        event_page,
        "get_event_hub",
        lambda name: {
            "event_name": name,
            "nav_title": "Chennai (9/5/2026)",
            "intro": "Hello Chennai",
            "workshops": [],
            "trial_events": [name],
        }
        if name == "Chennai (9/5/2026)"
        else None,
    )
    monkeypatch.setattr(
        event_page,
        "load_event_workshops",
        lambda name: ["Lab From Sheet"] if name == "Chennai (9/5/2026)" else [],
    )
    cfg = event_page.resolve_event_config("Chennai (9/5/2026)")
    assert cfg["workshops"] == ["Lab From Sheet"]


def test_resolve_event_config_defaults_without_hub(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(event_page, "get_event_hub", lambda _name: None)
    monkeypatch.setattr(
        event_page,
        "load_event_workshops",
        lambda name: ["Lab From Sheet"] if name == "Seoul (6/23/2026)" else [],
    )
    cfg = event_page.resolve_event_config("Seoul (6/23/2026)")
    assert cfg["title"] == "Seoul (6/23/2026)"
    assert cfg["workshops"] == ["Lab From Sheet"]
    assert cfg["trial_events"] == ["Seoul (6/23/2026)"]
    assert cfg["intro"]
