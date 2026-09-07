import traceback
from tkinter import ttk, scrolledtext, messagebox

import requests


class NewsClient:
    def __init__(self, app):
        self.app = app
        self.API_KEY = "0_g2C9WqwLvPZxY-rfys0Z7PAzEsGHxaL0Ge-SMOt6ZdYUE7"
        self.API_URL = "https://api.currentsapi.services/v1/latest-news"

    def get_news(self, country_code="au"):
        res = requests.get(
            self.API_URL,
            params={"country": country_code},
            headers={"Authorization": f"Bearer {self.API_KEY}"},
            timeout=10,
        )
        res.raise_for_status()
        data = res.json()

        if (
            not isinstance(data, dict)
            or data.get("status", "ok") != "ok"
            or not isinstance(data.get("news"), list)
            or not all(isinstance(article, dict) for article in data["news"])
        ):
            raise ValueError("The news service returned incomplete or invalid data.")
        return data

    def news(self):
        self.app.clear()
        self.app.setup_grid()

        ttk.Label(
            self.app.container, style="My.TLabel", text="Enter Country Code"
        ).grid(row=0, column=1, pady=(60, 20), sticky="W")
        cc_entry = ttk.Entry(self.app.container)
        cc_entry.grid(row=1, column=1)

        ttk.Button(
            self.app.container,
            text="Submit",
            style="My.TButton",
            command=lambda: self.view_news(cc_entry.get()),
        ).grid(row=2, column=1, pady=20)

        ttk.Button(
            self.app.container, text="Back", command=lambda: self.app.start_page()
        ).grid(row=4, column=1, pady=20)

    def view_news(self, country_code):
        country_code = country_code.strip().lower()

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
            data = self.get_news(country_code)

        except requests.exceptions.Timeout:
            message = "The news request timed out. Please try again."

        except requests.exceptions.ConnectionError:
            message = "Could not connect to the news service. Check your internet connection and try again."

        except requests.exceptions.HTTPError as error:
            status = error.response.status_code if error.response is not None else None

            if status in (401, 403):
                message = "The news service denied access. Check your API key and account permissions."

            elif status == 429:
                message = (
                    "The news request limit has been reached. Please try again later."
                )

            else:
                message = "The news service could not complete the request. Please try again later."

        except requests.exceptions.JSONDecodeError:
            message = "The news service returned invalid data. Please try again later."

        except requests.exceptions.RequestException:
            message = "The news request failed. Please try again later."

        except (ValueError, KeyError, TypeError):
            message = "The news service returned incomplete or invalid data. Please try again later."

        except Exception:
            traceback.print_exc()
            message = (
                "An unexpected error occurred while loading the news. Please try again."
            )

        else:
            self.display_news(data["news"])
            return

        messagebox.showerror("News error", message, parent=self.app)

    def display_news(self, news):
        for widget in self.app.container.grid_slaves(row=3, column=1):
            widget.destroy()

        text_box = scrolledtext.ScrolledText(self.app.container, height=15)
        text_box.grid(row=3, column=1, pady=10)

        if not news:
            text_box.insert("end", "No news articles found for this country.\n")

        for article in news:
            title = article.get("title", "No title")
            description = article.get("description", "No description")
            author = article.get("author", "Unknown")

            text_box.insert("end", f"Title: {title}\n")
            text_box.insert("end", f"Author: {author}\n\n")
            text_box.insert("end", f"Description: {description}\n")
            text_box.insert(
                "end",
                "********************************************************************************\n\n",
            )
        text_box.config(state="disabled")
