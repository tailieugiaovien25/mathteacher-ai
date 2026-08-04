from excel_engine.excel_reader import ExcelReader


EXCEL_FILE = "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"


def main() -> None:
    print("=" * 60)
    print("AI Teacher Platform")
    print("Robot 01 - Excel Reader")
    print("Version: 0.1.1")
    print("=" * 60)

    reader = ExcelReader()
    workbook_info = reader.read_workbook(EXCEL_FILE)

    print(f"\nWorkbook: {workbook_info['file_name']}")
    print(f"Số worksheet: {workbook_info['sheet_count']}")

    print("\nCấu trúc worksheet:")

    for index, worksheet in enumerate(
        workbook_info["worksheets"],
        start=1,
    ):
        print(
            f"{index:>2}. {worksheet['name']} "
            f"- Rows: {worksheet['row_count']} "
            f"- Columns: {worksheet['column_count']}"
        )

    used_range = reader.get_used_range(
        EXCEL_FILE,
        "LuuBG",
    )

    print("\nVùng dữ liệu thật của LuuBG:")
    print(f"Dòng cuối có dữ liệu: {used_range['last_data_row']}")
    print(f"Số cột hiện có: {used_range['column_count']}")

if __name__ == "__main__":
    main()