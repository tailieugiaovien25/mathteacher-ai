from .processor import Processor


class ProcessorRouter:

    def __init__(self) -> None:
        self._processors: dict[
            tuple[str, str],
            Processor,
        ] = {}

    def register(
        self,
        processor: Processor,
    ) -> None:

        data_type_id = (
            processor.data_type_id.strip()
        )

        capability = (
            processor.capability.strip()
        )

        if not data_type_id:
            raise ValueError(
                "processor.data_type_id "
                "không được để trống."
            )

        if not capability:
            raise ValueError(
                "processor.capability "
                "không được để trống."
            )

        key = (
            data_type_id,
            capability,
        )

        if key in self._processors:
            raise ValueError(
                "Processor đã tồn tại cho "
                f"{data_type_id} / {capability}"
            )

        self._processors[key] = processor

    def resolve(
        self,
        *,
        data_type_id: str,
        capability: str,
    ) -> Processor:

        key = (
            data_type_id,
            capability,
        )

        try:
            return self._processors[key]

        except KeyError as exc:
            raise KeyError(
                "Không tìm thấy Processor cho "
                f"{data_type_id} / {capability}"
            ) from exc

    def exists(
        self,
        *,
        data_type_id: str,
        capability: str,
    ) -> bool:

        return (
            data_type_id,
            capability,
        ) in self._processors

    def all(
        self,
    ) -> tuple[Processor, ...]:

        return tuple(
            self._processors.values()
        )