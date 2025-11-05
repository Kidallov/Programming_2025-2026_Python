from observer import Observer
from typing import Dict, Any
import json

class EmailNotifier(Observer):

    def __init__(self, email: str):
        self.email = email

    async def update(self, currency_data: Dict[str, Any]):
        timestamp = currency_data.get('timestamp', 'N/A')
        rates = currency_data.get('rates', {})

        message = f"Обновление курсов валют от {timestamp}:\n\n"
        for code, data in list(rates.items())[:5]:  # Показываем только первые 5 валют
            message += f"{code} ({data['name']}): {data['rate']:.4f} RUB\n"

        print(f"=== EMAIL УВЕДОМЛЕНИЕ ДЛЯ {self.email} ===")
        print(message)
        print("=" * 50)

class LoggerObserver(Observer):

    def __init__(self, log_file: str = "currency_changes.log"):
        self.log_file = log_file

    async def update(self, currency_data: Dict[str, Any]):
        timestamp = currency_data.get('timestamp', 'N/A')
        rates = currency_data.get('rates', {})

        changes = {}
        for code, data in rates.items():
            changes[code] = {
                'name': data['name'],
                'rate': data['rate'],
                'nominal': data['nominal']
            }

        log_entry = {
            'timestamp': timestamp,
            'changes': changes
        }

        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        print(f"Изменения записаны в лог-файл: {self.log_file}")

class ConsoleDisplay(Observer):
    def __init__(self, tracked_currencies: list = None):
        self.tracked_currencies = tracked_currencies or ['USD', 'EUR', 'GBP', 'CNY']

    async def update(self, currency_data: Dict[str, Any]):
        timestamp = currency_data.get('timestamp', 'N/A')
        rates = currency_data.get('rates', {})

        print(f"\n! ОБНОВЛЕНИЕ КУРСОВ ВАЛЮТ ({timestamp})")
        print("-" * 60)

        for currency in self.tracked_currencies:
            if currency in rates:
                data = rates[currency]
                print(f"* {currency} ({data['name']}): {data['rate']:.4f} RUB")

        print("-" * 60)



