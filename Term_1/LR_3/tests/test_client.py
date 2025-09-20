from fakeweather import FakeWeatherClient

def test_weather():
    client = FakeWeatherClient(seed=1)
    data = client.get_current_weather("London")
    assert "name" in data
    assert "main" in data
    assert "weather" in data
