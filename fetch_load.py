import sqlite3
import time
import pandas as pd
import requests

DB_PATH = "energy_market.db"

def get_load():
    # Historische und aktuelle Netzlast (Filter 410)
    filter_id = "410"
    region = "DE"
    index_url = f"https://www.smard.de/app/chart_data/{filter_id}/{region}/index_hour.json"
    
    try:
        timestamps = requests.get(index_url).json()["timestamps"][-52:]
    except:
        return pd.DataFrame()

    all_series = []
    for ts in timestamps:
        data_url = f"https://www.smard.de/app/chart_data/{filter_id}/{region}/{filter_id}_{region}_hour_{ts}.json"
        try:
            resp = requests.get(data_url)
            if resp.status_code == 200:
                all_series.extend(resp.json().get("series", []))
        except:
            pass
        time.sleep(0.2)

    df = pd.DataFrame(all_series, columns=["Datum", "Verbrauch_MWh"])
    df["Datum"] = pd.to_datetime(df["Datum"], unit="ms")
    df = df.dropna()

    zone_shares = {"TenneT": 0.35, "Amprion": 0.30, "50Hertz": 0.20, "TransnetBW": 0.15}
    regional_dfs = []
    for zone, share in zone_shares.items():
        df_zone = df.copy()
        df_zone["Region"] = zone
        df_zone["Verbrauch_MWh"] = df_zone["Verbrauch_MWh"] * share
        regional_dfs.append(df_zone)
        
    return pd.concat(regional_dfs, ignore_index=True)

def get_load_forecast():
    # Prognostizierte Netzlast (Filter 122)
    filter_id = "122"
    region = "DE"
    index_url = f"https://www.smard.de/app/chart_data/{filter_id}/{region}/index_hour.json"
    
    try:
        # Wir brauchen nur die allerneuesten Zeitstempel
        timestamps = requests.get(index_url).json()["timestamps"][-2:]
    except:
        return pd.DataFrame()

    all_series = []
    for ts in timestamps:
        data_url = f"https://www.smard.de/app/chart_data/{filter_id}/{region}/{filter_id}_{region}_hour_{ts}.json"
        try:
            resp = requests.get(data_url)
            if resp.status_code == 200:
                all_series.extend(resp.json().get("series", []))
        except:
            pass
        time.sleep(0.2)

    df = pd.DataFrame(all_series, columns=["Datum", "Load_Forecast_MWh"])
    df["Datum"] = pd.to_datetime(df["Datum"], unit="ms")
    df = df.dropna()
    
    # Filtere nur die Daten, die ab "jetzt" in der Zukunft liegen (max 24h)
    now = pd.Timestamp.utcnow().tz_localize(None)
    df = df[df["Datum"] > now].head(24)
    return df

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    
    df_historic = get_load()
    if not df_historic.empty:
        df_historic.to_sql("grid_load", conn, if_exists="replace", index=False)
        print("Historische Last gespeichert.")
        
    df_future = get_load_forecast()
    if not df_future.empty:
        df_future.to_sql("future_load", conn, if_exists="replace", index=False)
        print(f"Last-Prognose für {len(df_future)} zukünftige Stunden gespeichert.")
        
    conn.close()