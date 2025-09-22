from src import FakeWeather

def test_get_weather():
    api = FakeWeather()
    result = api.get_weather("Moscow")
    assert "city" in result
    assert "temperature" in result
    assert "condition" in result
