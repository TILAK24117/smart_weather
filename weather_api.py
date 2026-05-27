"""
╔══════════════════════════════════════════════════════════════╗
║          SMART WEATHER FORECAST APPLICATION                  ║
║          Built with Python, Tkinter & OpenWeatherMap API     ║
╚══════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import requests
import json
import threading
from datetime import datetime, timezone
import math
from config.settings import API_KEY, BASE_URL, FORECAST_URL
from utils.helpers import (
    kelvin_to_celsius, meters_to_km, ms_to_kmh,
    unix_to_time, get_wind_direction, get_uv_label,
    get_aqi_label, get_weather_emoji
)


# ─── COLOR PALETTE ────────────────────────────────────────────
COLORS = {
    "bg_dark":      "#0D1117",
    "bg_card":      "#161B22",
    "bg_card2":     "#1C2230",
    "bg_input":     "#21262D",
    "accent_blue":  "#58A6FF",
    "accent_cyan":  "#39D353",
    "accent_warm":  "#F0883E",
    "accent_red":   "#FF7B72",
    "text_primary": "#E6EDF3",
    "text_muted":   "#8B949E",
    "text_dim":     "#484F58",
    "border":       "#30363D",
    "gradient_1":   "#1A1F2E",
    "gradient_2":   "#0D1117",
    "hot":          "#FF6B35",
    "cold":         "#4ECDC4",
    "mild":         "#58A6FF",
    "btn_hover":    "#1F6FEB",
}

WEATHER_EMOJIS = {
    "clear sky":         "☀️",
    "few clouds":        "🌤️",
    "scattered clouds":  "⛅",
    "broken clouds":     "🌥️",
    "overcast clouds":   "☁️",
    "light rain":        "🌦️",
    "moderate rain":     "🌧️",
    "heavy rain":        "⛈️",
    "thunderstorm":      "⛈️",
    "snow":              "❄️",
    "light snow":        "🌨️",
    "mist":              "🌫️",
    "fog":               "🌁",
    "haze":              "😶‍🌫️",
    "drizzle":           "🌂",
    "default":           "🌈",
}


class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("⛅ Smart Weather Forecast")
        self.geometry("920x720")
        self.minsize(800, 640)
        self.configure(bg=COLORS["bg_dark"])
        self.resizable(True, True)

        # Center window on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (920 // 2)
        y = (self.winfo_screenheight() // 2) - (720 // 2)
        self.geometry(f"920x720+{x}+{y}")

        self._setup_fonts()
        self._setup_styles()
        self._build_ui()
        self._bind_keys()

        self.current_data = None
        self.forecast_data = None
        self.search_history = []

    def _setup_fonts(self):
        self.font_title   = font.Font(family="Segoe UI", size=28, weight="bold")
        self.font_h1      = font.Font(family="Segoe UI", size=20, weight="bold")
        self.font_h2      = font.Font(family="Segoe UI", size=14, weight="bold")
        self.font_h3      = font.Font(family="Segoe UI", size=11, weight="bold")
        self.font_body    = font.Font(family="Segoe UI", size=11)
        self.font_small   = font.Font(family="Segoe UI", size=9)
        self.font_mono    = font.Font(family="Consolas",  size=11)
        self.font_search  = font.Font(family="Segoe UI", size=13)
        self.font_temp    = font.Font(family="Segoe UI", size=52, weight="bold")
        self.font_emoji   = font.Font(family="Segoe UI Emoji", size=48)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook",
            background=COLORS["bg_dark"],
            borderwidth=0,
            tabmargins=0)
        style.configure("TNotebook.Tab",
            background=COLORS["bg_card"],
            foreground=COLORS["text_muted"],
            padding=[20, 8],
            font=("Segoe UI", 10, "bold"),
            borderwidth=0)
        style.map("TNotebook.Tab",
            background=[("selected", COLORS["bg_card2"])],
            foreground=[("selected", COLORS["accent_blue"])])

    def _build_ui(self):
        # ── Top bar ──────────────────────────────────────────
        topbar = tk.Frame(self, bg=COLORS["bg_card"], pady=12)
        topbar.pack(fill="x", side="top")

        tk.Label(topbar, text="⛅ SmartWeather",
            font=self.font_h2,
            bg=COLORS["bg_card"],
            fg=COLORS["accent_blue"]).pack(side="left", padx=20)

        self.lbl_time = tk.Label(topbar,
            text="", font=self.font_small,
            bg=COLORS["bg_card"], fg=COLORS["text_muted"])
        self.lbl_time.pack(side="right", padx=20)
        self._tick_clock()

        # ── Search bar ───────────────────────────────────────
        search_frame = tk.Frame(self, bg=COLORS["bg_dark"], pady=18)
        search_frame.pack(fill="x", padx=30)

        search_inner = tk.Frame(search_frame, bg=COLORS["bg_input"],
            highlightbackground=COLORS["border"],
            highlightthickness=1)
        search_inner.pack(fill="x")

        tk.Label(search_inner, text="🔍", font=self.font_body,
            bg=COLORS["bg_input"], fg=COLORS["text_muted"],
            padx=10).pack(side="left")

        self.entry = tk.Entry(search_inner,
            font=self.font_search,
            bg=COLORS["bg_input"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["accent_blue"],
            relief="flat",
            bd=0)
        self.entry.pack(side="left", fill="x", expand=True, ipady=10)
        self.entry.insert(0, "Search city name...")
        self.entry.bind("<FocusIn>",  self._clear_placeholder)
        self.entry.bind("<FocusOut>", self._restore_placeholder)

        self.btn_search = tk.Button(search_inner,
            text="  Search  ",
            font=self.font_h3,
            bg=COLORS["accent_blue"],
            fg="white",
            activebackground=COLORS["btn_hover"],
            activeforeground="white",
            relief="flat",
            bd=0,
            padx=16, pady=10,
            cursor="hand2",
            command=self._start_search)
        self.btn_search.pack(side="right", padx=4, pady=4)

        # ── Status / spinner ─────────────────────────────────
        self.lbl_status = tk.Label(self,
            text="Enter a city name above to get started",
            font=self.font_body,
            bg=COLORS["bg_dark"],
            fg=COLORS["text_muted"])
        self.lbl_status.pack(pady=4)

        # ── Tabs ─────────────────────────────────────────────
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=30, pady=(6, 20))

        self.tab_now      = tk.Frame(self.notebook, bg=COLORS["bg_dark"])
        self.tab_forecast = tk.Frame(self.notebook, bg=COLORS["bg_dark"])
        self.tab_details  = tk.Frame(self.notebook, bg=COLORS["bg_dark"])
        self.tab_history  = tk.Frame(self.notebook, bg=COLORS["bg_dark"])

        self.notebook.add(self.tab_now,      text="  🌡  Current  ")
        self.notebook.add(self.tab_forecast, text="  📅  Forecast  ")
        self.notebook.add(self.tab_details,  text="  📊  Details  ")
        self.notebook.add(self.tab_history,  text="  🕑  History  ")

        self._build_tab_now()
        self._build_tab_forecast()
        self._build_tab_details()
        self._build_tab_history()

    # ── TAB 1: CURRENT WEATHER ────────────────────────────────
    def _build_tab_now(self):
        p = self.tab_now

        # Hero card
        self.hero = tk.Frame(p, bg=COLORS["bg_card"],
            highlightbackground=COLORS["border"],
            highlightthickness=1)
        self.hero.pack(fill="x", pady=(16,10), padx=4)

        left = tk.Frame(self.hero, bg=COLORS["bg_card"], padx=24, pady=20)
        left.pack(side="left", fill="both", expand=True)

        self.lbl_city_name = tk.Label(left, text="—",
            font=self.font_h1,
            bg=COLORS["bg_card"], fg=COLORS["text_primary"])
        self.lbl_city_name.pack(anchor="w")

        self.lbl_country = tk.Label(left, text="—",
            font=self.font_body,
            bg=COLORS["bg_card"], fg=COLORS["text_muted"])
        self.lbl_country.pack(anchor="w")

        self.lbl_condition = tk.Label(left, text="—",
            font=self.font_h2,
            bg=COLORS["bg_card"], fg=COLORS["accent_blue"])
        self.lbl_condition.pack(anchor="w", pady=(8,0))

        self.lbl_updated = tk.Label(left, text="",
            font=self.font_small,
            bg=COLORS["bg_card"], fg=COLORS["text_dim"])
        self.lbl_updated.pack(anchor="w")

        right = tk.Frame(self.hero, bg=COLORS["bg_card"], padx=24, pady=16)
        right.pack(side="right")

        self.lbl_emoji = tk.Label(right, text="🌈",
            font=self.font_emoji,
            bg=COLORS["bg_card"])
        self.lbl_emoji.pack()

        self.lbl_temp = tk.Label(right, text="—°C",
            font=self.font_temp,
            bg=COLORS["bg_card"], fg=COLORS["text_primary"])
        self.lbl_temp.pack()

        self.lbl_feels = tk.Label(right, text="",
            font=self.font_small,
            bg=COLORS["bg_card"], fg=COLORS["text_muted"])
        self.lbl_feels.pack()

        # Quick stats grid
        grid = tk.Frame(p, bg=COLORS["bg_dark"])
        grid.pack(fill="x", padx=4, pady=4)

        self.stat_cards = {}
        stats = [
            ("💧", "Humidity",    "hum",  "%"),
            ("💨", "Wind Speed",  "wind", " km/h"),
            ("🧭", "Wind Dir",    "wdir", ""),
            ("👁", "Visibility",  "vis",  " km"),
            ("🔼", "Pressure",    "pres", " hPa"),
            ("🌡", "Feels Like",  "feel", "°C"),
        ]
        for i, (icon, label, key, unit) in enumerate(stats):
            card = tk.Frame(grid, bg=COLORS["bg_card"],
                highlightbackground=COLORS["border"],
                highlightthickness=1,
                padx=16, pady=14)
            card.grid(row=i//3, column=i%3, padx=5, pady=5, sticky="nsew")
            grid.columnconfigure(i%3, weight=1)

            tk.Label(card, text=f"{icon}  {label}",
                font=self.font_small,
                bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w")

            val_lbl = tk.Label(card, text="—",
                font=self.font_h2,
                bg=COLORS["bg_card"], fg=COLORS["text_primary"])
            val_lbl.pack(anchor="w", pady=(4,0))

            self.stat_cards[key] = (val_lbl, unit)

    # ── TAB 2: 5-DAY FORECAST ─────────────────────────────────
    def _build_tab_forecast(self):
        p = self.tab_forecast

        tk.Label(p, text="5-Day Forecast",
            font=self.font_h2,
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"]).pack(anchor="w", padx=6, pady=(14,8))

        self.forecast_frame = tk.Frame(p, bg=COLORS["bg_dark"])
        self.forecast_frame.pack(fill="both", expand=True, padx=4)

        for i in range(5):
            self.forecast_frame.columnconfigure(i, weight=1)

        self.forecast_slots = []
        for i in range(5):
            card = tk.Frame(self.forecast_frame, bg=COLORS["bg_card"],
                highlightbackground=COLORS["border"],
                highlightthickness=1,
                padx=12, pady=16)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")

            lbl_day   = tk.Label(card, text="—", font=self.font_h3,
                bg=COLORS["bg_card"], fg=COLORS["accent_blue"])
            lbl_day.pack()

            lbl_date  = tk.Label(card, text="", font=self.font_small,
                bg=COLORS["bg_card"], fg=COLORS["text_dim"])
            lbl_date.pack()

            lbl_icon  = tk.Label(card, text="🌈",
                font=font.Font(family="Segoe UI Emoji", size=28),
                bg=COLORS["bg_card"])
            lbl_icon.pack(pady=8)

            lbl_hi    = tk.Label(card, text="—", font=self.font_h2,
                bg=COLORS["bg_card"], fg=COLORS["accent_warm"])
            lbl_hi.pack()

            lbl_lo    = tk.Label(card, text="—", font=self.font_body,
                bg=COLORS["bg_card"], fg=COLORS["cold"])
            lbl_lo.pack()

            lbl_cond  = tk.Label(card, text="—", font=self.font_small,
                bg=COLORS["bg_card"], fg=COLORS["text_muted"],
                wraplength=110, justify="center")
            lbl_cond.pack(pady=(6,0))

            lbl_hum   = tk.Label(card, text="", font=self.font_small,
                bg=COLORS["bg_card"], fg=COLORS["text_dim"])
            lbl_hum.pack()

            self.forecast_slots.append({
                "day": lbl_day, "date": lbl_date,
                "icon": lbl_icon, "hi": lbl_hi,
                "lo": lbl_lo, "cond": lbl_cond, "hum": lbl_hum
            })

    # ── TAB 3: DETAILED INFO ──────────────────────────────────
    def _build_tab_details(self):
        p = self.tab_details

        canvas = tk.Canvas(p, bg=COLORS["bg_dark"], highlightthickness=0)
        scroll = tk.Scrollbar(p, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        self.details_inner = tk.Frame(canvas, bg=COLORS["bg_dark"])
        win_id = canvas.create_window((0,0), window=self.details_inner, anchor="nw")

        def _resize(e):
            canvas.itemconfig(win_id, width=e.width)
        canvas.bind("<Configure>", _resize)
        self.details_inner.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self.detail_labels = {}
        rows = [
            ("🌅 Sun & Moon",   [("Sunrise","sunrise"),("Sunset","sunset"),("Day Length","daylen")]),
            ("🌊 Atmosphere",   [("Humidity","hum"),("Dew Point","dew"),("Pressure","pres"),("Cloud Cover","clouds")]),
            ("🌬 Wind",         [("Speed","wind"),("Direction","wdir"),("Gust","gust")]),
            ("👁 Visibility",   [("Distance","vis"),("UV Index","uvi"),("UV Risk","uvrisk")]),
            ("📍 Location",     [("Latitude","lat"),("Longitude","lon"),("Timezone","tz"),("Country","country")]),
        ]

        for section_title, fields in rows:
            sec = tk.Frame(self.details_inner, bg=COLORS["bg_card"],
                highlightbackground=COLORS["border"],
                highlightthickness=1,
                padx=20, pady=14)
            sec.pack(fill="x", padx=6, pady=(10,0))

            tk.Label(sec, text=section_title, font=self.font_h3,
                bg=COLORS["bg_card"], fg=COLORS["accent_blue"]).pack(anchor="w", pady=(0,8))

            for label, key in fields:
                row = tk.Frame(sec, bg=COLORS["bg_card"])
                row.pack(fill="x", pady=2)
                tk.Label(row, text=label, font=self.font_body, width=14,
                    bg=COLORS["bg_card"], fg=COLORS["text_muted"],
                    anchor="w").pack(side="left")
                lbl = tk.Label(row, text="—", font=self.font_mono,
                    bg=COLORS["bg_card"], fg=COLORS["text_primary"],
                    anchor="w")
                lbl.pack(side="left", padx=(12,0))
                self.detail_labels[key] = lbl

    # ── TAB 4: SEARCH HISTORY ─────────────────────────────────
    def _build_tab_history(self):
        p = self.tab_history

        header = tk.Frame(p, bg=COLORS["bg_dark"])
        header.pack(fill="x", padx=6, pady=(14,4))

        tk.Label(header, text="Recent Searches",
            font=self.font_h2,
            bg=COLORS["bg_dark"], fg=COLORS["text_primary"]).pack(side="left")

        tk.Button(header, text="🗑  Clear",
            font=self.font_small,
            bg=COLORS["bg_card"], fg=COLORS["text_muted"],
            activebackground=COLORS["accent_red"],
            relief="flat", bd=0, padx=10, pady=4,
            cursor="hand2",
            command=self._clear_history).pack(side="right")

        self.history_frame = tk.Frame(p, bg=COLORS["bg_dark"])
        self.history_frame.pack(fill="both", expand=True, padx=4)

        self.lbl_no_history = tk.Label(self.history_frame,
            text="No searches yet. Start by searching a city!",
            font=self.font_body,
            bg=COLORS["bg_dark"], fg=COLORS["text_muted"])
        self.lbl_no_history.pack(pady=40)

    # ── SEARCH LOGIC ──────────────────────────────────────────
    def _bind_keys(self):
        self.entry.bind("<Return>", lambda e: self._start_search())
        self.bind("<Escape>", lambda e: self.entry.focus())

    def _clear_placeholder(self, e):
        if self.entry.get() == "Search city name...":
            self.entry.delete(0, "end")
            self.entry.config(fg=COLORS["text_primary"])

    def _restore_placeholder(self, e):
        if not self.entry.get():
            self.entry.insert(0, "Search city name...")
            self.entry.config(fg=COLORS["text_muted"])

    def _start_search(self):
        city = self.entry.get().strip()
        if not city or city == "Search city name...":
            messagebox.showwarning("Input Required", "Please enter a city name.")
            return

        self.btn_search.config(state="disabled", text="  Loading...  ")
        self.lbl_status.config(text=f"🔄  Fetching weather for '{city}'...",
            fg=COLORS["accent_blue"])
        self.update()
        threading.Thread(target=self._fetch_weather, args=(city,), daemon=True).start()

    def _fetch_weather(self, city):
        try:
            # Current weather
            curr_r = requests.get(BASE_URL, params={
                "q": city, "appid": API_KEY, "units": "metric"
            }, timeout=10)

            if curr_r.status_code == 401:
                self.after(0, lambda: self._show_error(
                    "Invalid API Key", "Check your API key in config/settings.py"))
                return
            if curr_r.status_code == 404:
                self.after(0, lambda: self._show_error(
                    "City Not Found", f"'{city}' not found. Check spelling."))
                return

            curr_r.raise_for_status()
            curr = curr_r.json()

            # 5-day forecast
            fore_r = requests.get(FORECAST_URL, params={
                "q": city, "appid": API_KEY, "units": "metric", "cnt": 40
            }, timeout=10)
            fore = fore_r.json() if fore_r.ok else None

            self.current_data  = curr
            self.forecast_data = fore
            self.after(0, lambda: self._render_weather(curr, fore, city))

        except requests.exceptions.ConnectionError:
            self.after(0, lambda: self._show_error(
                "Connection Error", "No internet connection. Please check your network."))
        except requests.exceptions.Timeout:
            self.after(0, lambda: self._show_error(
                "Timeout", "Request timed out. Try again."))
        except Exception as ex:
            self.after(0, lambda: self._show_error("Error", str(ex)))

    def _render_weather(self, d, fore, city):
        temp    = round(d["main"]["temp"])
        feels   = round(d["main"]["feels_like"])
        hum     = d["main"]["humidity"]
        pres    = d["main"]["pressure"]
        wind    = round(ms_to_kmh(d["wind"]["speed"]))
        gust    = round(ms_to_kmh(d["wind"].get("gust", 0)))
        wdir    = get_wind_direction(d["wind"].get("deg", 0))
        vis     = round(meters_to_km(d.get("visibility", 0)))
        clouds  = d["clouds"]["all"]
        cond    = d["weather"][0]["description"].title()
        cond_id = d["weather"][0]["description"].lower()
        country = d["sys"]["country"]
        lat     = d["coord"]["lat"]
        lon     = d["coord"]["lon"]
        tz      = d["timezone"]
        sunrise = unix_to_time(d["sys"]["sunrise"], tz)
        sunset  = unix_to_time(d["sys"]["sunset"], tz)
        day_sec = d["sys"]["sunset"] - d["sys"]["sunrise"]
        daylen  = f"{day_sec//3600}h {(day_sec%3600)//60}m"
        dew     = round(d["main"]["temp"] - ((100 - hum) / 5))
        emoji   = get_weather_emoji(cond_id, WEATHER_EMOJIS)
        now_str = datetime.now().strftime("%d %b %Y  %H:%M")

        # Temp color
        if temp >= 35:   tc = COLORS["hot"]
        elif temp <= 10: tc = COLORS["cold"]
        else:            tc = COLORS["mild"]

        # ── Tab 1: Current ──
        self.lbl_city_name.config(text=f"{d['name']}")
        self.lbl_country.config(text=f"📍 {country}  •  Lat {lat}°  Lon {lon}°")
        self.lbl_condition.config(text=cond)
        self.lbl_updated.config(text=f"Last updated: {now_str}")
        self.lbl_emoji.config(text=emoji)
        self.lbl_temp.config(text=f"{temp}°C", fg=tc)
        self.lbl_feels.config(text=f"Feels like {feels}°C")

        vals = {
            "hum":  (f"{hum}", "%"),
            "wind": (f"{wind}", " km/h"),
            "wdir": (wdir, ""),
            "vis":  (f"{vis}", " km"),
            "pres": (f"{pres}", " hPa"),
            "feel": (f"{feels}", "°C"),
        }
        for key, (val, unit) in vals.items():
            lbl, _ = self.stat_cards[key]
            lbl.config(text=f"{val}{unit}")

        # ── Tab 3: Details ──
        dl = self.detail_labels
        dl["sunrise"].config(text=sunrise)
        dl["sunset"].config(text=sunset)
        dl["daylen"].config(text=daylen)
        dl["hum"].config(text=f"{hum}%")
        dl["dew"].config(text=f"{dew}°C")
        dl["pres"].config(text=f"{pres} hPa")
        dl["clouds"].config(text=f"{clouds}%")
        dl["wind"].config(text=f"{wind} km/h")
        dl["wdir"].config(text=wdir)
        dl["gust"].config(text=f"{gust} km/h")
        dl["vis"].config(text=f"{vis} km")
        dl["uvi"].config(text="N/A (free tier)")
        dl["uvrisk"].config(text="—")
        dl["lat"].config(text=f"{lat}°")
        dl["lon"].config(text=f"{lon}°")
        dl["tz"].config(text=f"UTC{'+' if tz>=0 else ''}{tz//3600}")
        dl["country"].config(text=country)

        # ── Tab 2: Forecast ──
        if fore and fore.get("list"):
            daily = {}
            for item in fore["list"]:
                day_key = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
                if day_key not in daily:
                    daily[day_key] = []
                daily[day_key].append(item)

            day_list = list(daily.items())[:5]
            days_map = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]

            for i, (day_key, items) in enumerate(day_list):
                if i >= 5: break
                slot = self.forecast_slots[i]
                hi  = round(max(x["main"]["temp_max"] for x in items))
                lo  = round(min(x["main"]["temp_min"] for x in items))
                hm  = round(sum(x["main"]["humidity"] for x in items) / len(items))
                cc  = items[len(items)//2]["weather"][0]["description"]
                ico = get_weather_emoji(cc.lower(), WEATHER_EMOJIS)
                dt  = datetime.fromtimestamp(items[0]["dt"])
                dname = days_map[dt.weekday()]
                ddate = dt.strftime("%d %b")

                slot["day"].config(text=dname)
                slot["date"].config(text=ddate)
                slot["icon"].config(text=ico)
                slot["hi"].config(text=f"{hi}°C ▲")
                slot["lo"].config(text=f"{lo}°C ▼")
                slot["cond"].config(text=cc.title())
                slot["hum"].config(text=f"💧 {hm}%")

        # ── History ──
        self._add_history(d['name'], country, temp, cond, emoji)

        self.lbl_status.config(
            text=f"✅  Showing weather for {d['name']}, {country}",
            fg=COLORS["accent_cyan"])
        self.btn_search.config(state="normal", text="  Search  ")

    def _show_error(self, title, msg):
        self.lbl_status.config(text=f"❌  {msg}", fg=COLORS["accent_red"])
        self.btn_search.config(state="normal", text="  Search  ")
        messagebox.showerror(title, msg)

    def _add_history(self, city, country, temp, cond, emoji):
        entry_data = {
            "city": city, "country": country,
            "temp": temp, "cond": cond,
            "emoji": emoji,
            "time": datetime.now().strftime("%H:%M %d/%m/%Y")
        }
        self.search_history.insert(0, entry_data)
        self.lbl_no_history.pack_forget()

        card = tk.Frame(self.history_frame, bg=COLORS["bg_card"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            padx=16, pady=10,
            cursor="hand2")
        card.pack(fill="x", padx=4, pady=4)

        tk.Label(card, text=f"{emoji}  {city}, {country}",
            font=self.font_h2,
            bg=COLORS["bg_card"], fg=COLORS["text_primary"]).pack(side="left")

        right_info = tk.Frame(card, bg=COLORS["bg_card"])
        right_info.pack(side="right")

        tk.Label(right_info, text=f"{temp}°C",
            font=self.font_h2,
            bg=COLORS["bg_card"], fg=COLORS["accent_warm"]).pack(side="left", padx=10)

        tk.Label(right_info, text=entry_data["time"],
            font=self.font_small,
            bg=COLORS["bg_card"], fg=COLORS["text_dim"]).pack(side="left")

        # Click to re-search
        city_name = city
        for widget in [card] + card.winfo_children():
            widget.bind("<Button-1>", lambda e, c=city_name: self._quick_search(c))

    def _quick_search(self, city):
        self.entry.delete(0, "end")
        self.entry.insert(0, city)
        self.entry.config(fg=COLORS["text_primary"])
        self.notebook.select(self.tab_now)
        self._start_search()

    def _clear_history(self):
        self.search_history.clear()
        for w in self.history_frame.winfo_children():
            w.destroy()
        self.lbl_no_history = tk.Label(self.history_frame,
            text="No searches yet. Start by searching a city!",
            font=self.font_body,
            bg=COLORS["bg_dark"], fg=COLORS["text_muted"])
        self.lbl_no_history.pack(pady=40)

    def _tick_clock(self):
        now = datetime.now().strftime("🕐  %A, %d %B %Y  •  %I:%M:%S %p")
        self.lbl_time.config(text=now)
        self.after(1000, self._tick_clock)


if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()