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

## Доступные MCP методы

Сервер предоставляет 18 методов для работы с Tinkoff Invest API через протокол MCP.

### 💰 Портфель и балансы

#### `get_cash_balance`
Получить денежный баланс счета.
- Возвращает доступные и заблокированные средства по каждой валюте

#### `get_portfolio`
Получить состав портфеля.
- Возвращает все позиции с информацией о количестве, стоимости, средней цене покупки и P&L

### 📊 Операции и история

#### `get_operations`
Получить операции по счету за период.
- `from_date` - начальная дата в формате ISO 8601
- `to_date` - конечная дата (опционально)
- `state` - фильтр по статусу операции:
  - `OPERATION_STATE_EXECUTED` - исполненные операции
  - `OPERATION_STATE_CANCELED` - отмененные операции
- `instrument_uid` - фильтр по инструменту

### 📈 Рыночные данные

#### `get_candles`
Получить свечи по инструменту за период.
- `instrument_uid` - идентификатор инструмента
- `from_date` - начальная дата
- `to_date` - конечная дата (опционально)
- `interval` - интервал свечей:
  - `CANDLE_INTERVAL_1_MIN` - 1 минута
  - `CANDLE_INTERVAL_5_MIN` - 5 минут
  - `CANDLE_INTERVAL_15_MIN` - 15 минут
  - `CANDLE_INTERVAL_HOUR` - 1 час
  - `CANDLE_INTERVAL_DAY` - 1 день

#### `get_last_prices`
Получить последние цены по списку инструментов.
- `instrument_uids` - массив идентификаторов инструментов

#### `get_order_book`
Получить стакан заявок по инструменту.
- `instrument_uid` - идентификатор инструмента
- `depth` - глубина стакана (по умолчанию 10)

#### `get_trading_schedules`
Получить расписание торгов биржи.
- `exchange` - код биржи (по умолчанию "MOEX")
  - `MOEX` - Московская биржа
  - `MOEX_PLUS` - MOEX Plus
  - `MOEX_EVENING_WEEKEND` - Вечерние и выходные торги MOEX
  - `SPB` - СПБ Биржа
- `from_date` - начальная дата (опционально)
- `to_date` - конечная дата (опционально)

#### `get_trading_status`
Получить торговый статус инструмента.
- `instrument_uid` - идентификатор инструмента

### 🛒 Торговые заявки

#### `create_order`
Создать торговую заявку.
- `instrument_id` - идентификатор инструмента
- `quantity` - количество лотов
- `direction` - направление:
  - `ORDER_DIRECTION_BUY` - покупка
  - `ORDER_DIRECTION_SELL` - продажа
- `order_type` - тип заявки:
  - `ORDER_TYPE_MARKET` - рыночная заявка
  - `ORDER_TYPE_LIMIT` - лимитная заявка
- `price` - цена (только для лимитных заявок, float)

#### `cancel_order`
Отменить торговую заявку.
- `order_id` - идентификатор заявки

#### `get_orders`
Получить список активных торговых заявок.

### 🛑 Стоп-заявки

#### `post_stop_order`
Создать стоп-заявку.
- `instrument_id` - идентификатор инструмента
- `quantity` - количество лотов
- `direction` - направление:
  - `STOP_ORDER_DIRECTION_BUY` - покупка
  - `STOP_ORDER_DIRECTION_SELL` - продажа
- `stop_order_type` - тип стоп-заявки:
  - `STOP_ORDER_TYPE_TAKE_PROFIT` - тейк-профит
  - `STOP_ORDER_TYPE_STOP_LOSS` - стоп-лосс
  - `STOP_ORDER_TYPE_STOP_LIMIT` - стоп-лимит
- `stop_price` - цена активации (float)
- `expiration_type` - тип истечения:
  - `STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_CANCEL` - до отмены
  - `STOP_ORDER_EXPIRATION_TYPE_GOOD_TILL_DATE` - до даты
- `price` - цена исполнения (для STOP_LIMIT, float, опционально)
- `expire_date` - дата истечения (для GOOD_TILL_DATE, опционально)

#### `cancel_stop_order`
Отменить стоп-заявку.
- `stop_order_id` - идентификатор стоп-заявки

#### `get_stop_orders`
Получить список активных стоп-заявок.

### 🔍 Поиск инструментов

#### `find_instrument`
Найти инструмент по запросу.
- `query` - поисковый запрос (тикер, ISIN, FIGI или название)

#### `get_instrument_by_uid`
Получить инструмент по его UID.
- `uid` - уникальный идентификатор инструмента

#### `get_shares`
Получить список акций.
- `limit` - максимальное количество (по умолчанию 10)
- `offset` - смещение для пагинации (по умолчанию 0)

#### `get_bonds`
Получить список облигаций.
- `limit` - максимальное количество (по умолчанию 10)
- `offset` - смещение для пагинации (по умолчанию 0)

#### `get_etfs`
Получить список ETF.
- `limit` - максимальное количество (по умолчанию 10)
- `offset` - смещение для пагинации (по умолчанию 0)
