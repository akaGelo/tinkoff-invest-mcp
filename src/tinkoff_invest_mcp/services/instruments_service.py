"""Instruments service for Tinkoff Invest MCP."""

from typing import Any

from tinkoff.invest.schemas import InstrumentIdType

from ..models import Instrument, PaginatedInstrumentsResponse
from .base import BaseTinkoffService


class InstrumentsService(BaseTinkoffService):
    """Сервис для работы с инструментами."""

    # Константы пагинации
    DEFAULT_INSTRUMENTS_LIMIT = 100000  # Щедрый запас для загрузки всех инструментов
    DEFAULT_PAGINATION_OFFSET = 0

    def _paginate_instruments(
        self,
        method_name: str,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PaginatedInstrumentsResponse:
        """Универсальный метод для пагинации инструментов.

        Args:
            method_name: Имя метода API для вызова
            limit: Максимальное количество инструментов
            offset: Смещение для пагинации

        Returns:
            PaginatedInstrumentsResponse: Список инструментов с информацией о пагинации
        """
        if limit is None:
            limit = self.DEFAULT_INSTRUMENTS_LIMIT
        if offset is None:
            offset = self.DEFAULT_PAGINATION_OFFSET

        with self._client_context() as client:
            # Получаем нужный метод из клиента
            method = getattr(client.instruments, method_name)

            all_instruments = []
            current_offset = offset
            remaining = limit

            while remaining > 0:
                response = method()
                batch: list[Any] = response.instruments[
                    current_offset : current_offset + remaining
                ]

                if not batch:
                    break

                all_instruments.extend(batch)
                remaining -= len(batch)
                current_offset += len(batch)

                if len(batch) < remaining:
                    break

            instruments = [Instrument.from_tinkoff(inst) for inst in all_instruments]

            total = len(instruments)
            has_more = offset + limit < total

            return PaginatedInstrumentsResponse(
                instruments=instruments,
                total=total,
                limit=limit,
                offset=offset,
                has_more=has_more,
            )

    def find_instrument(self, query: str) -> list[Instrument]:
        """Найти инструмент по запросу.

        Args:
            query: Поисковый запрос (тикер, ISIN, FIGI или название)

        Returns:
            list[Instrument]: Список найденных инструментов
        """
        with self._client_context() as client:
            response = client.instruments.find_instrument(query=query)

            return [Instrument.from_tinkoff(inst) for inst in response.instruments]

    def get_instrument_by_uid(self, uid: str) -> Instrument:
        """Получить инструмент по его UID.

        Args:
            uid: Уникальный идентификатор инструмента

        Returns:
            Instrument: Информация об инструменте
        """
        with self._client_context() as client:
            response = client.instruments.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_UID, id=uid
            )

            return Instrument.from_tinkoff(response.instrument)

    def get_shares(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PaginatedInstrumentsResponse:
        """Получить список акций.

        Args:
            limit: Максимальное количество инструментов
            offset: Смещение для пагинации

        Returns:
            PaginatedInstrumentsResponse: Список акций с информацией о пагинации
        """
        if limit is None:
            limit = self.DEFAULT_INSTRUMENTS_LIMIT
        if offset is None:
            offset = self.DEFAULT_PAGINATION_OFFSET
        return self._paginate_instruments("shares", limit, offset)

    def get_bonds(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PaginatedInstrumentsResponse:
        """Получить список облигаций.

        Args:
            limit: Максимальное количество инструментов
            offset: Смещение для пагинации

        Returns:
            PaginatedInstrumentsResponse: Список облигаций с информацией о пагинации
        """
        if limit is None:
            limit = self.DEFAULT_INSTRUMENTS_LIMIT
        if offset is None:
            offset = self.DEFAULT_PAGINATION_OFFSET
        return self._paginate_instruments("bonds", limit, offset)

    def get_etfs(
        self,
        limit: int | None = None,
        offset: int | None = None,
    ) -> PaginatedInstrumentsResponse:
        """Получить список ETF.

        Args:
            limit: Максимальное количество инструментов
            offset: Смещение для пагинации

        Returns:
            PaginatedInstrumentsResponse: Список ETF с информацией о пагинации
        """
        if limit is None:
            limit = self.DEFAULT_INSTRUMENTS_LIMIT
        if offset is None:
            offset = self.DEFAULT_PAGINATION_OFFSET
        return self._paginate_instruments("etfs", limit, offset)
