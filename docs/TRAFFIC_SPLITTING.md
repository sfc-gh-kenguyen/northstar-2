# Splitting traffic across multiple Northstar apps

Streamlit Community Cloud runs **one Python process pool per app**. A single app URL can hit session and bandwidth limits when hundreds of attendees use it at once. The fix is to deploy **several identical apps** from the same GitHub repo and send different groups of attendees to different URLs.

All mirrors share the same ``events.json``, ``workshops.json``, and code (via GitHub + sheet sync). You only split **compute and connections**, not data.

## Recommended layout

| Instance | Main file | App name in Streamlit Cloud | URL |
|----------|-----------|----------------------------|-----|
| 1 (primary) | ``Home.py`` | ``northstar`` (existing) | ``https://northstar.streamlit.app`` |
| 2 | ``Instance2.py`` (or ``Home.py``) | ``northstar2`` | ``https://northstar2.streamlit.app`` |
| 3 | ``Instance3.py`` | ``northstar3`` | ``https://northstar3.streamlit.app`` |
| 4 | ``Instance4.py`` | ``northstar4`` | ``https://northstar4.streamlit.app`` |
| 5 | ``Instance5.py`` | ``northstar5`` | ``https://northstar5.streamlit.app`` |
| 6 | ``Instance6.py`` | ``northstar6`` | ``https://northstar6.streamlit.app`` |

The **App name** you pick in [share.streamlit.io](https://share.streamlit.io) becomes the subdomain. Names like ``northstar5`` / ``northstar6`` work with no extra configuration.

## One-time setup: create a new mirror

Do the following for each new instance (3–6). Steps below use **instance 5** as an example.

1. Go to [share.streamlit.io](https://share.streamlit.io) and sign in.
2. Click **Create app**.
3. Set:
   - **Repository:** ``sfc-gh-kenguyen/northstar`` (or your fork)
   - **Branch:** ``main``
   - **Main file path:** ``Instance5.py`` (or ``Instance3.py`` / ``Instance4.py`` / ``Instance6.py``)
   - **App URL (subdomain):** ``northstar5`` (must match instance number)
4. Click **Deploy** and wait until the app status is **Running** (often 2–5 minutes).
5. Open your **primary** app (``northstar``) → **Settings** → **Secrets**.
6. Copy the full secrets block (TOML) and paste it into **northstar5** → **Settings** → **Secrets** → **Save**.
7. Reboot **northstar5** if prompted (or wait for secrets to apply).
8. Open ``https://northstar5.streamlit.app`` and confirm:
   - Sidebar shows **Northstar instance 5**
   - Event Page lists events and shows the full checklist
   - Auto-Grader loads

### Instance 2 (if you do not have it yet)

Same as above, but:

- **Main file path:** ``Instance2.py`` (recommended — sets instance label in sidebar) or ``Home.py``
- **App URL:** ``northstar2`` (dashboard may show app name ``northstar-2``)

**Important:** Streamlit Cloud deploys ``northstar2`` from GitHub repo ``northstar-2``, not
``northstar``. A GitHub Action (``.github/workflows/sync-northstar2-mirror.yml``) mirrors
``main`` to ``northstar-2`` on every push.

**One-time setup:** In ``northstar`` repo → **Settings → Secrets → Actions**, add
``NORTHSTAR2_MIRROR_TOKEN`` — a fine-grained PAT with **Contents: Read and write** on
``northstar-2`` only (or classic ``repo`` scope). Either name works:
``northstar_mirror`` or ``NORTHSTAR2_MIRROR_TOKEN``. After the secret exists, push to ``main``
or run **Actions → Sync northstar-2 mirror → Run workflow**.

Verify in incognito: sidebar shows **Event Page** (and any configured event hub pages), not
**Trial Sign Up**.

## Before a high-traffic event

1. **Push repo changes** — ``Instance5.py``, ``Instance6.py``, etc. must be on ``main`` so Cloud can deploy them.
2. **Sheet sync** — still only **GitHub Sync → Push** once; all mirrors read the same JSON.
3. **Slide / QR codes** — assign URLs; do not send everyone to the same link.

### Four mirrors (~300 total)

| Link | Who to send |
|------|-------------|
| ``https://northstar.streamlit.app`` | ~25% of room (e.g. rows 1–5) |
| ``https://northstar2.streamlit.app`` | ~25% (e.g. rows 6–10) |
| ``https://northstar3.streamlit.app`` | ~25% (e.g. rows 11–15) |
| ``https://northstar4.streamlit.app`` | ~25% (e.g. rows 16–20) |

### Six mirrors (two workshops × ~300, or extra margin)

**Workshop A**

| Link | Who to send |
|------|-------------|
| ``https://northstar.streamlit.app`` | ~⅓ of room A |
| ``https://northstar2.streamlit.app`` | ~⅓ of room A |
| ``https://northstar5.streamlit.app`` | ~⅓ of room A |

**Workshop B**

| Link | Who to send |
|------|-------------|
| ``https://northstar3.streamlit.app`` | ~⅓ of room B |
| ``https://northstar4.streamlit.app`` | ~⅓ of room B |
| ``https://northstar6.streamlit.app`` | ~⅓ of room B |

4. Tell attendees: **“Use the link on your slide — left/right or section as shown.”**
5. **Event deep links** work on every mirror, e.g.  
   ``https://northstar5.streamlit.app/?event=Paris%20%286%2F25%2F2026%29``

## What you do *not* need to change

- Google Sheet or Apps Script
- ``events.json`` / ``workshops.json`` structure
- Separate data per mirror

## Optional secrets (usually unnecessary)

``Instance3.py`` … ``Instance6.py`` already set the instance id. You only need this if you use ``Home.py`` on a mirror URL and want a sidebar label:

```toml
NORTHSTAR_INSTANCE = "5"
```

## Checklist

- [ ] ``northstar5`` and ``northstar6`` deployed and **Running**
- [ ] Secrets copied from primary to each new app
- [ ] Smoke-tested Event Page + Auto-Grader on each URL
- [ ] All six URLs on slides (or four if not using 5–6)
- [ ] Optional: ``NORTHSTAR_GITHUB_TOKEN`` in secrets on **each** app for busy events

## Limits

- Traffic is **not** auto-balanced — you assign people to URLs.
- All mirrors share GitHub API usage for JSON refresh; token on each app helps at scale.
- Do **not** use ``LegacyAutograderRedirect.py`` for new mirrors.
