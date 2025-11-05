import aiohttp
import asyncio
from typing import Dict, Any
from datetime import datetime
import xml.etree.ElementTree as ET
import ssl
import urllib.request
import certifi
from observer import Subject

class CurrencyService(Subject):
    def __init__(self, update_interval: int = 60):
        super().__init__()
        self.update_interval = update_interval
        self.previous_rates: Dict[str, float] = {}
        self.current_rates: Dict[str, float] = {}
        self.is_running = False

    def has_changes(self) -> bool:

        if not self.previous_rates:
            return True

        for currency, currency_rate in self.current_rates.items():
            if currency in self.previous_rates:
                previous_rate = self.previous_rates[currency]
                if previous_rate != 0:
                    change = abs(previous_rate - currency_rate)
                    if change > 0:
                        return True
        return False

    async def fetch_currency_rates(self) -> Dict[str, Any]:
        url = 'https://www.cbr.ru/scripts/XML_daily.asp'

        try:
            ssl_context = ssl.create_default_context(cafile=certifi.where())

            connector = aiohttp.TCPConnector(ssl=ssl_context, keepalive_timeout=30, limit=100)

            timeout = aiohttp.ClientTimeout(total=30)

            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                async with session.get(url) as response:

                    if response.status == 200:
                        xml = await response.text()
                        print("Данные успешно получены от ЦБ РФ")

                        if len(xml) > 0:
                            print(f"Получено XML данных: {len(xml)} символов")
                            print(f"Начало XML: {xml[:200]}...")

                        return self.parse_xml_currency_rates(xml)

                    else:
                        print(f"Ошибка HTTP: {response.status}")
                        return {}

        except aiohttp.ClientSSLError as e:
            print(f"SSL ошибка: {e}")
            await self._diagnose_ssl_issue()
            return {}

        except aiohttp.ClientConnectorError as e:
            print(f"Ошибка подключения: {e}")
            return {}

        except asyncio.TimeoutError:
            print("Таймаут при подключении к серверу")
            return {}

        except Exception as e:
            print(f"Общая ошибка при получении данных: {e}")
            return {}

    async def _diagnose_ssl_issue(self):

        try:

            print("Диагностика SSL проблем...")
            cert_path = certifi.where()
            print(f"Путь к сертификатам: {cert_path}")

            context = ssl.create_default_context(cafile=certifi.where())

            with urllib.request.urlopen(
                    "https://www.cbr.ru/scripts/XML_daily.asp",
                    context=context,
                    timeout=10
            ) as response:
                print("Диагностика: Прямое подключение работает!")

        except Exception as e:
            print(f"Диагностика показала проблему: {e}")
            print("Попробуйте обновить сертификаты: pip install --upgrade certifi")

    def parse_xml_currency_rates(self, xml: str) -> Dict[str, Any]:

        try:
            root = ET.fromstring(xml)
            rates = {}
            timestamp = datetime.now().isoformat()
            date_str = root.get('Date', '')

            for valute in root.findall('Valute'):
                try:
                    char_code_elem = valute.find('CharCode')
                    value_elem = valute.find('Value')
                    nominal_elem = valute.find('Nominal')
                    name_elem = valute.find('Name')

                    if None in [char_code_elem, value_elem, nominal_elem, name_elem]:
                        print(f"Пропущена валюта из-за отсутствующих данных")
                        continue

                    char_code = char_code_elem.text
                    value_text = value_elem.text
                    nominal_text = nominal_elem.text
                    name = name_elem.text

                    if not all([char_code, value_text, nominal_text, name]):
                        print(f"Пропущена валюта {char_code} из-за пустых значений")
                        continue

                    try:
                        value_clean = value_text.replace(',', '.')
                        value = float(value_clean)
                        nominal = int(nominal_text)

                        if value <= 0 or nominal <= 0:
                            print(f"Некорректные значения для {char_code}: value={value}, nominal={nominal}")
                            continue

                        rate_per_unit = value / nominal

                        rates[char_code] = {
                            'rate': rate_per_unit,
                            'name': name,
                            'nominal': nominal,
                            'value': value,
                            'original_value': value_text
                        }

                        print(f"{char_code}: {rate_per_unit:.4f} RUB")

                    except ValueError as ve:
                        print(f"Ошибка преобразования чисел для {char_code}: value='{value_text}', nominal='{nominal_text}' - {ve}")
                        continue

                except Exception as e:
                    print(f"Ошибка обработки валюты: {e}")
                    continue

            result = {
                'timestamp': timestamp,
                'date': date_str,
                'rates': rates,
                'source': 'CBRF',
                'total_currencies': len(rates)
            }

            print(f"Успешно обработано {len(rates)} валют")
            return result

        except ET.ParseError as e:
            print(f"Ошибка при парсинге XML: {e}")
            return {}
        except Exception as e:
            print(f"Неожиданная ошибка при парсинге XML: {e}")
            return {}

    async def start_monitoring(self):

        self.is_running = True
        print(f"Мониторинг курсов валют запущен (интервал: {self.update_interval} сек)...")

        initial_data = await self.fetch_currency_rates()

        if initial_data and 'rates' in initial_data and initial_data['rates']:
            self.current_rates = {
                code: data['rate'] for code, data in initial_data['rates'].items()
            }
            print(f"Первоначальные курсы загружены ({len(self.current_rates)} валют)")

            await self.notify(initial_data)
        else:
            print("Не удалось загрузить первоначальные курсы")

        while self.is_running:
            try:
                currency_data = await self.fetch_currency_rates()

                if currency_data and 'rates' in currency_data and currency_data['rates']:
                    self.previous_rates = self.current_rates.copy()

                    self.current_rates = {
                        code: data['rate'] for code, data in currency_data['rates'].items()
                    }

                    if self.has_changes():
                        print(f"Обнаружены изменения курсов. Уведомляем наблюдателей...")
                        await self.notify(currency_data)
                    else:
                        print("Изменения в курсах валют не обнаружены")

                else:
                    print("Не удалось получить данные о курсах валют")

                await asyncio.sleep(self.update_interval)

            except Exception as e:
                print(f"Ошибка в мониторинге: {e}")
                await asyncio.sleep(self.update_interval)

    def stop_monitoring(self):
        self.is_running = False
        print("Мониторинг курсов валют остановлен")