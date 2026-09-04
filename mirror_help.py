"""Alternate mirror URLs and slow-load guidance for traffic splitting."""

from __future__ import annotations

import json

import streamlit.components.v1 as components

# Canonical Community Cloud mirrors (see docs/TRAFFIC_SPLITTING.md).
MIRROR_URLS: tuple[tuple[str, str], ...] = (
    ("1", "https://northstar.streamlit.app"),
    ("2", "https://northstar2.streamlit.app"),
    ("3", "https://northstar3.streamlit.app"),
    ("4", "https://northstar4.streamlit.app"),
    ("5", "https://northstar5.streamlit.app"),
    ("6", "https://northstar6.streamlit.app"),
)

SLOW_LOAD_DELAY_MS = 7000


def alternate_mirror_urls(current_label: str | None) -> list[tuple[str, str]]:
    """Return (label, url) pairs for mirrors other than ``current_label``."""
    if current_label:
        return [(label, url) for label, url in MIRROR_URLS if label != current_label]
    return list(MIRROR_URLS)


def render_slow_load_mirror_help(
    *,
    current_label: str | None = None,
    delay_ms: int | None = None,
    test_mode: bool = False,
) -> None:
    """If the app is still loading after ~7s, suggest other mirror URLs.

    Runs in the browser (injected into the parent frame). The timer uses elapsed
    time since the browser opened the page (not since this script runs), because
    Streamlit only renders the component after the first Python pass completes.

    Pass ``test_mode=True`` (or ``?mirror_help_test=1`` in the URL) to force the
    banner after 1.5s so you can verify deploy without simulating overload.
    """
    alternates = alternate_mirror_urls(current_label)
    if not alternates:
        return

    alternates_json = json.dumps([url for _, url in alternates])
    if delay_ms is None:
        delay_ms = 1500 if test_mode else SLOW_LOAD_DELAY_MS
    test_mode_js = "true" if test_mode else "false"
    banner_inner_html = json.dumps(
        "<strong>Taking a while to load?</strong>"
        "This link may be busy. Try another Northstar mirror "
        "(same app, your event link is preserved):"
        '<ul id="northstar-slow-load-links"></ul>'
        "<small>Wait once or refresh before switching. "
        "If one mirror is slow, the others are often faster.</small>"
        '<button type="button" id="northstar-slow-load-dismiss">Dismiss</button>'
    )

    components.html(
        f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    #northstar-slow-load-banner {{
      box-sizing: border-box;
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      z-index: 999999;
      padding: 0.85rem 1.25rem;
      background: #fff4e5;
      border-bottom: 2px solid #f5a623;
      color: #1a1a1a;
      font-family: "Source Sans Pro", -apple-system, BlinkMacSystemFont, sans-serif;
      font-size: 0.95rem;
      line-height: 1.45;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.12);
    }}
    #northstar-slow-load-banner.visible {{
      display: block;
    }}
    #northstar-slow-load-banner strong {{
      display: block;
      margin-bottom: 0.35rem;
      font-size: 1rem;
    }}
    #northstar-slow-load-banner ul {{
      margin: 0.35rem 0 0.5rem 1.1rem;
      padding: 0;
    }}
    #northstar-slow-load-banner li {{
      margin: 0.15rem 0;
    }}
    #northstar-slow-load-banner a {{
      color: #0066cc;
      word-break: break-all;
    }}
    #northstar-slow-load-dismiss {{
      margin-top: 0.35rem;
      padding: 0.35rem 0.75rem;
      border: 1px solid #ccc;
      border-radius: 0.35rem;
      background: #fff;
      cursor: pointer;
      font-size: 0.85rem;
    }}
  </style>
</head>
<body>
<script>
(function () {{
  const parentDoc = window.parent.document;
  const alternates = {alternates_json};
  const delayMs = {delay_ms};
  const testMode = {test_mode_js};
  const perf = window.parent.performance || window.performance;
  const elapsedMs = function () {{
    return perf.now ? perf.now() : 0;
  }};

  if (parentDoc.getElementById("northstar-slow-load-banner")) {{
    return;
  }}

  const banner = parentDoc.createElement("div");
  banner.id = "northstar-slow-load-banner";
  banner.innerHTML = {banner_inner_html};
  parentDoc.body.appendChild(banner);

  const list = parentDoc.getElementById("northstar-slow-load-links");
  const qs = window.parent.location.search || "";
  alternates.forEach(function (base) {{
    const li = parentDoc.createElement("li");
    const a = parentDoc.createElement("a");
    a.href = base + qs;
    a.target = "_top";
    a.rel = "noopener noreferrer";
    a.textContent = base + qs;
    li.appendChild(a);
    list.appendChild(li);
  }});

  parentDoc.getElementById("northstar-slow-load-dismiss").addEventListener("click", function () {{
    banner.classList.remove("visible");
  }});

  function appLooksReady() {{
    const main = parentDoc.querySelector('[data-testid="stMainBlockContainer"]');
    if (!main) return false;
    const text = (main.innerText || "").trim();
    if (text.length < 20) return false;
    return (
      text.indexOf("Snowflake Northstar") >= 0 ||
      text.indexOf("Event Page") >= 0 ||
      text.indexOf("Select your event") >= 0 ||
      text.indexOf("Auto-Grader") >= 0
    );
  }}

  function hideBanner() {{
    banner.classList.remove("visible");
  }}

  function showBannerIfNeeded() {{
    if (testMode || !appLooksReady()) {{
      banner.classList.add("visible");
    }}
  }}

  let shown = false;
  function maybeShowAfterDelay() {{
    if (testMode || !appLooksReady()) {{
      showBannerIfNeeded();
      shown = true;
    }}
  }}

  const alreadySlow = elapsedMs() >= delayMs;
  let timer = null;
  if (alreadySlow) {{
    maybeShowAfterDelay();
  }} else {{
    timer = window.setTimeout(maybeShowAfterDelay, delayMs - elapsedMs());
  }}

  const observer = new MutationObserver(function () {{
    if (!testMode && appLooksReady()) {{
      hideBanner();
      if (timer) window.clearTimeout(timer);
      observer.disconnect();
    }} else if (shown) {{
      showBannerIfNeeded();
    }}
  }});

  observer.observe(parentDoc.body, {{ childList: true, subtree: true }});

  window.setInterval(function () {{
    if (!testMode && appLooksReady()) {{
      hideBanner();
      if (timer) window.clearTimeout(timer);
      observer.disconnect();
    }}
  }}, 500);
}})();
</script>
</body>
</html>
        """.strip(),
        height=0,
        scrolling=False,
    )
