from __future__ import annotations

from mirror_help import alternate_mirror_urls


def test_alternate_mirror_urls_excludes_current() -> None:
    alts = alternate_mirror_urls("3")
    labels = [label for label, _ in alts]
    urls = [url for _, url in alts]
    assert labels == ["1", "2", "4", "5", "6"]
    assert "https://northstar3.streamlit.app" not in urls
    assert len(alts) == 5


def test_alternate_mirror_urls_all_when_unknown() -> None:
    assert len(alternate_mirror_urls(None)) == 6
