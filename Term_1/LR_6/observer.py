from abc import ABC, abstractmethod
from typing import List, Tuple, Dict, Any
import asyncio

# Интерфейс Наблюдателя
class Observer(ABC):
    @abstractmethod
    async def update(self, currency_data: Dict[str, Any]):
        pass

# Интерфейс Субъекта
class Subject(ABC):
    def __init__(self):
        self._observers: List[Observer] = []

    def attach(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)
            print(f"Наблюдатель {type(observer).__name__} зарегистрирован")

    def detach(self, observer: Observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)
            print(f"Наблюдатель {type(observer).__name__} удален")

    async def notify(self, currency_data: Dict[str, Any]) -> None:
        if not self._observers:
            print("Нет зарегистрированных наблюдателей")
            return
        print(f"Уведомление {len(self._observers)} наблюдателей...")

        tasks = [observer.update(currency_data) for observer in self._observers]
        await asyncio.gather(*tasks)