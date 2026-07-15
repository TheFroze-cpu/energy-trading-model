import requests
import json

def generate_uemb_geojson():
    print("Lade echte GeoJSON-Grenzen für Deutschland herunter...")
    
    # 1. Wir nutzen eine zuverlässige Open-Source GeoJSON der deutschen Bundesländer (niedrige Auflösung für schnelle Ladezeiten)
    url = "https://raw.githubusercontent.com/isellsoap/deutschlandGeoJSON/main/2_bundeslaender/4_niedrig.geo.json"
    response = requests.get(url)
    
    if response.status_code != 200:
        print("Fehler beim Herunterladen der Daten.")
        return
        
    geo_data = response.json()

    # 2. Das Mapping: Welches Bundesland gehört zu welchem ÜNB?
    # Hinweis: In der Realität gibt es kleine Überschneidungen, aber für Trading-Dashboards 
    # ist diese landesweite Zuordnung der absolute Industrie-Standard, wenn keine exakte Netztopologie vorliegt.
    unb_mapping = {
        "Baden-Württemberg": "TransnetBW",
        "Bayern": "TenneT",
        "Berlin": "50Hertz",
        "Brandenburg": "50Hertz",
        "Bremen": "TenneT",
        "Hamburg": "50Hertz",
        "Hessen": "TenneT",
        "Mecklenburg-Vorpommern": "50Hertz",
        "Niedersachsen": "TenneT",
        "Nordrhein-Westfalen": "Amprion",
        "Rheinland-Pfalz": "Amprion",
        "Saarland": "Amprion",
        "Sachsen": "50Hertz",
        "Sachsen-Anhalt": "50Hertz",
        "Schleswig-Holstein": "TenneT",
        "Thüringen": "50Hertz"
    }

    # 3. Wir überschreiben die Namen in der Datei mit unseren Regelzonen
    for feature in geo_data["features"]:
        state_name = feature["properties"]["name"]
        if state_name in unb_mapping:
            feature["properties"]["name"] = unb_mapping[state_name]

    # 4. Speichern als germany_zones.json
    with open("germany_zones.json", "w", encoding="utf-8") as f:
        json.dump(geo_data, f, ensure_ascii=False)

    print("Erfolg! Die Datei 'germany_zones.json' wurde mit den korrekten Outlines erstellt.")

if __name__ == "__main__":
    generate_uemb_geojson()