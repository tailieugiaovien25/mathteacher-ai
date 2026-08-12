from abc import ABC, abstractmethod
from typing import Any

from .validation_result import ValidationResult


class Validator(ABC):

    @property
    @abstractmethod
    def data_type_id(self) -> str:
        """
        Data Type mà validator này chịu trách nhiệm.
        """
        raise NotImplementedError

    @abstractmethod
    def validate(
        self,
        data: Any,
    ) -> ValidationResult:
        """
        Kiểm tra dữ liệu và trả ValidationResult.

        Validator không được âm thầm sửa dữ liệu.
        """
        raise NotImplementedError