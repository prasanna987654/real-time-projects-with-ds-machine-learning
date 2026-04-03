import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import requests
from datetime import datetime, timedelta

# ─────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────
st.set_page_config(
    page_title="AirPulse Smart City AQI Analyzer",
    page_icon="🌬️",
    layout="wide"
)

# ─────────────────────────────────────────
# SAMPLE CITY DATA
# ─────────────────────────────────────────
CITY_DATASET = {

    "Delhi": {"aqi": 185, "lat": 28.61, "lon": 77.20},
    "Mumbai": {"aqi": 95, "lat": 19.07, "lon": 72.87},
    "Hyderabad": {"aqi": 110, "lat": 17.38, "lon": 78.48},
    "Bangalore": {"aqi": 75, "lat": 12.97, "lon": 77.59},
    "Chennai": {"aqi": 90, "lat": 13.08, "lon": 80.27},
    "Kolkata": {"aqi": 140, "lat": 22.57, "lon": 88.36},
    "Pune": {"aqi": 85, "lat": 18.52, "lon": 73.85},
    "Ahmedabad": {"aqi": 120, "lat": 23.02, "lon": 72.57},
    "Jaipur": {"aqi": 130, "lat": 26.91, "lon": 75.79},
    "Lucknow": {"aqi": 150, "lat": 26.84, "lon": 80.94},

    "New York": {"aqi": 80, "lat": 40.71, "lon": -74.00},
    "Los Angeles": {"aqi": 95, "lat": 34.05, "lon": -118.24},
    "Chicago": {"aqi": 70, "lat": 41.87, "lon": -87.62},
    "Toronto": {"aqi": 65, "lat": 43.65, "lon": -79.38},
    "Mexico City": {"aqi": 120, "lat": 19.43, "lon": -99.13},

    "London": {"aqi": 55, "lat": 51.50, "lon": -0.12},
    "Paris": {"aqi": 60, "lat": 48.85, "lon": 2.35},
    "Berlin": {"aqi": 50, "lat": 52.52, "lon": 13.40},
    "Madrid": {"aqi": 70, "lat": 40.41, "lon": -3.70},
    "Rome": {"aqi": 75, "lat": 41.90, "lon": 12.49},

    "Tokyo": {"aqi": 70, "lat": 35.67, "lon": 139.65},
    "Beijing": {"aqi": 160, "lat": 39.90, "lon": 116.40},
    "Shanghai": {"aqi": 140, "lat": 31.23, "lon": 121.47},
    "Seoul": {"aqi": 90, "lat": 37.56, "lon": 126.97},
    "Bangkok": {"aqi": 130, "lat": 13.75, "lon": 100.50},

    "Dubai": {"aqi": 100, "lat": 25.20, "lon": 55.27},
    "Singapore": {"aqi": 65, "lat": 1.35, "lon": 103.82},
    "Sydney": {"aqi": 45, "lat": -33.86, "lon": 151.20},
    "Johannesburg": {"aqi": 85, "lat": -26.20, "lon": 28.04},
    "Cairo": {"aqi": 170, "lat": 30.04, "lon": 31.23}

}
# ─────────────────────────────────────────
# AQI CATEGORY FUNCTION
# ─────────────────────────────────────────
def get_aqi_category(aqi):

    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"

# ─────────────────────────────────────────
# GAUGE CHART
# ─────────────────────────────────────────
def render_gauge(aqi):

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=aqi,
        title={'text': "AQI Level"},
        gauge={
            'axis': {'range': [0, 300]},
            'steps': [
                {'range': [0, 50]},
                {'range': [50, 100]},
                {'range': [100, 150]},
                {'range': [150, 200]},
                {'range': [200, 300]},
            ],
        }
    ))

    return fig

# ─────────────────────────────────────────
# TREND DATA GENERATOR
# ─────────────────────────────────────────
def synthetic_historical(base_aqi, days=14):

    dates = []
    values = []

    for i in range(days):
        date = datetime.now() - timedelta(days=i)
        value = base_aqi + np.random.randint(-20, 20)

        dates.append(date)
        values.append(max(10, value))

    df = pd.DataFrame({
        "Date": dates,
        "AQI": values
    })

    return df.sort_values("Date")

# ─────────────────────────────────────────
# TREND CHART
# ─────────────────────────────────────────
def render_trend_chart(df, city):

    fig = px.line(
        df,
        x="Date",
        y="AQI",
        title=f"{city} AQI Trend",
        markers=True
    )

    return fig

# ─────────────────────────────────────────
# COMPARISON BAR
# ─────────────────────────────────────────
def render_comparison_bar(data):

    df = pd.DataFrame([
        {"City": c, "AQI": d["aqi"]}
        for c, d in data.items()
    ])

    fig = px.bar(
        df,
        x="City",
        y="AQI",
        title="City AQI Comparison"
    )

    return fig

# ─────────────────────────────────────────
# AQI CARD
# ─────────────────────────────────────────
def render_aqi_card(city, data):

    category = get_aqi_category(data["aqi"])

    st.metric(
        label=f"{city} AQI",
        value=data["aqi"],
        delta=category
    )

# ─────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────
def main():

    st.title("🌬️ AirPulse · Smart City AQI Analyzer")

    # Sidebar
    st.sidebar.header("Settings")

    city = st.sidebar.selectbox(
        "Select City",
        list(CITY_DATASET.keys())
    )

    trend_days = st.sidebar.slider("Trend Days", 7, 30, 14)

    # Tabs
    tab1, tab2, tab3 = st.tabs([
        "AQI Dashboard",
        "Compare Cities",
        "Top Polluted"
    ])

    # ───────── TAB 1 ─────────
    with tab1:

        data = CITY_DATASET[city]

        hist_df = synthetic_historical(data["aqi"], trend_days)

        col1, col2 = st.columns(2)

        with col1:
            render_aqi_card(city, data)

        with col2:
            st.plotly_chart(
                render_gauge(data["aqi"]),
                use_container_width=True
            )

        st.plotly_chart(
            render_trend_chart(hist_df, city),
            use_container_width=True
        )

    # ───────── TAB 2 ─────────
    with tab2:

        selected = st.multiselect(
            "Select Cities",
            list(CITY_DATASET.keys()),
            default=["Delhi", "Mumbai", "London"]
        )

        if selected:

            compare_data = {
                c: CITY_DATASET[c]
                for c in selected
            }

            st.plotly_chart(
                render_comparison_bar(compare_data),
                use_container_width=True
            )

    # ───────── TAB 3 ─────────
    with tab3:

        df = pd.DataFrame([
            {"City": c, "AQI": d["aqi"]}
            for c, d in CITY_DATASET.items()
        ])

        df = df.sort_values("AQI", ascending=False)

        st.dataframe(
            df.style.background_gradient(
                subset=["AQI"],
                cmap="RdYlGn_r"
            ),
            use_container_width=True
        )

        st.plotly_chart(
            render_comparison_bar(CITY_DATASET),
            use_container_width=True
        )

# ─────────────────────────────────────────
# RUN APP
# ─────────────────────────────────────────
if __name__ == "__main__":
    main()
