import json
from pathlib import Path


SOURCE_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "sources"
    / "SRC-CUR-MATH-2018.json"
)


def load_source() -> dict:
    with SOURCE_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def test_source_file_exists():
    assert SOURCE_FILE.exists()


def test_source_identity():
    source = load_source()

    assert source["source_id"] == "SRC-CUR-MATH-2018"
    assert source["source_type"] == "OFFICIAL_CURRICULUM"


def test_source_legal_basis():
    source = load_source()

    assert source["legal_authority"]["organization"] == (
        "Bộ Giáo dục và Đào tạo"
    )
    assert source["legal_basis"]["regulation_id"] == (
        "32/2018/TT-BGDĐT"
    )
    assert source["legal_basis"]["issued_date"] == "2018-12-26"


def test_source_scope_is_lower_secondary_math():
    source = load_source()

    assert source["scope"]["subject"] == "MATHEMATICS"
    assert source["scope"]["target_grades"] == [6, 7, 8, 9]


def test_source_is_authoritative():
    source = load_source()

    verification = source["verification"]

    assert verification["authority_verified"] is True
    assert verification["regulation_verified"] is True
    assert verification["source_status"] == "AUTHORITATIVE"