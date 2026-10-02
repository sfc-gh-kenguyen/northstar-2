"""Single source of truth for GitHub owner / repo / branch (see ``deploy.json``)."""

from __future__ import annotations

import json
import pathlib
from typing import Any

_ROOT = pathlib.Path(__file__).resolve().parent

_DEFAULT: dict[str, Any] = {
    "github": {"owner": "sfc-gh-kenguyen", "repo": "northstar", "branch": "main"}
}


def load_deploy(*, root: pathlib.Path | None = None) -> dict[str, Any]:
    """Load ``deploy.json``. If missing or invalid, return defaults (fork-safe fallback)."""
    base = root if root is not None else _ROOT
    path = base / "deploy.json"
    if not path.is_file():
        return json.loads(json.dumps(_DEFAULT))
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(_DEFAULT))


def get_github_coords(*, root: pathlib.Path | None = None) -> tuple[str, str, str]:
    """Return ``(owner, repo, branch)`` for API and raw.githubusercontent.com paths."""
    d = load_deploy(root=root)
    gh = d.get("github") or {}
    owner = str(gh.get("owner", "") or "").strip()
    repo = str(gh.get("repo", "") or "").strip()
    branch = str(gh.get("branch", "") or "").strip()
    if owner and repo and branch:
        return owner, repo, branch
    g0 = _DEFAULT["github"]
    return str(g0["owner"]), str(g0["repo"]), str(g0["branch"])
