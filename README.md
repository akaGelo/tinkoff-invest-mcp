# Tinkoff Invest MCP Server

MCP сервер для работы с Tinkoff Invest API.

## Установка

### Из исходников
```bash
uv tool install git+https://github.com/akaGelo/tinkoff-invest-mcp.git
```

### Для разработки
```bash
git clone git@github.com:akaGelo/tinkoff-invest-mcp.git
cd tinkoff-invest-mcp
uv tool install --editable .
```

## Конфигурация

### Переменные окружения

Необходимые переменные:

- **TINKOFF_TOKEN** - API токен от Tinkoff Invest
- **TINKOFF_ACCOUNT_ID** - ID счета для ограничения операций (обязательно для безопасности)
- **TINKOFF_MODE** - режим работы: `sandbox` (по умолчанию) или `production`
- **TINKOFF_APP_NAME** - имя приложения для логирования (опционально)

### Пример .env файла
```env
TINKOFF_TOKEN=your_api_token_here
TINKOFF_ACCOUNT_ID=your_account_id_here
TINKOFF_MODE=sandbox
TINKOFF_APP_NAME=tinkoff-invest-mcp
```

## Тестирование

Для отладки можно использовать MCP Inspector:
```bash
npx @modelcontextprotocol/inspector
```
