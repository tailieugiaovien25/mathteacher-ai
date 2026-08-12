from typing import Iterable

from .data_type_passport import (
    DataTypePassport,
    DataTypeStatus,
)


class DataTypeRegistry:
    def __init__(self) -> None:
        self._items: dict[str, DataTypePassport] = {}

    def register(
        self,
        passport: DataTypePassport,
    ) -> None:
        data_type_id = passport.data_type_id.strip()

        if not data_type_id:
            raise ValueError(
                "data_type_id không được để trống."
            )

        if data_type_id in self._items:
            raise ValueError(
                f"Data Type đã tồn tại: {data_type_id}"
            )

        self._items[data_type_id] = passport

    def get(
        self,
        data_type_id: str,
    ) -> DataTypePassport:
        try:
            return self._items[data_type_id]
        except KeyError as exc:
            raise KeyError(
                f"Không tìm thấy Data Type: {data_type_id}"
            ) from exc

    def exists(
        self,
        data_type_id: str,
    ) -> bool:
        return data_type_id in self._items

    def all(
        self,
    ) -> tuple[DataTypePassport, ...]:
        return tuple(
            self._items.values()
        )

    def accepted(
        self,
    ) -> tuple[DataTypePassport, ...]:
        return tuple(
            item
            for item in self._items.values()
            if item.status
            == DataTypeStatus.ACCEPTED
        )

    def register_many(
        self,
        passports: Iterable[DataTypePassport],
    ) -> None:
        for passport in passports:
            self.register(passport)