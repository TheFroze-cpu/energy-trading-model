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
    try:
        df = pd.read_sql("SELECT * FROM master_dataset", conn).set_index("Datum")
        df.index = pd.to_datetime(df.index)
    except:
        df = pd.DataFrame()
    try:
        df_load = pd.read_sql("SELECT * FROM grid_load", conn)
        df_load["Datum"] = pd.to_datetime(df_load["Datum"])
    except:
        df_load = pd.DataFrame()
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
if not df.empty:
    latest = df.iloc[-1]
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Strompreis (aktuell)", f"{latest['Preis_EUR']:.2f} €/MWh")
    col2.metric("Netzlast", f"{latest.get('Netzlast_MWh', 0):,.0f} MWh")
    col3.metric("Residuallast", f"{latest.get('Residuallast_MWh', 0):,.0f} MWh")
    col4.metric("Erneuerbare (Wind+Solar)", f"{latest.get('Erneuerbare_MWh', 0):,.0f} MWh")
    col5.metric("Temperatur", f"{latest.get('Temperatur_C', 0):.1f} °C")
else:
    st.warning("Kein Master-Datensatz gefunden.")

tab1, tab2, tab3 = st.tabs(["🔮 Trading: 24h Prognose", "📊 Backtest & Performance", "📍 Regionale Lastzonen"])

with tab1:
    st.subheader("Day-Ahead Preisprognose (Fundamentaler Ansatz)")
    if not df_future.empty:
        st.line_chart(df_future["Price_Forecast_EUR"], color="#ff2b2b")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Progn. Residuallast (MWh)**")
            if "Residual_Forecast_MWh" in df_future.columns:
                st.line_chart(df_future["Residual_Forecast_MWh"], color="#2b7dff")
        with c2:
            st.markdown("**Progn. Erneuerbare (MWh)**")
            if "Erneuerbare_Forecast_MWh" in df_future.columns:
                st.line_chart(df_future["Erneuerbare_Forecast_MWh"], color="#00ffcc")
        with c3:
            st.markdown("**Progn. Temperatur (°C)**")
            if "Temperatur_C_Forecast" in df_future.columns:
                st.line_chart(df_future["Temperatur_C_Forecast"], color="#ffaa00")
    else:
        st.warning("Noch keine Zukunftsdaten vorhanden.")

with tab2:
    st.subheader("Modell-Test (Random Forest vs. Marktpreis)")
    if not df_forecast.empty:
        df_backtest = df_forecast.copy()
        df_backtest["Absoluter_Fehler_EUR"] = (df_backtest["Target_Price"] - df_backtest["Vorhersage"]).abs()
        
        m1, m2 = st.columns(2)
        m1.metric("Mittlerer absoluter Fehler (MAE)", f"{df_backtest['Absoluter_Fehler_EUR'].mean():.2f} €/MWh")
        m2.metric("Maximaler Prognosefehler", f"{df_backtest['Absoluter_Fehler_EUR'].max():.2f} €/MWh")
        
        st.markdown("**Preispfade im Vergleich (Letzte 150 Stunden):**")
        st.line_chart(pd.DataFrame({
            "Echter Preis": df_backtest["Target_Price"],
            "Vorhersage": df_backtest["Vorhersage"]
        }).tail(150))
        
        st.markdown("**Backtest-Datenübersicht:**")
        display_cols = ["Target_Price", "Vorhersage", "Absoluter_Fehler_EUR", "Residuallast_MWh", "Temperatur_C", "Wind_kmh", "Stunde"]
        existing_cols = [c for c in display_cols if c in df_backtest.columns]
        st.dataframe(df_backtest[existing_cols].tail(10).style.format(precision=2))

with tab3:
    st.subheader("Fundamentaldaten in den Regelzonen")
    last_art = st.radio("Metrik:", ["Netzlast_MWh", "Residuallast_MWh", "Erneuerbare_MWh"])
    
    if not df_load.empty and 'Region' in df_load.columns:
        latest_regional = df_load.groupby('Region')[last_art].last().reset_index()
        region_choice = st.selectbox("Zone für Historie:", df_load['Region'].unique())
        filtered_load = df_load[df_load['Region'] == region_choice]
        st.line_chart(filtered_load.set_index("Datum")[last_art].tail(168))
        
        m = folium.Map(location=[51.1657, 10.4515], zoom_start=5)
        try:
            with open('germany_zones.json', 'r') as f:
                zones_data = json.load(f)
            folium.Choropleth(
                geo_data=zones_data, data=latest_regional,
                columns=['Region', last_art], key_on='feature.properties.name',
                fill_color='YlOrRd', fill_opacity=0.7, line_opacity=0.2
            ).add_to(m)
        except Exception as e:
            st.error(f"Konnte GeoJSON nicht laden: {e}")
        st_folium(m, width=800, height=500)