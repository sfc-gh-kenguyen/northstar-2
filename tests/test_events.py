from __future__ import annotations

import json

import pytest

import events


def test_workshops_from_value_single() -> None:
    assert events._workshops_from_value("CoCo Foundations: Getting Started with CoCo") == [
        "CoCo Foundations: Getting Started with CoCo"
    ]


def test_workshops_from_value_semicolon_separated() -> None:
    raw = (
        "Data Ingestion, Transformation, and Delivery with Snowflake; "
        "Creating Declarative Data Pipelines with Dynamic Tables"
    )
    assert events._workshops_from_value(raw) == [
        "Data Ingestion, Transformation, and Delivery with Snowflake",
        "Creating Declarative Data Pipelines with Dynamic Tables",
    ]


def test_load_event_records_includes_workshop(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps(
        [
            {
                "Event Name": "Raleigh (7/8/2026)",
                "Final URL": "https://example.com/trial",
                "Workshop": "CoCo Foundations: Getting Started with CoCo",
            }
        ]
    )
    monkeypatch.setattr(events, "read_repo_json", lambda _path: payload)
    rec = events.load_event_records()["Raleigh (7/8/2026)"]
    assert rec["workshops"] == ["CoCo Foundations: Getting Started with CoCo"]


def test_load_event_workshops_missing_event(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(events, "load_event_records", lambda: {})
    assert events.load_event_workshops("Unknown") == []


def test_load_event_records_parses_badge_column(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps(
        [
            {
                "Event Name": "Melbourne (04/13/2026)",
                "Final URL": "https://example.com/trial",
                "Workshop": "CoCo Foundations: Getting Started with CoCo",
                "Badge": "Cortex Code Foundations; Data Engineering Essentials",
                "Archived": True,
            }
        ]
    )
    monkeypatch.setattr(events, "read_repo_json", lambda _path: payload)
    rec = events.load_event_records()["Melbourne (04/13/2026)"]
    assert rec["badges"] == [
        "Cortex Code Foundations",
        "Data Engineering Essentials",
    ]
    assert events.event_badge_names(rec) == rec["badges"]


def test_load_event_records_badge_header_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = json.dumps(
        [
            {
                "Event Name": "Tokyo (4/21/2026)",
                "Final URL": None,
                "badge names": "Snowflake Cortex Badge",
                "Badges issued": True,
                "Archived": True,
            }
        ]
    )
    monkeypatch.setattr(events, "read_repo_json", lambda _path: payload)
    rec = events.load_event_records()["Tokyo (4/21/2026)"]
    assert rec["badges"] == ["Snowflake Cortex Badge"]
    assert rec["badges_issued"] is True


def test_badges_issued_is_not_read_as_badge_name() -> None:
    assert events._badge_names_str({"Badges issued": True}) is None
    assert events._badge_names_str({"Badges issued": "Yes"}) is None


def test_event_badge_names_falls_back_to_workshops() -> None:
    rec = {
        "badges": [],
        "workshops": ["Creating Declarative Data Pipelines with Dynamic Tables"],
    }
    assert events.event_badge_names(rec) == [
        "Creating Declarative Data Pipelines with Dynamic Tables"
    ]
