"""Event Hub config — richer Event Page content for selected high-traffic events.

Add entries to ``event_hubs.json`` (not the Google Sheet) before a big event.
Configured events get workshop lists and optional intro text on **Event Page**.
See ``docs/EVENT_HUB.md``.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

from repo_json import read_repo_json

_ROOT = pathlib.Path(__file__).resolve().parent
_BUNDLED_EVENT_HUBS = _ROOT / "event_hubs.json"


def _event_hubs_json_text() -> str:
    """Prefer ``event_hubs.json`` bundled with this deploy (same on every mirror at same commit)."""
    if _BUNDLED_EVENT_HUBS.is_file():
        return _BUNDLED_EVENT_HUBS.read_text(encoding="utf-8")
    return read_repo_json("event_hubs.json")


def _first_str(row: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        raw = row.get(key)
        if raw is None:
            continue
        s = str(raw).strip()
        if s:
            return s
    return None


def _str_list(row: dict[str, Any], keys: tuple[str, ...]) -> list[str]:
    for key in keys:
        raw = row.get(key)
        if isinstance(raw, list):
            return [str(item).strip() for item in raw if str(item).strip()]
        if isinstance(raw, str) and raw.strip():
            return [raw.strip()]
    return []


def load_event_hub_configs() -> list[dict[str, Any]]:
    """Return hub configs from ``event_hubs.json`` (may be empty)."""
    try:
        data = json.loads(_event_hubs_json_text())
    except FileNotFoundError:
        return []
    except (json.JSONDecodeError, TypeError):
        return []

    if not isinstance(data, list):
        return []

    out: list[dict[str, Any]] = []
    for row in data:
        if not isinstance(row, dict):
            continue
        event_name = _first_str(row, ("event_name", "Event Name", "event", "Event"))
        workshops = _str_list(row, ("workshops", "Workshops"))
        workshop = _first_str(row, ("workshop", "Workshop", "workshop_name", "Workshop name"))
        if not workshops and workshop:
            workshops = [workshop]
        page_path = _first_str(row, ("page", "page_path", "Page"))
        if not event_name:
            continue
        if not workshops and not page_path:
            continue
        hub_title = _first_str(row, ("hub_title", "Hub title", "title")) or event_name
        nav_title = _first_str(row, ("nav_title", "Nav title", "sidebar_title")) or hub_title
        intro = _first_str(row, ("intro", "Intro", "notes")) or ""
        trial_events = _str_list(row, ("trial_events", "trial_event_names", "Trial events"))
        out.append(
            {
                "event_name": event_name,
                "workshop": workshops[0] if workshops else (workshop or ""),
                "workshops": workshops,
                "trial_events": trial_events or [event_name],
                "hub_title": hub_title,
                "nav_title": nav_title,
                "page": page_path or "",
                "intro": intro,
            }
        )
    return out


def get_event_hub(event_name: str | None) -> dict[str, Any] | None:
    """Return hub config when ``event_name`` is configured for Event Hub."""
    if not event_name or event_name == "None":
        return None
    name = str(event_name).strip()
    for cfg in load_event_hub_configs():
        if cfg["event_name"] == name:
            return cfg
    return None


def is_event_hub_event(event_name: str | None) -> bool:
    return get_event_hub(event_name) is not None


_DEFAULT_HUB_PAGES: dict[str, str] = {
    "Chennai (9/5/2026)": "pages/5_Chennai.py",
}


def hub_page_path(cfg: dict[str, Any]) -> str | None:
    """Return the dedicated sidebar page path for a hub config, if any."""
    explicit = (cfg.get("page") or "").strip()
    if explicit:
        return explicit
    return _DEFAULT_HUB_PAGES.get(cfg["event_name"])
