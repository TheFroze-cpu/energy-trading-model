import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

DB_PATH = "energy_market.db"

def train_model():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM master_dataset", conn)
    except:
        print("Fehler: master_dataset nicht gefunden.")
        return

    df["Datum"] = pd.to_datetime(df["Datum"])
    df = df.sort_values("Datum")
    
    # Ziel: Preis für die nächste Stunde vorhersagen
    df["Target_Price"] = df["Preis_EUR"].shift(-1)
    df = df.dropna()

    # Wir nutzen Verbrauch und aktuellen Preis als Features
    X = df[["Preis_EUR", "Verbrauch_MWh"]]
    y = df["Target_Price"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"Modell trainiert! Mittlerer Vorhersagefehler (MAE): {mae:.2f} EUR")

    # Ergebnisse für das Dashboard speichern
    results = X_test.copy()
    results["Datum"] = df.loc[X_test.index, "Datum"]
    results["Target_Price"] = y_test
    results["Vorhersage"] = preds
    
    results.to_sql("forecast_results", conn, if_exists="replace", index=False)
    conn.close()

if __name__ == "__main__":
    train_model()