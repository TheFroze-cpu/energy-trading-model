import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error
import numpy as np
import warnings

warnings.filterwarnings('ignore')
DB_PATH = "energy_market.db"

def train_model():
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql("SELECT * FROM master_dataset", conn)
    except:
        print("Fehler: master_dataset nicht gefunden.")
        conn.close()
        return

    df["Datum"] = pd.to_datetime(df["Datum"])
    df = df.sort_values("Datum")
    
    df["Target_Price"] = df["Preis_EUR"].shift(-1)
    df = df.dropna()

    # Features basieren jetzt sauber auf der Residuallast
    features = ["Preis_EUR", "Residuallast_MWh", "Temperatur_C", "Wind_kmh", "price_change", "rolling_avg_3h"]
    X = df[features]
    y = df["Target_Price"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    print(f"Modell auf Residuallast trainiert! MAE: {mae:.2f} EUR")

    # Backtest-Ergebnisse speichern
    results = X_test.copy()
    results["Datum"] = df.loc[X_test.index, "Datum"]
    results["Target_Price"] = y_test
    results["Vorhersage"] = preds
    results.to_sql("forecast_results", conn, if_exists="replace", index=False)

    # --- ZUKUNFTS-PROGNOSE ---
    try:
        future_features = pd.read_sql("SELECT * FROM future_features", conn)
        future_features["Datum"] = pd.to_datetime(future_features["Datum"])
        future_features = future_features.sort_values("Datum")
        
        price_history = df["Preis_EUR"].tail(5).tolist()
        future_prices = []
        
        for _, row in future_features.iterrows():
            residual_val = row["Residual_Forecast_MWh"]  # Passt exakt zum Output deiner fetch_load.py
            temp_val = row["Temperatur_C_Forecast"]
            wind_val = row["Wind_kmh_Forecast"]
            
            current_price = price_history[-1]
            
            price_change_val = abs(current_price - price_history[-2])
            rolling_avg_val = np.mean(price_history[-3:])
            
            X_future = pd.DataFrame(
                [[current_price, residual_val, temp_val, wind_val, price_change_val, rolling_avg_val]], 
                columns=["Preis_EUR", "Residuallast_MWh", "Temperatur_C", "Wind_kmh", "price_change", "rolling_avg_3h"]
            )
            pred_price = model.predict(X_future)[0]
            
            future_prices.append(pred_price)
            price_history.append(pred_price)
            
        future_features["Price_Forecast_EUR"] = future_prices
        future_features.to_sql("future_price_forecast", conn, if_exists="replace", index=False)
        print("Zukunftsprognose auf Residuallast-Basis erfolgreich berechnet!")
    except Exception as e:
        print(f"Konnte Zukunftsprognose nicht erstellen: {e}")

    conn.close()

if __name__ == "__main__":
    train_model()