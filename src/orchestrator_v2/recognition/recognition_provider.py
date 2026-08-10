from abc import ABC, abstractmethod
from typing import Any

from src.orchestrator_v2.contracts.recognition_evidence import (
    RecognitionEvidence,
)


class RecognitionProvider(ABC):

    @property
    @abstractmethod
    def provider_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def recognize(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> tuple[RecognitionEvidence, ...]:
        """
        Trả về evidence nhận dạng.

        Provider không được:
        - tạo RecognitionResult cuối cùng;
        - tạo Identity;
        - tạo Data Type mới;
        - sửa Registry;
        - sửa Rule;
        - tự dispatch Processor.
        """
        raise NotImplementedError