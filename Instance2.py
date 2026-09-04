"""Streamlit Community Cloud main file — Northstar traffic mirror **instance 2**.

Create or point the **northstar-2** app at share.streamlit.io to this file
(subdomain ``northstar2`` → ``https://northstar2.streamlit.app``).
See ``docs/TRAFFIC_SPLITTING.md``.
"""

from __future__ import annotations

import os

os.environ.setdefault("NORTHSTAR_INSTANCE", "2")

from northstar_run import run_app

run_app()
