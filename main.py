from datetime import datetime, timezone

import openmeteo_requests
import requests
import requests_cache

from retry_requests import retry


class WeatherClient:
    DEFAULT_CITY = "Perth"
    DEFAULT_COUNTRY_CODE = "AU"

    GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
    FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

    WEATHER_CODES = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        56: "Light freezing drizzle",
        57: "Dense freezing drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        66: "Light freezing rain",
        67: "Heavy freezing rain",
        71: "Slight snowfall",
        73: "Moderate snowfall",
        75: "Heavy snowfall",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }

    def __init__(self):
        cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.openmeteo = openmeteo_requests.Client(session=retry_session)

    def get_weather(self):
        try:
            city = self.ask("Enter city", self.DEFAULT_CITY)
            country_code = self.ask(
                "Enter country code", self.DEFAULT_COUNTRY_CODE
            ).upper()

            latitude, longitude, city_name = self.get_location(city, country_code)
            weather = self.fetch_weather(latitude, longitude)

            self.print_current_weather(weather, city_name)
            self.print_hourly_forecast(weather)
            self.print_daily_forecast(weather)

        except requests.RequestException as error:
            print(f"Could not get weather data: {error}")

        except (KeyError, IndexError, ValueError) as error:
            print(f"Could not process weather data: {error}")

    def ask(self, prompt, default):
        answer = input(f"{prompt} ({default}): ").strip()
        return answer or default

    def get_location(self, city, country_code):
        params = {
            "name": city,
            "count": 1,
            "language": "en",
            "format": "json",
            "countryCode": country_code,
        }
        response = requests.get(self.GEOCODING_URL, params=params, timeout=10)
        response.raise_for_status()

        results = response.json().get("results", [])
        if not results:
            raise ValueError(f"No location found for {city}, {country_code}.")

        location = results[0]
        return location["latitude"], location["longitude"], location.get("name", city)

    def fetch_weather(self, latitude, longitude):
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": ["temperature_2m", "weather_code"],
            "hourly": "temperature_2m",
            "daily": "temperature_2m_mean",
            "timezone": "auto",
        }
        return self.openmeteo.weather_api(self.FORECAST_URL, params=params)[0]

    def print_current_weather(self, weather, city_name):
        now = datetime.now()
        current = weather.Current()
        temperature = round(current.Variables(0).Value())
        weather_code = int(current.Variables(1).Value())
        description = self.WEATHER_CODES.get(weather_code, "Unknown weather condition")

        print(f"\nCurrent date: {now.date()}")
        print(f"Current time: {now.strftime('%H:%M:%S')}")
        print(f"Current day: {now.strftime('%A')}")
        print(f"Current city: {city_name}")
        print(f"Current temperature: {temperature} deg C")
        print(f"Current weather: {description}")

    def print_hourly_forecast(self, weather):
        now = datetime.now()
        hourly = weather.Hourly()
        temperatures = hourly.Variables(0).ValuesAsNumpy()

        print("\nToday's hourly forecast")
        for index, temperature in enumerate(temperatures):
            forecast_time = self.local_api_time(
                hourly.Time(), hourly.Interval(), index, weather.UtcOffsetSeconds()
            )

            if forecast_time.date() == now.date() and forecast_time.hour >= now.hour:
                print(f"{forecast_time.strftime('%H:%M')}: {round(temperature)} deg C")

    def print_daily_forecast(self, weather):
        daily = weather.Daily()
        temperatures = daily.Variables(0).ValuesAsNumpy()

        print("\nDaily forecast")
        for index, temperature in enumerate(temperatures):
            forecast_date = self.local_api_time(
                daily.Time(), daily.Interval(), index, weather.UtcOffsetSeconds()
            )
            print(f"{forecast_date.strftime('%a')}: {round(temperature)} deg C")

    def local_api_time(self, start_time, interval, index, utc_offset_seconds):
        timestamp = start_time + utc_offset_seconds + (interval * index)
        return datetime.fromtimestamp(timestamp, timezone.utc)


class NewsClient:
    def __init__(self):
        self.API_KEY = "0_g2C9WqwLvPZxY-rfys0Z7PAzEsGHxaL0Ge-SMOt6ZdYUE7"
        self.API_URL = "https://api.currentsapi.services/v1/latest-news"

    def get_country(self):
        default = "au"
        country_code = input("Enter country code (au): ").lower().strip()

        return country_code or default

    def get_news(self):
        res = requests.get(
            self.API_URL,
            params={"country": self.get_country()},
            headers={"Authorization": f"Bearer {self.API_KEY}"},
        )
        try:
            res.raise_for_status()
            return res.json()

        except requests.RequestException as e:
            print(f"Could not fetch news: {e}")
            return {}

    def print_news(self):
        j = self.get_news()
        news = j.get("news", []) if isinstance(j, dict) else []

        for article in news:
            title = article.get("title", "No title")
            description = article.get("description", "No description")
            author = article.get("author", "Unknown")

            print("Title: " + title)
            print("Author: " + author + "\n")
            print("Description: " + description + "\n")
            print("***************************************************")


class CryptoClient:
    API_URL = "https://api.coingecko.com/api/v3/coins/markets"

    def ask(self, prompt, default):
        answer = input(f"{prompt} ({default}): ")
        return answer or default

    def get_top_coins(self):
        limit = self.ask("How many top coins?", "10")
        try:
            limit_int = int(limit)
            if limit_int <= 0:
                raise ValueError("limit must be positive")

        except ValueError:
            print("Invalid number for top coins, using 10.")
            limit_int = 10

        try:
            response = requests.get(
                self.API_URL,
                params={
                    "vs_currency": "aud",
                    "order": "market_cap_desc",
                    "per_page": limit_int,
                    "page": 1,
                    "sparkline": "false",
                },
                timeout=10,
            )
            response.raise_for_status()
            return response.json()

        except requests.RequestException as e:
            print(f"Could not fetch crypto data: {e}")
            return []

    def print_top_coins(self):
        j = self.get_top_coins()
        for c in j:
            coin = c["name"]
            price = c["current_price"]

            print(f"{coin}: ${price} AUD")


def main():
    weather = WeatherClient()
    news = NewsClient()
    crypto = CryptoClient()

    try:
        choice_str = input("Enter 1 for Weather, 2 for News, 3 for Crypto: ").strip()
        if not choice_str:
            print("No choice entered. Exiting.")
            return
        try:
            choice = int(choice_str)
        except ValueError:
            print("Invalid choice. Please enter 1, 2, or 3.")
            return

        if choice == 1:
            try:
                weather.get_weather()
            except Exception as e:
                print(f"Weather operation failed: {e}")

        elif choice == 2:
            try:
                news.print_news()
            except Exception as e:
                print(f"News operation failed: {e}")

        elif choice == 3:
            try:
                crypto.print_top_coins()
            except Exception as e:
                print(f"Crypto operation failed: {e}")

        else:
            print("Choice out of range. Enter 1, 2 or 3.")

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")

    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
