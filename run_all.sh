#!/bin/bash

# Farben für die Ausgabe im Terminal
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}--- Starte Daten-Pipeline ---${NC}"

# Step 1: Alle Datenquellen abrufen & vorbereiten
echo "Lade Day-Ahead-Preise von der Börse..."
python3 fetch_prices.py

echo "Lade neue Netzlast-Daten von SMARD..."
python3 fetch_load.py

echo "Lade historische und prognostizierte Wetterdaten..."
python3 fetch_weather.py

echo "Erstelle geografische Zonen-Grenzdaten (GeoJSON)..."
python3 generate_zones.py

# Step 2: Daten transformieren und mergen
echo "Baue Master-Datensatz..."
python3 build_master.py

# Step 3: Modell trainieren und Prognose berechnen
echo "Trainiere Modell und berechne 24h-Preispfad..."
python3 train_model.py

echo -e "${GREEN}--- Pipeline abgeschlossen. Dashboard startet jetzt! ---${NC}"

# Step 4: Dashboard starten
streamlit run dashboard.py