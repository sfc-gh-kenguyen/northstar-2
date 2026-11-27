from __future__ import annotations

from workshops import resolve_workshop_option, workshop_has_answer_key


def test_resolve_workshop_option_exact() -> None:
    options = ["None (auto-grader setup only)", "CoCo Foundations: Getting Started with CoCo"]
    assert resolve_workshop_option("CoCo Foundations: Getting Started with CoCo", options) == (
        "CoCo Foundations: Getting Started with CoCo"
    )


def test_resolve_workshop_option_case_insensitive() -> None:
    options = ["CoCo Foundations: Getting Started with CoCo"]
    assert resolve_workshop_option("coco foundations: getting started with coco", options) == (
        "CoCo Foundations: Getting Started with CoCo"
    )


def test_resolve_workshop_option_unknown() -> None:
    assert resolve_workshop_option("Unknown Lab", ["Lab A"]) is None


def test_workshop_has_answer_key_prerequisite() -> None:
    assert workshop_has_answer_key("Get Started with Snowflake CoCo Desktop") is False


def test_workshop_has_answer_key_lab() -> None:
    assert workshop_has_answer_key("CoCo Foundations: Getting Started with CoCo") is True
