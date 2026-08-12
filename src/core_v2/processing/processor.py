from abc import ABC, abstractmethod
from typing import Any


class Processor(ABC):

    @property
    @abstractmethod
    def processor_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def data_type_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def capability(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def process(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """
        Xử lý dữ liệu.

        Processor không quyết định
        Data Type nào được gửi đến nó.
        Việc đó thuộc ProcessorRouter.
        """
        raise NotImplementedError