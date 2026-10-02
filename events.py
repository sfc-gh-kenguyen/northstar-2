from __future__ import annotations

import json
from typing import Any

import streamlit as st

from repo_json import read_repo_json


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


def _norm_header(raw: Any) -> str:
    return " ".join(str(raw).replace("\u00a0", " ").split()).lower()


BADGE_NAME_HEADERS: tuple[str, ...] = (
    "Badge",
    "Badges",
    "Badge name",
    "Badge names",
    "Badge(s)",
    "Badge title",
    "Badge titles",
    "Badge earned",
    "Badges earned",
)


def _badge_names_str(row: dict[str, Any]) -> str | None:
    """Badge title cell, matching sheet headers case/space-insensitively.

    Exact-header matching keeps this from picking up ``Badges issued``.
    """
    wanted = {_norm_header(h): i for i, h in enumerate(BADGE_NAME_HEADERS)}
    best: tuple[int, str] | None = None
    for key, value in row.items():
        rank = wanted.get(_norm_header(key))
        if rank is None:
            continue
        text = _optional_str(value)
        if text and (best is None or rank < best[0]):
            best = (rank, text)
    return best[1] if best else None


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


def _workshops_from_value(raw: Any) -> list[str]:
    """Parse workshop name(s) from a sheet cell.

    Workshop titles often contain commas, so use ``;`` to separate multiple labs
    in one cell (e.g. two parallel tracks on the same day).
    """
    text = _optional_str(raw)
    if not text:
        return []
    if ";" in text:
        return [part.strip() for part in text.split(";") if part.strip()]
    return [text]


def load_event_records() -> dict[str, dict[str, Any]]:
    """Read events from events.json.

    Each value includes:
      - ``final_url``: str | None (trial signup link)
      - ``workshops``: list[str] — from optional sheet **Workshop** column
      - ``badges``: list[str] — from optional sheet **Badge** / **Badges** column
        (header matched case-insensitively; never ``Badges issued``)
      - ``badges_issued``: bool | None — True if badges sent, False if not yet, None if unset
      - ``archived``: bool — True if row came from the archive tab only (see Apps Script merge)
      - ``event_date``: str | None — optional, from sheet "Event Date"
      - ``issued_date``: str | None — optional, from sheet "Issued Date"
    """
    try:
        data = json.loads(read_repo_json("events.json"))
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
                "workshops": _workshops_from_value(
                    _first_header_str(
                        r,
                        (
                            "Workshop",
                            "Workshops",
                            "workshop",
                            "workshops",
                            "Workshop name",
                            "workshop name",
                            "Lab",
                            "Lab name",
                            "Labs",
                            "Course",
                            "Course name",
                        ),
                    )
                ),
                "badges": _workshops_from_value(_badge_names_str(r)),
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

    Used for Event Page (and optional ``?event=`` URL preselection). Archive-only events
    stay in ``events.json`` for Badge status but are not selectable here.
    """
    return {
        name: rec["final_url"]
        for name, rec in load_event_records().items()
        if not rec.get("archived")
    }


def event_badge_names(rec: dict[str, Any] | None) -> list[str]:
    """Badge titles for an event record (explicit Badge column, else workshops)."""
    if not rec:
        return []
    for key in ("badges", "workshops"):
        names = rec.get(key)
        if isinstance(names, list):
            out = [str(n).strip() for n in names if str(n).strip()]
            if out:
                return out
    return []


def load_event_workshops(event_name: str | None) -> list[str]:
    """Workshop name(s) from the Events sheet for ``event_name`` (may be empty)."""
    if not event_name or event_name == "None":
        return []
    rec = load_event_records().get(str(event_name).strip())
    if not rec:
        return []
    workshops = rec.get("workshops")
    if isinstance(workshops, list):
        return [str(w).strip() for w in workshops if str(w).strip()]
    return []
