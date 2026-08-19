from __future__ import annotations

import re

from dataclasses import dataclass
from datetime import date
from enum import Enum


class AcademicYearStatus(
    str,
    Enum,
):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


def normalize_academic_year(
    value: str,
) -> str:
    if not isinstance(
        value,
        str,
    ):
        raise TypeError(
            "academic_year must be str"
        )

    normalized = (
        value.strip()
        .replace("\u2013", "-")
        .replace("\u2014", "-")
    )

    normalized = re.sub(
        r"\s*-\s*",
        "-",
        normalized,
    )

    match = re.fullmatch(
        r"(\d{4})-(\d{4})",
        normalized,
    )

    if match is None:
        raise ValueError(
            "academic_year must use "
            "YYYY-YYYY format"
        )

    start_year = int(
        match.group(1)
    )

    end_year = int(
        match.group(2)
    )

    if end_year != start_year + 1:
        raise ValueError(
            "academic_year end year must "
            "equal start year + 1"
        )

    return (
        f"{start_year:04d}-"
        f"{end_year:04d}"
    )


@dataclass(frozen=True)
class AcademicYearConfiguration:
    academic_year_id: str
    academic_year: str
    start_date: date
    end_date: date
    opening_ceremony_date: date
    semester_1_start: date
    semester_1_end: date
    semester_2_start: date
    semester_2_end: date
    status: AcademicYearStatus = (
        AcademicYearStatus.DRAFT
    )
    is_current: bool = False

    def __post_init__(self) -> None:
        if not isinstance(
            self.academic_year_id,
            str,
        ):
            raise TypeError(
                "academic_year_id must be str"
            )

        academic_year_id = (
            self.academic_year_id.strip()
        )

        if not academic_year_id:
            raise ValueError(
                "academic_year_id must not be empty"
            )

        object.__setattr__(
            self,
            "academic_year_id",
            academic_year_id,
        )

        object.__setattr__(
            self,
            "academic_year",
            normalize_academic_year(
                self.academic_year
            ),
        )

        for field_name in (
            "start_date",
            "end_date",
            "opening_ceremony_date",
            "semester_1_start",
            "semester_1_end",
            "semester_2_start",
            "semester_2_end",
        ):
            if not isinstance(
                getattr(
                    self,
                    field_name,
                ),
                date,
            ):
                raise TypeError(
                    f"{field_name} must be date"
                )

        if self.start_date > self.end_date:
            raise ValueError(
                "start_date must not be "
                "after end_date"
            )

        if not (
            self.start_date
            <= self.opening_ceremony_date
            <= self.end_date
        ):
            raise ValueError(
                "opening_ceremony_date must "
                "be inside academic year"
            )

        if (
            self.semester_1_start
            > self.semester_1_end
        ):
            raise ValueError(
                "semester_1_start must not be "
                "after semester_1_end"
            )

        if (
            self.semester_2_start
            > self.semester_2_end
        ):
            raise ValueError(
                "semester_2_start must not be "
                "after semester_2_end"
            )

        if (
            self.semester_1_start
            < self.start_date
            or self.semester_2_end
            > self.end_date
        ):
            raise ValueError(
                "semester dates must be "
                "inside academic year"
            )

        if (
            self.semester_1_end
            >= self.semester_2_start
        ):
            raise ValueError(
                "semester 1 must end before "
                "semester 2 starts"
            )

        if not isinstance(
            self.status,
            AcademicYearStatus,
        ):
            raise TypeError(
                "status must be "
                "AcademicYearStatus"
            )

        if not isinstance(
            self.is_current,
            bool,
        ):
            raise TypeError(
                "is_current must be bool"
            )

        if (
            self.is_current
            and self.status
            is not AcademicYearStatus.ACTIVE
        ):
            raise ValueError(
                "current academic year "
                "must be ACTIVE"
            )
