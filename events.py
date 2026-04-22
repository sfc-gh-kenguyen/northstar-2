from __future__ import annotations

import json
import pathlib
from typing import Any

import streamlit as st

_EVENTS_FILE = pathlib.Path(__file__).parent / "events.json"


def _optional_str(raw: Any) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        if isinstance(raw, float) and raw.is_integer():
            raw = int(raw)
        s = str(raw).strip()
        return s if s else None
    s = str(raw).strip()
    return s if s else None


def _first_header_str(row: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    """First non-empty value among possible JSON / sheet key spellings."""
    for k in keys:
        v = _optional_str(row.get(k))
        if v:
            return v
    return None


def _parse_badges_issued(raw: Any) -> bool | None:
    """Normalize JSON / sheet values to True (issued), False (not yet), or None (unknown)."""
    if raw is None:
        return None
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)):
        if raw == 1:
            return True
        if raw == 0:
            return False
        return None
    if isinstance(raw, str):
        s = raw.strip().lower()
        if s in ("yes", "true", "1", "y", "issued"):
            return True
        if s in ("no", "false", "0", "n", "not yet", "not_yet", "pending"):
            return False
        if s == "":
            return None
    return None


def load_event_records() -> dict[str, dict[str, Any]]:
    """Read events from events.json.

    Each value includes:
      - ``final_url``: str | None (trial signup link)
      - ``badges_issued``: bool | None — True if badges sent, False if not yet, None if unset
      - ``archived``: bool — True if row came from the archive tab only (see Apps Script merge)
      - ``event_date``: str | None — optional, from sheet "Event Date"
      - ``issued_date``: str | None — optional, from sheet "Issued Date"
    """
    try:
        data = json.loads(_EVENTS_FILE.read_text())
        out: dict[str, dict[str, Any]] = {}
        for r in data:
            name = r.get("Event Name")
            if not name:
                continue
            name = str(name).strip()
            if not name:
                continue
            archived_raw = r.get("Archived", False)
            archived = archived_raw is True or str(archived_raw).lower() in ("true", "1", "yes")
            out[name] = {
                "final_url": r.get("Final URL") or None,
                "badges_issued": _parse_badges_issued(r.get("Badges issued")),
                "archived": archived,
                "event_date": _first_header_str(
                    r,
                    ("Event Date", "event_date", "Event date"),
                ),
                "issued_date": _first_header_str(
                    r,
                    (
                        "Issued Date",
                        "Issued date",
                        "issued_date",
                        "Date Issued",
                        "date_issued",
                        "IssuedDate",
                    ),
                ),
            }
        return out
    except (json.JSONDecodeError, KeyError, TypeError):
        st.warning("Could not load events — check events.json for formatting errors.", icon="⚠️")
        return {}
    except FileNotFoundError:
        return {}


def load_events() -> dict[str, str | None]:
    """Active roster events only (excludes archive-tab-only rows).

    Used for the sidebar event picker and Trial Sign Up. Archive-only events
    stay in ``events.json`` for Badge status but are not selectable here.
    """
    return {
        name: rec["final_url"]
        for name, rec in load_event_records().items()
        if not rec.get("archived")
    }
