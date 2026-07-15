import requests
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

def get_historical_weather():
    # Wir berechnen das exakte Datum von heute und von vor 365 Tagen
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    
    # Die spezielle Archive-API von Open-Meteo für lange Historien
    url = f"https://archive-api.open-meteo.com/v1/archive?latitude=49.89&longitude=10.89&start_date={start_date}&end_date={end_date}&hourly=temperature_2m,windspeed_10m"
    
    print(f"Lade Wetterdaten von {start_date} bis {end_date}...")
    response = requests.get(url)
    data = response.json()
    
    hourly = data.get("hourly", {})
    if not hourly:
        print("Fehler beim Abruf der Wetterdaten.")
        return
        
    df = pd.DataFrame({
        "Datum": pd.to_datetime(hourly["time"]),
        "Temperatur_C": hourly["temperature_2m"],
        "Wind_kmh": hourly["windspeed_10m"]
    })
    
    conn = sqlite3.connect("energy_market.db")
    df.to_sql("weather_data", conn, if_exists="replace", index=False)
    conn.close()
    print(f"Erfolg! {len(df)} Stunden Wetterdaten gespeichert.")

if __name__ == "__main__":
    get_historical_weather()