import sqlite3
import pandas as pd

DB_PATH = "energy_market.db"

def build_master():
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Daten laden (Fehler abfangen, falls eine Tabelle fehlt)
    try:
        prices = pd.read_sql("SELECT * FROM day_ahead_prices", conn)
        load_raw = pd.read_sql("SELECT * FROM grid_load", conn)
    except Exception as e:
        print("Fehler: 'day_ahead_prices' oder 'grid_load' fehlt in der Datenbank.")
        return pd.DataFrame()

    # 2. Last-Daten für das ML-Modell wieder auf Gesamt-DE aggregieren
    load = load_raw.groupby("Datum")["Verbrauch_MWh"].sum().reset_index()
    
    # 3. Datums-Formatierung
    for df in [prices, load]:
        df["Datum"] = pd.to_datetime(df["Datum"]).dt.round('h')

    # 4. Mergen
    master = prices.merge(load, on="Datum", how="inner")
    
    # Optional: Features mergen, falls vorhanden
    try:
        features = pd.read_sql("SELECT * FROM features", conn)
        features["Datum"] = pd.to_datetime(features["Datum"]).dt.round('h')
        overlap = (set(prices.columns) & set(features.columns)) - {"Datum"}
        features = features.drop(columns=overlap, errors='ignore')
        master = master.merge(features, on="Datum", how="inner")
    except:
        print("Info: Keine Feature-Tabelle gefunden. Fahre ohne fort.")

    master.to_sql("master_dataset", conn, if_exists="replace", index=False)
    conn.close()
    return master

if __name__ == "__main__":
    df = build_master()
    if not df.empty:
        print(f"Master-Datensatz erfolgreich erstellt: {len(df)} Zeilen.")