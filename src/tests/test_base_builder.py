import sys
from pathlib import Path

from openpyxl import Workbook

sys.path.insert(0, "src")

from intelligence.base_builder import BaseBuilder
from models.base_model import BaseModel


class SampleBuilder(BaseBuilder):
    """Builder tối thiểu dùng để kiểm thử BaseBuilder."""

    def build(
        self,
        *args,
        **kwargs,
    ) -> BaseModel:
        return BaseModel()


def main() -> None:
    builder = SampleBuilder()

    test_file = Path(
        "output/test_base_builder.xlsx"
    )
    test_file.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "LuuBG"
    worksheet["A1"] = "Test"
    workbook.save(test_file)
    workbook.close()

    try:
        validated_path = builder.validate_file(
            test_file
        )
        assert validated_path == test_file

        loaded_workbook = builder.open_workbook(
            test_file
        )

        try:
            loaded_sheet = builder.get_worksheet(
                loaded_workbook,
                "LuuBG",
            )
            assert loaded_sheet.title == "LuuBG"
        finally:
            loaded_workbook.close()

        assert builder.clean_text(
            "  Toán  "
        ) == "Toán"

        assert builder.clean_text(None) == ""

        assert builder.to_integer("12") == 12
        assert builder.to_integer(
            "không hợp lệ",
            None,
        ) is None

        assert builder.to_string_list(
            "Mục 1\n- Mục 2"
        ) == [
            "Mục 1",
            "Mục 2",
        ]

        assert builder.to_string_list(
            ["A", " B ", ""]
        ) == [
            "A",
            "B",
        ]

        assert builder.is_empty(None)
        assert builder.is_empty("   ")
        assert builder.is_empty([])
        assert not builder.is_empty(0)
        assert not builder.is_empty("Toán")

        try:
            builder.validate_file(
                "file_khong_ton_tai.xlsx"
            )
        except FileNotFoundError:
            pass
        else:
            raise AssertionError(
                "Phải phát sinh FileNotFoundError."
            )

        try:
            invalid_workbook = builder.open_workbook(
                test_file
            )

            try:
                builder.get_worksheet(
                    invalid_workbook,
                    "KhongTonTai",
                )
            finally:
                invalid_workbook.close()
        except ValueError:
            pass
        else:
            raise AssertionError(
                "Phải phát sinh ValueError."
            )

        print("=" * 60)
        print("M4-01B - BASEBUILDER TEST")
        print("=" * 60)
        print("- validate_file: PASS")
        print("- open_workbook: PASS")
        print("- get_worksheet: PASS")
        print("- clean_text: PASS")
        print("- to_integer: PASS")
        print("- to_string_list: PASS")
        print("- is_empty: PASS")
        print("- missing file exception: PASS")
        print("- missing worksheet exception: PASS")
        print("\nKẾT QUẢ: 9/9 TEST PASS")

    finally:
        if test_file.exists():
            test_file.unlink()


if __name__ == "__main__":
    main()