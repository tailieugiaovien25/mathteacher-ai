from dataclasses import dataclass


@dataclass(frozen=True)
class TeacherPlanEnrichment:
    """Teacher-product enrichment defaults.

    These values belong to the teacher product layer and do not modify
    curriculum, YCCD, PPCT, or educational-planning domain authority.
    """

    default_teaching_location: str | None = None
    default_teaching_equipment: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        location = self.default_teaching_location

        if location is not None:
            if not isinstance(location, str):
                raise TypeError(
                    "default_teaching_location must be a string or None"
                )

            location = location.strip()

            if not location:
                raise ValueError(
                    "default_teaching_location must not be empty"
                )

            object.__setattr__(
                self,
                "default_teaching_location",
                location,
            )

        equipment = self.default_teaching_equipment

        if not isinstance(equipment, tuple):
            raise TypeError(
                "default_teaching_equipment must be a tuple"
            )

        normalized = []

        for item in equipment:
            if not isinstance(item, str):
                raise TypeError(
                    "each teaching equipment item must be a string"
                )

            item = item.strip()

            if not item:
                raise ValueError(
                    "teaching equipment item must not be empty"
                )

            normalized.append(item)

        object.__setattr__(
            self,
            "default_teaching_equipment",
            tuple(normalized),
        )
