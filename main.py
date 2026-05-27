"""
╔══════════════════════════════════════════════════════════════╗
║         SMART WEATHER FORECAST APPLICATION v5               ║
║         Styled like the reference image:                    ║
║         Blue gradient hero · Sun/Cloud art · Forecast bar   ║
╚══════════════════════════════════════════════════════════════╝
"""

import tkinter as tk
from tkinter import messagebox, font
import requests
import threading
import math
from datetime import datetime
from config.settings import API_KEY, BASE_URL, FORECAST_URL
from utils.helpers import (
    meters_to_km, ms_to_kmh,
    unix_to_time, get_wind_direction, get_weather_emoji
)

# ─── PALETTE (mirrors reference image) ────────────────────────
C = {
    # Hero gradient stops (drawn on canvas)
    "hero_top":    "#0d47a1",
    "hero_mid":    "#1565c0",
    "hero_bot":    "#1976d2",

    # Condition-based hero overrides
    "hero_storm":  "#1a0540",
    "hero_rain":   "#0d2137",
    "hero_snow":   "#1a2a40",
    "hero_cloud":  "#1b2d4a",
    "hero_hot":    "#7b2505",
    "hero_warm":   "#5a2d00",

    # UI chrome
    "bg_dark":     "#060e1e",
    "bg_panel":    "#0a1628",
    "bg_card":     "#0f1f3a",
    "bg_card2":    "#132444",
    "border":      "#1e3a5f",

    # Forecast bar
    "fc_normal":   "#0d1e38",
    "fc_active":   "#1a3a6e",
    "fc_border":   "#1e3a5f",

    # Text
    "txt_white":   "#ffffff",
    "txt_sub":     "#b0c4de",
    "txt_dim":     "#5a7fa8",

    # Accents
    "acc_blue":    "#42a5f5",
    "acc_cyan":    "#00e5ff",
    "acc_warm":    "#ffb74d",
    "acc_cold":    "#80deea",
    "acc_red":     "#ef5350",
    "acc_green":   "#66bb6a",

    # Temp colours
    "temp_hot":    "#ff1744",
    "temp_warm":   "#ff6d00",
    "temp_mild":   "#29b6f6",
    "temp_cold":   "#00e5ff",

    # Sun / cloud art
    "sun_core":    "#ffe066",
    "sun_outer":   "#ffb300",
    "sun_glow":    "#ff8f00",
    "ray_col":     "#ffd54f",
    "cloud_hi":    "#f0f8ff",
    "cloud_lo":    "#c9dff5",
    "rain_drop":   "#42a5f5",
    "snow_dot":    "#e3f2fd",
    "storm_bolt":  "#ffd600",
    "mist_col":    "#80deea",
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

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ─── HELPER: pick hero colours from condition / temp ──────────
def hero_colours(temp: float, cond: str):
    """Return (top, mid, bot) gradient hex strings."""
    d = cond.lower()
    if "thunder" in d or "storm" in d:
        base = C["hero_storm"]
    elif "rain" in d or "drizzle" in d:
        base = C["hero_rain"]
    elif "snow" in d or "sleet" in d:
        base = C["hero_snow"]
    elif "cloud" in d or "mist" in d or "fog" in d or "haze" in d:
        base = C["hero_cloud"]
    elif temp >= 35:
        base = C["hero_hot"]
    elif temp >= 25:
        base = C["hero_warm"]
    else:
        base = C["hero_mid"]   # default blue

    # Lighten top a bit, darken bottom
    def _lshift(h, amt):
        r, g, b = int(h[1:3],16), int(h[3:5],16), int(h[5:7],16)
        return "#{:02x}{:02x}{:02x}".format(
            min(255, r+amt), min(255, g+amt), min(255, b+amt))
    def _dshift(h, amt):
        r, g, b = int(h[1:3],16), int(h[3:5],16), int(h[5:7],16)
        return "#{:02x}{:02x}{:02x}".format(
            max(0, r-amt), max(0, g-amt), max(0, b-amt))

    return _lshift(base, 28), base, _dshift(base, 28)


def temp_colour(t: float) -> str:
    if t >= 35:  return C["temp_hot"]
    if t >= 25:  return C["temp_warm"]
    if t >= 11:  return C["temp_mild"]
    return C["temp_cold"]


def get_weather_emoji_local(desc):
    return get_weather_emoji(desc.lower(), WEATHER_EMOJIS)


# ─── CANVAS WEATHER ICON ──────────────────────────────────────
def draw_icon(canvas: tk.Canvas, cond: str, size: int = 80):
    canvas.delete("all")
    c = cond.lower()
    cx, cy, r = size//2, size//2, size//2 - 4
    bg = canvas.cget("bg")

    if "thunder" in c or "storm" in c:
        _icon_storm(canvas, cx, cy, r, bg)
    elif "snow" in c or "sleet" in c:
        _icon_snow(canvas, cx, cy, r, bg)
    elif "rain" in c or "drizzle" in c:
        _icon_rain(canvas, cx, cy, r, bg)
    elif "clear" in c:
        _icon_sun(canvas, cx, cy, r)
    elif "few cloud" in c:
        _icon_sun_cloud(canvas, cx, cy, r, bg)
    elif "cloud" in c or "overcast" in c or "scattered" in c or "broken" in c:
        _icon_cloud(canvas, cx, cy, r, C["cloud_lo"])
    elif "mist" in c or "fog" in c or "haze" in c or "smoke" in c:
        _icon_mist(canvas, cx, cy, r)
    else:
        _icon_sun(canvas, cx, cy, r)


def _icon_sun(canvas, cx, cy, r):
    sr = int(r * 0.42)
    for a in range(0, 360, 45):
        rad = math.radians(a)
        x1 = cx + (sr+5)*math.cos(rad); y1 = cy + (sr+5)*math.sin(rad)
        x2 = cx + (sr+18)*math.cos(rad); y2 = cy + (sr+18)*math.sin(rad)
        canvas.create_line(x1,y1,x2,y2, fill=C["ray_col"], width=3, capstyle="round")
    canvas.create_oval(cx-sr,cy-sr,cx+sr,cy+sr,
                       fill=C["sun_core"], outline=C["sun_glow"], width=2)


def _icon_cloud(canvas, cx, cy, r, col=None):
    col = col or C["cloud_hi"]
    cr = int(r*0.38)
    # bottom bar
    canvas.create_oval(cx-cr, cy+int(cr*0.2), cx+cr, cy+cr*2,
                       fill=col, outline="")
    canvas.create_oval(cx-int(cr*1.4), cy+int(cr*0.7),
                       cx+int(cr*0.2), cy+cr*2, fill=col, outline="")
    canvas.create_oval(cx-int(cr*0.2), cy+int(cr*0.7),
                       cx+int(cr*1.4), cy+cr*2, fill=col, outline="")
    # top puff
    canvas.create_oval(cx-int(cr*0.9), cy-int(cr*0.5),
                       cx+int(cr*0.9), cy+int(cr*0.9), fill=col, outline="")


def _icon_sun_cloud(canvas, cx, cy, r, bg):
    sr = int(r*0.30)
    sx, sy = cx+int(r*0.25), cy-int(r*0.22)
    for a in range(0,360,60):
        rad = math.radians(a)
        x1 = sx+(sr+3)*math.cos(rad); y1 = sy+(sr+3)*math.sin(rad)
        x2 = sx+(sr+12)*math.cos(rad); y2 = sy+(sr+12)*math.sin(rad)
        canvas.create_line(x1,y1,x2,y2, fill=C["ray_col"], width=2, capstyle="round")
    canvas.create_oval(sx-sr,sy-sr,sx+sr,sy+sr,
                       fill=C["sun_core"], outline=C["sun_glow"], width=1)
    _icon_cloud(canvas, cx-int(r*0.1), cy+int(r*0.1), int(r*0.85), C["cloud_hi"])


def _icon_rain(canvas, cx, cy, r, cloud_col=None):
    cloud_col = cloud_col or "#5c8ea8"
    _icon_cloud(canvas, cx, cy-int(r*0.22), r, cloud_col)
    for i, ox in enumerate([-int(r*.45), -int(r*.15), int(r*.15), int(r*.45)]):
        y0 = cy+int(r*0.55)+(i%2)*6
        canvas.create_line(cx+ox, y0, cx+ox-4, y0+int(r*0.32),
                           fill=C["rain_drop"], width=2, capstyle="round")


def _icon_storm(canvas, cx, cy, r):
    _icon_cloud(canvas, cx, cy-int(r*0.28), r, "#7e57c2")
    lx, ly = cx, cy+int(r*0.42)
    pts = [lx+10,ly, lx,ly+18, lx+8,ly+18, lx-4,ly+36, lx+16,ly+14, lx+8,ly+14]
    canvas.create_polygon(pts, fill=C["storm_bolt"], outline="#ffa000", width=1)


def _icon_snow(canvas, cx, cy, r):
    _icon_cloud(canvas, cx, cy-int(r*0.22), r, C["cloud_lo"])
    sx, sy = cx, cy+int(r*0.60)
    sr2 = int(r*0.28)
    for a in range(0,360,60):
        rad = math.radians(a)
        canvas.create_line(sx,sy, sx+sr2*math.cos(rad), sy+sr2*math.sin(rad),
                           fill=C["snow_dot"], width=2, capstyle="round")
    canvas.create_oval(sx-4,sy-4,sx+4,sy+4, fill=C["snow_dot"], outline="")


def _icon_mist(canvas, cx, cy, r):
    for i, yoff in enumerate([-int(r*.25), 0, int(r*.25)]):
        xoff = (i%2)*int(r*.1)
        canvas.create_line(cx-int(r*.55)+xoff, cy+yoff,
                           cx+int(r*.55)+xoff, cy+yoff,
                           fill=C["mist_col"], width=5, capstyle="round")


# ─── CANVAS GRADIENT ──────────────────────────────────────────
def fill_gradient(canvas, w, h, top, mid, bot):
    """Fill canvas with a 3-stop vertical gradient using thin rectangles."""
    steps = h
    for i in range(steps):
        frac = i / steps
        if frac < 0.5:
            t = frac * 2
            r1,g1,b1 = int(top[1:3],16),int(top[3:5],16),int(top[5:7],16)
            r2,g2,b2 = int(mid[1:3],16),int(mid[3:5],16),int(mid[5:7],16)
        else:
            t = (frac-0.5)*2
            r1,g1,b1 = int(mid[1:3],16),int(mid[3:5],16),int(mid[5:7],16)
            r2,g2,b2 = int(bot[1:3],16),int(bot[3:5],16),int(bot[5:7],16)
        r = int(r1+(r2-r1)*t); g = int(g1+(g2-g1)*t); b = int(b1+(b2-b1)*t)
        col = "#{:02x}{:02x}{:02x}".format(r,g,b)
        canvas.create_line(0,i,w,i, fill=col)


# ─── HERO CANVAS: draws the whole top section ─────────────────
HERO_H = 280   # pixel height of the hero canvas

def draw_hero(canvas, w, cond, city, country, day_str, temp, hum, wind_str, pres,
              tc_top, tc_mid, tc_bot, temp_col):
    """Redraw the entire hero canvas."""
    canvas.delete("all")
    h = HERO_H

    # Background gradient
    fill_gradient(canvas, w, h, tc_top, tc_mid, tc_bot)

    # ── Sun (top-right quadrant) ──────────────────────────────
    sun_cx = int(w * 0.70)
    sun_cy = int(h * 0.32)
    sun_r  = 52

    # Outer glow rings
    for ring, alpha_step in [(sun_r+28, "#1a"), (sun_r+18, "#22"), (sun_r+8, "#33")]:
        col = C["sun_outer"] + alpha_step  # won't work in tkinter (no rgba), fake with shaded solid
        # Use lighter version of hero bg to fake glow
        canvas.create_oval(sun_cx-ring, sun_cy-ring, sun_cx+ring, sun_cy+ring,
                           outline=C["sun_glow"], width=1)

    # Sun rays
    for a in range(0, 360, 30):
        rad = math.radians(a)
        x1 = sun_cx + (sun_r+6)*math.cos(rad)
        y1 = sun_cy + (sun_r+6)*math.sin(rad)
        x2 = sun_cx + (sun_r+22)*math.cos(rad)
        y2 = sun_cy + (sun_r+22)*math.sin(rad)
        canvas.create_line(x1,y1,x2,y2, fill=C["ray_col"], width=3, capstyle="round")

    # Sun disk
    canvas.create_oval(sun_cx-sun_r, sun_cy-sun_r, sun_cx+sun_r, sun_cy+sun_r,
                       fill=C["sun_core"], outline=C["sun_outer"], width=3)

    # ── Cloud (centre-right, overlapping sun) ──────────────────
    cx_cloud = int(w * 0.58)
    cy_cloud = int(h * 0.50)
    cw = int(w * 0.30)   # cloud width scale
    cr = int(cw * 0.30)

    # Only draw cloud if condition is cloudy / mixed; always draw for mixed sky
    always_cloud = not ("clear" in cond.lower())
    show_cloud = True  # always show partial cloud for aesthetics

    if show_cloud:
        def cloud_oval(x, y, rw, rh, col=C["cloud_hi"]):
            canvas.create_oval(x-rw, y-rh, x+rw, y+rh, fill=col, outline="")

        # Shadow layer
        cloud_oval(cx_cloud, cy_cloud+8, cr*2+14, cr+8, "#a0bacc")
        # Main cloud body
        cloud_oval(cx_cloud, cy_cloud, cr*2+10, cr+4, C["cloud_hi"])
        cloud_oval(cx_cloud-cr, cy_cloud+int(cr*0.3), cr+6, cr, C["cloud_hi"])
        cloud_oval(cx_cloud+cr, cy_cloud+int(cr*0.3), cr+6, cr, C["cloud_hi"])
        # Top puff
        cloud_oval(cx_cloud-int(cr*0.5), cy_cloud-int(cr*0.6), cr, int(cr*0.9), C["cloud_hi"])
        cloud_oval(cx_cloud+int(cr*0.5), cy_cloud-int(cr*0.6), cr, int(cr*0.9), C["cloud_hi"])
        cloud_oval(cx_cloud, cy_cloud-int(cr*0.8), cr, int(cr*1.0), C["cloud_hi"])

    # ── Left text block ────────────────────────────────────────
    tx = 30
    ty = 30

    # City name (large)
    canvas.create_text(tx, ty, anchor="nw",
        text=city, fill=C["txt_white"],
        font=("Segoe UI", 22, "bold"))

    # Day name
    canvas.create_text(tx, ty+38, anchor="nw",
        text=day_str, fill=C["txt_sub"],
        font=("Segoe UI", 13))

    # Country / coords (small)
    canvas.create_text(tx, ty+60, anchor="nw",
        text=f"📍 {country}", fill=C["txt_dim"],
        font=("Segoe UI", 10))

    # ── Temperature (top right corner) ────────────────────────
    sign = "+" if temp >= 0 else ""
    canvas.create_text(w - 24, ty, anchor="ne",
        text=f"{sign}{temp} °C",
        fill=temp_col,
        font=("Segoe UI", 38, "bold"))

    # ── Stats row (bottom of hero) ─────────────────────────────
    stats_y = h - 48
    # Divider line
    canvas.create_line(tx, stats_y-14, w-tx, stats_y-14,
                       fill=C["border"], width=1)

    # Three stat items
    stats = [
        (f"💧  {hum}%",      "Humidity"),
        (f"💨  {wind_str}",   "Wind"),
        (f"🔼  {pres} hPa",  "Pressure"),
    ]
    gap = (w - tx*2) // 3
    for i, (val, label) in enumerate(stats):
        sx = tx + gap*i + gap//2
        canvas.create_text(sx, stats_y, anchor="center",
            text=val, fill=C["txt_white"],
            font=("Segoe UI", 12, "bold"))
        canvas.create_text(sx, stats_y+16, anchor="center",
            text=label, fill=C["txt_sub"],
            font=("Segoe UI", 9))


# ══════════════════════════════════════════════════════════════
class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("⛅ Smart Weather Forecast")
        self.geometry("440x700")
        self.minsize(400, 600)
        self.configure(bg=C["bg_dark"])
        self.resizable(True, True)

        self.update_idletasks()
        x = (self.winfo_screenwidth()//2) - 220
        y = (self.winfo_screenheight()//2) - 350
        self.geometry(f"440x700+{x}+{y}")

        self._setup_fonts()
        self._build_ui()
        self._bind_keys()

        self.current_data  = None
        self.forecast_data = None
        self._hero_cond    = "clear sky"
        self._hero_temp    = 20

    # ── FONTS ─────────────────────────────────────────────────
    def _setup_fonts(self):
        self.f_city    = font.Font(family="Segoe UI", size=18, weight="bold")
        self.f_h2      = font.Font(family="Segoe UI", size=13, weight="bold")
        self.f_h3      = font.Font(family="Segoe UI", size=11, weight="bold")
        self.f_body    = font.Font(family="Segoe UI", size=11)
        self.f_small   = font.Font(family="Segoe UI", size=9)
        self.f_search  = font.Font(family="Segoe UI", size=12)
        self.f_stat    = font.Font(family="Segoe UI", size=14, weight="bold")
        self.f_day     = font.Font(family="Segoe UI", size=10, weight="bold")
        self.f_temp_fc = font.Font(family="Segoe UI", size=12, weight="bold")
        self.f_mono    = font.Font(family="Consolas", size=10)

    # ── BUILD UI ──────────────────────────────────────────────
    def _build_ui(self):
        # ── Hero canvas ──────────────────────────────────────
        self.hero_canvas = tk.Canvas(self, height=HERO_H,
            bg=C["hero_mid"], highlightthickness=0)
        self.hero_canvas.pack(fill="x")
        self.hero_canvas.bind("<Configure>", self._on_hero_resize)

        # ── Search bar ───────────────────────────────────────
        sf = tk.Frame(self, bg=C["bg_panel"], pady=10)
        sf.pack(fill="x")

        si = tk.Frame(sf, bg=C["bg_card"],
            highlightbackground=C["border"], highlightthickness=1)
        si.pack(fill="x", padx=14)

        tk.Label(si, text="🔍", font=self.f_body,
            bg=C["bg_card"], fg=C["txt_dim"], padx=8).pack(side="left")

        self.entry = tk.Entry(si, font=self.f_search,
            bg=C["bg_card"], fg=C["txt_white"],
            insertbackground=C["acc_blue"],
            relief="flat", bd=0)
        self.entry.pack(side="left", fill="x", expand=True, ipady=9)
        self.entry.insert(0, "Search city name...")
        self.entry.bind("<FocusIn>",  self._clear_ph)
        self.entry.bind("<FocusOut>", self._restore_ph)

        self.btn_search = tk.Button(si, text=" Search ",
            font=self.f_h3, bg=C["acc_blue"], fg="white",
            activebackground="#1565c0", activeforeground="white",
            relief="flat", bd=0, padx=12, pady=9, cursor="hand2",
            command=self._start_search)
        self.btn_search.pack(side="right", padx=3, pady=3)

        # Status line
        self.lbl_status = tk.Label(self,
            text="Enter a city to get started",
            font=self.f_small, bg=C["bg_panel"], fg=C["txt_dim"])
        self.lbl_status.pack(pady=(0,4))

        # ── Details strip ─────────────────────────────────────
        ds = tk.Frame(self, bg=C["bg_card"],
            highlightbackground=C["border"], highlightthickness=1)
        ds.pack(fill="x", padx=14, pady=(2,6))

        self.det_labels = {}
        det_items = [
            ("Feels Like", "feels"),
            ("Visibility",  "vis"),
            ("Condition",   "cond"),
        ]
        for col_i, (lbl, key) in enumerate(det_items):
            ds.columnconfigure(col_i, weight=1)
            col = tk.Frame(ds, bg=C["bg_card"], pady=8)
            col.grid(row=0, column=col_i, sticky="nsew",
                padx=1 if col_i else 0)
            if col_i > 0:
                sep = tk.Frame(col, bg=C["border"], width=1)
                sep.pack(side="left", fill="y")
            inner = tk.Frame(col, bg=C["bg_card"])
            inner.pack(fill="both", expand=True)
            tk.Label(inner, text=lbl, font=self.f_small,
                bg=C["bg_card"], fg=C["txt_dim"]).pack()
            v = tk.Label(inner, text="—", font=self.f_h3,
                bg=C["bg_card"], fg=C["txt_white"])
            v.pack()
            self.det_labels[key] = v

        # ── Forecast bar label ────────────────────────────────
        tk.Label(self, text="  7-Day Forecast",
            font=self.f_small, bg=C["bg_panel"],
            fg=C["txt_sub"], anchor="w").pack(fill="x", padx=14)

        # ── Forecast strip ────────────────────────────────────
        self.fc_frame = tk.Frame(self, bg=C["bg_panel"])
        self.fc_frame.pack(fill="x", padx=14, pady=(2,10))

        self.fc_slots = []
        for i in range(7):
            slot_frame = tk.Frame(self.fc_frame, bg=C["fc_normal"],
                highlightbackground=C["fc_border"], highlightthickness=1,
                padx=4, pady=6, cursor="hand2")
            slot_frame.pack(side="left", fill="both", expand=True, padx=(0,3))

            lbl_day = tk.Label(slot_frame, text="—", font=self.f_day,
                bg=C["fc_normal"], fg=C["acc_blue"])
            lbl_day.pack()

            # Canvas icon for forecast (small)
            ic = tk.Canvas(slot_frame, width=36, height=36,
                bg=C["fc_normal"], highlightthickness=0)
            ic.pack(pady=2)

            lbl_hi = tk.Label(slot_frame, text="—", font=self.f_temp_fc,
                bg=C["fc_normal"], fg=C["txt_white"])
            lbl_hi.pack()
            lbl_lo = tk.Label(slot_frame, text="—", font=self.f_small,
                bg=C["fc_normal"], fg=C["txt_dim"])
            lbl_lo.pack()

            slot = {"frame": slot_frame, "day": lbl_day,
                    "canvas": ic, "hi": lbl_hi, "lo": lbl_lo}
            self.fc_slots.append(slot)

            def _activate(e, idx=i):
                self._set_active_fc(idx)
            for w in [slot_frame, lbl_day, ic, lbl_hi, lbl_lo]:
                w.bind("<Button-1>", _activate)

        # Clock at very bottom
        self.lbl_clock = tk.Label(self, text="",
            font=self.f_small, bg=C["bg_panel"], fg=C["txt_dim"])
        self.lbl_clock.pack(pady=(0,6))
        self._tick()

    def _set_active_fc(self, idx):
        for i, slot in enumerate(self.fc_slots):
            bg = C["fc_active"] if i == idx else C["fc_normal"]
            slot["frame"].config(bg=bg)
            slot["day"].config(bg=bg)
            slot["canvas"].config(bg=bg)
            slot["hi"].config(bg=bg)
            slot["lo"].config(bg=bg)

    def _on_hero_resize(self, e):
        self._redraw_hero()

    def _redraw_hero(self, d=None):
        w = self.hero_canvas.winfo_width()
        if w < 10:
            return
        # Reuse last known data or show placeholder
        cond    = getattr(self, "_hero_cond", "clear sky")
        city    = getattr(self, "_hero_city", "Some City")
        country = getattr(self, "_hero_country", "")
        day_str = getattr(self, "_hero_day", datetime.now().strftime("%A"))
        temp    = getattr(self, "_hero_temp", 20)
        hum     = getattr(self, "_hero_hum", "—")
        wind_s  = getattr(self, "_hero_wind", "— km/h")
        pres    = getattr(self, "_hero_pres", "—")
        tc      = getattr(self, "_hero_tcol", C["temp_mild"])

        top, mid, bot = hero_colours(temp, cond)
        draw_hero(self.hero_canvas, w, cond, city, country, day_str,
                  temp, hum, wind_s, pres, top, mid, bot, tc)

    # ── SEARCH ────────────────────────────────────────────────
    def _bind_keys(self):
        self.entry.bind("<Return>", lambda e: self._start_search())

    def _clear_ph(self, e):
        if self.entry.get() == "Search city name...":
            self.entry.delete(0, "end")
            self.entry.config(fg=C["txt_white"])

    def _restore_ph(self, e):
        if not self.entry.get():
            self.entry.insert(0, "Search city name...")
            self.entry.config(fg=C["txt_dim"])

    def _start_search(self):
        city = self.entry.get().strip()
        if not city or city == "Search city name...":
            messagebox.showwarning("Input Required", "Please enter a city name.")
            return
        self.btn_search.config(state="disabled", text=" Loading... ")
        self.lbl_status.config(text=f"Fetching '{city}'…", fg=C["acc_blue"])
        threading.Thread(target=self._fetch, args=(city,), daemon=True).start()

    def _fetch(self, city):
        try:
            r = requests.get(BASE_URL,
                params={"q": city, "appid": API_KEY, "units": "metric"},
                timeout=10)
            if r.status_code == 401:
                self.after(0, lambda: self._err("Invalid API Key",
                    "Check your key in config/settings.py")); return
            if r.status_code == 404:
                self.after(0, lambda: self._err("City Not Found",
                    f"'{city}' not found.")); return
            r.raise_for_status()
            curr = r.json()
            fr = requests.get(FORECAST_URL,
                params={"q": city, "appid": API_KEY,
                        "units": "metric", "cnt": 56},
                timeout=10)
            fore = fr.json() if fr.ok else None
            self.after(0, lambda: self._render(curr, fore))
        except requests.exceptions.ConnectionError:
            self.after(0, lambda: self._err("No Connection", "Check your network."))
        except requests.exceptions.Timeout:
            self.after(0, lambda: self._err("Timeout", "Request timed out."))
        except Exception as ex:
            self.after(0, lambda: self._err("Error", str(ex)))

    def _render(self, d, fore):
        temp   = round(d["main"]["temp"])
        feels  = round(d["main"]["feels_like"])
        hum    = d["main"]["humidity"]
        pres   = d["main"]["pressure"]
        wind   = round(ms_to_kmh(d["wind"]["speed"]))
        wdir   = get_wind_direction(d["wind"].get("deg", 0))
        vis    = round(meters_to_km(d.get("visibility", 0)))
        cond   = d["weather"][0]["description"]
        city   = d["name"]
        cntry  = d["sys"]["country"]
        day_s  = datetime.now().strftime("%A")
        tc     = temp_colour(temp)
        wind_s = f"{wdir}, {wind} km/h"

        # Cache for resize redraws
        self._hero_cond    = cond
        self._hero_city    = city
        self._hero_country = cntry
        self._hero_day     = day_s
        self._hero_temp    = temp
        self._hero_hum     = hum
        self._hero_wind    = wind_s
        self._hero_pres    = pres
        self._hero_tcol    = tc

        self._redraw_hero()

        # Details strip
        self.det_labels["feels"].config(text=f"{feels}°C")
        self.det_labels["vis"].config(text=f"{vis} km")
        short_cond = cond.title().split()[:2]
        self.det_labels["cond"].config(text=" ".join(short_cond))

        # Forecast
        if fore and fore.get("list"):
            daily = {}
            for item in fore["list"]:
                k = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
                daily.setdefault(k, []).append(item)

            for i, (dk, items) in enumerate(list(daily.items())[:7]):
                if i >= 7: break
                slot = self.fc_slots[i]
                hi  = round(max(x["main"]["temp_max"] for x in items))
                lo  = round(min(x["main"]["temp_min"] for x in items))
                mid_item = items[len(items)//2]
                fc_cond  = mid_item["weather"][0]["description"]
                dt       = datetime.fromtimestamp(items[0]["dt"])
                day_name = DAYS[dt.weekday()].upper()

                slot["day"].config(text=day_name)
                slot["hi"].config(text=f"{'+' if hi >= 0 else ''}{hi}°",
                                  fg=temp_colour(hi))
                slot["lo"].config(text=f"{'+' if lo >= 0 else ''}{lo}°")
                draw_icon(slot["canvas"], fc_cond.lower(), size=36)

        self._set_active_fc(0)
        self.lbl_status.config(
            text=f"✓  {city}, {cntry}  —  updated {datetime.now().strftime('%H:%M')}",
            fg=C["acc_green"])
        self.btn_search.config(state="normal", text=" Search ")

    def _err(self, title, msg):
        self.lbl_status.config(text=f"✗  {msg}", fg=C["acc_red"])
        self.btn_search.config(state="normal", text=" Search ")
        messagebox.showerror(title, msg)

    def _tick(self):
        self.lbl_clock.config(
            text=datetime.now().strftime("🕐  %A, %d %B %Y  •  %I:%M:%S %p"))
        self.after(1000, self._tick)


if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()
