# ============================================================
#  config/settings.py
#  ✅ STEP: Replace YOUR_API_KEY_HERE with your actual key
#     from: https://openweathermap.org/api
# ============================================================
 
from dotenv import load_dotenv 
import os

load_dotenv()
API_KEY = os.getenv("API_KEY")
 
BASE_URL     = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
 
# Default units: metric (°C) | imperial (°F) | standard (K)
UNITS = "metric"
 
# App window defaults
APP_TITLE  = "Smart Weather Forecast"
APP_WIDTH  = 920
APP_HEIGHT = 720
 
# Request timeout (seconds)
TIMEOUT = 10
 