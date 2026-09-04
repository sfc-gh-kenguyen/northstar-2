from __future__ import annotations

import json
import pathlib

import pytest

from lab_resources import (
    find_lab_resource_bundle,
    is_sql_lab_file,
    load_lab_resource_bundles,
    mime_type_for_filename,
    read_lab_file_bytes,
    read_lab_file_text,
)


def test_load_lab_resource_bundles() -> None:
    bundles = load_lab_resource_bundles()
    assert len(bundles) >= 4
    assert any("CoCo Foundations" in b.get("workshop_match", "") for b in bundles)
    assert any("Dynamic Tables" in b.get("workshop_match", "") for b in bundles)


def test_find_lab_resource_bundle_dynamic_tables() -> None:
    bundle = find_lab_resource_bundle(
        "Creating Declarative Data Pipelines with Dynamic Tables"
    )
    assert bundle is not None
    assert bundle["title"] == "Dynamic Tables lab files"


def test_find_lab_resource_bundle_cortex_rag() -> None:
    bundle = find_lab_resource_bundle(
        "Building AI Applications with Snowflake Cortex: RAG, Text-to-SQL & CoCo"
    )
    assert bundle is not None
    assert "RAG" in bundle["title"]


def test_read_lab_file_text() -> None:
    text = read_lab_file_text("lab_assets/dynamic-tables/setup.sql")
    assert "compute_wh" in text.lower()


def test_is_sql_lab_file() -> None:
    assert is_sql_lab_file("setup.sql") is True
    assert is_sql_lab_file("notes.csv") is False


def test_find_lab_resource_bundle_case_insensitive() -> None:
    bundle = find_lab_resource_bundle("coco foundations: getting started with coco")
    assert bundle is not None
    assert bundle["title"] == "CoCo Foundations lab files"


def test_find_lab_resource_bundle_unknown() -> None:
    assert find_lab_resource_bundle("Unknown Workshop") is None


def test_read_lab_file_bytes_rejects_path_traversal(tmp_path: pathlib.Path) -> None:
    manifest = {
        "bundles": [
            {
                "workshop_match": "Demo",
                "groups": [{"files": [{"name": "x.txt", "path": "../outside.txt"}]}],
            }
        ]
    }
    (tmp_path / "lab_resources.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="escapes project root"):
        read_lab_file_bytes("../outside.txt", root=tmp_path)


def test_read_lab_file_bytes_reads_bundled_asset() -> None:
    data = read_lab_file_bytes("lab_assets/from-zero-to-agents/setup.sql")
    assert b"snowflake_intelligence_admin" in data.lower()
    assert len(data) > 100


def test_mime_type_for_filename() -> None:
    assert mime_type_for_filename("setup.sql") == "text/sql"
    assert mime_type_for_filename("marketing_data.csv") == "text/csv"
