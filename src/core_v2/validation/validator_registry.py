from .validator import Validator


class ValidatorRegistry:
    def __init__(self) -> None:
        self._validators: dict[str, Validator] = {}

    def register(
        self,
        validator: Validator,
    ) -> None:
        data_type_id = validator.data_type_id.strip()

        if not data_type_id:
            raise ValueError(
                "validator.data_type_id không được để trống."
            )

        if data_type_id in self._validators:
            raise ValueError(
                f"Validator đã tồn tại cho Data Type: "
                f"{data_type_id}"
            )

        self._validators[data_type_id] = validator

    def get(
        self,
        data_type_id: str,
    ) -> Validator:
        try:
            return self._validators[data_type_id]
        except KeyError as exc:
            raise KeyError(
                f"Không tìm thấy Validator cho Data Type: "
                f"{data_type_id}"
            ) from exc

    def exists(
        self,
        data_type_id: str,
    ) -> bool:
        return data_type_id in self._validators

    def all(
        self,
    ) -> tuple[Validator, ...]:
        return tuple(
            self._validators.values()
        )