
import json
from shapely.geometry import MultiPolygon, shape, mapping
from shapely.geometry.polygon import orient

input_path = "data/heritage_funding_polygons.geojson"
output_path = "data/heritage_funding_polygons_simplified.geojson"


def is_coarse_rectangle(geom):
    if geom.geom_type != "Polygon":
        return False

    coordinates = list(geom.exterior.coords)
    if len(coordinates) != 5:
        return False

    longitudes = [coordinate[0] for coordinate in coordinates]
    latitudes = [coordinate[1] for coordinate in coordinates]
    width = max(longitudes) - min(longitudes)
    height = max(latitudes) - min(latitudes)
    if min(width, height) < 0.1:
        return False

    longitude_tolerance = width * 0.01
    latitude_tolerance = height * 0.01
    return all(
        abs(start[0] - end[0]) <= longitude_tolerance
        or abs(start[1] - end[1]) <= latitude_tolerance
        for start, end in zip(coordinates, coordinates[1:])
    )


with open(input_path, "r", encoding="utf-8") as f:
    geojson = json.load(f)

for feature in geojson["features"]:
    if feature.get("geometry"):
        geom = shape(feature["geometry"])
        approximate_location = feature.get("properties", {}).get("SOURCE") == "approx"

        # Simplify boundaries while preserving topology
        geom = geom.simplify(
            tolerance=0.005,
            preserve_topology=True
        )

        if geom.geom_type == "Polygon":
            if approximate_location or is_coarse_rectangle(geom):
                geom = geom.representative_point()
            else:
                geom = orient(geom, sign=-1.0)
        elif geom.geom_type == "MultiPolygon":
            if approximate_location:
                geom = geom.representative_point()
            else:
                geom = MultiPolygon(
                    [orient(polygon, sign=-1.0) for polygon in geom.geoms]
                )

        feature["geometry"] = mapping(geom)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(geojson, f, separators=(",", ":"))

import os

original_size = os.path.getsize(input_path) / (1024 * 1024)
new_size = os.path.getsize(output_path) / (1024 * 1024)

print(f"Original size: {original_size:.2f} MB")
print(f"Simplified size: {new_size:.2f} MB")
print(f"Features preserved: {len(geojson['features'])}")
