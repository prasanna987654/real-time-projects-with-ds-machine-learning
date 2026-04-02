# 🌬️ AirPulse — Smart City Air Quality Analyzer

A production-grade Streamlit app that shows real AQI values, pollutant
breakdowns, trend charts, and multi-city comparisons.

---

## Quick Start (Dataset Mode — no API key needed)

```bash
# 1. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## Enabling Live API Mode

1. Register at https://openweathermap.org/api (free tier is sufficient)
2. Copy your API key
3. In the app sidebar, choose **"🌐 Live API"** and paste your key
4. The app will fetch real-time air pollution data and the last 7–30 days
   of historical readings for any city worldwide

---

## Features

| Feature | Dataset | Live API |
|---|---|---|
| AQI for 30 pre-loaded cities | ✅ | — |
| Real-time AQI for any city | — | ✅ |
| Historical trend (7/14/30 days) | ✅ synthetic | ✅ real |
| PM2.5, PM10, NO₂, O₃, CO breakdown | ✅ | ✅ |
| Multi-city comparison bar chart | ✅ | ✅ |
| AQI gauge | ✅ | ✅ |
| Configurable health alert threshold | ✅ | ✅ |
| Top-N most polluted cities | ✅ | — |

---

## AQI Classification (US EPA)

| Range | Category |
|---|---|
| 0–50 | 🟢 Good |
| 51–100 | 🟡 Moderate |
| 101–150 | 🟠 Unhealthy for Sensitive Groups |
| 151–200 | 🔴 Unhealthy |
| 201–300 | 🟣 Very Unhealthy |
| 301–500 | ⚫ Hazardous |

---

## Project Structure

```
smart_city_aqi/
├── app.py            ← main application (all logic + UI)
├── requirements.txt  ← Python dependencies
└── README.md         ← this file
```

---

## AQI Calculation Notes

When live API data is used, AQI is computed from raw pollutant
concentrations (µg/m³) using the **US EPA linear interpolation formula**
across PM2.5 and PM10 24-hour breakpoints. The higher sub-index is
reported as the composite AQI — exactly matching the EPA standard.
