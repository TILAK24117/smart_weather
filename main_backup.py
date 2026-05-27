"""
╔══════════════════════════════════════════════════════════════╗
║          SMART WEATHER FORECAST APPLICATION v4              ║
║          Built with Python, Tkinter & OpenWeatherMap API     ║
╚══════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import requests
import threading
from datetime import datetime
from config.settings import API_KEY, BASE_URL, FORECAST_URL
from utils.helpers import (
    kelvin_to_celsius, meters_to_km, ms_to_kmh,
    unix_to_time, get_wind_direction, get_uv_label,
    get_aqi_label, get_weather_emoji
)

# ─── STATIC COLORS (cards, input, borders etc.) ────────────────
COLORS = {
    "bg_dark":      "#06090F",
    "bg_card":      "#0D1526",
    "bg_card2":     "#111E36",
    "bg_input":     "#0A1020",
    "accent_blue":  "#4FC3F7",
    "accent_cyan":  "#00E676",
    "accent_warm":  "#FFB74D",
    "accent_red":   "#EF5350",
    "text_primary": "#E8F4FD",
    "text_muted":   "#6B9ABF",
    "text_dim":     "#2D4A6A",
    "border":       "#162B50",
    "shadow":       "#020408",
    # Temperature label colors
    "temp_hot":  "#FF1744",   # ≥ 35°C
    "temp_warm": "#FF6D00",   # 25–34°C
    "temp_mild": "#29B6F6",   # 11–24°C
    "temp_cold": "#00E5FF",   # ≤ 10°C
    # ── BIG, VISIBLE hero backgrounds ──────────────────────────
    # These are noticeably different so user can FEEL the mood
    "hero_fire":   "#3D0800",   # hot sunny   – deep crimson
    "hero_warm":   "#2E1400",   # warm        – dark amber
    "hero_cool":   "#001E3C",   # mild/cool   – midnight blue
    "hero_ice":    "#001824",   # cold        – deep teal-black
    "hero_cloud":  "#141E2E",   # cloudy      – dark slate-blue
    "hero_rain":   "#021220",   # rain        – deep ocean navy
    "hero_storm":  "#0C0420",   # storm       – near-black purple
    "hero_snow":   "#0A1A2C",   # snow        – cold dark blue
    "hero_mist":   "#0A1820",   # mist/fog    – grey-blue dark
    # Condition text colors
    "cond_clear":  "#FFD700",
    "cond_few":    "#90CAF9",
    "cond_scat":   "#64B5F6",
    "cond_broken": "#90A4AE",
    "cond_over":   "#B0BEC5",
    "cond_rain":   "#42A5F5",
    "cond_storm":  "#CE93D8",
    "cond_snow":   "#E3F2FD",
    "cond_mist":   "#80DEEA",
    "cond_haze":   "#BCAAA4",
    "btn_hover":   "#1565C0",
}

WEATHER_EMOJIS = {
    "clear sky":        "☀️",
    "few clouds":       "🌤️",
    "scattered clouds": "⛅",
    "broken clouds":    "🌥️",
    "overcast clouds":  "☁️",
    "light rain":       "🌦️",
    "moderate rain":    "🌧️",
    "heavy rain":       "⛈️",
    "thunderstorm":     "⛈️",
    "snow":             "❄️",
    "light snow":       "🌨️",
    "mist":             "🌫️",
    "fog":              "🌁",
    "haze":             "😶‍🌫️",
    "drizzle":          "🌂",
    "default":          "🌈",
}


# ─── CANVAS WEATHER ICON DRAWING ───────────────────────────────
# We draw icons with tkinter Canvas so they are ALWAYS visible,
# colorful, and not dependent on emoji font rendering.

def draw_weather_icon(canvas, cond: str, size=80):
    """Draw a colorful weather icon onto a tk.Canvas.
    canvas must already be created with the right width/height.
    Returns the canvas (for chaining).
    """
    c = cond.lower()
    canvas.delete("all")
    bg = canvas["bg"]
    cx, cy = size // 2, size // 2
    r = size // 2 - 6

    if "thunder" in c or "storm" in c:
        _draw_storm(canvas, cx, cy, r, bg)
    elif "snow" in c or "sleet" in c:
        _draw_snow(canvas, cx, cy, r, bg)
    elif "rain" in c or "drizzle" in c:
        _draw_rain(canvas, cx, cy, r, bg)
    elif "clear" in c:
        _draw_sun(canvas, cx, cy, r)
    elif "few cloud" in c:
        _draw_sun_cloud(canvas, cx, cy, r)
    elif "scattered" in c or "broken" in c or "overcast" in c or "cloud" in c:
        _draw_cloud(canvas, cx, cy, r, "#90CAF9" if "few" in c else "#78909C")
    elif "mist" in c or "fog" in c or "haze" in c or "smoke" in c or "dust" in c:
        _draw_mist(canvas, cx, cy, r)
    else:
        _draw_sun(canvas, cx, cy, r)  # default sunny
    return canvas


def _draw_sun(canvas, cx, cy, r):
    sun_r = int(r * 0.42)
    ray_len = int(r * 0.26)
    # Rays
    import math
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        inner = sun_r + 5
        x1 = cx + inner * math.cos(rad)
        y1 = cy + inner * math.sin(rad)
        x2 = cx + (inner + ray_len) * math.cos(rad)
        y2 = cy + (inner + ray_len) * math.sin(rad)
        canvas.create_line(x1, y1, x2, y2, fill="#FFD700", width=3, capstyle="round")
    # Sun circle
    canvas.create_oval(cx - sun_r, cy - sun_r, cx + sun_r, cy + sun_r,
                       fill="#FFD700", outline="#FFA000", width=2)


def _draw_cloud(canvas, cx, cy, r, color="#90A4AE"):
    # Main cloud body — 3 overlapping ovals
    cr = int(r * 0.38)
    canvas.create_oval(cx - cr, cy, cx + cr, cy + cr * 2,
                       fill=color, outline="", )
    canvas.create_oval(cx - cr * 1.4, cy + int(cr * 0.5),
                       cx + cr * 0.2, cy + cr * 2,
                       fill=color, outline="")
    canvas.create_oval(cx - int(cr * 0.2), cy + int(cr * 0.5),
                       cx + cr * 1.4, cy + cr * 2,
                       fill=color, outline="")
    canvas.create_oval(cx - int(cr * 0.6), cy + int(cr * 0.2),
                       cx + int(cr * 0.6), cy + int(cr * 1.0),
                       fill=color, outline="")
    # Top puff
    canvas.create_oval(cx - int(cr * 0.9), cy - int(cr * 0.5),
                       cx + int(cr * 0.9), cy + int(cr * 0.9),
                       fill=color, outline="")


def _draw_sun_cloud(canvas, cx, cy, r):
    import math
    # Small sun peeking top-right
    sr = int(r * 0.28)
    sx, sy = cx + int(r * 0.22), cy - int(r * 0.18)
    for angle in range(0, 360, 60):
        rad = math.radians(angle)
        x1 = sx + (sr + 3) * math.cos(rad)
        y1 = sy + (sr + 3) * math.sin(rad)
        x2 = sx + (sr + 12) * math.cos(rad)
        y2 = sy + (sr + 12) * math.sin(rad)
        canvas.create_line(x1, y1, x2, y2, fill="#FFD700", width=2, capstyle="round")
    canvas.create_oval(sx - sr, sy - sr, sx + sr, sy + sr,
                       fill="#FFD700", outline="#FFA000", width=1)
    # Cloud in front
    _draw_cloud(canvas, cx - int(r * 0.12), cy + int(r * 0.1),
                int(r * 0.85), "#90CAF9")


def _draw_rain(canvas, cx, cy, r, cloud_color="#5C8EA8"):
    _draw_cloud(canvas, cx, cy - int(r * 0.22), r, cloud_color)
    # Raindrops
    drop_color = "#42A5F5"
    offsets = [-int(r * 0.45), -int(r * 0.15), int(r * 0.15), int(r * 0.45)]
    for i, ox in enumerate(offsets):
        y_start = cy + int(r * 0.58) + (i % 2) * 6
        canvas.create_line(cx + ox, y_start,
                           cx + ox - 4, y_start + int(r * 0.32),
                           fill=drop_color, width=2, capstyle="round")


def _draw_storm(canvas, cx, cy, r):
    _draw_cloud(canvas, cx, cy - int(r * 0.28), r, "#7E57C2")
    # Lightning bolt
    lx, ly = cx, cy + int(r * 0.42)
    pts = [
        lx + 10, ly,
        lx,      ly + 18,
        lx + 8,  ly + 18,
        lx - 4,  ly + 36,
        lx + 16, ly + 14,
        lx + 8,  ly + 14,
    ]
    canvas.create_polygon(pts, fill="#FFD600", outline="#FFA000", width=1)


def _draw_snow(canvas, cx, cy, r):
    _draw_cloud(canvas, cx, cy - int(r * 0.22), r, "#90CAF9")
    import math
    # Snowflake
    sx, sy = cx, cy + int(r * 0.62)
    snow_r = int(r * 0.28)
    for angle in range(0, 360, 60):
        rad = math.radians(angle)
        canvas.create_line(sx, sy,
                           sx + snow_r * math.cos(rad),
                           sy + snow_r * math.sin(rad),
                           fill="#E3F2FD", width=2, capstyle="round")
    canvas.create_oval(sx - 4, sy - 4, sx + 4, sy + 4, fill="#E3F2FD", outline="")


def _draw_mist(canvas, cx, cy, r):
    mist_color = "#80DEEA"
    for i, yoff in enumerate([-int(r * 0.25), 0, int(r * 0.25)]):
        xoff = (i % 2) * int(r * 0.1)
        canvas.create_line(cx - int(r * 0.55) + xoff, cy + yoff,
                           cx + int(r * 0.55) + xoff, cy + yoff,
                           fill=mist_color, width=5, capstyle="round")


# ─── HELPER FUNCTIONS ──────────────────────────────────────────

def temp_color(t: float):
    """Return (label_fg, hero_bg) for a temperature in °C."""
    if t >= 35:  return COLORS["temp_hot"],  COLORS["hero_fire"]
    if t >= 25:  return COLORS["temp_warm"], COLORS["hero_warm"]
    if t >= 11:  return COLORS["temp_mild"], COLORS["hero_cool"]
    return            COLORS["temp_cold"], COLORS["hero_ice"]


def cond_color(cond: str) -> str:
    c = cond.lower()
    if "clear" in c:                         return COLORS["cond_clear"]
    if "few cloud" in c:                     return COLORS["cond_few"]
    if "scattered" in c:                     return COLORS["cond_scat"]
    if "broken" in c:                        return COLORS["cond_broken"]
    if "overcast" in c:                      return COLORS["cond_over"]
    if "rain" in c or "drizzle" in c:        return COLORS["cond_rain"]
    if "thunder" in c or "storm" in c:       return COLORS["cond_storm"]
    if "snow" in c or "sleet" in c:          return COLORS["cond_snow"]
    if "mist" in c or "fog" in c:            return COLORS["cond_mist"]
    if "haze" in c or "dust" in c:           return COLORS["cond_haze"]
    return COLORS["accent_blue"]


def hero_bg_from_cond(cond: str):
    """Condition-based hero background (overrides temp). Returns None if no match."""
    c = cond.lower()
    if "thunder" in c or "storm" in c:      return COLORS["hero_storm"]
    if "rain" in c or "drizzle" in c:       return COLORS["hero_rain"]
    if "snow" in c or "sleet" in c:         return COLORS["hero_snow"]
    if "mist" in c or "fog" in c or "haze" in c or "smoke" in c or "dust" in c:
        return COLORS["hero_mist"]
    if "cloud" in c:                        return COLORS["hero_cloud"]
    return None


def set_bg_all(widget, color: str):
    """Recursively set bg on widget and every child, skipping unsupported widgets."""
    try:
        widget.config(bg=color)
    except Exception:
        pass
    for child in widget.winfo_children():
        set_bg_all(child, color)


# ══════════════════════════════════════════════════════════════
class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⛅ Smart Weather Forecast")
        self.geometry("960x780")
        self.minsize(820, 680)
        self.configure(bg=COLORS["bg_dark"])
        self.resizable(True, True)

        self.update_idletasks()
        x = (self.winfo_screenwidth()  // 2) - 480
        y = (self.winfo_screenheight() // 2) - 390
        self.geometry(f"960x780+{x}+{y}")

        self._setup_fonts()
        self._setup_styles()
        self._build_ui()
        self._bind_keys()

        self.current_data  = None
        self.forecast_data = None
        self.search_history = []

    # ── FONTS ─────────────────────────────────────────────────
    def _setup_fonts(self):
        self.font_h1     = font.Font(family="Segoe UI", size=22, weight="bold")
        self.font_h2     = font.Font(family="Segoe UI", size=14, weight="bold")
        self.font_h3     = font.Font(family="Segoe UI", size=11, weight="bold")
        self.font_body   = font.Font(family="Segoe UI", size=11)
        self.font_small  = font.Font(family="Segoe UI", size=9)
        self.font_mono   = font.Font(family="Consolas",  size=11)
        self.font_search = font.Font(family="Segoe UI", size=13)
        self.font_temp   = font.Font(family="Segoe UI", size=56, weight="bold")

    # ── STYLES ────────────────────────────────────────────────
    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook",
            background=COLORS["bg_dark"], borderwidth=0, tabmargins=0)
        style.configure("TNotebook.Tab",
            background=COLORS["bg_card"],
            foreground=COLORS["text_muted"],
            padding=[20, 8],
            font=("Segoe UI", 10, "bold"),
            borderwidth=0)
        style.map("TNotebook.Tab",
            background=[("selected", COLORS["bg_card2"])],
            foreground=[("selected", COLORS["accent_blue"])])

    # ── BUILD UI ──────────────────────────────────────────────
    def _build_ui(self):
        # Top bar
        topbar = tk.Frame(self, bg=COLORS["bg_card"], pady=12)
        topbar.pack(fill="x", side="top")
        tk.Label(topbar, text="⛅ SmartWeather",
            font=self.font_h2, bg=COLORS["bg_card"],
            fg=COLORS["accent_blue"]).pack(side="left", padx=20)
        self.lbl_time = tk.Label(topbar, text="",
            font=self.font_small, bg=COLORS["bg_card"], fg=COLORS["text_muted"])
        self.lbl_time.pack(side="right", padx=20)
        self._tick_clock()

        # Search bar
        sf = tk.Frame(self, bg=COLORS["bg_dark"], pady=16)
        sf.pack(fill="x", padx=30)
        si = tk.Frame(sf, bg=COLORS["bg_input"],
            highlightbackground=COLORS["border"], highlightthickness=2)
        si.pack(fill="x")
        tk.Label(si, text="🔍", font=self.font_body,
            bg=COLORS["bg_input"], fg=COLORS["text_muted"], padx=10).pack(side="left")
        self.entry = tk.Entry(si, font=self.font_search,
            bg=COLORS["bg_input"], fg=COLORS["text_primary"],
            insertbackground=COLORS["accent_blue"], relief="flat", bd=0)
        self.entry.pack(side="left", fill="x", expand=True, ipady=10)
        self.entry.insert(0, "Search city name...")
        self.entry.bind("<FocusIn>",  self._clear_ph)
        self.entry.bind("<FocusOut>", self._restore_ph)
        self.btn_search = tk.Button(si, text="  Search  ",
            font=self.font_h3, bg=COLORS["accent_blue"], fg="white",
            activebackground=COLORS["btn_hover"], activeforeground="white",
            relief="flat", bd=0, padx=16, pady=10, cursor="hand2",
            command=self._start_search)
        self.btn_search.pack(side="right", padx=4, pady=4)

        # Status
        self.lbl_status = tk.Label(self,
            text="Enter a city name above to get started",
            font=self.font_body, bg=COLORS["bg_dark"], fg=COLORS["text_muted"])
        self.lbl_status.pack(pady=4)

        # Tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=30, pady=(4, 16))
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

    # ── TAB 1: CURRENT ────────────────────────────────────────
    def _build_tab_now(self):
        p = self.tab_now

        # ── Hero card (full-width, background changes with weather) ──
        self.hero = tk.Frame(p, bg=COLORS["bg_card"],
            highlightbackground=COLORS["border"], highlightthickness=2)
        self.hero.pack(fill="x", pady=(14, 10), padx=6)

        # Left: city / condition text
        self._hero_left = tk.Frame(self.hero, bg=COLORS["bg_card"],
            padx=28, pady=24)
        self._hero_left.pack(side="left", fill="both", expand=True)

        self.lbl_city = tk.Label(self._hero_left, text="—",
            font=self.font_h1, bg=COLORS["bg_card"], fg=COLORS["text_primary"])
        self.lbl_city.pack(anchor="w")

        self.lbl_country = tk.Label(self._hero_left, text="—",
            font=self.font_body, bg=COLORS["bg_card"], fg=COLORS["text_muted"])
        self.lbl_country.pack(anchor="w")

        self.lbl_cond = tk.Label(self._hero_left, text="—",
            font=self.font_h2, bg=COLORS["bg_card"], fg=COLORS["accent_blue"])
        self.lbl_cond.pack(anchor="w", pady=(12, 0))

        self.lbl_updated = tk.Label(self._hero_left, text="",
            font=self.font_small, bg=COLORS["bg_card"], fg=COLORS["text_dim"])
        self.lbl_updated.pack(anchor="w")

        # Right: canvas icon + temperature
        self._hero_right = tk.Frame(self.hero, bg=COLORS["bg_card"],
            padx=30, pady=20)
        self._hero_right.pack(side="right")

        # Canvas icon — drawn with shapes, always colorful & visible
        self.icon_canvas = tk.Canvas(self._hero_right,
            width=100, height=100, bg=COLORS["bg_card"],
            highlightthickness=0)
        self.icon_canvas.pack()

        self.lbl_temp = tk.Label(self._hero_right, text="—°C",
            font=self.font_temp, bg=COLORS["bg_card"],
            fg=COLORS["temp_mild"])
        self.lbl_temp.pack()

        self.lbl_feels = tk.Label(self._hero_right, text="",
            font=self.font_small, bg=COLORS["bg_card"],
            fg=COLORS["text_muted"])
        self.lbl_feels.pack()

        # ── Stat cards grid ──────────────────────────────────
        grid_outer = tk.Frame(p, bg=COLORS["bg_dark"])
        grid_outer.pack(fill="x", padx=6, pady=6)

        self.stat_cards = {}
        stats = [
            ("💧", "Humidity",   "hum",  "%",      COLORS["accent_blue"]),
            ("💨", "Wind Speed", "wind", " km/h",  COLORS["accent_cyan"]),
            ("🧭", "Wind Dir",   "wdir", "",        COLORS["text_primary"]),
            ("👁",  "Visibility", "vis",  " km",    COLORS["accent_blue"]),
            ("🔼", "Pressure",   "pres", " hPa",   COLORS["text_muted"]),
            ("🌡", "Feels Like", "feel", "°C",      COLORS["accent_warm"]),
        ]
        for i, (icon, label, key, unit, vc) in enumerate(stats):
            col, row = i % 3, i // 3
            shadow = tk.Frame(grid_outer, bg=COLORS["shadow"])
            shadow.grid(row=row, column=col, padx=(5, 0), pady=(5, 0), sticky="nsew")
            grid_outer.columnconfigure(col, weight=1)
            card = tk.Frame(shadow, bg=COLORS["bg_card"],
                highlightbackground=COLORS["border"], highlightthickness=1,
                padx=16, pady=14)
            card.pack(fill="both", expand=True, padx=(0, 4), pady=(0, 4))
            tk.Label(card, text=f"{icon}  {label}", font=self.font_small,
                bg=COLORS["bg_card"], fg=COLORS["text_muted"]).pack(anchor="w")
            val_lbl = tk.Label(card, text="—", font=self.font_h2,
                bg=COLORS["bg_card"], fg=vc)
            val_lbl.pack(anchor="w", pady=(4, 0))
            self.stat_cards[key] = (val_lbl, unit)

    # ── TAB 2: FORECAST ───────────────────────────────────────
    def _build_tab_forecast(self):
        p = self.tab_forecast
        tk.Label(p, text="5-Day Forecast", font=self.font_h2,
            bg=COLORS["bg_dark"], fg=COLORS["text_primary"]).pack(
            anchor="w", padx=6, pady=(14, 8))

        ff = tk.Frame(p, bg=COLORS["bg_dark"])
        ff.pack(fill="both", expand=True, padx=4)
        for i in range(5):
            ff.columnconfigure(i, weight=1)

        self.forecast_slots = []
        for i in range(5):
            shadow = tk.Frame(ff, bg=COLORS["shadow"])
            shadow.grid(row=0, column=i, padx=(5, 0), pady=(5, 0), sticky="nsew")

            card = tk.Frame(shadow, bg=COLORS["bg_card"],
                highlightbackground=COLORS["border"], highlightthickness=1,
                padx=10, pady=14)
            card.pack(fill="both", expand=True, padx=(0, 4), pady=(0, 4))

            lbl_day  = tk.Label(card, text="—", font=self.font_h3,
                bg=COLORS["bg_card"], fg=COLORS["accent_blue"])
            lbl_day.pack()
            lbl_date = tk.Label(card, text="", font=self.font_small,
                bg=COLORS["bg_card"], fg=COLORS["text_dim"])
            lbl_date.pack()

            # Canvas icon for forecast (smaller, 64px)
            fc_canvas = tk.Canvas(card, width=64, height=64,
                bg=COLORS["bg_card"], highlightthickness=0)
            fc_canvas.pack(pady=6)

            lbl_hi = tk.Label(card, text="—", font=self.font_h2,
                bg=COLORS["bg_card"], fg=COLORS["accent_warm"])
            lbl_hi.pack()
            lbl_lo = tk.Label(card, text="—", font=self.font_body,
                bg=COLORS["bg_card"], fg=COLORS["temp_cold"])
            lbl_lo.pack()
            lbl_cond = tk.Label(card, text="—", font=self.font_small,
                bg=COLORS["bg_card"], fg=COLORS["text_muted"],
                wraplength=110, justify="center")
            lbl_cond.pack(pady=(4, 0))
            lbl_hum = tk.Label(card, text="", font=self.font_small,
                bg=COLORS["bg_card"], fg=COLORS["text_dim"])
            lbl_hum.pack()

            self.forecast_slots.append({
                "day": lbl_day, "date": lbl_date, "canvas": fc_canvas,
                "hi": lbl_hi, "lo": lbl_lo, "cond": lbl_cond, "hum": lbl_hum
            })

    # ── TAB 3: DETAILS ────────────────────────────────────────
    def _build_tab_details(self):
        p = self.tab_details
        canvas = tk.Canvas(p, bg=COLORS["bg_dark"], highlightthickness=0)
        scroll = tk.Scrollbar(p, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        inner = tk.Frame(canvas, bg=COLORS["bg_dark"])
        wid = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(wid, width=e.width))
        inner.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        self.detail_labels = {}
        sections = [
            ("🌅 Sun & Moon",  [("Sunrise","sunrise"),("Sunset","sunset"),("Day Length","daylen")]),
            ("🌊 Atmosphere",  [("Humidity","hum"),("Dew Point","dew"),("Pressure","pres"),("Cloud Cover","clouds")]),
            ("🌬 Wind",        [("Speed","wind"),("Direction","wdir"),("Gust","gust")]),
            ("👁 Visibility",  [("Distance","vis"),("UV Index","uvi"),("UV Risk","uvrisk")]),
            ("📍 Location",    [("Latitude","lat"),("Longitude","lon"),("Timezone","tz"),("Country","country")]),
        ]
        for title, fields in sections:
            shadow = tk.Frame(inner, bg=COLORS["shadow"])
            shadow.pack(fill="x", padx=(6, 0), pady=(10, 0))
            sec = tk.Frame(shadow, bg=COLORS["bg_card"],
                highlightbackground=COLORS["border"], highlightthickness=1,
                padx=20, pady=14)
            sec.pack(fill="x", padx=(0, 4), pady=(0, 4))
            tk.Label(sec, text=title, font=self.font_h3,
                bg=COLORS["bg_card"], fg=COLORS["accent_blue"]).pack(anchor="w", pady=(0, 8))
            for label, key in fields:
                row = tk.Frame(sec, bg=COLORS["bg_card"])
                row.pack(fill="x", pady=2)
                tk.Label(row, text=label, font=self.font_body, width=14,
                    bg=COLORS["bg_card"], fg=COLORS["text_muted"], anchor="w").pack(side="left")
                lbl = tk.Label(row, text="—", font=self.font_mono,
                    bg=COLORS["bg_card"], fg=COLORS["text_primary"], anchor="w")
                lbl.pack(side="left", padx=(12, 0))
                self.detail_labels[key] = lbl

    # ── TAB 4: HISTORY ────────────────────────────────────────
    def _build_tab_history(self):
        p = self.tab_history
        hdr = tk.Frame(p, bg=COLORS["bg_dark"])
        hdr.pack(fill="x", padx=6, pady=(14, 4))
        tk.Label(hdr, text="Recent Searches", font=self.font_h2,
            bg=COLORS["bg_dark"], fg=COLORS["text_primary"]).pack(side="left")
        tk.Button(hdr, text="🗑  Clear", font=self.font_small,
            bg=COLORS["bg_card"], fg=COLORS["text_muted"],
            activebackground=COLORS["accent_red"],
            relief="flat", bd=0, padx=10, pady=4, cursor="hand2",
            command=self._clear_history).pack(side="right")
        self.history_frame = tk.Frame(p, bg=COLORS["bg_dark"])
        self.history_frame.pack(fill="both", expand=True, padx=4)
        self.lbl_no_history = tk.Label(self.history_frame,
            text="No searches yet. Start by searching a city!",
            font=self.font_body, bg=COLORS["bg_dark"], fg=COLORS["text_muted"])
        self.lbl_no_history.pack(pady=40)

    # ── SEARCH ────────────────────────────────────────────────
    def _bind_keys(self):
        self.entry.bind("<Return>", lambda e: self._start_search())
        self.bind("<Escape>", lambda e: self.entry.focus())

    def _clear_ph(self, e):
        if self.entry.get() == "Search city name...":
            self.entry.delete(0, "end")
            self.entry.config(fg=COLORS["text_primary"])

    def _restore_ph(self, e):
        if not self.entry.get():
            self.entry.insert(0, "Search city name...")
            self.entry.config(fg=COLORS["text_muted"])

    def _start_search(self):
        city = self.entry.get().strip()
        if not city or city == "Search city name...":
            messagebox.showwarning("Input Required", "Please enter a city name.")
            return
        self.btn_search.config(state="disabled", text="  Loading...  ")
        self.lbl_status.config(
            text=f"🔄  Fetching weather for '{city}'...",
            fg=COLORS["accent_blue"])
        self.update()
        threading.Thread(target=self._fetch_weather, args=(city,), daemon=True).start()

    def _fetch_weather(self, city):
        try:
            r = requests.get(BASE_URL,
                params={"q": city, "appid": API_KEY, "units": "metric"},
                timeout=10)
            if r.status_code == 401:
                self.after(0, lambda: self._show_error("Invalid API Key",
                    "Check your API key in .env or config/settings.py"))
                return
            if r.status_code == 404:
                self.after(0, lambda: self._show_error("City Not Found",
                    f"'{city}' not found. Check spelling."))
                return
            r.raise_for_status()
            curr = r.json()
            fr = requests.get(FORECAST_URL,
                params={"q": city, "appid": API_KEY, "units": "metric", "cnt": 40},
                timeout=10)
            fore = fr.json() if fr.ok else None
            self.current_data  = curr
            self.forecast_data = fore
            self.after(0, lambda: self._render(curr, fore))
        except requests.exceptions.ConnectionError:
            self.after(0, lambda: self._show_error("Connection Error",
                "No internet connection."))
        except requests.exceptions.Timeout:
            self.after(0, lambda: self._show_error("Timeout", "Request timed out."))
        except Exception as ex:
            self.after(0, lambda: self._show_error("Error", str(ex)))

    # ── RENDER ────────────────────────────────────────────────
    def _render(self, d, fore):
        temp    = round(d["main"]["temp"])
        feels   = round(d["main"]["feels_like"])
        hum     = d["main"]["humidity"]
        pres    = d["main"]["pressure"]
        wind    = round(ms_to_kmh(d["wind"]["speed"]))
        gust    = round(ms_to_kmh(d["wind"].get("gust", 0)))
        wdir    = get_wind_direction(d["wind"].get("deg", 0))
        vis     = round(meters_to_km(d.get("visibility", 0)))
        clouds  = d["clouds"]["all"]
        cond_raw = d["weather"][0]["description"]
        cond    = cond_raw.title()
        cond_id = cond_raw.lower()
        country = d["sys"]["country"]
        lat     = d["coord"]["lat"]
        lon     = d["coord"]["lon"]
        tz      = d["timezone"]
        sunrise = unix_to_time(d["sys"]["sunrise"], tz)
        sunset  = unix_to_time(d["sys"]["sunset"],  tz)
        day_sec = d["sys"]["sunset"] - d["sys"]["sunrise"]
        daylen  = f"{day_sec//3600}h {(day_sec%3600)//60}m"
        dew     = round(d["main"]["temp"] - ((100 - hum) / 5))
        now_str = datetime.now().strftime("%d %b %Y  %H:%M")

        # ── Colors ──────────────────────────────────────────
        tc, h_bg_temp = temp_color(temp)
        h_bg_cond     = hero_bg_from_cond(cond_id)
        h_bg          = h_bg_cond if h_bg_cond else h_bg_temp  # condition wins
        cc            = cond_color(cond_id)

        # ── Apply hero background to ENTIRE hero card and labels ──
        # We explicitly set bg on the hero frame, both sub-frames, and each label
        for widget in [self.hero, self._hero_left, self._hero_right]:
            widget.config(bg=h_bg)

        self.lbl_city.config(    text=d["name"],   fg=COLORS["text_primary"], bg=h_bg)
        self.lbl_country.config( text=f"📍 {country}  •  {lat}°, {lon}°",
                                 fg=COLORS["text_muted"], bg=h_bg)
        self.lbl_cond.config(    text=cond,         fg=cc,                    bg=h_bg)
        self.lbl_updated.config( text=f"Updated: {now_str}",
                                 fg=COLORS["text_dim"], bg=h_bg)

        # ── Canvas weather icon (always visible, drawn with shapes) ──
        self.icon_canvas.config(bg=h_bg)
        draw_weather_icon(self.icon_canvas, cond_id, size=100)

        # ── Temperature with color ───────────────────────────
        self.lbl_temp.config(  text=f"{temp}°C",        fg=tc, bg=h_bg)
        self.lbl_feels.config( text=f"Feels like {feels}°C",
                               fg=COLORS["text_muted"], bg=h_bg)

        # ── Stat cards ───────────────────────────────────────
        vals = {
            "hum":  f"{hum}%",
            "wind": f"{wind} km/h",
            "wdir": wdir,
            "vis":  f"{vis} km",
            "pres": f"{pres} hPa",
            "feel": f"{feels}°C",
        }
        for key, val in vals.items():
            lbl, _ = self.stat_cards[key]
            lbl.config(text=val)

        # ── Tab 3: Details ───────────────────────────────────
        dl = self.detail_labels
        dl["sunrise"].config(text=sunrise)
        dl["sunset"].config( text=sunset)
        dl["daylen"].config( text=daylen)
        dl["hum"].config(    text=f"{hum}%")
        dl["dew"].config(    text=f"{dew}°C")
        dl["pres"].config(   text=f"{pres} hPa")
        dl["clouds"].config( text=f"{clouds}%")
        dl["wind"].config(   text=f"{wind} km/h")
        dl["wdir"].config(   text=wdir)
        dl["gust"].config(   text=f"{gust} km/h")
        dl["vis"].config(    text=f"{vis} km")
        dl["uvi"].config(    text="N/A (free tier)")
        dl["uvrisk"].config( text="—")
        dl["lat"].config(    text=f"{lat}°")
        dl["lon"].config(    text=f"{lon}°")
        dl["tz"].config(     text=f"UTC{'+' if tz >= 0 else ''}{tz//3600}")
        dl["country"].config(text=country)

        # ── Tab 2: Forecast ──────────────────────────────────
        if fore and fore.get("list"):
            daily = {}
            for item in fore["list"]:
                k = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
                daily.setdefault(k, []).append(item)

            days_map = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
            for i, (dk, items) in enumerate(list(daily.items())[:5]):
                s        = self.forecast_slots[i]
                hi       = round(max(x["main"]["temp_max"] for x in items))
                lo       = round(min(x["main"]["temp_min"] for x in items))
                hm       = round(sum(x["main"]["humidity"] for x in items) / len(items))
                fc       = items[len(items)//2]["weather"][0]["description"]
                hi_tc, _ = temp_color(hi)
                lo_tc, _ = temp_color(lo)
                dt       = datetime.fromtimestamp(items[0]["dt"])

                s["day"].config(  text=days_map[dt.weekday()])
                s["date"].config( text=dt.strftime("%d %b"))
                # Draw canvas icon for this forecast day
                draw_weather_icon(s["canvas"], fc.lower(), size=64)
                s["hi"].config(   text=f"{hi}°C ▲", fg=hi_tc)
                s["lo"].config(   text=f"{lo}°C ▼", fg=lo_tc)
                s["cond"].config( text=fc.title(),   fg=cond_color(fc.lower()))
                s["hum"].config(  text=f"💧 {hm}%")

        # ── History + status ─────────────────────────────────
        emoji = get_weather_emoji(cond_id, WEATHER_EMOJIS)
        self._add_history(d["name"], country, temp, cond, emoji, tc)
        self.lbl_status.config(
            text=f"✅  Showing weather for {d['name']}, {country}",
            fg=COLORS["accent_cyan"])
        self.btn_search.config(state="normal", text="  Search  ")

    def _show_error(self, title, msg):
        self.lbl_status.config(text=f"❌  {msg}", fg=COLORS["accent_red"])
        self.btn_search.config(state="normal", text="  Search  ")
        messagebox.showerror(title, msg)

    def _add_history(self, city, country, temp, cond, emoji, tc):
        data = {"city": city, "country": country, "temp": temp,
                "cond": cond, "emoji": emoji,
                "time": datetime.now().strftime("%H:%M %d/%m/%Y")}
        self.search_history.insert(0, data)
        self.lbl_no_history.pack_forget()

        shadow = tk.Frame(self.history_frame, bg=COLORS["shadow"])
        shadow.pack(fill="x", padx=(4, 0), pady=(4, 0))
        card = tk.Frame(shadow, bg=COLORS["bg_card"],
            highlightbackground=COLORS["border"], highlightthickness=1,
            padx=16, pady=10, cursor="hand2")
        card.pack(fill="x", padx=(0, 4), pady=(0, 4))

        tk.Label(card, text=f"{emoji}  {city}, {country}",
            font=self.font_h2, bg=COLORS["bg_card"],
            fg=COLORS["text_primary"]).pack(side="left")

        ri = tk.Frame(card, bg=COLORS["bg_card"])
        ri.pack(side="right")
        tk.Label(ri, text=f"{temp}°C", font=self.font_h2,
            bg=COLORS["bg_card"], fg=tc).pack(side="left", padx=10)
        tk.Label(ri, text=data["time"], font=self.font_small,
            bg=COLORS["bg_card"], fg=COLORS["text_dim"]).pack(side="left")

        cn = city
        all_w = [card, shadow] + list(card.winfo_children()) + list(ri.winfo_children())
        for w in all_w:
            w.bind("<Button-1>", lambda e, c=cn: self._quick_search(c))

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
            font=self.font_body, bg=COLORS["bg_dark"], fg=COLORS["text_muted"])
        self.lbl_no_history.pack(pady=40)

    def _tick_clock(self):
        self.lbl_time.config(
            text=datetime.now().strftime("🕐  %A, %d %B %Y  •  %I:%M:%S %p"))
        self.after(1000, self._tick_clock)


if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()
