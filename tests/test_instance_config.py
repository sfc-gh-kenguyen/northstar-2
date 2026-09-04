from __future__ import annotations

import pytest

from instance_config import get_instance_label, instance_page_title_suffix


def test_get_instance_label_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NORTHSTAR_INSTANCE", "4")
    assert get_instance_label() == "4"


def test_instance_page_title_suffix() -> None:
    import instance_config

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setenv("NORTHSTAR_INSTANCE", "3")
    monkeypatch.setattr(instance_config, "_from_streamlit_secrets", lambda: None)
    monkeypatch.setattr(instance_config, "_from_request_host", lambda: None)
    try:
        assert instance_page_title_suffix() == " (3)"
        monkeypatch.setenv("NORTHSTAR_INSTANCE", "1")
        assert instance_page_title_suffix() == ""
    finally:
        monkeypatch.undo()
