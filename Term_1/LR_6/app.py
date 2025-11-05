from fastapi import FastAPI
from typing import List
import asyncio

from uvicorn import lifespan

from currency_service import CurrencyService
from observers import EmailNotifier, LoggerObserver, ConsoleDisplay
import uvicorn
from contextlib import asynccontextmanager

currency_service = CurrencyService(update_interval=10)

@asynccontextmanager
async def lifespan(app: FastAPI):

    currency_service.attach(EmailNotifier("admin@example.com"))
    currency_service.attach(LoggerObserver())
    currency_service.attach(ConsoleDisplay(['USD', 'EUR', 'GBP', 'CNY', 'JPY']))

    asyncio.create_task(currency_service.start_monitoring())
    print("Приложение запущено и мониторинг активирован")

    yield

    if currency_service:
        currency_service.stop_monitoring()
    print("Приложение остановлено")

app = FastAPI(
    title="Currency Service",
    description="API для отслеживания курсов валют ЦБ РФ с использованием паттерна Наблюдатель",
    version="1.0.0",
    lifespan = lifespan
)

@app.get("/")
async def root():
    return {
        "message": "Currency Observer API",
        "status": "running",
        "update_interval_seconds": currency_service.update_interval
    }

@app.get("/current-rates")
async def get_current_rates():

    currency_data = await currency_service.fetch_currency_rates()
    return currency_data

@app.get("/rates/{currency_code}")
async def get_specific_rate(currency_code: str):

    currency_data = await currency_service.fetch_currency_rates()
    rates = currency_data.get('rates', {})

    if currency_code.upper() in rates:
        return {
            "currency": currency_code.upper(),
            "data": rates[currency_code.upper()]
        }
    else:
        return {"error": f"Валюта {currency_code} не найдена"}

@app.post('/observers/email')
async def register_email_observer(email: str):

    observer = EmailNotifier(email)
    currency_service.attach(observer)
    return {"message": f"Email наблюдатель для {email} зарегистрирован"}

@app.post("/observers/console")
async def register_console_observer(currencies: List[str] = None):

    observer = ConsoleDisplay(currencies)
    currency_service.attach(observer)
    return {"message": "Консольный наблюдатель зарегистрирован"}

@app.get("/status")
async def get_status():
    """Получить статус системы"""
    return {
        "is_monitoring": currency_service.is_running,
        "total_observers": len(currency_service._observers),
        "update_interval": currency_service.update_interval,
        "tracked_currencies_count": len(currency_service.current_rates)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)