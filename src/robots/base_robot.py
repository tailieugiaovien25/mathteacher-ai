from abc import ABC, abstractmethod
from time import perf_counter


class BaseRobot(ABC):
    """Lớp nền dùng chung cho các Robot của hệ thống."""

    def __init__(
        self,
        name: str,
        version: str,
    ) -> None:
        self.name = name
        self.version = version

    def execute(self) -> None:
        """Điểm chạy chung của mọi Robot."""
        start_time = perf_counter()

        self._print_header()

        try:
            self.run()
        except Exception as error:
            self._print_error(error)
            raise
        finally:
            elapsed_time = perf_counter() - start_time
            self._print_footer(elapsed_time)

    @abstractmethod
    def run(self) -> None:
        """Mỗi Robot con phải tự cài đặt quy trình xử lý."""
        raise NotImplementedError

    def _print_header(self) -> None:
        print("=" * 60)
        print("AI Teacher Platform")
        print(self.name)
        print(f"Version: {self.version}")
        print("=" * 60)

    def _print_footer(self, elapsed_time: float) -> None:
        print("\n" + "=" * 60)
        print(f"Hoàn thành trong: {elapsed_time:.2f} giây")
        print("=" * 60)

    def _print_error(self, error: Exception) -> None:
        print("\nĐã xảy ra lỗi:")
        print(f"{type(error).__name__}: {error}")