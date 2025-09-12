"""Константы для Tinkoff Invest MCP Server."""

# Дефолтные значения для пагинации
DEFAULT_INSTRUMENTS_LIMIT = 100000  # Щедрый запас для загрузки всех инструментов
DEFAULT_PAGINATION_OFFSET = 0

# Значения по умолчанию для инструментов
UNKNOWN_INSTRUMENT_NAME = "Unknown"
UNKNOWN_INSTRUMENT_TICKER = "UNKNOWN"

# Настройки кэша
CACHE_LOADING_LOG_MESSAGE = "Loading instruments into cache..."

# Режимы работы
SANDBOX_MODE = "sandbox"
PRODUCTION_MODE = "production"

# Имя приложения по умолчанию
DEFAULT_APP_NAME = "tinkoff-invest-mcp"

# Переменные окружения
ENV_TINKOFF_TOKEN = "TINKOFF_TOKEN"
ENV_TINKOFF_ACCOUNT_ID = "TINKOFF_ACCOUNT_ID"
ENV_TINKOFF_MODE = "TINKOFF_MODE"
ENV_TINKOFF_APP_NAME = "TINKOFF_APP_NAME"
