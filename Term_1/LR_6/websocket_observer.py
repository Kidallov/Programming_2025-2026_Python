from observer import Observer
from typing import Dict, Any, Set
import json

class WebsocketObserver(Observer):

    def __init__(self):
        self.connections: Set = set()

    async def update(self, currency_data: Dict[str, Any]):
        if self.connections:
            message = json.dumps({
                "type": "currency_update",
                "data": currency_data,
                "timestamp": currency_data.get('timestamp')
            }, ensure_ascii = False)

            for connection in self.connections:
                try:
                    await connection.send_text(message)
                except Exception as e:
                    print(f"Error sending message: {e}")
        else:
            print("Нет подключенных WebSocket клиентов")

    def add_connection(self, websocket):
        self.connections.add(websocket)
        print(f"WebSocket клиент подключен. Всего: {len(self.connections)}")

    def remove_connection(self, websocket):
        if websocket in self.connections:
            self.connections.remove(websocket)
            print(f"WebSocket клиент отключен. Всего: {len(self.connections)}")
