import sqlite3
import time
import pandas as pd
import requests

DB_PATH = "energy_market.db"

def get_residual_load():
    # Realisierte Residuallast (Filter 4359 statt ehemals 410)
    filter_id = "4359"
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

    df = pd.DataFrame(all_series, columns=["Datum", "Residuallast_MWh"])
    df["Datum"] = pd.to_datetime(df["Datum"], unit="ms")
    df = df.dropna()

    # Regionale Aufteilung (Die prozentuale Heuristik bezieht sich nun auf die Residuallast)
    zone_shares = {"TenneT": 0.35, "Amprion": 0.30, "50Hertz": 0.20, "TransnetBW": 0.15}
    regional_dfs = []
    for zone, share in zone_shares.items():
        df_zone = df.copy()
        df_zone["Region"] = zone
        df_zone["Residuallast_MWh"] = df_zone["Residuallast_MWh"] * share
        regional_dfs.append(df_zone)
        
    return pd.concat(regional_dfs, ignore_index=True)

def get_residual_forecast():
    # Prognostizierte Residuallast (Filter 122)
    filter_id = "122"
    region = "DE"
    index_url = f"https://www.smard.de/app/chart_data/{filter_id}/{region}/index_hour.json"
    
    try:
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

    # Spalte direkt als Residual_Forecast benennen
    df = pd.DataFrame(all_series, columns=["Datum", "Residual_Forecast_MWh"])
    df["Datum"] = pd.to_datetime(df["Datum"], unit="ms")
    df = df.dropna()
    return df

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    
    df_historic = get_residual_load()
    if not df_historic.empty:
        # Wir behalten die Tabellennamen bei, damit build_master.py nichts vermisst
        df_historic.to_sql("grid_load", conn, if_exists="replace", index=False)
        print("Historische Residuallast in 'grid_load' gespeichert.")
        
    df_future = get_residual_forecast()
    if not df_future.empty:
        # Wir behalten auch hier 'future_load' als Tabellenname bei
        df_future.to_sql("future_load", conn, if_exists="replace", index=False)
        print(f"Residuallast-Prognose für {len(df_future)} Stunden in 'future_load' gespeichert.")
        
    conn.close()