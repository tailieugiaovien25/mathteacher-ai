from .mapping import (
    Mapping,
    MappingStatus,
)


class MappingRegistry:

    def __init__(self) -> None:
        self._mappings: dict[str, Mapping] = {}

    def register(
        self,
        mapping: Mapping,
    ) -> None:

        mapping_id = mapping.mapping_id.strip()

        if not mapping_id:
            raise ValueError(
                "mapping_id không được để trống."
            )

        if mapping_id in self._mappings:
            raise ValueError(
                f"Mapping đã tồn tại: {mapping_id}"
            )

        if not mapping.source_data_type.strip():
            raise ValueError(
                "source_data_type không được để trống."
            )

        if not mapping.source_id.strip():
            raise ValueError(
                "source_id không được để trống."
            )

        if not mapping.target_data_type.strip():
            raise ValueError(
                "target_data_type không được để trống."
            )

        if not mapping.target_id.strip():
            raise ValueError(
                "target_id không được để trống."
            )

        self._mappings[mapping_id] = mapping

    def get(
        self,
        mapping_id: str,
    ) -> Mapping:

        try:
            return self._mappings[mapping_id]

        except KeyError as exc:
            raise KeyError(
                f"Không tìm thấy Mapping: "
                f"{mapping_id}"
            ) from exc

    def all(
        self,
    ) -> tuple[Mapping, ...]:

        return tuple(
            self._mappings.values()
        )

    def find_from(
        self,
        *,
        source_data_type: str,
        source_id: str,
        mapping_type: str | None = None,
    ) -> tuple[Mapping, ...]:

        matches = []

        for mapping in self._mappings.values():

            if (
                mapping.status
                != MappingStatus.ACTIVE
            ):
                continue

            if (
                mapping.source_data_type
                != source_data_type
            ):
                continue

            if mapping.source_id != source_id:
                continue

            if (
                mapping_type is not None
                and mapping.mapping_type
                != mapping_type
            ):
                continue

            matches.append(mapping)

        matches.sort(
            key=lambda item: item.priority
        )

        return tuple(matches)