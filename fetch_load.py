import sqlite3
import time
import pandas as pd
import requests

DB_PATH = "energy_market.db"

def fetch_smard_series(filter_id, region="DE", limit=52):
    """Zieht beliebige SMARD-Datenreihen als DataFrame."""
    index_url = f"https://www.smard.de/app/chart_data/{filter_id}/{region}/index_hour.json"
    try:
        timestamps = requests.get(index_url).json()["timestamps"][-limit:]
    except:
        return pd.DataFrame(columns=["Datum", f"Wert_{filter_id}"])

    all_series = []
    for ts in timestamps:
        data_url = f"https://www.smard.de/app/chart_data/{filter_id}/{region}/{filter_id}_{region}_hour_{ts}.json"
        try:
            resp = requests.get(data_url)
            if resp.status_code == 200:
                all_series.extend(resp.json().get("series", []))
        except:
            pass
        time.sleep(0.05) # Kurze Pause für die API

    df = pd.DataFrame(all_series, columns=["Datum", f"Wert_{filter_id}"])
    df["Datum"] = pd.to_datetime(df["Datum"], unit="ms")
    return df.dropna()

def get_fundamental_history():
    print("Lade reale Netzlast und Einspeisedaten (kann einen Moment dauern)...")
    df_load = fetch_smard_series("410").rename(columns={"Wert_410": "Netzlast_MWh"})
    df_pv = fetch_smard_series("4066").rename(columns={"Wert_4066": "Solar_MWh"})
    df_won = fetch_smard_series("4067").rename(columns={"Wert_4067": "WindOn_MWh"})
    df_woff = fetch_smard_series("4068").rename(columns={"Wert_4068": "WindOff_MWh"})

    df = df_load.merge(df_pv, on="Datum", how="outer") \
                .merge(df_won, on="Datum", how="outer") \
                .merge(df_woff, on="Datum", how="outer").fillna(0)

    # Die fundamental exakte Berechnung
    df["Erneuerbare_MWh"] = df["Solar_MWh"] + df["WindOn_MWh"] + df["WindOff_MWh"]
    df["Residuallast_MWh"] = df["Netzlast_MWh"] - df["Erneuerbare_MWh"]

    # Regionale Verteilung
    zone_shares = {"TenneT": 0.35, "Amprion": 0.30, "50Hertz": 0.20, "TransnetBW": 0.15}
    regional_dfs = []
    for zone, share in zone_shares.items():
        df_zone = df.copy()
        df_zone["Region"] = zone
        df_zone["Netzlast_MWh"] = df_zone["Netzlast_MWh"] * share
        df_zone["Residuallast_MWh"] = df_zone["Residuallast_MWh"] * share
        df_zone["Erneuerbare_MWh"] = df_zone["Erneuerbare_MWh"] * share
        regional_dfs.append(df_zone)
        
    return pd.concat(regional_dfs, ignore_index=True)

def get_fundamental_forecast():
    print("Lade Prognosen für Netzlast und Erneuerbare Energien...")
    df_load = fetch_smard_series("122", limit=2).rename(columns={"Wert_122": "Netzlast_Forecast_MWh"})
    df_pv = fetch_smard_series("125", limit=2).rename(columns={"Wert_125": "Solar_Forecast_MWh"})
    df_won = fetch_smard_series("123", limit=2).rename(columns={"Wert_123": "WindOn_Forecast_MWh"})
    df_woff = fetch_smard_series("124", limit=2).rename(columns={"Wert_124": "WindOff_Forecast_MWh"})

    df = df_load.merge(df_pv, on="Datum", how="outer") \
                .merge(df_won, on="Datum", how="outer") \
                .merge(df_woff, on="Datum", how="outer").fillna(0)

    df["Erneuerbare_Forecast_MWh"] = df["Solar_Forecast_MWh"] + df["WindOn_Forecast_MWh"] + df["WindOff_Forecast_MWh"]
    df["Residual_Forecast_MWh"] = df["Netzlast_Forecast_MWh"] - df["Erneuerbare_Forecast_MWh"]

    return df

if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)
    
    df_historic = get_fundamental_history()
    if not df_historic.empty:
        df_historic.to_sql("grid_load", conn, if_exists="replace", index=False)
        print("Fundamentaldaten Historie (Netzlast & Erneuerbare) gespeichert.")
        
    df_future = get_fundamental_forecast()
    if not df_future.empty:
        df_future.to_sql("future_load", conn, if_exists="replace", index=False)
        print(f"Fundamentaldaten Prognose für {len(df_future)} Stunden gespeichert.")
        
    conn.close()