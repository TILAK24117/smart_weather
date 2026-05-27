# ⛅ Smart Weather Forecast Application

A professional Python desktop application for real-time weather data using
OpenWeatherMap API and Tkinter GUI.

---

## 📁 Project Structure

```
WeatherApp/
├── weather_app.py          ← Main application (run this)
├── requirements.txt        ← Python packages to install
├── README.md               ← This file
│
├── config/
│   ├── __init__.py         ← Makes config a Python package
│   └── settings.py         ← API key and app settings (EDIT THIS)
│
└── utils/
    ├── __init__.py         ← Makes utils a Python package
    └── helpers.py          ← Conversion and formatting functions
```

---

## ⚙️ Setup Instructions

### Step 1 – Install Python 3.10+
- Download from https://python.org/downloads
- During install: ✅ check "Add Python to PATH"
- Verify: `python --version`

### Step 2 – Get a Free API Key
1. Go to https://openweathermap.org/api
2. Click "Sign Up" → create free account
3. Go to "My API Keys" tab
4. Copy your default API key

### Step 3 – Add Your API Key
Open `config/settings.py` and replace:
```python
API_KEY = "YOUR_API_KEY_HERE"
```
with your actual key.

### Step 4 – Install Dependencies
Open terminal/command prompt in the WeatherApp folder:
```bash
pip install -r requirements.txt
```

### Step 5 – Run the App
```bash
python weather_app.py
```

---

## 🌟 Features

- Real-time weather for any city worldwide
- Temperature, humidity, wind speed & direction
- Sunrise/sunset times
- 5-day forecast
- Search history with click-to-reload
- Dark theme UI
- Live clock in header
- Error handling for invalid cities / no internet

---

## 📡 API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `/data/2.5/weather` | Current weather |
| `/data/2.5/forecast` | 5-day / 3-hour forecast |

Free tier: 60 calls/minute, 1,000,000 calls/month

---

## 🛠 Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core language |
| Tkinter | GUI framework (built-in) |
| requests | HTTP API calls |
| threading | Non-blocking API requests |
| datetime | Time/date formatting |
| OpenWeatherMap | Weather data source |