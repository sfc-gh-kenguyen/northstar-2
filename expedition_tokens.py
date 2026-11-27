"""Rotate the signup ``t=`` token on Expedition (virtual, always-on) trial links.

Signup Link Generator tokens are valid 2 days before through ~3 days after the
chosen Event Date (UTC). ``expedition_tokens.json`` (hand-maintained, not touched by
the sheet sync) lists pre-generated tokens by event date; the token whose window
covers today replaces ``t=`` on every URL whose ``utm_content`` starts with
``expedition-``. UTMs and the rest of the URL are left unchanged.
"""

from __future__ import annotations

import datetime as dt
import json
import urllib.parse
from typing import Any

from repo_json import read_repo_json

TOKENS_FILE = "expedition_tokens.json"
UTM_CONTENT_PREFIX = "expedition-"
DAYS_BEFORE = 2
# Generator says "3 days following"; use 2 so we never serve a token on its edge day.
DAYS_AFTER = 2


def _parse_tokens(raw: Any) -> list[tuple[dt.date, str]]:
    out: list[tuple[dt.date, str]] = []
    if not isinstance(raw, list):
        return out
    for row in raw:
        if not isinstance(row, dict):
            continue
        token = str(row.get("t") or "").strip()
        date_str = str(row.get("event_date") or "").strip()
        if not token or not date_str:
            continue
        try:
            out.append((dt.date.fromisoformat(date_str), token))
        except ValueError:
            continue
    return out


def load_tokens() -> list[tuple[dt.date, str]]:
    try:
        return _parse_tokens(json.loads(read_repo_json(TOKENS_FILE)))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def current_token(
    tokens: list[tuple[dt.date, str]], today: dt.date | None = None
) -> str | None:
    """Token whose validity window covers ``today`` (UTC); latest event date wins."""
    today = today or dt.datetime.now(dt.timezone.utc).date()
    covering = [
        (event_date, token)
        for event_date, token in tokens
        if event_date - dt.timedelta(days=DAYS_BEFORE)
        <= today
        <= event_date + dt.timedelta(days=DAYS_AFTER)
    ]
    if not covering:
        return None
    return max(covering)[1]


def is_expedition_url(url: str | None) -> bool:
    if not url:
        return False
    query = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    return any(v.startswith(UTM_CONTENT_PREFIX) for v in query.get("utm_content", []))


def with_token(url: str, token: str) -> str:
    """Replace (or add) ``t=`` in ``url``, preserving all other params and order."""
    parts = urllib.parse.urlsplit(url)
    pairs = urllib.parse.parse_qsl(parts.query, keep_blank_values=True)
    replaced = False
    new_pairs: list[tuple[str, str]] = []
    for key, value in pairs:
        if key == "t":
            new_pairs.append((key, token))
            replaced = True
        else:
            new_pairs.append((key, value))
    if not replaced:
        new_pairs.append(("t", token))
    return urllib.parse.urlunsplit(
        parts._replace(query=urllib.parse.urlencode(new_pairs, safe=""))
    )


def rotate_url(url: str | None, token: str | None) -> str | None:
    """Apply ``token`` to Expedition URLs; return others (or no token) unchanged."""
    if not url or not token or not is_expedition_url(url):
        return url
    return with_token(url, token)
