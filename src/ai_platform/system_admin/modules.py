from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SystemAdminModule:
    module_id: str
    label: str
    mode: str
    description: str


SYSTEM_ADMIN_MODULES = (
    SystemAdminModule("system_monitor", "System Monitor", "read_only", "Theo dõi trạng thái runtime, tài nguyên và health checks."),
    SystemAdminModule("log_analyst", "Log Analyst", "read_only", "Phân tích log, gom nhóm lỗi và chỉ ra bằng chứng liên quan."),
    SystemAdminModule("database_assistant", "Database Assistant", "read_only", "Kiểm tra schema/trạng thái dữ liệu; không tự ghi production."),
    SystemAdminModule("security_assistant", "Security Assistant", "read_only", "Kiểm tra cấu hình bảo mật và các dấu hiệu cần rà soát."),
    SystemAdminModule("backup_recovery", "Backup & Recovery", "human_approved", "Kiểm tra backup/recovery readiness; thao tác khôi phục cần người duyệt."),
    SystemAdminModule("deployment_assistant", "Deployment Assistant", "human_approved", "Kiểm tra release/deploy readiness; không tự deploy."),
    SystemAdminModule("support_agent", "Support Agent", "human_approved", "Soạn phản hồi hỗ trợ dựa trên bằng chứng; không tự thay đổi tài khoản."),
)


def system_admin_modules() -> tuple[SystemAdminModule, ...]:
    return SYSTEM_ADMIN_MODULES
