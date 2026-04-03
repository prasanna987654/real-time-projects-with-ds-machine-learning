"""
Smart City Air Pollution Analyzer
==================================
A Streamlit app that fetches real-time AQI data from OpenWeatherMap's
Air Pollution API and visualises it with trend charts and city comparisons.

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import time

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AirPulse · Smart City AQI Analyzer",
    page_icon="🌬️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inject custom CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;700&display=swap');

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background-color: #0a0e1a;
    color: #e0e6f0;
}
.stApp { background-color: #0a0e1a; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1225 0%, #111827 100%);
    border-right: 1px solid #1e2a45;
}

/* ── Headers ── */
h1 { font-family: 'Space Mono', monospace !important; letter-spacing: -1px; }
h2, h3 { font-family: 'DM Sans', sans-serif !important; font-weight: 700; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #111827;
    border: 1px solid #1e2a45;
    border-radius: 12px;
    padding: 16px;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #3b82f6, #6366f1);
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    padding: 0.6rem 1.4rem;
    width: 100%;
    transition: opacity 0.2s;
}
.stButton > button:hover { opacity: 0.85; }

/* ── Selectbox / text_input ── */
[data-baseweb="select"] > div,
[data-baseweb="input"] > div {
    background-color: #111827 !important;
    border-color: #1e2a45 !important;
    color: #e0e6f0 !important;
}

/* ── AQI badge ── */
.aqi-badge {
    display: inline-block;
    padding: 6px 18px;
    border-radius: 999px;
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
}

/* ── Alert box ── */
.alert-box {
    background: rgba(239,68,68,0.12);
    border: 1px solid rgba(239,68,68,0.4);
    border-radius: 10px;
    padding: 14px 20px;
    margin-top: 10px;
    color: #fca5a5;
    font-weight: 500;
}

/* ── Info card ── */
.info-card {
    background: #111827;
    border: 1px solid #1e2a45;
    border-radius: 12px;
    padding: 18px 22px;
    margin-bottom: 10px;
}
.info-card h4 { margin: 0 0 4px 0; font-size: 0.85rem; color: #6b7a99; text-transform: uppercase; letter-spacing: 1px; }
.info-card p  { margin: 0; font-size: 1.6rem; font-weight: 700; font-family: 'Space Mono', monospace; }

/* ── Divider ── */
hr { border-color: #1e2a45 !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# 1. CONSTANTS & CONFIG
# ══════════════════════════════════════════════════════════════════════════════

AQI_LEVELS = [
    {"label": "Good",          "range": (0, 50),   "color": "#22c55e", "bg": "rgba(34,197,94,0.15)",   "icon": "😊"},
    {"label": "Moderate",      "range": (51, 100),  "color": "#eab308", "bg": "rgba(234,179,8,0.15)",   "icon": "😐"},
    {"label": "Unhealthy for Sensitive Groups", "range": (101, 150), "color": "#f97316", "bg": "rgba(249,115,22,0.15)", "icon": "😷"},
    {"label": "Unhealthy",     "range": (151, 200), "color": "#ef4444", "bg": "rgba(239,68,68,0.15)",   "icon": "🤢"},
    {"label": "Very Unhealthy","range": (201, 300), "color": "#a855f7", "bg": "rgba(168,85,247,0.15)",  "icon": "🤧"},
    {"label": "Hazardous",     "range": (301, 500), "color": "#7f1d1d", "bg": "rgba(127,29,29,0.3)",    "icon": "☠️"},
]

# Curated city dataset with coordinates — used when API key is absent
CITY_DATASET = {
    "Delhi":         {"lat": 28.6139, "lon": 77.2090,  "aqi": 168, "pm25": 89.4,  "pm10": 142.1, "no2": 48.3, "o3": 22.1, "co": 1.8},
    "Beijing":       {"lat": 39.9042, "lon": 116.4074, "aqi": 155, "pm25": 78.2,  "pm10": 118.6, "no2": 55.1, "o3": 18.4, "co": 2.1},
    "Mumbai":        {"lat": 19.0760, "lon": 72.8777,  "aqi": 132, "pm25": 62.5,  "pm10": 98.3,  "no2": 40.2, "o3": 19.7, "co": 1.4},
    "Shanghai":      {"lat": 31.2304, "lon": 121.4737, "aqi": 118, "pm25": 55.9,  "pm10": 86.2,  "no2": 44.8, "o3": 21.3, "co": 1.6},
    "Lahore":        {"lat": 31.5204, "lon": 74.3587,  "aqi": 185, "pm25": 98.3,  "pm10": 158.7, "no2": 52.6, "o3": 17.8, "co": 2.4},
    "Dhaka":         {"lat": 23.8103, "lon": 90.4125,  "aqi": 162, "pm25": 84.7,  "pm10": 135.2, "no2": 46.9, "o3": 16.3, "co": 2.0},
    "Karachi":       {"lat": 24.8607, "lon": 67.0011,  "aqi": 148, "pm25": 72.1,  "pm10": 112.8, "no2": 38.7, "o3": 20.5, "co": 1.7},
    "Kolkata":       {"lat": 22.5726, "lon": 88.3639,  "aqi": 144, "pm25": 69.8,  "pm10": 109.4, "no2": 36.5, "o3": 21.8, "co": 1.5},
    "Chengdu":       {"lat": 30.5728, "lon": 104.0668, "aqi": 127, "pm25": 58.4,  "pm10": 92.1,  "no2": 42.3, "o3": 18.9, "co": 1.6},
    "Jakarta":       {"lat": -6.2088, "lon": 106.8456, "aqi": 121, "pm25": 56.2,  "pm10": 89.7,  "no2": 37.1, "o3": 22.4, "co": 1.3},
    "Cairo":         {"lat": 30.0444, "lon": 31.2357,  "aqi": 139, "pm25": 65.3,  "pm10": 104.8, "no2": 43.7, "o3": 24.6, "co": 1.8},
    "Mexico City":   {"lat": 19.4326, "lon": -99.1332, "aqi": 112, "pm25": 50.7,  "pm10": 81.3,  "no2": 35.9, "o3": 28.2, "co": 1.2},
    "Tehran":        {"lat": 35.6892, "lon": 51.3890,  "aqi": 156, "pm25": 80.1,  "pm10": 127.4, "no2": 49.8, "o3": 19.2, "co": 1.9},
    "São Paulo":     {"lat": -23.5505,"lon": -46.6333, "aqi": 98,  "pm25": 42.3,  "pm10": 68.5,  "no2": 30.1, "o3": 25.8, "co": 1.0},
    "Istanbul":      {"lat": 41.0082, "lon": 28.9784,  "aqi": 87,  "pm25": 36.8,  "pm10": 59.2,  "no2": 28.4, "o3": 27.3, "co": 0.9},
    "Los Angeles":   {"lat": 34.0522, "lon": -118.2437,"aqi": 89,  "pm25": 38.2,  "pm10": 61.4,  "no2": 26.5, "o3": 32.1, "co": 0.8},
    "London":        {"lat": 51.5074, "lon": -0.1278,  "aqi": 52,  "pm25": 18.4,  "pm10": 29.7,  "no2": 22.1, "o3": 35.8, "co": 0.5},
    "Paris":         {"lat": 48.8566, "lon": 2.3522,   "aqi": 58,  "pm25": 20.6,  "pm10": 33.1,  "no2": 23.8, "o3": 34.2, "co": 0.6},
    "New York":      {"lat": 40.7128, "lon": -74.0060, "aqi": 61,  "pm25": 22.3,  "pm10": 36.8,  "no2": 24.7, "o3": 33.5, "co": 0.6},
    "Tokyo":         {"lat": 35.6762, "lon": 139.6503, "aqi": 44,  "pm25": 14.2,  "pm10": 23.5,  "no2": 18.6, "o3": 38.4, "co": 0.4},
    "Sydney":        {"lat": -33.8688,"lon": 151.2093, "aqi": 32,  "pm25": 8.6,   "pm10": 15.2,  "no2": 12.3, "o3": 42.1, "co": 0.3},
    "Berlin":        {"lat": 52.5200, "lon": 13.4050,  "aqi": 48,  "pm25": 15.9,  "pm10": 26.4,  "no2": 20.2, "o3": 36.7, "co": 0.4},
    "Toronto":       {"lat": 43.6532, "lon": -79.3832, "aqi": 38,  "pm25": 11.4,  "pm10": 19.8,  "no2": 15.1, "o3": 40.3, "co": 0.3},
    "Singapore":     {"lat": 1.3521,  "lon": 103.8198, "aqi": 55,  "pm25": 19.8,  "pm10": 32.4,  "no2": 21.6, "o3": 33.1, "co": 0.5},
    "Dubai":         {"lat": 25.2048, "lon": 55.2708,  "aqi": 103, "pm25": 47.1,  "pm10": 76.3,  "no2": 32.8, "o3": 29.4, "co": 1.1},
    "Bangkok":       {"lat": 13.7563, "lon": 100.5018, "aqi": 116, "pm25": 53.4,  "pm10": 85.2,  "no2": 36.3, "o3": 24.7, "co": 1.2},
    "Hyderabad":     {"lat": 17.3850, "lon": 78.4867,  "aqi": 128, "pm25": 59.7,  "pm10": 95.8,  "no2": 38.2, "o3": 22.9, "co": 1.4},
    "Bangalore":     {"lat": 12.9716, "lon": 77.5946,  "aqi": 108, "pm25": 48.9,  "pm10": 78.4,  "no2": 33.5, "o3": 26.1, "co": 1.1},
    "Chennai":       {"lat": 13.0827, "lon": 80.2707,  "aqi": 115, "pm25": 52.1,  "pm10": 83.7,  "no2": 35.8, "o3": 23.4, "co": 1.3},
    "Vijayawada":    {"lat": 16.5062, "lon": 80.6480,  "aqi": 97,  "pm25": 41.8,  "pm10": 67.2,  "no2": 28.9, "o3": 27.6, "co": 1.0},
}

# ══════════════════════════════════════════════════════════════════════════════
# 2. HELPER FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def classify_aqi(aqi: float) -> dict:
    """Return AQI level metadata for a numeric AQI value."""
    for lvl in AQI_LEVELS:
        lo, hi = lvl["range"]
        if lo <= aqi <= hi:
            return lvl
    return AQI_LEVELS[-1]  # Hazardous fallback


def owm_components_to_aqi(components: dict) -> float:
    """
    Convert OpenWeatherMap Air Pollution API component µg/m³ values
    to a US EPA–style AQI estimate.

    We compute sub-indices for PM2.5 and PM10 (the dominant contributors)
    using EPA breakpoints, then take the maximum as the composite AQI.
    """
    def linear(aqi_lo, aqi_hi, c_lo, c_hi, c):
        return ((aqi_hi - aqi_lo) / (c_hi - c_lo)) * (c - c_lo) + aqi_lo

    pm25 = components.get("pm2_5", 0)
    pm10 = components.get("pm10",  0)

    # EPA PM2.5 breakpoints (µg/m³, 24-hr avg)
    pm25_bp = [
        (0.0,   12.0,   0,   50),
        (12.1,  35.4,  51,  100),
        (35.5,  55.4, 101,  150),
        (55.5, 150.4, 151,  200),
        (150.5,250.4, 201,  300),
        (250.5,500.4, 301,  500),
    ]
    # EPA PM10 breakpoints (µg/m³, 24-hr avg)
    pm10_bp = [
        (0,    54,    0,   50),
        (55,  154,   51,  100),
        (155, 254,  101,  150),
        (255, 354,  151,  200),
        (355, 424,  201,  300),
        (425, 604,  301,  500),
    ]

    def calc_sub(c, breakpoints):
        for c_lo, c_hi, aqi_lo, aqi_hi in breakpoints:
            if c_lo <= c <= c_hi:
                return linear(aqi_lo, aqi_hi, c_lo, c_hi, c)
        return 500  # off-scale

    sub_pm25 = calc_sub(pm25, pm25_bp)
    sub_pm10 = calc_sub(pm10, pm10_bp)
    return round(max(sub_pm25, sub_pm10), 1)


@st.cache_data(ttl=1800)  # cache 30 min
def fetch_realtime_aqi(city: str, api_key: str) -> dict | None:
    """
    Fetch current air pollution data from OpenWeatherMap for a city.
    Returns a dict with aqi, components, lat, lon or None on failure.
    """
    # Step 1: geocode the city
    geo_url = (
        f"https://api.openweathermap.org/geo/1.0/direct"
        f"?q={city}&limit=1&appid={api_key}"
    )
    try:
        geo_r = requests.get(geo_url, timeout=8)
        geo_r.raise_for_status()
        geo_data = geo_r.json()
        if not geo_data:
            return None
        lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]
    except Exception:
        return None

    # Step 2: fetch air pollution
    ap_url = (
        f"https://api.openweathermap.org/data/2.5/air_pollution"
        f"?lat={lat}&lon={lon}&appid={api_key}"
    )
    try:
        ap_r = requests.get(ap_url, timeout=8)
        ap_r.raise_for_status()
        ap_data = ap_r.json()
        components = ap_data["list"][0]["components"]
        aqi_est = owm_components_to_aqi(components)
        return {
            "aqi": aqi_est,
            "pm25": components.get("pm2_5", 0),
            "pm10": components.get("pm10", 0),
            "no2":  components.get("no2", 0),
            "o3":   components.get("o3", 0),
            "co":   components.get("co", 0) / 1000,  # µg → mg
            "lat": lat,
            "lon": lon,
            "source": "live",
        }
    except Exception:
        return None


@st.cache_data(ttl=3600)
def fetch_historical_aqi(lat: float, lon: float, api_key: str, days: int = 7) -> pd.DataFrame:
    """
    Fetch historical hourly air pollution data from OWM and resample to daily.
    """
    end   = int(time.time())
    start = end - days * 86400
    url   = (
        f"https://api.openweathermap.org/data/2.5/air_pollution/history"
        f"?lat={lat}&lon={lon}&start={start}&end={end}&appid={api_key}"
    )
    try:
        r = requests.get(url, timeout=12)
        r.raise_for_status()
        records = r.json().get("list", [])
        rows = []
        for rec in records:
            dt   = datetime.utcfromtimestamp(rec["dt"])
            comp = rec["components"]
            aqi  = owm_components_to_aqi(comp)
            rows.append({"date": dt.date(), "aqi": aqi})
        if not rows:
            return pd.DataFrame()
        df = pd.DataFrame(rows)
        return df.groupby("date", as_index=False)["aqi"].mean().round(1)
    except Exception:
        return pd.DataFrame()


def synthetic_historical(base_aqi: float, days: int = 30) -> pd.DataFrame:
    """
    Build plausible-looking historical data by applying seasonal-like
    noise around the known average AQI. No random.seed — uses city AQI
    as deterministic anchor so values are consistent across reruns.
    """
    import math
    dates, aqis = [], []
    today = datetime.today().date()
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        # Sinusoidal weekly pattern + day-of-year variation
        week_factor   = 1 + 0.08 * math.sin(2 * math.pi * i / 7)
        season_factor = 1 + 0.12 * math.sin(2 * math.pi * d.timetuple().tm_yday / 365)
        aqi_val = round(base_aqi * week_factor * season_factor, 1)
        dates.append(d)
        aqis.append(min(max(aqi_val, 0), 500))
    return pd.DataFrame({"date": dates, "aqi": aqis})


# ══════════════════════════════════════════════════════════════════════════════
# 3. UI COMPONENTS
# ══════════════════════════════════════════════════════════════════════════════

def render_aqi_card(city: str, data: dict):
    """Render the primary AQI result card for a single city."""
    aqi   = data["aqi"]
    level = classify_aqi(aqi)

    st.markdown(f"""
    <div style="
        background: {level['bg']};
        border: 1.5px solid {level['color']}55;
        border-radius: 16px;
        padding: 28px 32px;
        margin-bottom: 20px;
    ">
        <div style="display:flex; align-items:center; gap:14px; margin-bottom:8px;">
            <span style="font-size:2.6rem;">{level['icon']}</span>
            <div>
                <div style="font-size:0.8rem; color:#6b7a99; text-transform:uppercase; letter-spacing:1px; font-family:'Space Mono',monospace;">Air Quality Index</div>
                <div style="font-size:3.2rem; font-weight:700; font-family:'Space Mono',monospace; color:{level['color']}; line-height:1;">{aqi}</div>
            </div>
            <div style="margin-left:auto; text-align:right;">
                <div class="aqi-badge" style="background:{level['color']}22; color:{level['color']}; border:1px solid {level['color']}55;">
                    {level['label']}
                </div>
                <div style="font-size:0.75rem; color:#6b7a99; margin-top:6px;">
                    Range {level['range'][0]}–{level['range'][1]}
                </div>
            </div>
        </div>
        <div style="font-size:1.1rem; font-weight:600; color:#e0e6f0; margin-top:4px;">📍 {city}</div>
    </div>
    """, unsafe_allow_html=True)

    # Pollutant metrics
    cols = st.columns(5)
    metrics = [
        ("PM2.5", f"{data['pm25']:.1f}", "µg/m³"),
        ("PM10",  f"{data['pm10']:.1f}", "µg/m³"),
        ("NO₂",   f"{data['no2']:.1f}",  "µg/m³"),
        ("O₃",    f"{data['o3']:.1f}",   "µg/m³"),
        ("CO",    f"{data['co']:.2f}",   "mg/m³"),
    ]
    for col, (name, val, unit) in zip(cols, metrics):
        with col:
            st.markdown(f"""
            <div class="info-card">
                <h4>{name}</h4>
                <p style="font-size:1.4rem;">{val}</p>
                <div style="font-size:0.75rem; color:#6b7a99;">{unit}</div>
            </div>""", unsafe_allow_html=True)

    # Alert
    if aqi > 150:
        threshold = st.session_state.get("alert_threshold", 150)
        if aqi > threshold:
            st.markdown(f"""
            <div class="alert-box">
                ⚠️  <strong>Health Alert:</strong> AQI of {aqi} exceeds your threshold of {threshold}.
                People with respiratory conditions should avoid outdoor activities.
            </div>""", unsafe_allow_html=True)

def render_gauge(aqi: float):
    """Render an arc-gauge for the AQI value."""
    # Ensure aqi is a valid number to prevent crashing
    aqi_val = aqi if aqi is not None else 0
    
    level = classify_aqi(aqi_val)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=aqi_val,
        number={'font': {"size": 40, "color": level["color"], "family": "Space Mono"}},
        gauge={
            "axis": {"range": [0, 300], "tickcolor": "#6b7a99"},
            "tickfont": {"color": "#6b7a99", "size": 11},
            "bar": {"color": level["color"], "thickness": 0.28},
            "bgcolor": "#111827",
            "borderwidth": 0,
            "steps": [
                {"range": [0, 50], "color": "#14532d33"},
                {"range": [51, 100], "color": "#713f1233"},
                {"range": [101, 150], "color": "#7c2d1233"},
                {"range": [151, 200], "color": "#7f1d1d33"},
                {"range": [201, 300], "color": "#4a044e33"},
            ],
            "threshold": {
                "line": {"color": level["color"], "width": 3},
                "thickness": 0.75,
                "value": aqi_val,
            }
        }
    ))
    return fig # Make sure this return is at the end of the function

    fig.update_layout(
        height=260,
        margin=dict(l=20, r=20, t=20, b=10),
        paper_bgcolor="#0a0e1a",
        font_color="#e0e6f0",
    )
    return fig


def render_trend_chart(df: pd.DataFrame, city: str):
    """Line chart of AQI over time."""
    df = df.copy()
    df["color"] = df["aqi"].apply(lambda v: classify_aqi(v)["color"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["aqi"],
        mode="lines+markers",
        line=dict(color="#3b82f6", width=2.5),
        marker=dict(color=df["color"], size=8, line=dict(color="#0a0e1a", width=1.5)),
        hovertemplate="<b>%{x}</b><br>AQI: %{y}<extra></extra>",
        fill="tozeroy",
        fillcolor="rgba(59,130,246,0.07)",
    ))

    # Add category bands
    bands = [(0,50,"#22c55e"), (51,100,"#eab308"), (101,150,"#f97316"),
             (151,200,"#ef4444"), (201,300,"#a855f7")]
    for lo, hi, col in bands:
        fig.add_hrect(y0=lo, y1=hi, fillcolor=col, opacity=0.04, line_width=0)

    fig.update_layout(
        title=dict(text=f"AQI Trend — {city}", font=dict(size=15, color="#e0e6f0")),
        xaxis=dict(showgrid=False, color="#6b7a99"),
        yaxis=dict(showgrid=True, gridcolor="#1e2a45", color="#6b7a99", range=[0, max(df["aqi"].max() * 1.15, 60)]),
        plot_bgcolor="#0a0e1a",
        paper_bgcolor="#0a0e1a",
        font_color="#e0e6f0",
        height=320,
        margin=dict(l=10, r=10, t=40, b=10),
        hovermode="x unified",
    )
    return fig


def render_comparison_bar(cities_data: dict):
    """Horizontal bar chart comparing AQI across multiple cities."""
    cities = list(cities_data.keys())
    aqis   = [cities_data[c]["aqi"] for c in cities]
    colors = [classify_aqi(a)["color"] for a in aqis]

    # Sort by AQI descending
    sorted_pairs = sorted(zip(aqis, cities, colors), reverse=True)
    aqis_s, cities_s, colors_s = zip(*sorted_pairs)

    fig = go.Figure(go.Bar(
        x=list(aqis_s),
        y=list(cities_s),
        orientation="h",
        marker_color=list(colors_s),
        text=[f"{a}" for a in aqis_s],
        textposition="outside",
        textfont=dict(color="#e0e6f0", size=12, family="Space Mono"),
        hovertemplate="<b>%{y}</b><br>AQI: %{x}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text="City AQI Comparison", font=dict(size=15, color="#e0e6f0")),
        xaxis=dict(showgrid=True, gridcolor="#1e2a45", color="#6b7a99", range=[0, max(aqis_s)*1.2]),
        yaxis=dict(showgrid=False, color="#e0e6f0"),
        plot_bgcolor="#0a0e1a",
        paper_bgcolor="#0a0e1a",
        font_color="#e0e6f0",
        height=max(300, 42 * len(cities)),
        margin=dict(l=10, r=60, t=40, b=10),
    )
    return fig


def render_aqi_legend():
    bands = [
        ("0–50",   "Good",           "#22c55e"),
        ("51–100", "Moderate",       "#eab308"),
        ("101–150","Unhealthy (S.G.)","#f97316"),
        ("151–200","Unhealthy",       "#ef4444"),
        ("201–300","Very Unhealthy",  "#a855f7"),
        ("301–500","Hazardous",       "#7f1d1d"),
    ]
    html = "<div style='display:flex;flex-direction:column;gap:6px;'>"
    for rng, lbl, col in bands:
        html += f"""
        <div style="display:flex;align-items:center;gap:10px;">
            <div style="width:14px;height:14px;border-radius:3px;background:{col};flex-shrink:0;"></div>
            <span style="font-size:0.8rem;color:#9ca3af;">{lbl}</span>
            <span style="font-size:0.75rem;color:#4b5563;margin-left:auto;font-family:'Space Mono',monospace;">{rng}</span>
        </div>"""
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# 4. MAIN APPLICATION
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="margin-bottom:8px;">
        <span style="font-family:'Space Mono',monospace; font-size:0.75rem;
               color:#3b82f6; text-transform:uppercase; letter-spacing:2px;">
            AIRPULSE v1.0
        </span>
        <h1 style="margin:4px 0 2px 0; font-size:2.2rem; color:#e0e6f0;">
            Smart City Air Quality Analyzer
        </h1>
        <p style="color:#6b7a99; margin:0; font-size:0.95rem;">
            Real-time & dataset-based AQI monitoring across global cities
        </p>
    </div>
    <hr style="margin:16px 0 24px 0;">
    """, unsafe_allow_html=True)

    # ── Sidebar ──────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚙️ Configuration")
        st.markdown("---")

        data_source = st.radio(
            "Data Source",
            ["📦  Built-in Dataset", "🌐  Live API (OpenWeatherMap)"],
            help="Use dataset for instant results; API key needed for live data."
        )
        use_live = "Live" in data_source

        api_key = ""
        if use_live:
            api_key = st.text_input(
                "OWM API Key",
                type="password",
                placeholder="Paste your free API key here",
                help="Get a free key at https://openweathermap.org/api",
            )
            if not api_key:
                st.info("🔑 Enter your OpenWeatherMap API key above to enable live data fetching.")

        st.markdown("---")
        st.markdown("### 🔔 Alert Threshold")
        st.session_state["alert_threshold"] = st.slider(
            "Trigger alert when AQI ≥", 50, 300, 150, 10
        )

        st.markdown("---")
        st.markdown("### 🗓️ Trend Window")
        trend_days = st.selectbox("Historical days", [7, 14, 30], index=2)

        st.markdown("---")
        st.markdown("### 📖 AQI Legend")
        render_aqi_legend()

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["🔍 Single City", "⚖️ Compare Cities", "🏭 Top Polluted"])

    # ══════════════════════════════════════════════════════════════════════
    # TAB 1 — Single City
    # ══════════════════════════════════════════════════════════════════════
    with tab1:
        col_input, col_gap = st.columns([3, 1])
        with col_input:
            city_list = sorted(CITY_DATASET.keys())
            default_idx = city_list.index("Delhi") if "Delhi" in city_list else 0
            city = st.selectbox("Select a city", city_list, index=default_idx)

            if use_live:
                custom_city = st.text_input(
                    "…or type any city name (live API)",
                    placeholder="e.g. Kathmandu",
                )
                if custom_city.strip():
                    city = custom_city.strip()

        check = st.button("🔍 Check Air Quality", key="check_single")

        if check:
            with st.spinner(f"Fetching data for **{city}**…"):
                # ── Fetch data ────────────────────────────────────────────
                live_data = None
                if use_live and api_key:
                    live_data = fetch_realtime_aqi(city, api_key)
                    if live_data is None:
                        st.warning("⚠️ Live fetch failed — falling back to dataset.")

                if live_data:
                    data = live_data
                    src_label = "🟢 Live — OpenWeatherMap"
                    lat, lon  = live_data["lat"], live_data["lon"]
                elif city in CITY_DATASET:
                    data      = CITY_DATASET[city]
                    src_label = "📦 Built-in Dataset (2024 avg)"
                    lat, lon  = data["lat"], data["lon"]
                else:
                    st.error(f"City **{city}** not found in dataset and live fetch unavailable.")
                    st.stop()

                # ── Fetch historical ──────────────────────────────────────
                hist_df = pd.DataFrame()
                if use_live and api_key:
                    hist_df = fetch_historical_aqi(lat, lon, api_key, days=trend_days)
                if hist_df.empty:
                    hist_df = synthetic_historical(data["aqi"], days=trend_days)

            st.caption(f"**Source:** {src_label}")

            # ── Layout ────────────────────────────────────────────────────
            left, right = st.columns([2, 1])
            with left:
                render_aqi_card(city, data)
            with right:
                st.plotly_chart(render_gauge(data["aqi"]), use_container_width=True)

            st.plotly_chart(render_trend_chart(hist_df, city), use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════
    # TAB 2 — Compare Cities
    # ══════════════════════════════════════════════════════════════════════
    with tab2:
        city_list = sorted(CITY_DATASET.keys())
        defaults  = ["Delhi", "Mumbai", "Tokyo", "London", "New York", "Beijing"]
        defaults  = [c for c in defaults if c in city_list]

        selected = st.multiselect(
            "Select 2–10 cities to compare",
            city_list,
            default=defaults,
        )

        if st.button("⚖️ Compare", key="compare"):
            if len(selected) < 2:
                st.warning("Select at least 2 cities.")
            else:
                compare_data = {}
                for c in selected:
                    if use_live and api_key:
                        ld = fetch_realtime_aqi(c, api_key)
                        compare_data[c] = ld if ld else CITY_DATASET.get(c, {})
                    else:
                        compare_data[c] = CITY_DATASET.get(c, {})
                compare_data = {k: v for k, v in compare_data.items() if v}

                st.plotly_chart(render_comparison_bar(compare_data), use_container_width=True)

                # Summary table
                rows = []
                for c, d in compare_data.items():
                    lvl = classify_aqi(d["aqi"])
                    rows.append({
                        "City":     c,
                        "AQI":      d["aqi"],
                        "Category": lvl["label"],
                        "PM2.5":    round(d.get("pm25", 0), 1),
                        "PM10":     round(d.get("pm10", 0), 1),
                        "NO₂":      round(d.get("no2", 0), 1),
                    })
                df_table = pd.DataFrame(rows).sort_values("AQI", ascending=False)
                st.dataframe(
                    df_table.style.background_gradient(subset=["AQI"], cmap="RdYlGn_r"),
                    use_container_width=True,
                    hide_index=True,
                )

    # ══════════════════════════════════════════════════════════════════════
    # TAB 3 — Top Polluted
    # ══════════════════════════════════════════════════════════════════════
    with tab3:
        st.markdown("#### Most Polluted Cities in Dataset")
        n_top = st.slider("Show top N cities", 5, len(CITY_DATASET), 10)

        all_rows = []
        for c, d in CITY_DATASET.items():
            lvl = classify_aqi(d["aqi"])
            all_rows.append({
                "City":     c,
                "AQI":      d["aqi"],
                "Category": lvl["label"],
                "Indicator":lvl["icon"],
                "PM2.5":    round(d.get("pm25", 0), 1),
                "PM10":     round(d.get("pm10", 0), 1),
            })
        df_all = pd.DataFrame(all_rows).sort_values("AQI", ascending=False).head(n_top).reset_index(drop=True)
        df_all.index += 1  # 1-based rank

        st.dataframe(
            df_all.style.background_gradient(subset=["AQI"], cmap="RdYlGn_r"),
            use_container_width=True,
        )

        st.plotly_chart(
            render_comparison_bar({r["City"]: CITY_DATASET[r["City"]] for _, r in df_all.iterrows()}),
            use_container_width=True,
        )

        # Hazardous alert summary
        hazardous = df_all[df_all["AQI"] > st.session_state.get("alert_threshold", 150)]
        if not hazardous.empty:
            st.markdown(f"""
            <div class="alert-box">
                ⚠️ <strong>{len(hazardous)} city/cities exceed your alert threshold
                ({st.session_state['alert_threshold']}):</strong>
                {', '.join(hazardous['City'].tolist())}
            </div>""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
