
import csv
import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

GRANTS_FILE = DATA_DIR / "australian_heritage_grants.csv"
GEOJSON_FILE = DATA_DIR / "national_heritage_list.geojson"
OUTPUT_FILE = DATA_DIR / "heritage_funding_polygons.geojson"


def normalise_name(name):
    """Normalise capitalisation, punctuation and whitespace."""
    name = unicodedata.normalize("NFKC", name or "")
    name = name.replace("’", "'").replace("‘", "'")
    name = name.casefold()

    # Treat punctuation as separators rather than meaningful differences.
    name = re.sub(r"[^\w\s]", " ", name)
    return re.sub(r"\s+", " ", name).strip()


# Map genuinely different grant-site names to existing polygon names.
# Keys and values are normalised automatically.
SITE_ALIASES = {
    "australian academy of science building the shine dome":
        "Australian Academy of Science Building",

    "australian fossil mammal site naracoorte":
        "Australian Fossil Mammal Sites (Naracoorte)",
    "australian fossil mammals sites naracoorte":
        "Australian Fossil Mammal Sites (Naracoorte)",

    "australian cornish mining sites burra":
        "Australian Cornish Mining Sites: Burra",
    "australian cornish mining sites moonta":
        "Australian Cornish Mining Sites: Moonta",

    "the city of broken hill":
        "City of Broken Hill",

    "qantas hangar longreach":
        "QANTAS Hangar Longreach",

    "the great barrier reef":
        "Great Barrier Reef",
    "west kimberley":
        "The West Kimberley",

    "grampians national park":
        "Grampians National Park (Gariwerd)",
    "grampians national park gariwerd":
        "Grampians National Park (Gariwerd)",

    "k gari fraser island":
        "K'gari",
    "fraser island":
        "K'gari",

    "bonegilla migrant camp":
        "Bonegilla Migrant Camp - Block 19",

    "beechworth administration precinct":
        "Beechworth Administrative Precinct",

    "the goldfields water supply scheme":
        "Goldfields Water Supply Scheme, Western Australia",
    "the goldfields water supply schemes":
        "Goldfields Water Supply Scheme, Western Australia",

    "witjira national park dalhousie great artesian basin springs":
        "Great Artesian Basin Springs: Witjira-Dalhousie",
    "witjira dalhousie springs":
        "Great Artesian Basin Springs: Witjira-Dalhousie",

    "greater blue mountains":
        "The Greater Blue Mountains Area",
    "greater blue mountains world heritage area":
        "The Greater Blue Mountains Area",

    "western tasmanian aboriginal cultural landscape":
        "Western Tasmania Aboriginal Cultural Landscape",

    "the adelaide park lands and city layout":
        "The Adelaide Park Lands and City Layout",

    "melbourne s domain parklands and memorial precinct":
        "Melbourne's Domain Parkland and Memorial Precinct",

    "royal exhibition building carlton gardens":
        "Royal Exhibition Building National Historic Place",

    "murtoa no 1 grain store":
        "Murtoa No 1 Grain Store",

    "australian fossil mammal sites naracoorte":
        "Australian Fossil Mammal Sites (Naracoorte)",

    
    # Additional variants found in the latest unmatched report
    "adelaide park lands and city layout":
        "The Adelaide Park Lands and City Layout",

    "brewarrina aboriginal fish traps baiames ngunnhu":
        "Brewarrina Aboriginal Fish Traps (Baiame's Ngunnhu)",

    "elizabeth springs":
        "Great Artesian Basin Springs: Elizabeth",

    "fremantle prison":
        "Fremantle Prison (former)",

    "mawson s huts and mawsons huts historic site":
        "Mawsons Huts and Mawsons Huts Historic Site",

    "murtoa no1 grainstore":
        "Murtoa No 1 Grain Store",

    "royal exhibition building and carlton gardens":
        "Royal Exhibition Building National Historic Place",

    "shark bay":
        "Shark Bay, Western Australia",

    "willandra lakes world heritage area":
        "Willandra Lakes Region",

    "grampian s national park":
        "Grampians National Park (Gariwerd)",

    "fraser island k gari":
        "K'gari",

    "gondwana rainforests of australia world heritage property":
        "Gondwana Rainforests of Australia",
}


ALIASES = {
    normalise_name(alias): normalise_name(canonical)
    for alias, canonical in SITE_ALIASES.items()
}


def canonicalise_name(name):
    """Normalise a name and resolve an explicit alias."""
    name = normalise_name(name)
    return ALIASES.get(name, name)


# 1. Read the polygon data and index its actual names.
with open(GEOJSON_FILE, encoding="utf-8-sig") as file:
    geojson = json.load(file)

polygon_names = set()
polygon_features_by_name = defaultdict(list)

for feature in geojson["features"]:
    properties = feature.get("properties", {})
    original_name = properties.get("NAME", "")
    canonical_name = canonicalise_name(original_name)

    if canonical_name:
        polygon_names.add(canonical_name)
        polygon_features_by_name[canonical_name].append(feature)


# 2. Aggregate grant funding by canonical site name.

# Special allocation rules for grants covering multiple sites.
# Fractions must add up to 1.0 for each allocated grant.

SPECIAL_ALLOCATIONS = {
    "australian alps national parks and reserves alpine national park": [
        ("Australian Alps National Parks and Reserves", 1.0),
    ],

    "australian cornish mining sites moonta australian cornish mining sites burra": [
        ("Australian Cornish Mining Sites: Moonta", 0.5),
        ("Australian Cornish Mining Sites: Burra", 0.5),
    ],

    "budj bim national heritage landscape": [
        ("Budj Bim National Heritage Landscape - Tyrendarra Area", 0.5),
        ("Budj Bim National Heritage Landscape - Mt Eccles Lake Condah Area", 0.5),
    ],

    "great barrier reef and wet tropics of queensland": [
        ("Great Barrier Reef", 0.5),
        ("Wet Tropics of Queensland", 0.5),
    ],
}


def get_allocations(original_site):
    """Return (target site, allocation fraction) pairs."""
    source = normalise_name(original_site)

    if source == "multiple":
        return []

    if source in SPECIAL_ALLOCATIONS:
        return [
            (canonicalise_name(site), fraction)
            for site, fraction in SPECIAL_ALLOCATIONS[source]
        ]

    return [(canonicalise_name(original_site), 1.0)]


# 2. Aggregate grant funding by allocated heritage site.
funding = defaultdict(float)
funding_count = defaultdict(int)
project_titles = defaultdict(list)
grant_sites = set()
missing_amounts = 0
negative_amounts = 0
unallocated_multiple_funding = 0.0

with open(GRANTS_FILE, encoding="utf-8-sig", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        original_site = row.get("nhl_site", "").strip()

        if not original_site:
            continue

        raw_amount = (row.get("funding_ex_gst") or "").strip()
        amount_text = raw_amount.replace(",", "").replace("$", "")

        try:
            amount = float(amount_text)
        except (ValueError, TypeError):
            missing_amounts += 1
            continue

        if amount < 0:
            negative_amounts += 1
            print(
                f"WARNING: Negative funding for "
                f"{original_site}: {amount}"
            )
            continue

        allocations = get_allocations(original_site)

        # Keep unidentified multi-site funding out of the map.
        if not allocations:
            if normalise_name(original_site) == "multiple":
                unallocated_multiple_funding += amount
            continue

        title = (row.get("project_title") or "").strip()

        for site, fraction in allocations:
            allocated_amount = amount * fraction

            grant_sites.add(site)
            funding[site] += allocated_amount
            funding_count[site] += 1

            if title and title not in project_titles[site]:
                project_titles[site].append(title)




# 3. Identify matches and unmatched grant sites.
matched_sites = grant_sites & polygon_names
unmatched_grant_sites = grant_sites - polygon_names

# Sites represented by multiple polygon features.
multiple_feature_sites = {
    site: len(polygon_features_by_name[site])
    for site in matched_sites
    if len(polygon_features_by_name[site]) > 1
}


# 4. Attach funding to each polygon feature.
for feature in geojson["features"]:
    properties = feature.get("properties", {})
    site = canonicalise_name(properties.get("NAME", ""))

    if site in matched_sites and funding_count[site] > 0:
        properties["total_funding"] = round(funding[site], 2)
        properties["funding_records"] = funding_count[site]
        properties["project_titles"] = project_titles[site]
    else:
        properties["total_funding"] = None
        properties["funding_records"] = 0
        properties["project_titles"] = []


# 5. Save the joined GeoJSON.
with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
    json.dump(geojson, file, ensure_ascii=False)


# 6. Report results.
print("\nGrant sites without a matching polygon:")
for site in sorted(unmatched_grant_sites):
    print(f"- {site}")

print("\nSites matching multiple polygon features:")
for site, count in sorted(multiple_feature_sites.items()):
    print(f"- {site}: {count} features")

print(f"\nCreated: {OUTPUT_FILE.name}")
print(f"Heritage polygon features: {len(geojson['features'])}")
print(f"Unique polygon names: {len(polygon_names)}")
print(f"Matched grant sites: {len(matched_sites)}")
print(f"Unmatched grant sites: {len(unmatched_grant_sites)}")
print(f"Rows with missing/invalid funding: {missing_amounts}")
print(f"Rows with negative funding: {negative_amounts}")
print(
    "Total funding represented by matched sites: "
    f"${sum(funding[s] for s in matched_sites):,.2f}"
)
