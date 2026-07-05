from pathlib import Path

import pytest

from lesson18_practice_pytest import (
    build_report,
    load_report,
    normalize_tags,
    require_order_id,
    save_report,
)


def test_normalize_tags() -> None:
    assert normalize_tags([" Python ", "AI", "python", "", " FastAPI "]) == [
        "python",
        "ai",
        "fastapi",
    ]


def test_require_order_id_success() -> None:
    text = "用户咨询订单 ORD-20260705-001 的退款问题"

    assert require_order_id(text) == "ORD-20260705-001"


def test_require_order_id_error() -> None:
    with pytest.raises(ValueError):
        require_order_id("用户没有提供订单号")


def test_build_report() -> None:
    report = build_report(
        user_name=" Panpan ",
        tags=[" Python ", "AI", "python"],
        order_id="ORD-20260705-001",
    )

    assert report == {
        "user_name": "Panpan",
        "tags": ["python", "ai"],
        "order_id": "ORD-20260705-001",
    }


def test_build_report_requires_user_name() -> None:
    with pytest.raises(ValueError):
        build_report("", ["python"], "ORD-20260705-001")


def test_save_and_load_report(tmp_path: Path) -> None:
    report_file = tmp_path / "reports" / "report.json"
    report = {
        "user_name": "Panpan",
        "tags": ["python", "pytest"],
        "order_id": "ORD-20260705-001",
    }

    save_report(report_file, report)
    loaded_report = load_report(report_file)

    assert report_file.exists()
    assert loaded_report == report
