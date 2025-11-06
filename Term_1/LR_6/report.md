# Отчет по лабораторной работе: Реализация паттерна "Наблюдатель" для отслеживания курсов валют ЦБ РФ

## Введение

**Цель работы:** Реализация системы мониторинга курсов валют с использованием паттерна "Наблюдатель", интегрированной с API Центробанка РФ и предоставляющей REST API через FastAPI.

**Технологический стек:**
- Python
- FastAPI + Uvicorn
- aiohttp для асинхронных HTTP запросов
- SSL/TLS для безопасного соединения
- XML парсинг для обработки данных ЦБ РФ
- WebSocket для реального времени

## Архитектура системы

### Структура проекта
```
project/
├── observer.py            # Базовые классы паттерна "Наблюдатель"
├── observers.py           # Конкретные реализации наблюдателей
├── currency_service.py    # Сервис работы с API ЦБ РФ
├── websocket_observer.py  # WebSocket с Наблюдателем
├── index.html             # Веб-интерфейс для отображения курсов
└── app.py                 # FastAPI приложение
```

## Детали реализации

### 1. Паттерн "Наблюдатель" (observer.py)

**Абстрактный класс Observer:**
```python
class Observer(ABC):
    @abstractmethod
    async def update(self, currency_data: Dict[str, Any]):
        """Асинхронный метод обновления для всех наблюдателей"""
```

**Класс Subject (Субъект):**
```python
class Subject(ABC):
    def __init__(self):
        self._observers: List[Observer] = []
    
    async def notify(self, currency_data: Dict[str, Any]) -> None:
        tasks = [observer.update(currency_data) for observer in self._observers]
        await asyncio.gather(*tasks)  # Параллельное выполнение
```

**Важный момент:** Использование `asyncio.gather()` позволяет уведомлять всех наблюдателей параллельно, что значительно повышает производительность. Иначе пользователи будут стоять в очереди и ждать, пока обработается один запрос, чтобы перейти к следующему.

## 2. WebSocket Observer (websocket_observer.py)

Архитектура WebSocket наблюдателя

python
class WebsocketObserver(Observer):
    def __init__(self):
        self.connections: Set = set()  # Множество активных соединений
Ключевые особенности:

Множество соединений - использует set() для хранения активных WebSocket соединений
Обработка ошибок - каждая отправка обернута в try-except блок
Статистика подключений - отслеживание количества активных клиентов
Метод update()

python
async def update(self, currency_data: Dict[str, Any]):
    if self.connections:
        message = json.dumps({
            "type": "currency_update",
            "data": currency_data,
            "timestamp": currency_data.get('timestamp')
        }, ensure_ascii=False)
        
        for connection in self.connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error sending message: {e}")
Формат сообщения:

type: "currency_update" - идентификатор типа сообщения
data: полные данные о валютах
timestamp: временная метка обновления
Управление соединениями

python
def add_connection(self, websocket):
    self.connections.add(websocket)
    print(f"WebSocket клиент подключен. Всего: {len(self.connections)}")

def remove_connection(self, websocket):
    if websocket in self.connections:
        self.connections.remove(websocket)
        print(f"WebSocket клиент отключен. Всего: {len(self.connections)}")
Преимущества использования Set:

Автоматическое предотвращение дубликатов
Быстрый поиск и удаление O(1)
Эффективное управление памятью

## 3. Интеграция в FastAPI приложение

WebSocket endpoint

python
@app.websocket("/ws/currency")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    websocket_observer.add_connection(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            await handle_websocket_message(data, websocket)
    except WebSocketDisconnect:
        websocket_observer.remove_connection(websocket)
Обработка сообщений от клиентов

python
async def handle_websocket_message(message: str, websocket: WebSocket):
    try:
        data = json.loads(message)
        if data.get("type") == "subscribe":
            await websocket.send_text(json.dumps({
                "type": "subscribed",
                "message": "Вы подписаны на обновления курсов валют"
            }, ensure_ascii=False))
    except json.JSONDecodeError:
        pass

### 4. Конкретные наблюдатели (observers.py)

* **EmailNotifier:** Имитирует отправку email-уведомлений
* **LoggerObserver:** Записывает данные в JSON-лог файл
* **ConsoleDisplay:** Форматирует вывод в консоль

### 5. Сервис валют (currency_service.py)

#### SSL/TLS Безопасное соединение
```python
async def fetch_currency_rates(self) -> Dict[str, Any]:
    ssl_context = ssl.create_default_context(cafile=certifi.where())  # Берем все актуальные SSL сертификаты
    connector = aiohttp.TCPConnector(ssl=ssl_context, keepalive_timeout=30, limit=100)
     # Применяет наш безопасный SSL контекст ко всем соединениям,
      # Принимает в течении 30 секунд запросы, чтобы не закрывать и не открывать шифрование при каждом запросе, что уменьшает нагрузку на сервер
      # Ставим лимит в 100 запросов одновременно, чтобы исключить DDoS, то есть 101 запрос будет ждать, пока какой-то из тех 100 освободится
    timeout = aiohttp.ClientTimeout(total=30) # Устанавливаем на весь запрос 30 секунд, чтобы выдать ошибку, если вдруг пойдет что-то не так, иначе будет висеть бесконечно
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        async with session.get(url) as response:
            # Защищенное HTTPS соединение
```

**Особенность:** Использование `certifi` ГАРАНТИРУЕТ актуальные SSL сертификаты, что критически важно для безопасного соединения с API ЦБ РФ.

#### Детальный парсинг XML
```python
def parse_xml_currency_rates(self, xml_data: str) -> Dict[str, Any]:
    for valute in root.findall('Valute'):
        # Многоуровневая проверка данных:
        # 1. Существование элементов
        # 2. Наличие текстового содержимого
        # 3. Корректность числовых значений
        # 4. Валидность расчетов
```

**Ключевые проверки:**
- Проверка на `None` для всех XML элементов
- Валидация числовых значений (`value > 0`, `nominal > 0`)
- Обработка формата чисел с запятыми (`"70,1234" → 70.1234`)
- Расчет курса за 1 единицу валюты

#### Алгоритм обнаружения изменений
```python
def has_changes(self) -> bool:
    change = abs(previous_rate - currency_rate)
    return change > 0  # Любое изменение приведет к уведомлению наблюдателей
```

### 6. FastAPI приложение (app.py)

#### Современный Lifespan менеджер
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup логика
    currency_service = CurrencyService()
    asyncio.create_task(currency_service.start_monitoring())
    
    yield  # Работа приложения
    
    # Shutdown логика
    currency_service.stop_monitoring()
```

**Преимущества перед устаревшим `@app.on_event`:**
- Более чистая и понятная структура
- Лучшая обработка ошибок
- Совместимость с будущими версиями FastAPI
- Phtonic структура

#### API Endpoints

```python
@app.get("/current-rates")          # Все курсы валют
@app.get("/rates/{currency_code}")  # Конкретная валюта
@app.post("/observers/email")       # Регистрация наблюдателя
@app.get("/status")                 # Статус системы
```

### Система диагностики SSL

#### Функция `_diagnose_ssl_issue`

Объявляем синхронную функцию, так как в асинхронности в данном случае смысла нет. Используем `try-except` для безопасного выполнения диагностики.

```
    async def _diagnose_ssl_issue(self):

        try:

            print("Диагностика SSL проблем...")

            cert_path = certifi.where() # Проверяем, где находятся сертификаты, чтобы проверить: существует ли файл, не поврежден ли он, не пустой ли он 

            print(f"Путь к сертификатам: {cert_path}")

            context = ssl.create_default_context(cafile=certifi.where()) # Создаем объект SSL и указываем, что используем сертификаты из certifi

            # Используем urllib вместо aiohttp, чтобы изолировать проблему и проверить подключение
            with urllib.request.urlopen( 
                    "https://www.cbr.ru/scripts/XML_daily.asp",
                    context=context,
                    timeout=10
            ) as response:
                print("Диагностика: Прямое подключение работает!")

        except Exception as e:
            print(f"Диагностика показала проблему: {e}")
            print("Попробуйте обновить сертификаты: pip install --upgrade certifi")
```

### Назначение и функциональность

#### Цель диагностики:

* Определить точную причину SSL ошибок
* Проверить корректность установки сертификатов
* Предоставить пользователю конкретные инструкции по решению

#### Преимущества диагностической системы:

* Самостоятельное решение проблем - пользователь получает конкретные инструкции
* Сокращение времени отладки - быстрое определение корневой причины
* Улучшенный пользовательский опыт - понятные сообщения об ошибках
* Проактивное обслуживание - рекомендации по обновлению сертификатов

## Ключевые особенности

### Безопасность
- **SSL/TLS шифрование** всех соединений с API ЦБ РФ
- **Валидация сертификатов** через актуальную базу *certifi*
- **Обработка SSL ошибок** с диагностикой проблем

### Асинхронность
- **Неблокирующие HTTP запросы** через aiohttp
- **Параллельное уведомление** наблюдателей через `asyncio.gather()`
- **Фоновый мониторинг** без блокировки основного потока

### Real-time обновления через WebSocket
- **Мгновенная доставка** обновлений всем подключенным клиентам
- **Автоматическое управление** соединениями
- **Обработка ошибок** передачи с сохранением стабильности системы

### Точность обработки данных
- **Многоуровневая валидация** XML структуры
- **Корректное преобразование** числовых форматов
- **Детальное логирование** процесса парсинга

### Гибкость архитектуры
- **Легкое добавление** новых типов наблюдателей
- **Настраиваемые параметры** (интервалы, пороги изменений)
- **Расширяемая API** с автоматической документацией

### Доступные endpoints
- **Документация API:** http://localhost:8000/docs
- **Текущие курсы:** http://localhost:8000/current-rates
- **Статус системы:** http://localhost:8000/status
- WebSocket: ws://localhost:8000/ws/currency

## Примеры работы

### Консольный вывод при запуске

```
! ОБНОВЛЕНИЕ КУРСОВ ВАЛЮТ (2025-11-06T12:00:53.183880)
------------------------------------------------------------
* USD (Доллар США): 81.1885 RUB
* EUR (Евро): 93.5131 RUB
* GBP (Фунт стерлингов): 105.9185 RUB
* CNY (Юань): 11.3362 RUB
* JPY (Иен): 0.5291 RUB
------------------------------------------------------------
```

## WebSocket взаимодействие

### Клиент подключается:

```
text
WebSocket клиент подключен. Всего: 1
```
### Обновление данных:
```
json
{
  "type": "currency_update",
  "data": {
    "rates": {
      "USD": {"rate": 81.1885, "name": "Доллар США", "nominal": 1},
      "EUR": {"rate": 93.5131, "name": "Евро", "nominal": 1}
    },
    "timestamp": "2025-11-06T12:00:53.183880"
  }
}
```
## Полный вывод программы

### Двойной запрос в начале - это особенность реализации, которая обеспечивает:

* Мгновенную инициализацию системы при запуске
* Немедленное уведомление наблюдателей о текущих курсах
* Начало мониторинга с актуальными данными

```
INFO:     Started server process [85772]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
Наблюдатель EmailNotifier зарегистрирован
Наблюдатель LoggerObserver зарегистрирован
Наблюдатель ConsoleDisplay зарегистрирован
Приложение запущено и мониторинг активирован
Мониторинг курсов валют запущен (интервал: 10 сек)...
Данные успешно получены от ЦБ РФ
Получено XML данных: 9690 символов
Начало XML: <?xml version="1.0" encoding="windows-1251"?><ValCurs Date="06.11.2025" name="Foreign Currency Market"><Valute ID="R01010"><NumCode>036</NumCode><CharCode>AUD</CharCode><Nominal>1</Nominal><Name>Австр...
AUD: 52.7076 RUB
AZN: 47.7579 RUB
DZD: 0.6212 RUB
GBP: 105.9185 RUB
AMD: 0.2122 RUB
BHD: 215.8802 RUB
BYN: 27.2673 RUB
BGN: 47.7004 RUB
BOB: 11.7494 RUB
BRL: 15.0787 RUB
HUF: 0.2406 RUB
VND: 0.0032 RUB
HKD: 10.4597 RUB
GEL: 29.9489 RUB
DKK: 12.4961 RUB
AED: 22.1071 RUB
USD: 81.1885 RUB
EUR: 93.5131 RUB
EGP: 1.7138 RUB
INR: 0.9160 RUB
IDR: 0.0049 RUB
IRR: 0.0001 RUB
KZT: 0.1554 RUB
CAD: 57.6214 RUB
QAR: 22.3045 RUB
KGS: 0.9284 RUB
CNY: 11.3362 RUB
CUP: 3.3828 RUB
MDL: 4.7402 RUB
MNT: 0.0227 RUB
NGN: 0.0566 RUB
NZD: 45.7944 RUB
NOK: 7.9558 RUB
OMR: 211.1534 RUB
PLN: 21.8890 RUB
SAR: 21.6503 RUB
RON: 18.3311 RUB
XDR: 110.0129 RUB
SGD: 62.1135 RUB
TJS: 8.7546 RUB
THB: 2.4935 RUB
BDT: 0.6655 RUB
TRY: 1.9311 RUB
TMT: 23.1967 RUB
UZS: 0.0068 RUB
UAH: 1.9297 RUB
CZK: 3.8277 RUB
SEK: 8.4917 RUB
CHF: 100.1462 RUB
ETB: 0.5305 RUB
RSD: 0.7959 RUB
ZAR: 4.6483 RUB
KRW: 0.0565 RUB
JPY: 0.5291 RUB
MMK: 0.0387 RUB
Успешно обработано 55 валют
Первоначальные курсы загружены (55 валют)
Уведомление 3 наблюдателей...
=== EMAIL УВЕДОМЛЕНИЕ ДЛЯ admin@example.com ===
Обновление курсов валют от 2025-11-06T12:00:53.183880:

AUD (Австралийский доллар): 52.7076 RUB
AZN (Азербайджанский манат): 47.7579 RUB
DZD (Алжирских динаров): 0.6212 RUB
GBP (Фунт стерлингов): 105.9185 RUB
AMD (Армянских драмов): 0.2122 RUB

==================================================
Изменения записаны в лог-файл: currency_changes.log

! ОБНОВЛЕНИЕ КУРСОВ ВАЛЮТ (2025-11-06T12:00:53.183880)
------------------------------------------------------------
* USD (Доллар США): 81.1885 RUB
* EUR (Евро): 93.5131 RUB
* GBP (Фунт стерлингов): 105.9185 RUB
* CNY (Юань): 11.3362 RUB
* JPY (Иен): 0.5291 RUB
------------------------------------------------------------
Данные успешно получены от ЦБ РФ
Получено XML данных: 9690 символов
Начало XML: <?xml version="1.0" encoding="windows-1251"?><ValCurs Date="06.11.2025" name="Foreign Currency Market"><Valute ID="R01010"><NumCode>036</NumCode><CharCode>AUD</CharCode><Nominal>1</Nominal><Name>Австр...
AUD: 52.7076 RUB
AZN: 47.7579 RUB
DZD: 0.6212 RUB
GBP: 105.9185 RUB
AMD: 0.2122 RUB
BHD: 215.8802 RUB
BYN: 27.2673 RUB
BGN: 47.7004 RUB
BOB: 11.7494 RUB
BRL: 15.0787 RUB
HUF: 0.2406 RUB
VND: 0.0032 RUB
HKD: 10.4597 RUB
GEL: 29.9489 RUB
DKK: 12.4961 RUB
AED: 22.1071 RUB
USD: 81.1885 RUB
EUR: 93.5131 RUB
EGP: 1.7138 RUB
INR: 0.9160 RUB
IDR: 0.0049 RUB
IRR: 0.0001 RUB
KZT: 0.1554 RUB
CAD: 57.6214 RUB
QAR: 22.3045 RUB
KGS: 0.9284 RUB
CNY: 11.3362 RUB
CUP: 3.3828 RUB
MDL: 4.7402 RUB
MNT: 0.0227 RUB
NGN: 0.0566 RUB
NZD: 45.7944 RUB
NOK: 7.9558 RUB
OMR: 211.1534 RUB
PLN: 21.8890 RUB
SAR: 21.6503 RUB
RON: 18.3311 RUB
XDR: 110.0129 RUB
SGD: 62.1135 RUB
TJS: 8.7546 RUB
THB: 2.4935 RUB
BDT: 0.6655 RUB
TRY: 1.9311 RUB
TMT: 23.1967 RUB
UZS: 0.0068 RUB
UAH: 1.9297 RUB
CZK: 3.8277 RUB
SEK: 8.4917 RUB
CHF: 100.1462 RUB
ETB: 0.5305 RUB
RSD: 0.7959 RUB
ZAR: 4.6483 RUB
KRW: 0.0565 RUB
JPY: 0.5291 RUB
MMK: 0.0387 RUB
Успешно обработано 55 валют
Изменения в курсах валют не обнаружены
INFO:     Shutting down
Мониторинг курсов валют остановлен
Приложение остановлено
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [85772]

Process finished with exit code 0

```

## Заключение

Реализованная система успешно демонстрирует:

* Корректную работу паттерна "Наблюдатель" в асинхронной среде
* Безопасное взаимодействие с внешним API
* Эффективную обработку и валидацию финансовых данных
* Современные подходы к разработке на FastAPI
* Масштабируемую и поддерживаемую архитектуру
* Real-time обновления через WebSocket для веб-клиентов
**WebSocket Observer** обеспечивает мгновенную доставку обновлений всем подключенным клиентам, а **веб-интерфейс** предоставляет удобный способ визуализации данных в реальном времени.
