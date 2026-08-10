from .recognition_provider import (
    RecognitionProvider,
)


class RecognitionProviderRegistry:

    def __init__(self) -> None:
        self._providers: dict[
            str,
            RecognitionProvider,
        ] = {}

    def register(
        self,
        provider: RecognitionProvider,
    ) -> None:

        provider_id = (
            provider.provider_id.strip()
        )

        if not provider_id:
            raise ValueError(
                "provider_id không được để trống."
            )

        if provider_id in self._providers:
            raise ValueError(
                f"Recognition Provider đã tồn tại: "
                f"{provider_id}"
            )

        self._providers[
            provider_id
        ] = provider

    def get(
        self,
        provider_id: str,
    ) -> RecognitionProvider:

        try:
            return self._providers[
                provider_id
            ]

        except KeyError as exc:
            raise KeyError(
                f"Không tìm thấy Recognition Provider: "
                f"{provider_id}"
            ) from exc

    def exists(
        self,
        provider_id: str,
    ) -> bool:

        return (
            provider_id
            in self._providers
        )

    def all(
        self,
    ) -> tuple[
        RecognitionProvider,
        ...
    ]:

        return tuple(
            self._providers.values()
        )