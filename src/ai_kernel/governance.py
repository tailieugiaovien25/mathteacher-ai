from __future__ import annotations

from dataclasses import dataclass

from .contracts import AIActionClass, AIOwnership, AIKernelRequest


class AdminPolicyError(PermissionError):
    """Raised when an AI operation violates ADMIN ownership policy."""


@dataclass(frozen=True)
class AIKernelGovernance:
    """Immutable runtime guard; mutable policy remains ADMIN-owned configuration."""

    require_admin_for_configuration: bool = True
    allow_user_to_switch_model: bool = False
    allow_user_to_switch_provider: bool = False
    allow_ai_self_modification: bool = False
    allow_user_mutation: bool = False

    def authorize_configuration(self, owner: AIOwnership) -> None:
        if self.require_admin_for_configuration and owner is not AIOwnership.ADMIN:
            raise AdminPolicyError("Chỉ ADMIN được cấu hình AI Kernel.")

    def authorize_request(self, request: AIKernelRequest) -> None:
        if request.owner is AIOwnership.SYSTEM:
            return
        if request.action in {AIActionClass.MUTATING, AIActionClass.GOVERNANCE}:
            if request.owner is not AIOwnership.ADMIN:
                raise AdminPolicyError("Chỉ ADMIN mới được yêu cầu AI thực hiện tác vụ thay đổi hệ thống.")
        if request.owner is AIOwnership.USER and request.metadata.get("mutating", "false").lower() == "true":
            if not self.allow_user_mutation:
                raise AdminPolicyError("AI chức năng không được tự thực hiện thao tác thay đổi dữ liệu/hệ thống.")

    def authorize_model_switch(self, owner: AIOwnership) -> None:
        if not self.allow_user_to_switch_model:
            self.authorize_configuration(owner)

    def authorize_provider_switch(self, owner: AIOwnership) -> None:
        if not self.allow_user_to_switch_provider:
            self.authorize_configuration(owner)

    def authorize_self_modification(self, owner: AIOwnership = AIOwnership.SYSTEM) -> None:
        del owner
        if not self.allow_ai_self_modification:
            raise AdminPolicyError("AI Kernel không được tự sửa code lõi hoặc tự thay đổi governance.")
