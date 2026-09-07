import tkinter as tk
import traceback
from tkinter import ttk, messagebox


class App(tk.Tk):
    def __init__(self):
        super().__init__()

        try:
            self.setup()

        except Exception as error:
            traceback.print_exc()
            messagebox.showerror(
                "Startup error",
                f"The application could not start.\n\n{error}",
                parent=self,
            )
            self.destroy()
            raise

    def setup(self):
        import weather
        import news
        import crypto

        self.title("Live Datas")
        self.geometry("900x600")

        s = ttk.Style()

        s.theme_use("clam")
        s.configure("My.TButton", background="#E48A00", foreground="white")
        s.map("My.TButton", background=[("active", "#E48A00")])

        s.configure("My.TFrame", background="#02606F")
        s.configure("My.TLabel", background="#02606F", foreground="#B0B0B0")

        self.container = ttk.Frame(self, style="My.TFrame")
        self.container.pack(fill="both", expand=True)

        self.Weather = weather.WeatherClient(self)
        self.News = news.NewsClient(self)
        self.Crypto = crypto.CryptoClient()

        self.start_page()

    def report_callback_exception(self, exc_type, error, tb):
        traceback.print_exception(exc_type, error, tb)
        messagebox.showerror(
            "Application error",
            f"The action could not be completed. Please try again.\n\n{error}",
            parent=self,
        )

    def clear(self):
        for widget in self.container.winfo_children():
            widget.destroy()

        for col in range(self.container.grid_size()[0]):
            self.container.columnconfigure(col, weight=0)
        for row in range(self.container.grid_size()[1]):
            self.container.rowconfigure(row, weight=0)

    def setup_grid(self):
        self.container.columnconfigure(0, weight=1)
        self.container.columnconfigure(1, weight=0)
        self.container.columnconfigure(2, weight=1)

    def start_page(self):
        self.clear()
        self.setup_grid()

        self.container.rowconfigure(4, weight=1)

        ttk.Button(
            self.container,
            command=lambda: self.Weather.weather(),
            text="Check Live Weather",
            style="My.TButton",
        ).grid(column=1, row=0, pady=(60, 20))

        ttk.Button(
            self.container,
            command=lambda: self.News.news(),
            text="Check Top Headlines",
            style="My.TButton",
        ).grid(column=1, row=1, pady=20)

        ttk.Button(
            self.container,
            # command=,
            text="Top Cryptocurrency Prices",
            style="My.TButton",
        ).grid(column=1, row=2, pady=20)

        ttk.Button(
            self.container,
            # command=,
            text="Back",
        ).grid(column=1, row=3, pady=20)


if __name__ == "__main__":
    app = App()
    app.mainloop()
