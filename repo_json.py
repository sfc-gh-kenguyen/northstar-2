"""Load ``events.json`` / ``workshops.json`` from GitHub when hosted on Streamlit Cloud.

Community Cloud can serve an older git checkout in the container until reboot; fetching
``raw.githubusercontent.com`` at a **commit SHA** reflects the repo after sheet sync without
re-downloading on every widget rerun.

Coordinates come from ``deploy.json`` via ``deploy_config`` (single source of truth).
"""

from __future__ import annotations

import json
import os
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from deploy_config import get_github_coords

_ROOT = pathlib.Path(__file__).resolve().parent

_SESSION_SHA = "_northstar_branch_sha"
_SESSION_CHECKED = "_northstar_sha_checked_at"
_SESSION_FORCE = "_northstar_force_sha_refresh"

_DEFAULT_SHA_CHECK_INTERVAL_SEC = 300


def build_raw_github_url(owner: str, repo: str, ref: str, relative_path: str) -> str:
    """Return a ``raw.githubusercontent.com`` URL for ``relative_path`` at ``ref`` (branch or SHA)."""
    path = relative_path.lstrip("/")
    return f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}"


def fetch_branch_head_sha(
    owner: str,
    repo: str,
    branch: str,
    *,
    token: str | None = None,
    timeout: float = 15,
) -> str:
    """Return the current commit SHA for ``branch`` via the GitHub git ref API."""
    ref_path = urllib.parse.quote(f"heads/{branch}", safe="")
    url = f"https://api.github.com/repos/{owner}/{repo}/git/ref/{ref_path}"
    headers = {
        "User-Agent": "northstar-streamlit-json",
        "Accept": "application/vnd.github+json",
    }
    if token:
        headers["Authorization"] = f"token {token.strip()}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
    obj = data.get("object") or {}
    sha = str(obj.get("sha", "")).strip()
    if not sha:
        raise ValueError(f"Git ref response missing object.sha: {url}")
    return sha


def _http_get_text(url: str, *, timeout: float = 20) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "northstar-streamlit-json"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8")


def _sha_check_interval_sec() -> int:
    raw = os.environ.get("NORTHSTAR_SHA_CHECK_INTERVAL_SEC", str(_DEFAULT_SHA_CHECK_INTERVAL_SEC))
    try:
        return max(60, int(raw))
    except ValueError:
        return _DEFAULT_SHA_CHECK_INTERVAL_SEC


def _get_github_token() -> str | None:
    for key in ("NORTHSTAR_GITHUB_TOKEN", "GITHUB_TOKEN"):
        val = os.environ.get(key, "").strip()
        if val:
            return val
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except Exception:
        return None
    if get_script_run_ctx() is None:
        return None
    try:
        import streamlit as st

        for key in ("NORTHSTAR_GITHUB_TOKEN", "GITHUB_TOKEN"):
            try:
                v = st.secrets[key]
                if v:
                    return str(v).strip()
            except Exception:
                pass
    except Exception:
        pass
    return None


def _in_streamlit_session() -> bool:
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except Exception:
        return False
    return get_script_run_ctx() is not None


def _raw_base_url() -> str | None:
    """Base URL without trailing slash, or None to read from disk only."""
    env = os.environ.get("NORTHSTAR_JSON_RAW_BASE", "").strip().rstrip("/")
    if env:
        return env
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
    except Exception:
        return None
    if get_script_run_ctx() is None:
        return None
    try:
        import streamlit as st

        try:
            v = st.secrets["NORTHSTAR_JSON_RAW_BASE"]
            if v:
                return str(v).strip().rstrip("/")
        except Exception:
            pass
        try:
            force = st.secrets.get("NORTHSTAR_FORCE_RAW_JSON", False)
            if str(force).lower() in ("1", "true", "yes"):
                owner, repo, branch = get_github_coords()
                return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}"
        except Exception:
            pass
        host = (st.context.headers.get("Host") or st.context.headers.get("host") or "").lower()
        if ".streamlit.app" in host or ".streamlit.cloud" in host:
            owner, repo, branch = get_github_coords()
            return f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}"
    except Exception:
        pass
    return None


def clear_json_data_cache() -> None:
    """Drop cached raw JSON bodies (e.g. after a sheet push or manual refresh)."""
    if _fetch_raw_json_cached is not None:
        try:
            _fetch_raw_json_cached.clear()
        except Exception:
            pass


def request_refresh_json_cache() -> None:
    """Force a branch SHA re-check and clear cached JSON on the next rerun."""
    if _in_streamlit_session():
        import streamlit as st

        st.session_state[_SESSION_FORCE] = True
    clear_json_data_cache()


def _resolve_branch_sha(owner: str, repo: str, branch: str) -> str:
    """Return commit SHA for raw URLs; re-checks HEAD periodically, not every rerun."""
    import streamlit as st

    now = time.time()
    interval = _sha_check_interval_sec()
    cached = st.session_state.get(_SESSION_SHA)
    last_checked = float(st.session_state.get(_SESSION_CHECKED, 0.0) or 0.0)
    force = bool(st.session_state.pop(_SESSION_FORCE, False))

    need_check = force or not cached or (now - last_checked) >= interval
    if not need_check:
        return str(cached)

    token = _get_github_token()
    try:
        sha = fetch_branch_head_sha(owner, repo, branch, token=token)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, ValueError):
        if cached:
            return str(cached)
        return branch

    if cached and sha != cached:
        clear_json_data_cache()

    st.session_state[_SESSION_SHA] = sha
    st.session_state[_SESSION_CHECKED] = now
    return sha


def _fetch_raw_json_uncached(relative_path: str, ref: str, owner: str, repo: str) -> str:
    url = build_raw_github_url(owner, repo, ref, relative_path)
    return _http_get_text(url)


try:
    import streamlit as _st

    @_st.cache_data(show_spinner=False)
    def _fetch_raw_json_cached(relative_path: str, ref: str, owner: str, repo: str) -> str:
        return _fetch_raw_json_uncached(relative_path, ref, owner, repo)

except Exception:
    _fetch_raw_json_cached = None  # type: ignore[assignment,misc]


def _fetch_raw_json(relative_path: str, ref: str, owner: str, repo: str) -> str:
    """Cached raw file fetch; ``ref`` should be a commit SHA when possible."""
    if _in_streamlit_session() and _fetch_raw_json_cached is not None:
        return _fetch_raw_json_cached(relative_path, ref, owner, repo)
    return _fetch_raw_json_uncached(relative_path, ref, owner, repo)


def read_repo_json(relative_path: str) -> str:
    """Return file text. Hosted Streamlit: GitHub raw at pinned SHA; local dev: repo copy on disk."""
    if os.environ.get("NORTHSTAR_READ_JSON_FROM_DISK", "").lower() in ("1", "true", "yes"):
        return (_ROOT / relative_path).read_text(encoding="utf-8")

    if not _raw_base_url():
        return (_ROOT / relative_path).read_text(encoding="utf-8")

    owner, repo, branch = get_github_coords()
    ref = branch
    if _in_streamlit_session():
        ref = _resolve_branch_sha(owner, repo, branch)

    try:
        return _fetch_raw_json(relative_path, ref, owner, repo)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError):
        pass

    return (_ROOT / relative_path).read_text(encoding="utf-8")
