import traceback
from datetime import datetime, timezone
from tkinter import ttk, scrolledtext, messagebox

import openmeteo_requests
import requests
import requests_cache
from openmeteo_requests.Client import OpenMeteoRequestsError
from retry_requests import retry


class LocationNotFoundError(ValueError):
    """The geocoding service could not find the requested location."""


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

    def __init__(self, app):
        self.app = app
        cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.openmeteo = openmeteo_requests.Client(session=retry_session)

    def weather(self):
        self.app.clear()
        self.app.setup_grid()

        ttk.Label(self.app.container, text="Enter city", style="My.TLabel").grid(
            row=0, column=1, pady=(60, 20), sticky="W"
        )
        city_entry = ttk.Entry(self.app.container)
        city_entry.grid(row=1, column=1)

        ttk.Label(self.app.container, text="Enter country code", style="My.TLabel").grid(
            row=2, column=1, pady=20, sticky="W"
        )
        cc_entry = ttk.Entry(self.app.container)
        cc_entry.grid(row=3, column=1)

        ttk.Button(
            self.app.container,
            text="Submit",
            style="My.TButton",
            command=lambda: self.view_weather(city_entry.get(), cc_entry.get()),
        ).grid(row=4, column=1, pady=20)

        ttk.Button(
            self.app.container,
            text="Back",
            command=lambda: self.app.start_page(),
        ).grid(row=6, column=1, pady=20)

    def view_weather(self, city, country_code):
        city = city.strip()
        country_code = country_code.strip().upper()

        if not city:
            messagebox.showerror(
                "Invalid city", "Please enter a city name.", parent=self.app
            )
            return

        if (
            len(country_code) != 2
            or not country_code.isascii()
            or not country_code.isalpha()
        ):
            messagebox.showerror(
                "Invalid country code",
                "Please enter a two-letter country code, such as AU or US.",
                parent=self.app,
            )
            return

        try:
            latitude, longitude, city_name = self.get_location(city, country_code)
            weather = self.fetch_weather(latitude, longitude)
            current = self.get_current_weather(weather, city_name)
            hourly = self.get_hourly_forecast(weather)
            daily = self.get_daily_forecast(weather)

        except requests.exceptions.Timeout:
            message = "The weather request timed out. Please try again."

        except requests.exceptions.ConnectionError:
            message = "Could not connect to the weather service. Check your internet connection and try again."

        except (requests.exceptions.RequestException, OpenMeteoRequestsError):
            message = "The weather service could not complete the request. Please try again later."

        except LocationNotFoundError as error:
            message = str(error)

        except (ValueError, KeyError, IndexError, TypeError, AttributeError):
            message = "The weather service returned incomplete or invalid data. Please try again later."

        except Exception:
            traceback.print_exc()
            message = "An unexpected error occurred while loading the weather. Please try again."

        else:
            self.display_weather(current, hourly, daily)
            return

        messagebox.showerror("Weather error", message, parent=self.app)

    def display_weather(self, current, hourly, daily):
        for widget in self.app.container.grid_slaves(row=5, column=1):
            widget.destroy()
        text_box = scrolledtext.ScrolledText(self.app.container, height=12)
        text_box.grid(row=5, column=1, pady=10)

        text_box.insert("end", "CURRENT WEATHER:\n")
        for c in current:
            text_box.insert("end", c + "\n")

        text_box.insert("end", "\nHOURLY FORECAST:\n")
        for h in hourly:
            text_box.insert("end", h + "\n")

        text_box.insert("end", "\nDAILY FORECAST:\n")
        for d in daily:
            text_box.insert("end", d + "\n")

        text_box.configure(state="disabled")

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
            raise LocationNotFoundError(
                f"No location found for {city}, {country_code}. Check the city and country code."
            )

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
        return self.openmeteo.weather_api(self.FORECAST_URL, params=params, timeout=10)[
            0
        ]

    def get_current_weather(self, weather, city_name):
        now = datetime.now()
        current = weather.Current()
        temperature = round(current.Variables(0).Value())
        weather_code = int(current.Variables(1).Value())
        description = self.WEATHER_CODES.get(weather_code, "Unknown weather condition")

        current_f = [
            f"\nCurrent date: {now.date()}",
            f"Current time: {now.strftime('%H:%M:%S')}",
            f"Current day: {now.strftime('%A')}",
            f"Current city: {city_name}",
            f"Current temperature: {temperature} deg C",
            f"Current weather: {description}",
        ]

        return current_f

    def get_hourly_forecast(self, weather):
        now = datetime.now()
        hourly = weather.Hourly()
        temperatures = hourly.Variables(0).ValuesAsNumpy()
        hourly_f = []

        for index, temperature in enumerate(temperatures):
            forecast_time = self.local_api_time(
                hourly.Time(), hourly.Interval(), index, weather.UtcOffsetSeconds()
            )

            if forecast_time.date() == now.date() and forecast_time.hour >= now.hour:
                hourly_f.append(
                    f"{forecast_time.strftime('%H:%M')}: {round(temperature)} deg C"
                )

        return hourly_f

    def get_daily_forecast(self, weather):
        daily = weather.Daily()
        temperatures = daily.Variables(0).ValuesAsNumpy()
        daily_f = []

        for index, temperature in enumerate(temperatures):
            forecast_date = self.local_api_time(
                daily.Time(), daily.Interval(), index, weather.UtcOffsetSeconds()
            )
            daily_f.append(
                f"{forecast_date.strftime('%a')}: {round(temperature)} deg C"
            )

        return daily_f

    def local_api_time(self, start_time, interval, index, utc_offset_seconds):
        timestamp = start_time + utc_offset_seconds + (interval * index)
        return datetime.fromtimestamp(timestamp, timezone.utc)
