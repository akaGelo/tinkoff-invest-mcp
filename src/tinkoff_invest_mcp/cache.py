"""Кэширование для Tinkoff Invest MCP Server."""

import logging
from collections.abc import Callable
from contextlib import AbstractContextManager
from typing import TYPE_CHECKING

from .models import Instrument

if TYPE_CHECKING:
    from tinkoff.invest.services import Services


class InstrumentsCache:
    """Кэш для инструментов с единым хранилищем."""

    def __init__(
        self, client_factory: Callable[[], AbstractContextManager["Services"]]
    ) -> None:
        """Инициализация кэша.

        Args:
            client_factory: Фабрика для создания клиентов
        """
        self._instruments_cache: dict[str, Instrument] = {}
        self._instruments_loaded: bool = False
        self._client_factory = client_factory
        self._logger = logging.getLogger("tinkoff-invest-mcp.cache")

    def ensure_loaded(self) -> None:
        """Загрузить все инструменты в кэш если еще не загружены."""
        if self._instruments_loaded:
            return

        with self._client_factory() as client:
            self._logger.info("Loading instruments into cache...")

            # Загружаем все типы инструментов
            shares = client.instruments.shares()
            bonds = client.instruments.bonds()
            etfs = client.instruments.etfs()

            # Добавляем в единый кэш
            for share in shares.instruments:
                instrument = Instrument.from_tinkoff_share(share)
                self._instruments_cache[instrument.uid] = instrument

            for bond in bonds.instruments:
                instrument = Instrument.from_tinkoff_bond(bond)
                self._instruments_cache[instrument.uid] = instrument

            for etf in etfs.instruments:
                instrument = Instrument.from_tinkoff_etf(etf)
                self._instruments_cache[instrument.uid] = instrument

            self._instruments_loaded = True
            self._logger.info(
                f"Loaded {len(self._instruments_cache)} instruments into cache"
            )

    def get_instrument_info(self, uid: str) -> tuple[str, str]:
        """Получить имя и тикер инструмента по UID.

        Args:
            uid: UID инструмента

        Returns:
            tuple: (name, ticker) или ("Unknown", "UNKNOWN") если не найдено
        """
        self.ensure_loaded()
        instrument = self._instruments_cache.get(uid)
        if instrument:
            return instrument.name, instrument.ticker

        # Логируем неудачные поиски для отладки
        self._logger.warning(f"Instrument not found in cache: {uid}")
        return "Unknown", "UNKNOWN"

    def get_instruments_by_type(self, instrument_type: str) -> list[Instrument]:
        """Получить список инструментов по типу.

        Args:
            instrument_type: Тип инструмента (share, bond, etf)

        Returns:
            list[Instrument]: Список инструментов указанного типа
        """
        self.ensure_loaded()
        return [
            inst
            for inst in self._instruments_cache.values()
            if inst.instrument_type == instrument_type
        ]

    def clear_cache(self) -> None:
        """Очистить кэш (для принудительного обновления)."""
        self._instruments_cache.clear()
        self._instruments_loaded = False
        self._logger.info("Instruments cache cleared")

    @property
    def cache_size(self) -> int:
        """Размер кэша."""
        return len(self._instruments_cache)

    @property
    def is_loaded(self) -> bool:
        """Проверить загружен ли кэш."""
        return self._instruments_loaded
