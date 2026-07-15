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
    df = pd.read_sql("SELECT * FROM master_dataset", conn)
    df["Datum"] = pd.to_datetime(df["Datum"])
    df = df.set_index("Datum")
    
    df_load = pd.read_sql("SELECT * FROM grid_load", conn)
    df_load["Datum"] = pd.to_datetime(df_load["Datum"])
    
    try:
        df_forecast = pd.read_sql("SELECT * FROM forecast_results", conn)
        df_forecast["Datum"] = pd.to_datetime(df_forecast["Datum"])
        df_forecast = df_forecast.set_index("Datum")
    except:
        df_forecast = pd.DataFrame()
        
    conn.close()
    return df, df_load, df_forecast

df, df_load, df_forecast = load_data()

# --- KPIs ---
st.subheader("Aktuelle Marktlage")
latest = df.iloc[-1]
col1, col2 = st.columns(2)
col1.metric("Strompreis", f"{latest['Preis_EUR']:.2f} €/MWh")
col2.metric("Netzlast (Gesamt)", f"{latest['Verbrauch_MWh']:,.0f} MWh")

# --- Tabs für Übersichtlichkeit ---
tab1, tab2 = st.tabs(["📊 Modell & Forecast", "📍 Regionale Strompreiszonen"])

with tab1:
    st.subheader("Random Forest Vorhersage vs. Marktpreis")
    if not df_forecast.empty:
        chart_data = pd.DataFrame({
            "Echter Preis": df_forecast["Target_Price"],
            "Vorhersage": df_forecast["Vorhersage"]
        })
        st.line_chart(chart_data.tail(150))
    else:
        st.warning("Keine Vorhersagedaten vorhanden.")

with tab2:
    st.subheader("Netzlast in den 4 Regelzonen")
    
    # 1. Letzte Werte berechnen für die Karte
    latest_regional = df_load.groupby('Region')['Verbrauch_MWh'].last().reset_index()
    
    # Besonderer Blick auf Übertragungsnetze (z.B. Transport in den Süden)
    region_choice = st.selectbox("Wähle eine Zone für die Historie:", df_load['Region'].unique())
    filtered_load = df_load[df_load['Region'] == region_choice]
    st.line_chart(filtered_load.set_index("Datum")["Verbrauch_MWh"].tail(168))
    
    # 2. Interaktive Map
    m = folium.Map(location=[51.1657, 10.4515], zoom_start=5)
    
    try:
        with open('germany_zones.json', 'r') as f:
            zones_data = json.load(f)
            
        folium.Choropleth(
            geo_data=zones_data,
            data=latest_regional,
            columns=['Region', 'Verbrauch_MWh'],
            key_on='feature.properties.name',
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name='Netzlast pro Zone (MWh)'
        ).add_to(m)
    except Exception as e:
        st.error(f"Karten-Fehler: {e}")

    st_folium(m, width=800, height=500)