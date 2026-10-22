from __future__ import annotations

import json
import re
from typing import Any

import streamlit as st

from repo_json import read_repo_json

_GITHUB_BLOB_RE = re.compile(
    r"^https?://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$",
    re.IGNORECASE,
)


def answer_key_fetch_url(url: str) -> str:
    """Return a URL suitable for HTTP GET of file contents (raw.githubusercontent.com).

    Accepts existing raw URLs or ``github.com/.../blob/branch/path`` links from the sheet.
    """
    s = (url or "").strip()
    if not s:
        return s
    if "raw.githubusercontent.com" in s.lower():
        return s
    m = _GITHUB_BLOB_RE.match(s)
    if m:
        user, repo, branch, path = m.groups()
        return f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}"
    return s


def _optional_str(raw: Any) -> str | None:
    if raw is None:
        return None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        s = str(raw).strip()
        return s if s else None
    s = str(raw).strip()
    return s if s else None


def _first(row: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    for k in keys:
        v = _optional_str(row.get(k))
        if v:
            return v
    return None


_DEFAULT_PENDING = "Coming soon"


def resolve_workshop_option(name: str, options: list[str]) -> str | None:
    """Match ``name`` to a dropdown option (exact, then case-insensitive)."""
    title = (name or "").strip()
    if not title:
        return None
    if title in options:
        return title
    lower = title.lower()
    for opt in options:
        if opt.strip().lower() == lower:
            return opt
    return None


def load_workshop_rows() -> list[dict[str, str]]:
    """Load workshop rows from ``workshops.json`` (sheet → Apps Script → repo).

    Each dict has: ``workshop``, ``guide_url``, ``answer_key_url`` (may be empty),
    ``guide_label``, ``answer_key_label``, ``guide_pending_text``, ``answer_key_pending_text``.
    Empty URLs show ``guide_pending_text`` / ``answer_key_pending_text`` on the Guides page
    (default *Coming soon*). Optional sheet/JSON columns **Guide placeholder** and
    **Answer Key placeholder** override that text per row.
    """
    try:
        data = json.loads(read_repo_json("workshops.json"))
    except FileNotFoundError:
        st.warning("workshops.json not found — add it via GitHub or sheet sync.", icon="⚠️")
        return []
    except (json.JSONDecodeError, TypeError):
        st.warning("Could not load workshops — check workshops.json for formatting errors.", icon="⚠️")
        return []

    if not isinstance(data, list):
        st.warning("workshops.json must be a JSON array of workshop objects.", icon="⚠️")
        return []

    out: list[dict[str, str]] = []
    for r in data:
        if not isinstance(r, dict):
            continue
        workshop = _first(
            r,
            (
                "Workshop",
                "workshop",
                "Workshop name",
                "workshop name",
                "Course",
                "course",
                "Course name",
                "course name",
                "Title",
                "title",
                "Workshop title",
                "workshop title",
            ),
        )
        guide_url = _first(
            r,
            ("Guide URL", "Guide url", "guide_url", "guide url"),
        ) or ""
        answer_key_url = _first(
            r,
            (
                "Answer Key URL",
                "Answer key URL",
                "answer_key_url",
                "Answer key url",
                "Answer Key url",
            ),
        ) or ""
        if not workshop:
            continue
        guide_pending = _first(
            r,
            (
                "Guide placeholder",
                "Guide status",
                "guide placeholder",
                "guide status",
            ),
        ) or _DEFAULT_PENDING
        answer_key_pending = _first(
            r,
            (
                "Answer Key placeholder",
                "Answer key placeholder",
                "answer key placeholder",
                "Answer Key status",
                "Answer key status",
            ),
        ) or _DEFAULT_PENDING
        guide_label = _first(
            r,
            ("Guide link text", "Guide Link Text", "guide_link_text", "guide link text"),
        ) or "View Guide"
        answer_key_label = _first(
            r,
            (
                "Answer Key link text",
                "Answer key link text",
                "answer_key_link_text",
                "Answer key Link Text",
            ),
        )
        if answer_key_url and not answer_key_label:
            answer_key_label = answer_key_url.rsplit("/", 1)[-1] or "Answer key"
        elif not answer_key_url:
            answer_key_label = answer_key_pending
        out.append(
            {
                "workshop": workshop,
                "guide_url": guide_url,
                "answer_key_url": answer_key_url,
                "guide_label": guide_label,
                "answer_key_label": answer_key_label,
                "guide_pending_text": guide_pending,
                "answer_key_pending_text": answer_key_pending,
            }
        )
    return out


def load_answer_key_map() -> dict[str, str]:
    """Workshop title → raw URL for answer-key fetch (Auto-Grader).

    Workshops with no **Answer Key URL** are omitted until a URL is added.
    """
    out: dict[str, str] = {}
    for row in load_workshop_rows():
        url = (row.get("answer_key_url") or "").strip()
        if not url:
            continue
        raw = answer_key_fetch_url(url)
        if raw:
            out[row["workshop"]] = raw
    return out


def workshop_has_answer_key(workshop_title: str) -> bool:
    """True when ``workshop_title`` has an answer key (Auto-Grader eligible)."""
    title = (workshop_title or "").strip()
    if not title:
        return False
    options = list(load_answer_key_map().keys())
    return resolve_workshop_option(title, options) is not None
