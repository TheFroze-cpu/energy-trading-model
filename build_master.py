import sqlite3
import pandas as pd
from features import build_features 

DB_PATH = "energy_market.db"

def build_master():
    conn = sqlite3.connect(DB_PATH)
    print("Berechne mathematische Preis-Features...")
    build_features() 
    
    try:
        prices = pd.read_sql("SELECT * FROM day_ahead_prices", conn)
        load_raw = pd.read_sql("SELECT * FROM grid_load", conn)
        weather = pd.read_sql("SELECT * FROM weather_data", conn)
        calc_features = pd.read_sql("SELECT * FROM features", conn)
    except Exception as e:
        print(f"Fehler beim Laden der historischen Tabellen: {e}")
        conn.close()
        return pd.DataFrame()

    # Wir aggregieren alle neuen Fundamentaldaten
    load = load_raw.groupby("Datum")[["Netzlast_MWh", "Residuallast_MWh", "Erneuerbare_MWh"]].sum().reset_index()
    
    for df in [prices, load, weather, calc_features]:
        df["Datum"] = pd.to_datetime(df["Datum"]).dt.round('h')

    calc_features = calc_features[["Datum", "price_change", "rolling_avg_3h"]]

    master = prices.merge(load, on="Datum", how="inner")
    master = master.merge(weather, on="Datum", how="inner")
    master = master.merge(calc_features, on="Datum", how="inner")
    
    master["Stunde"] = pd.to_datetime(master["Datum"]).dt.hour
    
    master.to_sql("master_dataset", conn, if_exists="replace", index=False)
    print(f"Master-Datensatz erstellt: {len(master)} Zeilen.")

    try:
        future_load = pd.read_sql("SELECT * FROM future_load", conn)
        future_weather = pd.read_sql("SELECT * FROM future_weather", conn)
        
        future_load["Datum"] = pd.to_datetime(future_load["Datum"]).dt.round('h')
        future_weather["Datum"] = pd.to_datetime(future_weather["Datum"]).dt.round('h')
        
        future_features = pd.merge(future_load, future_weather, on="Datum", how="inner")
        
        now = pd.Timestamp.now('UTC').tz_localize(None)
        future_features = future_features[future_features["Datum"] > now].head(24)
        future_features["Stunde"] = pd.to_datetime(future_features["Datum"]).dt.hour
        
        future_features.to_sql("future_features", conn, if_exists="replace", index=False)
        print(f"Zukunfts-Features für {len(future_features)} Stunden gespeichert.")
    except Exception as e:
        print(f"Konnte Zukunfts-Features nicht zusammenführen: {e}")

    conn.close()
    return master

if __name__ == "__main__":
    build_master()