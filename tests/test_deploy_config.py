from __future__ import annotations

import json
import pathlib

from deploy_config import get_github_coords, load_deploy


def test_load_deploy_defaults_when_file_missing(tmp_path: pathlib.Path) -> None:
    d = load_deploy(root=tmp_path)
    assert d["github"]["owner"] == "sfc-gh-kenguyen"
    assert d["github"]["repo"] == "northstar"


def test_load_deploy_reads_file(tmp_path: pathlib.Path) -> None:
    payload = {"github": {"owner": "acme", "repo": "demo", "branch": "develop"}}
    (tmp_path / "deploy.json").write_text(json.dumps(payload), encoding="utf-8")
    assert get_github_coords(root=tmp_path) == ("acme", "demo", "develop")


def test_get_github_coords_incomplete_file_falls_back(tmp_path: pathlib.Path) -> None:
    (tmp_path / "deploy.json").write_text(json.dumps({"github": {"owner": "", "repo": "x"}}), encoding="utf-8")
    o, r, b = get_github_coords(root=tmp_path)
    assert (o, r, b) == ("sfc-gh-kenguyen", "northstar", "main")
