"""
FakeWeather API client.
Симулирует работу с OpenWeather API (для учебных целей).
"""
import random

class FakeWeather:

    def __init__(self, api_key: str = "demo"):
        self.api_key = api_key

    def get_weather(self, city: str) -> dict:
        """Возвращает случайную погоду для города"""
        return {
            "city": city,
            "temperature": round(random.uniform(-10, 35), 1),
            "condition": random.choice(["sunny", "cloudy", "rainy", "snowy"]),
        }
