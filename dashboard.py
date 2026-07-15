import streamlit as st
import pandas as pd
import sqlite3
import folium
from streamlit_folium import st_folium
import json

st.set_page_config(page_title="Energy Quant Dashboard", layout="wide")
st.title("⚡ Strommarkt Monitoring & Forecast")

@st.cache_data
def load_data():
    conn = sqlite3.connect("energy_market.db")
    df = pd.read_sql("SELECT * FROM master_dataset", conn).set_index("Datum")
    df.index = pd.to_datetime(df.index)
    
    df_load = pd.read_sql("SELECT * FROM grid_load", conn)
    df_load["Datum"] = pd.to_datetime(df_load["Datum"])
    
    try:
        df_forecast = pd.read_sql("SELECT * FROM forecast_results", conn).set_index("Datum")
        df_forecast.index = pd.to_datetime(df_forecast.index)
    except:
        df_forecast = pd.DataFrame()
        
    try:
        df_future = pd.read_sql("SELECT * FROM future_price_forecast", conn).set_index("Datum")
        df_future.index = pd.to_datetime(df_future.index)
    except:
        df_future = pd.DataFrame()
        
    conn.close()
    return df, df_load, df_forecast, df_future

df, df_load, df_forecast, df_future = load_data()

st.subheader("Aktuelle Marktlage")
latest = df.iloc[-1]
col1, col2 = st.columns(2)
col1.metric("Strompreis (aktuell)", f"{latest['Preis_EUR']:.2f} €/MWh")
col2.metric("Netzlast (aktuell)", f"{latest['Verbrauch_MWh']:,.0f} MWh")

# --- Neue Tabs ---
tab1, tab2, tab3 = st.tabs(["🔮 Trading: 24h Prognose", "📊 Backtest & Performance", "📍 Regionale Lastzonen"])

with tab1:
    st.subheader("Day-Ahead Preisprognose (Out-of-Sample)")
    st.info("Diese Vorhersage basiert auf der prognostizierten Netzlast der ÜNB für die kommenden 24 Stunden.")
    if not df_future.empty:
        st.line_chart(df_future["Price_Forecast_EUR"], color="#ff2b2b")
        
        with st.expander("Prognostizierte Netzlast (Feature) anzeigen"):
            st.line_chart(df_future["Load_Forecast_MWh"], color="#2b7dff")
    else:
        st.warning("Noch keine Zukunftsdaten vorhanden. Bitte Pipeline ausführen.")

with tab2:
    st.subheader("Modell-Test (Random Forest vs. Marktpreis)")
    if not df_forecast.empty:
        chart_data = pd.DataFrame({
            "Echter Preis": df_forecast["Target_Price"],
            "Vorhersage": df_forecast["Vorhersage"]
        })
        st.line_chart(chart_data.tail(150))

with tab3:
    st.subheader("Netzlast in den 4 Regelzonen")
    latest_regional = df_load.groupby('Region')['Verbrauch_MWh'].last().reset_index()
    
    region_choice = st.selectbox("Wähle eine Zone für die Historie:", df_load['Region'].unique())
    filtered_load = df_load[df_load['Region'] == region_choice]
    st.line_chart(filtered_load.set_index("Datum")["Verbrauch_MWh"].tail(168))
    
    m = folium.Map(location=[51.1657, 10.4515], zoom_start=5)
    try:
        with open('germany_zones.json', 'r') as f:
            zones_data = json.load(f)
        folium.Choropleth(
            geo_data=zones_data, data=latest_regional,
            columns=['Region', 'Verbrauch_MWh'], key_on='feature.properties.name',
            fill_color='YlOrRd', fill_opacity=0.7, line_opacity=0.2
        ).add_to(m)
    except:
        pass
    st_folium(m, width=800, height=500)