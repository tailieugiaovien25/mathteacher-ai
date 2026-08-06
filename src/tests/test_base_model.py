import sys

sys.path.insert(0, "src")

from models.base_model import BaseModel


def main() -> None:
    model = BaseModel(
        source_file="sample.xlsx",
        source_sheet="LuuBG",
        source_row=81,
    )

    assert not model.has_warnings()

    model.add_warning(
        "Thiếu yêu cầu cần đạt."
    )
    model.add_warning(
        "Thiếu yêu cầu cần đạt."
    )
    model.add_warning("   ")

    assert model.has_warnings()
    assert model.warnings == [
        "Thiếu yêu cầu cần đạt."
    ]

    model.set_metadata(
        "schema",
        "LuuBG",
    )

    assert model.get_metadata(
        "schema"
    ) == "LuuBG"

    assert model.get_metadata(
        "missing",
        "default",
    ) == "default"

    model_data = model.to_dict()

    assert model_data["source_file"] == "sample.xlsx"
    assert model_data["source_sheet"] == "LuuBG"
    assert model_data["source_row"] == 81
    assert model_data["metadata"]["schema"] == "LuuBG"

    model.clear_warnings()

    assert not model.has_warnings()

    print("=" * 60)
    print("M3.5-01B - BASEMODEL TEST")
    print("=" * 60)
    print("- add_warning: PASS")
    print("- duplicate warning protection: PASS")
    print("- has_warnings: PASS")
    print("- clear_warnings: PASS")
    print("- set_metadata: PASS")
    print("- get_metadata: PASS")
    print("- to_dict: PASS")
    print("\nKẾT QUẢ: 7/7 TEST PASS")


if __name__ == "__main__":
    main()