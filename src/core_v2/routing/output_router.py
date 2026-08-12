from .output_adapter import OutputAdapter


class OutputRouter:

    def __init__(self) -> None:
        self._adapters: dict[
            str,
            OutputAdapter,
        ] = {}

    def register(
        self,
        adapter: OutputAdapter,
    ) -> None:

        output_type = (
            adapter.output_type.strip()
        )

        if not output_type:
            raise ValueError(
                "adapter.output_type "
                "không được để trống."
            )

        if output_type in self._adapters:
            raise ValueError(
                f"Output Adapter đã tồn tại: "
                f"{output_type}"
            )

        self._adapters[
            output_type
        ] = adapter

    def resolve(
        self,
        output_type: str,
    ) -> OutputAdapter:

        try:
            return self._adapters[
                output_type
            ]

        except KeyError as exc:
            raise KeyError(
                f"Không tìm thấy Output Adapter: "
                f"{output_type}"
            ) from exc

    def exists(
        self,
        output_type: str,
    ) -> bool:

        return (
            output_type
            in self._adapters
        )

    def all(
        self,
    ) -> tuple[OutputAdapter, ...]:

        return tuple(
            self._adapters.values()
        )