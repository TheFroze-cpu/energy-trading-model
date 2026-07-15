import sqlite3
import time

import pandas as pd
import requests

DB_PATH = "energy_market.db"


def get_prices():
    # 1. Lade die Index-Liste mit allen verfügbaren Zeitpaketen
    index_url = "https://www.smard.de/app/chart_data/4169/DE-LU/index_hour.json"
    timestamps = requests.get(index_url).json()["timestamps"][-52:]

    # 2. Lade die Preisdaten für die letzten 52 Wochen (ca. 1 Jahr)
    all_series = []
    for ts in timestamps:
        data_url = f"https://www.smard.de/app/chart_data/4169/DE-LU/4169_DE-LU_hour_{ts}.json"
        data = requests.get(data_url).json()["series"]
        all_series.extend(data)
        time.sleep(0.2)

    # 3. Mache eine Tabelle daraus und rechne die Zeit um
    df = pd.DataFrame(all_series, columns=["Datum", "Preis_EUR"])
    df["Datum"] = pd.to_datetime(df["Datum"], unit="ms")

    # 4. Lösche alle leeren Werte (NaN) aus der Zukunft
    df = df.dropna()

    return df


if __name__ == "__main__":
    df = get_prices()

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("day_ahead_prices", conn, if_exists="replace", index=False)
    conn.close()

    print(f"Geladen: {len(df)} Stunden mit Day-Ahead-Preisen\n")
    print("Die 24 aktuellsten echten Strompreise:\n")
    print(df.tail(24).to_string(index=False))
