#!/bin/bash

# Farben für die Ausgabe im Terminal
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${GREEN}--- Starte Daten-Pipeline ---${NC}"

# 1. Daten holen
echo "Lade neue Netzlast-Daten..."
python3 fetch_load.py

# 2. Master-Datensatz bauen
echo "Baue Master-Datensatz..."
python3 build_master.py

# 3. Modell trainieren
echo "Trainiere Modell..."
python3 train_model.py

echo -e "${GREEN}--- Pipeline abgeschlossen. Dashboard startet jetzt! ---${NC}"

echo "Erstelle GeoJSON-Datei..."
python3 generate_zones.py

# 4. Dashboard starten
streamlit run dashboard.py