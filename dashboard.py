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
    
    # Enthält nun die Residuallast-Daten aus grid_load
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
col1, col2, col3, col4 = st.columns(4)
col1.metric("Strompreis (aktuell)", f"{latest['Preis_EUR']:.2f} €/MWh")

# HIER WAR DER FEHLER: Wir mappen nun auf 'Residuallast_MWh'
col2.metric("Residuallast (aktuell)", f"{latest['Residuallast_MWh']:,.0f} MWh")

col3.metric("Temperatur (aktuell)", f"{latest['Temperatur_C']:.1f} °C")
col4.metric("Windgeschwindigkeit", f"{latest['Wind_kmh']:.1f} km/h")

tab1, tab2, tab3 = st.tabs(["🔮 Trading: 24h Prognose", "📊 Backtest & Performance", "📍 Regionale Lastzonen"])

with tab1:
    st.subheader("Day-Ahead Preisprognose (Out-of-Sample)")
    st.info("Diese Vorhersage basiert auf der prognostizierten Residuallast und der Wetterprognose (Temperatur & Wind) für morgen.")
    if not df_future.empty:
        st.line_chart(df_future["Price_Forecast_EUR"], color="#ff2b2b")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Prognostizierte Residuallast (MWh)**")
            st.line_chart(df_future["Residual_Forecast_MWh"], color="#2b7dff")
        with c2:
            st.markdown("**Prognostizierte Temperatur (°C)**")
            st.line_chart(df_future["Temperatur_C_Forecast"], color="#ffaa00")
        with c3:
            st.markdown("**Prognostizierte Windgeschwindigkeit (km/h)**")
            st.line_chart(df_future["Wind_kmh_Forecast"], color="#00ffcc")
    else:
        st.warning("Noch keine Zukunftsdaten vorhanden. Bitte Pipeline ausführen.")

with tab2:
    st.subheader("Modell-Test (Random Forest vs. Marktpreis)")
    
    if not df_forecast.empty:
        # Berechne die neue Spalte für den Backtest-Fehler direkt im Dataframe
        df_backtest = df_forecast.copy()
        df_backtest["Absoluter_Fehler_EUR"] = (df_backtest["Target_Price"] - df_backtest["Vorhersage"]).abs()
        
        # 1. Metriken zur Performance
        mean_error = df_backtest["Absoluter_Fehler_EUR"].mean()
        max_error = df_backtest["Absoluter_Fehler_EUR"].max()
        
        m1, m2 = st.columns(2)
        m1.metric("Mittlerer absoluter Fehler (MAE)", f"{mean_error:.2f} €/MWh")
        m2.metric("Maximaler Prognosefehler", f"{max_error:.2f} €/MWh")
        
        # 2. Chart mit den Kurven
        st.markdown("**Preispfade im Vergleich (Letzte 150 Stunden des Test-Sets):**")
        chart_data = pd.DataFrame({
            "Echter Preis": df_backtest["Target_Price"],
            "Vorhersage": df_backtest["Vorhersage"]
        })
        st.line_chart(chart_data.tail(150))
        
        # 3. Das Highlight: Visualisierung des Fehlers als eigene Spalte/Chart
        st.markdown("**Der Prognosefehler über die Zeit (Neue Spalte: Absoluter Fehler in €):**")
        st.area_chart(df_backtest["Absoluter_Fehler_EUR"].tail(150), color="#ff4b4b")
        
        # 4. Datentabelle mit der neuen Spalte anzeigen
        st.markdown("**Backtest-Datenübersicht (Letzte 10 Teststunden):**")
        display_cols = ["Target_Price", "Vorhersage", "Absoluter_Fehler_EUR", "Residuallast_MWh", "Temperatur_C", "Wind_kmh"]
        # Falls Spalten fehlen sollten, filtern wir nur die vorhandenen heraus
        existing_cols = [c for c in display_cols if c in df_backtest.columns]
        
        st.dataframe(
            df_backtest[existing_cols].tail(10).style.format({
                "Target_Price": "{:.2f} €",
                "Vorhersage": "{:.2f} €",
                "Absoluter_Fehler_EUR": "{:.2f} €",
                "Residuallast_MWh": "{:,.0f} MWh",
                "Temperatur_C": "{:.1f} °C",
                "Wind_kmh": "{:.1f} km/h"
            })
        )
    else:
        st.warning("Keine Backtest-Ergebnisse in 'forecast_results' gefunden. Bitte trainiere das Modell zuerst.")

        
with tab3:
    st.subheader("Residuallast in den 4 Regelzonen")
    latest_regional = df_load.groupby('Region')['Residuallast_MWh'].last().reset_index()
    
    region_choice = st.selectbox("Wähle eine Zone für die Historie:", df_load['Region'].unique())
    filtered_load = df_load[df_load['Region'] == region_choice]
    st.line_chart(filtered_load.set_index("Datum")["Residuallast_MWh"].tail(168))
    
    m = folium.Map(location=[51.1657, 10.4515], zoom_start=5)
    try:
        with open('germany_zones.json', 'r') as f:
            zones_data = json.load(f)
        folium.Choropleth(
            geo_data=zones_data, data=latest_regional,
            columns=['Region', 'Residuallast_MWh'], key_on='feature.properties.name',
            fill_color='YlOrRd', fill_opacity=0.7, line_opacity=0.2
        ).add_to(m)
    except:
        pass
    st_folium(m, width=800, height=500)