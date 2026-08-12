from dataclasses import dataclass
from enum import Enum

from .lifecycle import LifecycleStatus


class UpdatePolicy(str, Enum):
    SIMPLE = "SIMPLE"
    CONTROLLED = "CONTROLLED"
    VERSIONED = "VERSIONED"


class RetentionPolicy(str, Enum):
    ACTIVE_ONLY = "ACTIVE_ONLY"
    ACTIVE_FIRST = "ACTIVE_FIRST"
    KEEP_HISTORY = "KEEP_HISTORY"


@dataclass(frozen=True)
class GovernancePolicy:
    update_policy: UpdatePolicy
    retention_policy: RetentionPolicy

    publish_required: bool = False
    allow_overwrite_before_publish: bool = True
    allow_hard_delete: bool = False

    def can_hard_delete(
        self,
        *,
        status: LifecycleStatus,
        is_referenced: bool,
    ) -> bool:

        if not self.allow_hard_delete:
            return False

        if is_referenced:
            return False

        return status in {
            LifecycleStatus.DRAFT,
            LifecycleStatus.INACTIVE,
            LifecycleStatus.ARCHIVED,
        }

    def should_use_in_engine(
        self,
        status: LifecycleStatus,
    ) -> bool:

        if self.retention_policy == RetentionPolicy.ACTIVE_ONLY:
            return status == LifecycleStatus.ACTIVE

        if self.retention_policy == RetentionPolicy.ACTIVE_FIRST:
            return status == LifecycleStatus.ACTIVE

        if self.retention_policy == RetentionPolicy.KEEP_HISTORY:
            return status in {
                LifecycleStatus.ACTIVE,
                LifecycleStatus.ARCHIVED,
            }

        return False