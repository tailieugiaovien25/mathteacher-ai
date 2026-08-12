from enum import Enum


class ProviderStatus(str, Enum):
    """
    Runtime / lifecycle status của AI Provider.

    Trạng thái này được dùng bởi Multi-AI subsystem
    để routing, governance và failure handling.

    ProviderStatus không chứa business logic.
    """

    REGISTERED = "REGISTERED"
    SANDBOX = "SANDBOX"
    EVALUATED = "EVALUATED"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    DEGRADED = "DEGRADED"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"