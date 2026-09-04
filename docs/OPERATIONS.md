# Northstar — operations

## Streamlit entrypoints

| Main file | Purpose |
|-----------|---------|
| `Home.py` | Primary Northstar app (instance 1): `st.navigation`, sheet-driven JSON, all features. **Use this** for the default Community Cloud deployment. |
| `Instance2.py` | Traffic mirror **instance 2** — for the `northstar-2` app (`northstar2.streamlit.app`). Same as `Home.py` with sidebar instance label. |
| `Instance3.py` | Traffic mirror **instance 3** — same app as `Home.py`; use as **Main file** on a **second** Community Cloud app. See [TRAFFIC_SPLITTING.md](TRAFFIC_SPLITTING.md). |
| `Instance4.py` | Traffic mirror **instance 4** — same as above. |
| `Instance5.py` | Traffic mirror **instance 5** — optional extra capacity for very large events. |
| `Instance6.py` | Traffic mirror **instance 6** — optional extra capacity for very large events. |
| `pages/1_Event_Page.py` | **Event Page** — select any event for the full checklist. |
| `pages/5_Chennai.py` | Dedicated sidebar hub for Chennai (9/5/2026). See [EVENT_HUB.md](EVENT_HUB.md). |
| `LegacyAutograderRedirect.py` | Only for a **separate** Streamlit app still bound to the legacy hostname `northstarautograder.streamlit.app`. It redirects browsers to the canonical `northstar.streamlit.app` (and preserves path/query). **Do not** set this as the main app’s entry if you want the full product. |
| `home_page.py` | Loaded as a **page** by `Home.py`, not run alone on Community Cloud (except backup / local experiments noted in code comments). |

After changing entrypoints, confirm each Community Cloud app’s **main file** in the deploy UI matches the row above.

## High-traffic events (multiple apps)

Deploy extra Community Cloud apps from the same repo to split sessions across URLs. Full steps: **[TRAFFIC_SPLITTING.md](TRAFFIC_SPLITTING.md)**.

## GitHub and sheet sync

- **Source of truth for repo coordinates:** `deploy.json` at the repository root (`github.owner`, `github.repo`, `github.branch`).
- **Python / Streamlit:** `deploy_config.py` and `repo_json.py` read `deploy.json` (with sensible defaults if the file is missing).
- **Google Apps Script (`apps_script.js`):** On each push, the script loads `deploy.json` from **raw GitHub** using `NORTHSTAR_DEPLOY_JSON_URL` (bootstrap URL). If that fetch fails, it falls back to `REPO_FALLBACK_*` constants — **keep those aligned with `deploy.json`** when you fork or rename the repo.
- When you **fork** or move the repo, update: `deploy.json`, `NORTHSTAR_DEPLOY_JSON_URL` in Apps Script, and the fallback constants in one pass.
- **northstar2 mirror:** ``northstar2.streamlit.app`` deploys from repo ``northstar-2``. Workflow ``sync-northstar2-mirror.yml`` copies ``main`` there on each push; requires Actions secret ``northstar_mirror`` (or ``NORTHSTAR2_MIRROR_TOKEN``). See [TRAFFIC_SPLITTING.md](TRAFFIC_SPLITTING.md).

## Data files (`events.json`, `workshops.json`)

- Updated by **Apps Script → GitHub Contents API** (see `apps_script.js`).
- **Events sheet columns:** `Event Name`, `Final URL` (required). Optional: `Workshop` (lab name for Event Page — must match **Workshop** on the Guides tab exactly), `Badge` / `Badges` (names on Badge status; falls back to Workshop), `Badges issued`, `Event Date`, `Issued Date`. Use `;` in **Workshop** or **Badge** for multiple titles (workshop titles may contain commas).
- **Apps Script tab names:** Set `SHEET_MAIN` to your **Events** tab (live/upcoming rows). Set `SHEET_ARCHIVE` to your **Archive** tab (past events for badge status). Do **not** point `SHEET_MAIN` at the archive tab — if `SHEET_MAIN` is empty, the script uses whichever tab is active when you push, which is easy to get wrong.
- The hosted app prefers **raw.githubusercontent.com** (see `repo_json.py`) so JSON changes do not depend on the container’s git checkout staying fresh.

## Fresh JSON after sheet sync (no reboot)

- The app loads ``events.json`` / ``workshops.json`` from **raw.githubusercontent.com** whenever it detects Streamlit Community Cloud (host contains ``.streamlit.app`` or ``.streamlit.cloud``), so updates are **not** tied to the container’s git checkout.
- JSON is **cached per commit SHA**: the app checks branch HEAD occasionally (default every 5 minutes per browser session), not on every widget rerun. After **GitHub Sync → Push**, new data appears automatically once the branch HEAD check runs (or when the user starts a new session).
- Optional Streamlit secret ``NORTHSTAR_GITHUB_TOKEN`` (or env ``GITHUB_TOKEN``): GitHub PAT with ``public_repo`` (or repo scope) raises API rate limits for SHA checks during busy events.
- Env ``NORTHSTAR_SHA_CHECK_INTERVAL_SEC`` (default ``300``): seconds between automatic branch HEAD checks.
- If the app URL is a **custom domain** that does **not** include ``.streamlit.app``, set either:
  - ``NORTHSTAR_JSON_RAW_BASE`` in **Secrets** to  
    ``https://raw.githubusercontent.com/<owner>/<repo>/<branch>`` (no trailing slash), or  
  - ``NORTHSTAR_FORCE_RAW_JSON`` = ``true`` to use the same raw base as ``deploy.json`` without relying on the hostname.

## Local development

- Install: `pip install -r requirements.txt`
- Tests: `pip install -r requirements-dev.txt` then `pytest`
- To force disk-only JSON (no remote fetch): set environment variable `NORTHSTAR_READ_JSON_FROM_DISK=1`.
