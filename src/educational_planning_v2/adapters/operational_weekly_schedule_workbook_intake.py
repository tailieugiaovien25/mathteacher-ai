from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from zipfile import BadZipFile

from educational_planning_v2.adapters.weekly_schedule_excel_adapter import (
    WeeklyScheduleExcelAdapter,
    WeeklyScheduleSourceData,
    WeeklyScheduleWorkbookError,
    WeeklyScheduleWorkbookSchema,
)
from educational_planning_v2.models.operational_data_io import (
    OperationalInputLocation,
)
from educational_planning_v2.services.operational_input_selection_service import (
    OperationalInputSelection,
)


@dataclass(frozen=True)
class WeeklyScheduleWorkbookIntakeResult:
    selection: OperationalInputSelection
    source_data: WeeklyScheduleSourceData

    def __post_init__(self) -> None:
        if not isinstance(
            self.selection,
            OperationalInputSelection,
        ):
            raise TypeError(
                "selection must be OperationalInputSelection"
            )

        if not isinstance(
            self.source_data,
            WeeklyScheduleSourceData,
        ):
            raise TypeError(
                "source_data must be WeeklyScheduleSourceData"
            )


class WeeklyScheduleWorkbookIntakeAdapter:
    """
    Application-facing adapter for LOCAL_UPLOAD weekly-schedule
    workbooks.

    The workbook is a transport container only. Its contents are
    delegated to WeeklyScheduleExcelAdapter, which emits canonical
    weekly-schedule source domain objects.
    """

    def __init__(
        self,
        schema: WeeklyScheduleWorkbookSchema | None = None,
    ) -> None:
        if (
            schema is not None
            and not isinstance(
                schema,
                WeeklyScheduleWorkbookSchema,
            )
        ):
            raise TypeError(
                "schema must be WeeklyScheduleWorkbookSchema or None"
            )

        self._schema = schema

    def load(
        self,
        *,
        selection: OperationalInputSelection,
        workbook_bytes: bytes,
    ) -> WeeklyScheduleWorkbookIntakeResult:
        if not isinstance(
            selection,
            OperationalInputSelection,
        ):
            raise TypeError(
                "selection must be OperationalInputSelection"
            )

        if (
            selection.reference.location
            is not OperationalInputLocation.LOCAL_UPLOAD
        ):
            raise ValueError(
                "workbook intake requires LOCAL_UPLOAD selection"
            )

        if not isinstance(
            workbook_bytes,
            bytes,
        ):
            raise TypeError(
                "workbook_bytes must be bytes"
            )

        if not workbook_bytes:
            raise ValueError(
                "workbook_bytes must not be empty"
            )

        adapter = WeeklyScheduleExcelAdapter(
            self._schema
        )

        try:
            source_data = adapter.load(
                BytesIO(workbook_bytes)
            )
        except BadZipFile as exc:
            raise WeeklyScheduleWorkbookError(
                "tep Excel khong hop le"
            ) from exc

        return WeeklyScheduleWorkbookIntakeResult(
            selection=selection,
            source_data=source_data,
        )
