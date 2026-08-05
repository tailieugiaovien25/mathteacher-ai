from robots.robot01 import Robot01


EXCEL_FILE = "data/input/LBG-TUYEN_chuan_VBA_macro.xlsm"
REPORT_FILE = "output/reports/workbook_report.json"


def main() -> None:
    robot = Robot01(
        excel_file=EXCEL_FILE,
        report_file=REPORT_FILE,
        target_sheet="LuuBG",
    )

    robot.execute()


if __name__ == "__main__":
    main()