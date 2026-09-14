import traceback
from tkinter import ttk, scrolledtext, messagebox

import requests


class CryptoClient:
    API_URL = "https://api.coingecko.com/api/v3/coins/markets"

    def __init__(self, app):
        self.app = app

    def get_top_coins(self):
        response = requests.get(
            self.API_URL,
            params={
                "vs_currency": "aud",
                "order": "market_cap_desc",
                "per_page": 10,
                "page": 1,
                "sparkline": "false",
            },
            timeout=10,
        )
        response.raise_for_status()
        coins = response.json()

        if not isinstance(coins, list) or not all(
            isinstance(coin, dict)
            and isinstance(coin.get("name"), str)
            and coin["name"].strip()
            and "current_price" in coin
            and (
                coin["current_price"] is None
                or type(coin["current_price"]) in (int, float)
            )
            for coin in coins
        ):
            raise ValueError("The crypto service returned incomplete or invalid data.")

        return coins

    def crypto(self):
        self.app.clear()
        self.app.setup_grid()

        text_box = scrolledtext.ScrolledText(self.app.container, height=15)
        text_box.grid(row=1, column=1, pady=(60, 20))

        ttk.Button(
            self.app.container,
            command=lambda: self.app.start_page(),
            text="Back",
        ).grid(row=2, column=1, pady=20)

        try:
            coins = self.get_top_coins()

        except requests.exceptions.Timeout:
            message = "The crypto request timed out. Please try again."

        except requests.exceptions.ConnectionError:
            message = "Could not connect to the crypto service. Check your internet connection and try again."

        except requests.exceptions.HTTPError as error:
            status = error.response.status_code if error.response is not None else None

            if status == 429:
                message = (
                    "The crypto request limit has been reached. Please try again later."
                )
            else:
                message = "The crypto service could not complete the request. Please try again later."

        except requests.exceptions.JSONDecodeError:
            message = (
                "The crypto service returned invalid data. Please try again later."
            )

        except requests.exceptions.RequestException:
            message = "The crypto request failed. Please try again later."

        except (ValueError, KeyError, TypeError):
            message = "The crypto service returned incomplete or invalid data. Please try again later."

        except Exception:
            traceback.print_exc()
            message = "An unexpected error occurred while loading crypto prices. Please try again."

        else:
            if not coins:
                text_box.insert("end", "No cryptocurrency prices found.\n")

            for coin in coins:
                name = coin["name"]
                price = coin["current_price"]
                price_text = "Price unavailable" if price is None else f"${price:,} AUD"
                text_box.insert("end", f"{name}: {price_text}\n")

            text_box.config(state="disabled")
            return

        text_box.insert("end", message + "\n")
        text_box.config(state="disabled")
        messagebox.showerror("Crypto error", message, parent=self.app)
