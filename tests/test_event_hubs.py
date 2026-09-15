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
    assert rows[0]["trial_urls_by_instance"] == {}
    assert rows[0]["trial_regions_by_instance"] == {}
    assert rows[0]["trial_split_by_instance"] is False
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
                "event_name": "APAC Virtual (9/14/2026)",
                "nav_title": "APAC Virtual — Day 1 (9/14)",
                "page": "pages/5_APAC_Virtual_Day1.py",
                "intro": "Hello APAC",
            }
        ]
    )

    monkeypatch.setattr(event_hubs, "_event_hubs_json_text", lambda: payload)
    rows = event_hubs.load_event_hub_configs()
    assert len(rows) == 1
    assert rows[0]["event_name"] == "APAC Virtual (9/14/2026)"
    assert rows[0]["workshops"] == []
    assert rows[0]["page"] == "pages/5_APAC_Virtual_Day1.py"


def test_load_event_hub_configs_parses_instance_trial_maps(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.dumps(
        [
            {
                "event_name": "APAC Virtual (9/15/2026)",
                "page": "pages/6_APAC_Virtual_Day2.py",
                "trial_split_by_instance": True,
                "trial_urls_by_instance": {
                    "northstar2": "https://signup.example/two",
                },
                "trial_regions_by_instance": {"3": "eu-west-1"},
            }
        ]
    )
    monkeypatch.setattr(event_hubs, "_event_hubs_json_text", lambda: payload)
    rows = event_hubs.load_event_hub_configs()
    assert rows[0]["trial_split_by_instance"] is True
    assert rows[0]["trial_urls_by_instance"] == {"2": "https://signup.example/two"}
    assert rows[0]["trial_regions_by_instance"] == {"3": "eu-west-1"}


def test_replace_signup_region_keeps_token() -> None:
    url = (
        "https://signup.snowflake.com/?trial=student&cloud=aws&region=ap-northeast-1"
        "&utm_content=apac-virtual-0915&t=abc123"
    )
    out = event_hubs.replace_signup_region(url, "us-west-2")
    assert "region=us-west-2" in out
    assert "t=abc123" in out
    assert "utm_content=apac-virtual-0915" in out
    assert "ap-northeast-1" not in out


def test_resolve_instance_trial_url_prefers_full_url() -> None:
    hub = {
        "event_name": "APAC Virtual (9/15/2026)",
        "trial_urls_by_instance": {"2": "https://signup.example/ns2"},
        "trial_split_by_instance": True,
    }
    sheet = "https://signup.snowflake.com/?region=ap-northeast-1&t=abc"
    assert (
        event_hubs.resolve_instance_trial_url(sheet, hub, instance_label="northstar2")
        == "https://signup.example/ns2"
    )


def test_default_instance_trial_regions() -> None:
    assert event_hubs.DEFAULT_INSTANCE_TRIAL_REGIONS == {
        "1": "ap-northeast-1",
        "2": "ap-northeast-2",
        "3": "ap-northeast-3",
        "4": "ap-south-1",
        "5": "ap-northeast-1",
        "6": "ap-northeast-2",
    }


def test_resolve_instance_trial_url_rewrites_region_when_split() -> None:
    hub = {
        "event_name": "APAC Virtual (9/15/2026)",
        "trial_split_by_instance": True,
        "trial_urls_by_instance": {},
    }
    sheet = "https://signup.snowflake.com/?trial=student&region=ap-northeast-1&t=abc"
    out = event_hubs.resolve_instance_trial_url(sheet, hub, instance_label="2")
    assert "region=ap-northeast-2" in out
    assert "t=abc" in out


def test_resolve_instance_trial_url_instance_one_keeps_tokyo() -> None:
    hub = {
        "event_name": "APAC Virtual (9/14/2026)",
        "trial_split_by_instance": True,
        "trial_urls_by_instance": {},
    }
    sheet = "https://signup.snowflake.com/?region=ap-northeast-1&t=abc"
    out = event_hubs.resolve_instance_trial_url(sheet, hub, instance_label="1")
    assert out == sheet


def test_resolve_instance_trial_url_without_hub_uses_sheet() -> None:
    sheet = "https://signup.snowflake.com/?region=ap-northeast-1"
    assert event_hubs.resolve_instance_trial_url(sheet, None, instance_label="2") == sheet


def test_resolve_instance_trial_url_ignores_non_apac_hub() -> None:
    sheet = "https://signup.snowflake.com/?region=eu-west-1&t=milan"
    hub = {
        "event_name": "Milan (9/17/2026)",
        "trial_split_by_instance": True,
        "trial_urls_by_instance": {"2": "https://signup.example/should-not-use"},
    }
    assert event_hubs.resolve_instance_trial_url(sheet, hub, instance_label="2") == sheet


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
            "nav_title": "APAC Virtual — Day 1 (9/14)",
            "intro": "Hello APAC",
            "workshops": [],
            "trial_events": [name],
        }
        if name == "APAC Virtual (9/14/2026)"
        else None,
    )
    monkeypatch.setattr(
        event_page,
        "load_event_workshops",
        lambda name: ["Lab From Sheet"] if name == "APAC Virtual (9/14/2026)" else [],
    )
    cfg = event_page.resolve_event_config("APAC Virtual (9/14/2026)")
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
