import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import warnings

warnings.filterwarnings('ignore') # Unterdrückt irrelevante Sklearn-Warnungen

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
    
    df["Target_Price"] = df["Preis_EUR"].shift(-1)
    df = df.dropna()

    X = df[["Preis_EUR", "Verbrauch_MWh"]]
    y = df["Target_Price"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"Modell trainiert! MAE: {mae:.2f} EUR")

    # Historische Ergebnisse speichern
    results = X_test.copy()
    results["Datum"] = df.loc[X_test.index, "Datum"]
    results["Target_Price"] = y_test
    results["Vorhersage"] = preds
    results.to_sql("forecast_results", conn, if_exists="replace", index=False)

    # --- ZUKUNFTS-PROGNOSE (Autoregressiv) ---
    try:
        future_load = pd.read_sql("SELECT * FROM future_load", conn)
        future_load["Datum"] = pd.to_datetime(future_load["Datum"])
        future_load = future_load.sort_values("Datum")
        
        # Startpunkt: Der letzte echte bekannte Strompreis
        current_price = df["Preis_EUR"].iloc[-1]
        future_prices = []
        
        for _, row in future_load.iterrows():
            load_val = row["Load_Forecast_MWh"]
            
            # Modell nimmt den letzten Preis und die zukünftige Last
            X_future = pd.DataFrame([[current_price, load_val]], columns=["Preis_EUR", "Verbrauch_MWh"])
            pred_price = model.predict(X_future)[0]
            
            future_prices.append(pred_price)
            # Der vorhergesagte Preis wird zum "aktuellen" Preis für die nächste Stunde
            current_price = pred_price 
            
        future_load["Price_Forecast_EUR"] = future_prices
        future_load.to_sql("future_price_forecast", conn, if_exists="replace", index=False)
        print("Zukunftsprognose (24h) erfolgreich berechnet und gespeichert!")
    except Exception as e:
        print(f"Konnte Zukunftsprognose nicht erstellen: {e}")

    conn.close()

if __name__ == "__main__":
    train_model()