import sqlite3

import pandas as pd

DB_PATH = "energy_market.db"


def build_features():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM day_ahead_prices", conn)

    price_col = "Preis_EUR" if "Preis_EUR" in df.columns else "Price_EUR_MWh"

    df["price_change"] = df[price_col].diff().abs()
    df["rolling_avg_3h"] = df[price_col].rolling(window=3).mean()

    df.to_sql("features", conn, if_exists="replace", index=False)
    conn.close()

    return df


if __name__ == "__main__":
    df = build_features()

    print("Die 5 Stunden mit der stärksten Preisänderung:\n")
    top5 = df.nlargest(5, "price_change")
    print(top5.to_string(index=False))
