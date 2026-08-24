from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from educational_planning_v2.models.operational_data_source import (
    OperationalDataSource,
    OperationalDataStatus,
    OperationalDataType,
)
from educational_planning_v2.models.teacher_operational_data_workspace import (
    TeacherOperationalDataWorkspace,
)


class TeacherDataWorkspaceItemState(str, Enum):
    READY = "READY"
    MISSING = "MISSING"


@dataclass(frozen=True)
class TeacherDataWorkspaceItemView:
    data_type: OperationalDataType
    label: str
    state: TeacherDataWorkspaceItemState
    source_id: str | None
    source_name: str | None
    source_version: str | None
    status: OperationalDataStatus | None

    def __post_init__(self) -> None:
        if not isinstance(
            self.data_type,
            OperationalDataType,
        ):
            raise TypeError(
                "data_type must be OperationalDataType"
            )

        if not isinstance(
            self.state,
            TeacherDataWorkspaceItemState,
        ):
            raise TypeError(
                "state must be TeacherDataWorkspaceItemState"
            )

        if not isinstance(
            self.label,
            str,
        ):
            raise TypeError(
                "label must be str"
            )

        normalized_label = self.label.strip()

        if not normalized_label:
            raise ValueError(
                "label must not be empty"
            )

        object.__setattr__(
            self,
            "label",
            normalized_label,
        )

        if self.state is TeacherDataWorkspaceItemState.MISSING:
            if any(
                value is not None
                for value in (
                    self.source_id,
                    self.source_name,
                    self.source_version,
                    self.status,
                )
            ):
                raise ValueError(
                    "missing item must not expose source metadata"
                )

        if self.state is TeacherDataWorkspaceItemState.READY:
            if self.source_id is None:
                raise ValueError(
                    "ready item requires source_id"
                )

            if self.status is not OperationalDataStatus.ACTIVE:
                raise ValueError(
                    "ready item requires ACTIVE source"
                )

    @classmethod
    def from_source(
        cls,
        *,
        data_type: OperationalDataType,
        label: str,
        source: OperationalDataSource | None,
    ) -> "TeacherDataWorkspaceItemView":
        if not isinstance(
            data_type,
            OperationalDataType,
        ):
            raise TypeError(
                "data_type must be OperationalDataType"
            )

        if source is None:
            return cls(
                data_type=data_type,
                label=label,
                state=TeacherDataWorkspaceItemState.MISSING,
                source_id=None,
                source_name=None,
                source_version=None,
                status=None,
            )

        if not isinstance(
            source,
            OperationalDataSource,
        ):
            raise TypeError(
                "source must be OperationalDataSource or None"
            )

        if source.data_type is not data_type:
            raise ValueError(
                "source data type does not match item data type"
            )

        return cls(
            data_type=data_type,
            label=label,
            state=TeacherDataWorkspaceItemState.READY,
            source_id=source.source_id,
            source_name=source.source_name,
            source_version=source.source_version,
            status=source.status,
        )


@dataclass(frozen=True)
class TeacherDataWorkspaceViewModel:
    owner_id: str
    academic_year: str
    items: tuple[TeacherDataWorkspaceItemView, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "owner_id",
            "academic_year",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(
                value,
                str,
            ):
                raise TypeError(
                    f"{field_name} must be str"
                )

            normalized = value.strip()

            if not normalized:
                raise ValueError(
                    f"{field_name} must not be empty"
                )

            object.__setattr__(
                self,
                field_name,
                normalized,
            )

        if not isinstance(
            self.items,
            tuple,
        ):
            raise TypeError(
                "items must be tuple"
            )

        if not all(
            isinstance(
                item,
                TeacherDataWorkspaceItemView,
            )
            for item in self.items
        ):
            raise TypeError(
                "items contain invalid value"
            )

    def item_for(
        self,
        data_type: OperationalDataType,
    ) -> TeacherDataWorkspaceItemView:
        if not isinstance(
            data_type,
            OperationalDataType,
        ):
            raise TypeError(
                "data_type must be OperationalDataType"
            )

        for item in self.items:
            if item.data_type is data_type:
                return item

        raise ValueError(
            "data type is not represented in workspace view"
        )


class TeacherDataWorkspacePresenter:
    def present(
        self,
        *,
        workspace: TeacherOperationalDataWorkspace,
    ) -> TeacherDataWorkspaceViewModel:
        if not isinstance(
            workspace,
            TeacherOperationalDataWorkspace,
        ):
            raise TypeError(
                "workspace must be TeacherOperationalDataWorkspace"
            )

        items = (
            TeacherDataWorkspaceItemView.from_source(
                data_type=OperationalDataType.PPCT,
                label="PPCT",
                source=workspace.ppct_source,
            ),
            TeacherDataWorkspaceItemView.from_source(
                data_type=OperationalDataType.TIMETABLE,
                label="Th\u1eddi kh\u00f3a bi\u1ec3u",
                source=workspace.timetable_source,
            ),
            TeacherDataWorkspaceItemView.from_source(
                data_type=OperationalDataType.ACADEMIC_WEEK,
                label="Tu\u1ea7n h\u1ecdc",
                source=workspace.academic_week_source,
            ),
        )

        return TeacherDataWorkspaceViewModel(
            owner_id=workspace.owner_id,
            academic_year=workspace.academic_year,
            items=items,
        )
