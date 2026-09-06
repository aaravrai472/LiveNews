import requests

import tkinter
from tkinter import ttk


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
