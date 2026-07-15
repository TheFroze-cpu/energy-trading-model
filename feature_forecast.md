# Feature-Implementierung: Zukunfts-Prognose für 24 Stunden

## Rolle
Du bist ein Senior Python Data Engineer und Quant Researcher.

## Zielsetzung
Erweitere die bestehende Pipeline um eine echte Zukunftsprognose (Weg 2). Das System soll die "Prognostizierte Netzlast" (Load Forecast) für die kommenden 24 Stunden aus dem Internet abrufen und das bestehende Machine-Learning-Modell nutzen, um daraus einen zukünftigen Strompreis (Price Forecast) zu berechnen.

## Strikte Regeln für das Refactoring
1. **Keine Zerstörung bestehender Logik:** Die bisherige Funktionalität (historisches Monitoring, Modell-Test-Set, Dashboard-Zonen) MUSS exakt so erhalten bleiben.
2. **Daten-Pipeline (`fetch_load.py`):**
   - Füge eine NEUE Funktion `get_load_forecast()` hinzu.
   - Nutze die SMARD-API für die "Prognostizierte Netzlast" (Filter-ID: 122, Region: DE-LU oder DE).
   - Speichere diese zukünftigen Daten in einer neuen SQLite-Tabelle namens `future_load`.
3. **Modell-Inferenz (`train_model.py`):**
   - Das Modell soll wie bisher trainiert werden.
   - Lade NACH dem Training die neue Tabelle `future_load`.
   - Nutze das trainierte Modell (`RandomForestRegressor`), um auf Basis der `future_load` die Preise für die nächsten 24 Stunden vorherzusagen.
   - Speichere das Ergebnis (Datum, Load Forecast, Price Forecast) in einer neuen Tabelle `future_price_forecast`.
4. **Dashboard-Erweiterung (`dashboard.py`):**
   - Lade die neue Tabelle `future_price_forecast`.
   - Füge ganz oben im Dashboard (oder in einem neuen Tab "🔮 Zukunfts-Prognose") einen prominenten Chart ein, der den zukünftigen Preis und die prognostizierte Netzlast für die nächsten 24 Stunden anzeigt.
5. **Clean Code:** Ergänze Type Hints und Docstrings für alle neuen Funktionen.