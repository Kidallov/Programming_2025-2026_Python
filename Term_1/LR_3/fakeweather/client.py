import random

class FakeWeatherClient:
    def __init__(self, seed=None):
        if seed is not None:
            random.seed(seed)

    def get_current_weather(self, city: str, units: str = "metric", lang: str = "en") -> dict:
        """Имитация получения погоды."""
        temps = {"metric": (0, 30), "imperial": (30, 100)}
        descriptions = {
            "en": ["clear sky", "rain", "cloudy", "snow"],
            "ru": ["ясно", "дождь", "облачно", "снег"]
        }

        temp_range = temps.get(units, (0, 30))
        description_list = descriptions.get(lang, descriptions["en"])

        return {
            "name": city,
            "main": {"temp": random.randint(*temp_range)},
            "weather": [{"description": random.choice(description_list)}]
        }
