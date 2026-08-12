from abc import ABC, abstractmethod
from typing import Any


class OutputAdapter(ABC):

    @property
    @abstractmethod
    def adapter_id(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def output_type(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def render(
        self,
        data: Any,
        *,
        context: dict[str, Any] | None = None,
    ) -> Any:
        """
        Chuyển dữ liệu đã xử lý thành đầu ra.

        Adapter không được thay đổi dữ liệu nền.
        """
        raise NotImplementedError