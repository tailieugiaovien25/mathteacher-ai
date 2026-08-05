from config import settings


class ConfigManager:
    """Quản lý cấu hình của hệ thống."""

    @property
    def project_name(self) -> str:
        return settings.PROJECT_NAME

    @property
    def version(self) -> str:
        return settings.VERSION

    @property
    def excel_file(self) -> str:
        return settings.EXCEL_FILE

    @property
    def report_file(self) -> str:
        return settings.REPORT_FILE

    @property
    def target_sheet(self) -> str:
        return settings.TARGET_SHEET