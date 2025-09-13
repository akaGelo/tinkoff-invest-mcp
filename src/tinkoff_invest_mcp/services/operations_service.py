"""Operations service for Tinkoff Invest MCP."""

from datetime import datetime

from ..models import OperationsResponse
from .base import BaseTinkoffService


class OperationsService(BaseTinkoffService):
    """Сервис для работы с операциями."""

    def get_operations(
        self,
        from_date: str,
        to_date: str | None = None,
        state: str | None = None,
        instrument_uid: str | None = None,
    ) -> OperationsResponse:
        """Получить операции по счету за период.

        Args:
            from_date: Начальная дата периода в формате ISO 8601 (например, '2024-01-01T00:00:00Z')
            to_date: Конечная дата периода. Если не указана, используется текущий момент
            state: Фильтр по статусу операции. Возможные значения:
                - OPERATION_STATE_EXECUTED - исполненные операции
                - OPERATION_STATE_CANCELED - отмененные операции
            instrument_uid: Фильтр по идентификатору инструмента

        Returns:
            OperationsResponse: Список операций за период
        """
        from_dt = self._parse_datetime(from_date)
        to_dt = self._parse_datetime(to_date) if to_date else datetime.now()

        with self._client_context() as client:
            response = client.operations.get_operations(
                account_id=self.config.account_id,
                from_=from_dt,
                to=to_dt,
                state=state,
                figi=instrument_uid or "",
            )

            return OperationsResponse.from_tinkoff(response)
