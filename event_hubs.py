"""Event Hub config — richer Event Page content for selected high-traffic events.

Add entries to ``event_hubs.json`` (not the Google Sheet) before a big event.
Configured events get workshop lists and optional intro text on **Event Page**.
See ``docs/EVENT_HUB.md``.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from instance_config import get_instance_label, normalize_instance_key
from repo_json import read_repo_json

# Default student-trial AWS regions when a hub sets ``trial_split_by_instance``.
# Keys are instance labels (northstar → 1, northstar2 → 2, …).
DEFAULT_INSTANCE_TRIAL_REGIONS: dict[str, str] = {
    "1": "ap-northeast-1",
    "2": "ap-northeast-2",
    "3": "ap-northeast-3",
    "4": "ap-south-1",
    "5": "ap-northeast-1",
    "6": "ap-northeast-2",
}

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


def _instance_str_map(row: dict[str, Any], keys: tuple[str, ...]) -> dict[str, str]:
    for key in keys:
        raw = row.get(key)
        if not isinstance(raw, dict):
            continue
        out: dict[str, str] = {}
        for map_key, map_val in raw.items():
            inst = normalize_instance_key(str(map_key))
            val = str(map_val).strip() if map_val is not None else ""
            if inst and val:
                out[inst] = val
        return out
    return {}


def replace_signup_region(url: str, region: str) -> str:
    """Return ``url`` with the ``region`` query parameter set to ``region``."""
    parts = urlparse(url)
    pairs: list[tuple[str, str]] = []
    replaced = False
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if key == "region":
            pairs.append((key, region))
            replaced = True
        else:
            pairs.append((key, value))
    if not replaced:
        pairs.append(("region", region))
    return urlunparse(parts._replace(query=urlencode(pairs)))


def resolve_instance_trial_url(
    sheet_url: str | None,
    hub: dict[str, Any] | None,
    *,
    instance_label: str | None = None,
) -> str | None:
    """Pick a trial signup URL for the current traffic-mirror instance.

    Only **APAC Virtual** hubs may override the sheet link. All other events
    always return ``sheet_url``.

    Precedence for APAC Virtual:
    1. ``trial_urls_by_instance`` for this instance (full URL)
    2. ``trial_regions_by_instance`` (or defaults when ``trial_split_by_instance``)
       applied to the sheet URL's ``region`` query param
    3. The Events sheet ``Final URL``
    """
    if instance_label is None:
        instance_label = get_instance_label()
    inst = normalize_instance_key(instance_label)
    # Instance-specific trial links are APAC Virtual only; every other event uses the sheet URL.
    event_name = str((hub or {}).get("event_name") or "")
    if hub and event_name.lower().startswith("apac virtual"):
        urls = hub.get("trial_urls_by_instance")
        if isinstance(urls, dict):
            override = urls.get(inst)
            if override:
                return str(override).strip() or sheet_url
        regions = hub.get("trial_regions_by_instance")
        region = None
        if isinstance(regions, dict) and regions.get(inst):
            region = str(regions[inst]).strip()
        elif hub.get("trial_split_by_instance"):
            region = DEFAULT_INSTANCE_TRIAL_REGIONS.get(inst)
        if region and sheet_url:
            return replace_signup_region(sheet_url, region)
    return sheet_url


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
        trial_urls_by_instance = _instance_str_map(
            row, ("trial_urls_by_instance", "trial_urls")
        )
        trial_regions_by_instance = _instance_str_map(
            row, ("trial_regions_by_instance", "trial_regions")
        )
        split_raw = row.get("trial_split_by_instance", row.get("split_trial_by_instance"))
        trial_split_by_instance = split_raw is True or str(split_raw).strip().lower() in (
            "true",
            "1",
            "yes",
        )
        out.append(
            {
                "event_name": event_name,
                "workshop": workshops[0] if workshops else (workshop or ""),
                "workshops": workshops,
                "trial_events": trial_events or [event_name],
                "trial_urls_by_instance": trial_urls_by_instance,
                "trial_regions_by_instance": trial_regions_by_instance,
                "trial_split_by_instance": trial_split_by_instance,
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


def hub_page_path(cfg: dict[str, Any]) -> str | None:
    """Return the dedicated sidebar page path for a hub config, if any."""
    explicit = (cfg.get("page") or "").strip()
    return explicit or None
