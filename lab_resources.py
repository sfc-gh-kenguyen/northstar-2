"""Lab file bundles for workshops when upstream GitHub assets are unavailable."""

from __future__ import annotations

import json
import mimetypes
import pathlib
from typing import Any

_ROOT = pathlib.Path(__file__).resolve().parent
_MANIFEST_PATH = _ROOT / "lab_resources.json"


def _normalize_match(value: str) -> str:
    return (value or "").strip().casefold()


def load_lab_resource_bundles(*, root: pathlib.Path | None = None) -> list[dict[str, Any]]:
    """Return lab resource bundle definitions from ``lab_resources.json``."""
    base = root or _ROOT
    path = base / "lab_resources.json"
    if not path.is_file():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    bundles = data.get("bundles")
    if not isinstance(bundles, list):
        return []
    return [b for b in bundles if isinstance(b, dict)]


def find_lab_resource_bundle(
    workshop_title: str,
    *,
    event_name: str | None = None,
    root: pathlib.Path | None = None,
) -> dict[str, Any] | None:
    """Return the lab bundle for ``workshop_title``.

    A bundle with ``event_match`` is used only when ``event_name`` contains that
    text. Those bundles take precedence over the shared workshop bundle so one
    event can offer a different download (for example a translated notebook).
    """
    title = _normalize_match(workshop_title)
    if not title:
        return None
    event = _normalize_match(event_name or "")
    bundles = load_lab_resource_bundles(root=root)
    if event:
        for bundle in bundles:
            event_needle = _normalize_match(str(bundle.get("event_match", "")))
            needle = _normalize_match(str(bundle.get("workshop_match", "")))
            if event_needle and event_needle in event and needle and needle in title:
                return bundle
    for bundle in bundles:
        if str(bundle.get("event_match") or "").strip():
            continue
        needle = _normalize_match(str(bundle.get("workshop_match", "")))
        if needle and needle in title:
            return bundle
    return None


def read_lab_file_bytes(relative_path: str, *, root: pathlib.Path | None = None) -> bytes:
    """Read a bundled lab asset relative to the project root."""
    base = root or _ROOT
    path = (base / relative_path).resolve()
    root_resolved = base.resolve()
    if root_resolved not in path.parents and path != root_resolved:
        raise ValueError(f"Lab asset path escapes project root: {relative_path}")
    if not path.is_file():
        raise FileNotFoundError(relative_path)
    return path.read_bytes()


def read_lab_file_text(relative_path: str, *, root: pathlib.Path | None = None) -> str:
    """Read a bundled lab asset as UTF-8 text."""
    return read_lab_file_bytes(relative_path, root=root).decode("utf-8")


def is_sql_lab_file(filename: str) -> bool:
    return filename.lower().endswith(".sql")


def mime_type_for_filename(filename: str) -> str:
    if filename.endswith(".sql"):
        return "text/sql"
    guessed, _ = mimetypes.guess_type(filename)
    if guessed:
        return guessed
    return "application/octet-stream"
