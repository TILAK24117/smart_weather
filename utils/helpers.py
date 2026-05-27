# ============================================================
#  utils/helpers.py
#  All conversion and formatting helper functions
# ============================================================
 
from datetime import datetime, timezone, timedelta
 
 
def kelvin_to_celsius(k):
    """Convert Kelvin to Celsius."""
    return round(k - 273.15, 1)
 
 
def kelvin_to_fahrenheit(k):
    """Convert Kelvin to Fahrenheit."""
    return round((k - 273.15) * 9/5 + 32, 1)
 
 
def celsius_to_fahrenheit(c):
    """Convert Celsius to Fahrenheit."""
    return round((c * 9/5) + 32, 1)
 
 
def ms_to_kmh(ms):
    """Convert meters/second to km/h."""
    return ms * 3.6
 
 
def ms_to_mph(ms):
    """Convert meters/second to miles/hour."""
    return ms * 2.237
 
 
def meters_to_km(m):
    """Convert meters to km, max 10km."""
    return min(round(m / 1000, 1), 10)
 
 
def unix_to_time(unix_ts, timezone_offset_seconds=0):
    """Convert Unix timestamp to human-readable local time."""
    local_ts = unix_ts + timezone_offset_seconds
    dt = datetime.utcfromtimestamp(local_ts)
    return dt.strftime("%I:%M %p")
 
 
def unix_to_date(unix_ts):
    """Convert Unix timestamp to date string."""
    return datetime.fromtimestamp(unix_ts).strftime("%a, %d %b")
 
 
def get_wind_direction(degrees):
    """Convert degrees to cardinal direction."""
    directions = [
        "N", "NNE", "NE", "ENE",
        "E", "ESE", "SE", "SSE",
        "S", "SSW", "SW", "WSW",
        "W", "WNW", "NW", "NNW"
    ]
    idx = round(degrees / 22.5) % 16
    return directions[idx]
 
 
def get_uv_label(uv_index):
    """Return UV risk label from index."""
    if uv_index is None:
        return "N/A"
    uv = float(uv_index)
    if uv < 3:    return "Low"
    if uv < 6:    return "Moderate"
    if uv < 8:    return "High"
    if uv < 11:   return "Very High"
    return "Extreme"
 
 
def get_aqi_label(aqi):
    """Return air quality label from AQI value (1–5 scale from OpenWeather)."""
    labels = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
    return labels.get(aqi, "Unknown")
 
 
def get_weather_emoji(description, emoji_map):
    """Return the best matching emoji for a weather description."""
    desc = description.lower()
    for keyword, emoji in emoji_map.items():
        if keyword in desc:
            return emoji
    return emoji_map.get("default", "🌈")
 
 
def format_pressure(hpa):
    """Format pressure with trend hint."""
    if hpa > 1020:
        return f"{hpa} hPa (High)"
    elif hpa < 1000:
        return f"{hpa} hPa (Low)"
    return f"{hpa} hPa (Normal)"
 
 
def calculate_dew_point(temp_c, humidity_percent):
    """Calculate approximate dew point using Magnus formula."""
    a, b = 17.27, 237.7
    alpha = ((a * temp_c) / (b + temp_c)) + (humidity_percent / 100.0)
    import math
    dew = (b * alpha) / (a - alpha)
    return round(dew, 1)
 
 
def human_readable_timezone(offset_seconds):
    """Convert UTC offset seconds to ±HH:MM string."""
    sign   = "+" if offset_seconds >= 0 else "-"
    total  = abs(offset_seconds)
    hours  = total // 3600
    minutes = (total % 3600) // 60
    return f"UTC{sign}{hours:02d}:{minutes:02d}"
 