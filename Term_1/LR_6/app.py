from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import asyncio
from currency_service import CurrencyService
from observers import EmailNotifier, LoggerObserver, ConsoleDisplay
from websocket_observer import WebsocketObserver
import uvicorn
from contextlib import asynccontextmanager
from fastapi.responses import Response, HTMLResponse
import json
from datetime import datetime

websocket_observer = WebsocketObserver()
currency_service = CurrencyService(update_interval=10)

@asynccontextmanager
async def lifespan(app: FastAPI):

    currency_service.attach(EmailNotifier("admin@example.com"))
    currency_service.attach(LoggerObserver())
    currency_service.attach(ConsoleDisplay(['USD', 'EUR', 'GBP', 'CNY', 'JPY']))
    currency_service.attach(websocket_observer)

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

@app.websocket("/ws/currency")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()
    websocket_observer.add_connection(websocket)

    if currency_service.current_rates:
        current_data = {
            "timestamp": datetime.now().isoformat(),
            "date": "текущие",
            "rates": {code: {
                'rate': rate,
                'name': 'текущие данные',
                'nominal': 1,
                'value': rate,
                'original_value': str(rate)
            } for code, rate in currency_service.current_rates.items()},
            "source": "CBRF",
            "total_currencies": len(currency_service.current_rates)
        }

        await websocket.send_text(json.dumps({
            "type": "currency_update",
            "data": current_data
        }, ensure_ascii=False))

    try:
        while True:
            data = await websocket.receive_text()
            await handle_websocket_message(data, websocket)
    except WebSocketDisconnect:
        websocket_observer.remove_connection(websocket)

async def handle_websocket_message(message: str, websocket: WebSocket):

    try:

        data = json.loads(message)

        if data.get('type') == 'subscribe':
            await websocket.send_text(json.dumps({
                "type": "subscribe",
                "message": "Вы подписаны на обновления курсов валют"
            }, ensure_ascii=False))

        elif data.get('type') == 'force_update':
            currency_data = await currency_service.fetch_currency_rates()
            if currency_data:
                await websocket_observer.update(currency_data)

    except json.JSONDecodeError:
        pass
@app.get("/")
async def root():
    with open("index.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)

@app.get("/current-rates")
async def get_current_rates():

    if currency_service:

        currency_data = await currency_service.fetch_currency_rates()

        if currency_data:

            formatted_json = json.dumps(currency_data, ensure_ascii=False, indent=2)

            return Response(
                content=formatted_json,
                media_type="application/json; charset=utf-8",
                headers={"Content-Disposition": "inline"}
            )
    return {"error": "No currency data found"}

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

    return {
        "is_monitoring": currency_service.is_running,
        "total_observers": len(currency_service._observers),
        "update_interval": currency_service.update_interval,
        "tracked_currencies_count": len(currency_service.current_rates)
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
