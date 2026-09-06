import requests

import tkinter as tk
from tkinter import ttk


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
