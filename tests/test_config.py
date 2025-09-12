"""Тесты для конфигурации."""

import os
from unittest.mock import patch

import pytest
from tinkoff.invest.constants import INVEST_GRPC_API, INVEST_GRPC_API_SANDBOX

from src.tinkoff_invest_mcp.config import Mode, TinkoffConfig


class TestTinkoffConfig:
    """Тесты для класса TinkoffConfig."""

    def test_config_creation(self):
        """Тест создания конфигурации с валидными параметрами."""
        config = TinkoffConfig(token="test-token-123", account_id="test-account-456")

        assert config.token == "test-token-123"
        assert config.account_id == "test-account-456"
        assert config.mode == Mode.SANDBOX
        assert config.app_name == "tinkoff-invest-mcp"
        assert config.target == INVEST_GRPC_API_SANDBOX

    def test_config_with_production_mode(self):
        """Тест создания конфигурации в production режиме."""
        config = TinkoffConfig(
            token="test-token", account_id="test-account", mode=Mode.PRODUCTION
        )

        assert config.mode == Mode.PRODUCTION
        assert config.target == INVEST_GRPC_API

    def test_config_validation_empty_token(self):
        """Тест валидации пустого токена."""
        with pytest.raises(ValueError, match="Token cannot be empty"):
            TinkoffConfig(token="", account_id="test")

    def test_config_validation_whitespace_token(self):
        """Тест валидации токена из пробелов."""
        with pytest.raises(ValueError, match="Token cannot be empty"):
            TinkoffConfig(token="   ", account_id="test")

    def test_config_validation_empty_account_id(self):
        """Тест валидации пустого account_id."""
        with pytest.raises(ValueError, match="Account ID cannot be empty"):
            TinkoffConfig(token="test", account_id="")

    def test_config_validation_whitespace_account_id(self):
        """Тест валидации account_id из пробелов."""
        with pytest.raises(ValueError, match="Account ID cannot be empty"):
            TinkoffConfig(token="test", account_id="   ")

    @patch.dict(
        os.environ,
        {
            "TINKOFF_TOKEN": "env-token-123",
            "TINKOFF_ACCOUNT_ID": "env-account-456",
            "TINKOFF_MODE": "production",
            "TINKOFF_APP_NAME": "test-app",
        },
    )
    def test_config_from_env_all_vars(self):
        """Тест создания конфигурации из всех переменных окружения."""
        config = TinkoffConfig.from_env()

        assert config.token == "env-token-123"
        assert config.account_id == "env-account-456"
        assert config.mode == Mode.PRODUCTION
        assert config.app_name == "test-app"
        assert config.target == INVEST_GRPC_API

    @patch.dict(
        os.environ,
        {"TINKOFF_TOKEN": "env-token", "TINKOFF_ACCOUNT_ID": "env-account"},
        clear=True,
    )
    def test_config_from_env_minimal_vars(self):
        """Тест создания конфигурации с минимальным набором переменных."""
        config = TinkoffConfig.from_env()

        assert config.token == "env-token"
        assert config.account_id == "env-account"
        assert config.mode == Mode.SANDBOX  # default
        assert config.app_name == "tinkoff-invest-mcp"  # default
        assert config.target == INVEST_GRPC_API_SANDBOX

    @patch.dict(os.environ, {}, clear=True)
    def test_config_from_env_missing_token(self):
        """Тест ошибки при отсутствии токена в env."""
        with pytest.raises(
            ValueError, match="Required environment variable 'TINKOFF_TOKEN' not set"
        ):
            TinkoffConfig.from_env()

    @patch.dict(os.environ, {"TINKOFF_TOKEN": "test"}, clear=True)
    def test_config_from_env_missing_account_id(self):
        """Тест ошибки при отсутствии account_id в env."""
        with pytest.raises(
            ValueError,
            match="Required environment variable 'TINKOFF_ACCOUNT_ID' not set",
        ):
            TinkoffConfig.from_env()

    @patch.dict(
        os.environ,
        {
            "TINKOFF_TOKEN": "test-token",
            "TINKOFF_ACCOUNT_ID": "test-account",
            "TINKOFF_MODE": "invalid-mode",
        },
    )
    def test_config_from_env_invalid_mode(self):
        """Тест ошибки при невалидном режиме."""
        with pytest.raises(ValueError, match="Invalid TINKOFF_MODE='invalid-mode'"):
            TinkoffConfig.from_env()

    def test_config_for_testing(self):
        """Тест создания тестовой конфигурации."""
        config = TinkoffConfig.for_testing()

        assert config.token == "test-token"
        assert config.account_id == "test-account"
        assert config.mode == Mode.SANDBOX
        assert config.app_name == "test-app"

    def test_config_for_testing_with_params(self):
        """Тест создания тестовой конфигурации с параметрами."""
        config = TinkoffConfig.for_testing(
            token="custom-token", account_id="custom-account", mode=Mode.PRODUCTION
        )

        assert config.token == "custom-token"
        assert config.account_id == "custom-account"
        assert config.mode == Mode.PRODUCTION
        assert config.app_name == "test-app"

    def test_mask_sensitive_data_short_values(self):
        """Тест маскирования коротких чувствительных данных."""
        config = TinkoffConfig(token="short", account_id="123")

        masked = config.mask_sensitive_data()
        assert masked["token"] == "***"
        assert masked["account_id"] == "***"
        assert masked["mode"] == "sandbox"
        assert masked["app_name"] == "tinkoff-invest-mcp"

    def test_mask_sensitive_data_long_values(self):
        """Тест маскирования длинных чувствительных данных."""
        config = TinkoffConfig(
            token="very-secret-token-12345", account_id="my-account-id-67890"
        )

        masked = config.mask_sensitive_data()
        assert masked["token"] == "very...2345"
        assert masked["account_id"] == "my-a...7890"
        assert "secret" not in masked["token"]
        assert "account-id" not in masked["account_id"]

    def test_mode_enum_values(self):
        """Тест значений enum для режимов."""
        assert Mode.SANDBOX.value == "sandbox"
        assert Mode.PRODUCTION.value == "production"

    def test_config_immutability_after_creation(self):
        """Тест что конфигурация остается валидной после создания."""
        config = TinkoffConfig(
            token="test-token", account_id="test-account", mode=Mode.PRODUCTION
        )

        # Проверяем что target правильно вычислился
        assert config.target == INVEST_GRPC_API

        # Попытка изменить mode не должна влиять на target
        # (dataclass по умолчанию не frozen, но target устанавливается в __post_init__)
        original_target = config.target
        config.mode = (
            Mode.SANDBOX
        )  # Изменение mode не влияет на уже установленный target
        assert config.target == original_target  # target не изменится
