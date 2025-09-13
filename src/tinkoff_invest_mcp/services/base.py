"""Base service class for Tinkoff Invest services."""

from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime

import fastmcp.utilities.logging
from tinkoff.invest import Client
from tinkoff.invest.services import Services

from ..cache import InstrumentsCache
from ..config import TinkoffConfig


class BaseTinkoffService:
    """Базовый класс для всех сервисов Tinkoff Invest."""

    def __init__(self, config: TinkoffConfig, cache: InstrumentsCache) -> None:
        """Инициализация базового сервиса.

        Args:
            config: Конфигурация сервиса
            cache: Кэш инструментов
        """
        self.config = config
        self._cache = cache
        self.logger = fastmcp.utilities.logging.get_logger(self.__class__.__name__)
        self._initialized = False

    def set_initialized(self, value: bool) -> None:
        """Установить флаг инициализации.

        Args:
            value: Значение флага инициализации
        """
        self._initialized = value

    @contextmanager
    def _client_context(self) -> Generator[Services, None, None]:
        """Контекстный менеджер для работы с клиентом."""
        if not self._initialized:
            raise RuntimeError("Service not initialized. Call initialize() first.")

        client = Client(
            self.config.token, target=self.config.target, app_name=self.config.app_name
        )
        with client as client_instance:
            yield client_instance

    def _get_instrument_info(self, uid: str) -> tuple[str, str]:
        """Получить имя и тикер инструмента по UID.

        Args:
            uid: Уникальный идентификатор инструмента

        Returns:
            Кортеж из имени и тикера инструмента
        """
        return self._cache.get_instrument_info(uid)

    @staticmethod
    def _parse_datetime(date_str: str | datetime) -> datetime:
        """Преобразовать строку ISO в datetime.

        Args:
            date_str: Строка в формате ISO 8601 или объект datetime

        Returns:
            datetime: Преобразованная дата
        """
        if isinstance(date_str, str):
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        return date_str
