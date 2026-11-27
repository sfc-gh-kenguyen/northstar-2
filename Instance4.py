"""Streamlit Community Cloud main file — Northstar traffic mirror **instance 4**.

Create a **new** app at share.streamlit.io from this repo, set **Main file path** to
``Instance4.py``, and give the app a unique subdomain (e.g. ``northstar-4``).
See ``docs/TRAFFIC_SPLITTING.md``.
"""

from __future__ import annotations

import os

os.environ.setdefault("NORTHSTAR_INSTANCE", "4")

from northstar_run import run_app

run_app()
