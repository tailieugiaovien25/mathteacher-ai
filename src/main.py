from config.config_manager import ConfigManager
from robots.robot01 import Robot01


def main() -> None:
    config = ConfigManager()

    robot = Robot01(
        excel_file=config.excel_file,
        report_file=config.report_file,
        target_sheet=config.target_sheet,
    )

    robot.execute()


if __name__ == "__main__":
    main()