"""Утилиты для Tinkoff Invest MCP Server."""

from datetime import datetime
from typing import Any, ClassVar

from tinkoff.invest.schemas import CandleInterval


class DateTimeUtils:
    """Утилиты для работы с датами и временем."""

    @staticmethod
    def parse_iso_datetime(date_str: str | datetime) -> datetime:
        """Преобразовать строку ISO в datetime.

        Args:
            date_str: Строка в формате ISO 8601 или объект datetime

        Returns:
            datetime: Преобразованная дата
        """
        if isinstance(date_str, str):
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return date_str

    @staticmethod
    def parse_datetime(date_str: str | datetime) -> datetime:
        """Алиас для parse_iso_datetime для обратной совместимости."""
        return DateTimeUtils.parse_iso_datetime(date_str)


class CandleUtils:
    """Утилиты для работы со свечами."""

    INTERVAL_MAP: ClassVar[dict[str, CandleInterval]] = {
        "CANDLE_INTERVAL_1_MIN": CandleInterval.CANDLE_INTERVAL_1_MIN,
        "CANDLE_INTERVAL_5_MIN": CandleInterval.CANDLE_INTERVAL_5_MIN,
        "CANDLE_INTERVAL_15_MIN": CandleInterval.CANDLE_INTERVAL_15_MIN,
        "CANDLE_INTERVAL_HOUR": CandleInterval.CANDLE_INTERVAL_HOUR,
        "CANDLE_INTERVAL_DAY": CandleInterval.CANDLE_INTERVAL_DAY,
        "1min": CandleInterval.CANDLE_INTERVAL_1_MIN,
        "5min": CandleInterval.CANDLE_INTERVAL_5_MIN,
        "15min": CandleInterval.CANDLE_INTERVAL_15_MIN,
        "hour": CandleInterval.CANDLE_INTERVAL_HOUR,
        "day": CandleInterval.CANDLE_INTERVAL_DAY,
    }

    @classmethod
    def get_candle_interval(cls, interval: str) -> CandleInterval:
        """Преобразовать строковый интервал в enum.

        Args:
            interval: Строковое представление интервала

        Returns:
            CandleInterval: Enum интервала

        Raises:
            ValueError: Если интервал не поддерживается
        """
        candle_interval = cls.INTERVAL_MAP.get(interval)
        if not candle_interval:
            raise ValueError(f"Unsupported interval: {interval}")
        return candle_interval

    @classmethod
    def get_tinkoff_interval(cls, interval: str) -> CandleInterval:
        """Алиас для get_candle_interval для обратной совместимости."""
        return cls.get_candle_interval(interval)


class OrderUtils:
    """Утилиты для работы с ордерами."""

    @staticmethod
    def create_order_response(
        success: bool, time: datetime | None = None, **kwargs: Any
    ) -> dict[str, Any]:
        """Создать стандартный ответ для операций с ордерами.

        Args:
            success: Успешность операции
            time: Время выполнения операции
            **kwargs: Дополнительные поля для ответа

        Returns:
            dict: Стандартизированный ответ
        """
        response = {"success": success, **kwargs}
        if time:
            response["time"] = time.isoformat()
        return response
