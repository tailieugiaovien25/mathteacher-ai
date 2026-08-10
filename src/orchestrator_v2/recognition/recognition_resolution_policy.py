from abc import ABC, abstractmethod

from src.orchestrator_v2.contracts.recognition_evidence import (
    RecognitionEvidence,
)
from src.orchestrator_v2.contracts.recognition_result import (
    RecognitionResult,
)


class RecognitionResolutionPolicy(ABC):
    """
    Contract quyết định RecognitionResult cuối cùng
    từ tập RecognitionEvidence.

    Policy chịu trách nhiệm:
    - đánh giá evidence;
    - xử lý cạnh tranh giữa các candidate;
    - quyết định RECOGNIZED / AMBIGUOUS / UNRESOLVED;
    - tạo RecognitionResult.

    Policy không được:
    - gọi RecognitionProvider;
    - sửa Provider Registry;
    - dispatch Processor;
    - tạo Data Type mới.
    """

    @abstractmethod
    def resolve(
        self,
        evidence: tuple[RecognitionEvidence, ...],
    ) -> RecognitionResult:
        raise NotImplementedError