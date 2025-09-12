"""Конфигурация для Tinkoff Invest MCP Server."""

import os
from dataclasses import dataclass, field
from enum import Enum

from tinkoff.invest.constants import INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX

from .constants import (
    DEFAULT_APP_NAME,
    ENV_TINKOFF_ACCOUNT_ID,
    ENV_TINKOFF_APP_NAME,
    ENV_TINKOFF_MODE,
    ENV_TINKOFF_TOKEN,
    SANDBOX_MODE,
)


class Mode(Enum):
    """Режимы работы с API."""

    SANDBOX = "sandbox"
    PRODUCTION = "production"


@dataclass
class TinkoffConfig:
    """Конфигурация для работы с Tinkoff Invest API."""

    # Обязательные параметры
    token: str
    account_id: str

    # Опциональные параметры с дефолтами
    mode: Mode = Mode.SANDBOX
    app_name: str = DEFAULT_APP_NAME

    # Вычисляемые поля
    target: str = field(init=False)

    def __post_init__(self) -> None:
        """Валидация и вычисление полей после инициализации."""
        # Валидация токена
        if not self.token or self.token.isspace():
            raise ValueError("Token cannot be empty")

        # Валидация account_id
        if not self.account_id or self.account_id.isspace():
            raise ValueError("Account ID cannot be empty")

        # Определяем target на основе mode
        self.target = (
            INVEST_GRPC_API_SANDBOX if self.mode == Mode.SANDBOX else INVEST_GRPC_API
        )

    @classmethod
    def from_env(cls) -> "TinkoffConfig":
        """Создать конфигурацию из переменных окружения.

        Returns:
            TinkoffConfig: Валидированная конфигурация

        Raises:
            ValueError: Если обязательные переменные не установлены
        """
        token = os.environ.get(ENV_TINKOFF_TOKEN)
        if not token:
            raise ValueError(
                f"Required environment variable '{ENV_TINKOFF_TOKEN}' not set. "
                "Please set it with your Tinkoff Invest API token"
            )

        account_id = os.environ.get(ENV_TINKOFF_ACCOUNT_ID)
        if not account_id:
            raise ValueError(
                f"Required environment variable '{ENV_TINKOFF_ACCOUNT_ID}' not set. "
                "Please set it with your Tinkoff account ID"
            )

        # Парсим mode с валидацией
        mode_str = os.environ.get(ENV_TINKOFF_MODE, SANDBOX_MODE).lower()
        try:
            mode = Mode(mode_str)
        except ValueError:
            valid_modes = [m.value for m in Mode]
            raise ValueError(
                f"Invalid {ENV_TINKOFF_MODE}='{mode_str}'. "
                f"Valid values are: {', '.join(valid_modes)}"
            ) from None

        app_name = os.environ.get(ENV_TINKOFF_APP_NAME, DEFAULT_APP_NAME)

        return cls(token=token, account_id=account_id, mode=mode, app_name=app_name)

    @classmethod
    def for_testing(
        cls,
        token: str = "test-token",
        account_id: str = "test-account",
        mode: Mode = Mode.SANDBOX,
    ) -> "TinkoffConfig":
        """Создать тестовую конфигурацию.

        Args:
            token: Тестовый токен
            account_id: Тестовый ID аккаунта
            mode: Режим работы

        Returns:
            TinkoffConfig: Конфигурация для тестов
        """
        return cls(token=token, account_id=account_id, mode=mode, app_name="test-app")

    def mask_sensitive_data(self) -> dict[str, str]:
        """Получить конфигурацию с замаскированными чувствительными данными.

        Returns:
            dict: Конфигурация для логирования
        """
        return {
            "token": (
                f"{self.token[:4]}...{self.token[-4:]}"
                if len(self.token) > 8
                else "***"
            ),
            "account_id": (
                f"{self.account_id[:4]}...{self.account_id[-4:]}"
                if len(self.account_id) > 8
                else "***"
            ),
            "mode": self.mode.value,
            "app_name": self.app_name,
            "target": self.target,
        }
