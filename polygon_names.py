
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
GEOJSON_FILE = BASE_DIR / "data" / "national_heritage_list.geojson"

with open(GEOJSON_FILE, encoding="utf-8-sig") as file:
    geojson = json.load(file)

print(f"Total polygons: {len(geojson['features'])}\n")

for i, feature in enumerate(geojson["features"], start=1):
    properties = feature.get("properties", {})
    name = properties.get("NAME", "(No NAME field)")
    print(f"{i}. {name}")
