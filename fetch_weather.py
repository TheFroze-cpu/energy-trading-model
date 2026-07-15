import requests
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

DB_PATH = "energy_market.db"

def get_historical_weather():
    # Berechne das exakte Datum von heute und von vor 365 Tagen
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # Die spezielle Archive-API von Open-Meteo für lange Historien
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude=49.89&longitude=10.89&start_date={start_date}&end_date={end_date}&hourly=temperature_2m,windspeed_10m"
    
    print(f"Lade historische Wetterdaten von {start_date} bis {end_date}...")
    try:
        response = requests.get(url)
        data = response.json()
        hourly = data.get("hourly", {})
        if not hourly:
            print("Fehler beim Abruf der historischen Wetterdaten.")
            return pd.DataFrame()
            
        df = pd.DataFrame({
            "Datum": pd.to_datetime(hourly["time"]),
            "Temperatur_C": hourly["temperature_2m"],
            "Wind_kmh": hourly["windspeed_10m"]
        })
        return df
    except Exception as e:
        print(f"Fehler bei historischem Wetter: {e}")
        return pd.DataFrame()

def get_weather_forecast():
    # Wetter-Forecast für die kommenden Tage live von Open-Meteo
    url = "https://api.open-meteo.com/v1/forecast?latitude=49.89&longitude=10.89&hourly=temperature_2m,windspeed_10m"
    print("Lade Wetter-Forecast für morgen...")
    try:
        response = requests.get(url)
        data = response.json()
        hourly = data.get("hourly", {})
        if not hourly:
            print("Fehler beim Abruf des Wetter-Forecasts.")
            return pd.DataFrame()
            
        df = pd.DataFrame({
            "Datum": pd.to_datetime(hourly["time"]),
            "Temperatur_C_Forecast": hourly["temperature_2m"],
            "Wind_kmh_Forecast": hourly["windspeed_10m"]
        })
        return df
    except Exception as e:
        print(f"Fehler bei Wetter-Forecast: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Historisches Wetter speichern
    df_hist = get_historical_weather()
    if not df_hist.empty:
        df_hist.to_sql("weather_data", conn, if_exists="replace", index=False)
        print(f"Erfolg! {len(df_hist)} historische Wetterdaten in 'weather_data' gespeichert.")
        
    # 2. Wetter-Forecast speichern
    df_fore = get_weather_forecast()
    if not df_fore.empty:
        df_fore.to_sql("future_weather", conn, if_exists="replace", index=False)
        print(f"Erfolg! {len(df_fore)} prognostizierte Wetterdaten in 'future_weather' gespeichert.")
        
    conn.close()