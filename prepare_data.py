import csv
from collections import Counter
from datetime import datetime
from pathlib import Path
import json

# Project folders
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "au-national-heritage-list-places_2026-02-26.csv"


def read_csv(filename):
    """Read a CSV file while preserving the original field values."""
    with open(filename, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    print(f"Loaded {len(rows)} rows from {filename.name}")
    print("Columns:", list(rows[0].keys()) if rows else [])
    return rows


def parse_date(value):
    """Parse common date formats without guessing invalid dates."""
    if not value:
        return None

    value = value.strip()

    formats = [
        "%d/%m/%Y",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%m/%d/%Y",
    ]

    for date_format in formats:
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue

    return None


def write_counts(filename, field_name, counts):
    """Save category counts as a CSV for Vega-Lite."""
    output_path = DATA_DIR / filename

    with open(output_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([field_name, "count"])

        for category, count in sorted(counts.items()):
            writer.writerow([category, count])

    print(f"Created: {output_path.name}")


def main():
    rows = read_csv(INPUT_FILE)

    if not rows:
        print("The input CSV is empty.")
        return

    # Remove surrounding whitespace from field names and values.
    cleaned_rows = []

    for row in rows:
        cleaned_row = {
            (key or "").strip(): (value or "").strip()
            for key, value in row.items()
            if key is not None
        }
        cleaned_rows.append(cleaned_row)

    # Check for repeated place IDs before counting.
    place_ids = [
        row.get("place_id", "")
        for row in cleaned_rows
        if row.get("place_id", "")
    ]

    duplicate_ids = [
        place_id
        for place_id, count in Counter(place_ids).items()
        if count > 1
    ]

    print(f"Rows in source: {len(cleaned_rows)}")
    print(f"Unique non-empty place IDs: {len(set(place_ids))}")
    print(f"Repeated place IDs: {len(duplicate_ids)}")

    # Inspect all rows belonging to repeated place IDs.
    print("\n--- Repeated place ID details ---")

    for place_id in duplicate_ids:
        matching_rows = [
            row for row in cleaned_rows
            if row.get("place_id", "") == place_id
        ]

        print(f"\nPlace ID: {place_id}")

        for row in matching_rows:
            print({
                "name": row.get("name"),
                "class": row.get("class"),
                "status": row.get("status"),
                "state": row.get("state"),
                "register_date": row.get("register_date"),
                "area_ha": row.get("area_ha"),
            })

    # For summary charts, count each place ID once.
    # Keep the first row for each ID and report repetitions rather
    # than treating multiple geometry records as separate places.
    unique_places = {}
    missing_id_rows = 0

    for row in cleaned_rows:
        place_id = row.get("place_id", "")

        if not place_id:
            missing_id_rows += 1
            continue

        if place_id not in unique_places:
            unique_places[place_id] = row

    places = list(unique_places.values())

    print(f"Unique places used for summaries: {len(places)}")
    print(f"Rows with missing place IDs: {missing_id_rows}")

    # Line chart: distinct listed heritage places registered each year
    year_counts = Counter()
    listed_dates_by_place = {}
    missing_dates = 0
    invalid_dates = 0
    missing_id_rows = 0

    for row in cleaned_rows:
        # Only include formally listed places
        if row.get("status", "").strip() != "Listed place":
            continue

        place_id = row.get("place_id", "").strip()

        if not place_id:
            missing_id_rows += 1
            continue

        raw_date = row.get("register_date", "").strip()
        parsed_date = parse_date(raw_date)

        if not raw_date:
            missing_dates += 1
            continue

        if parsed_date is None:
            invalid_dates += 1
            continue

        # Group valid registration years by unique place ID.
        # This avoids counting multiple spatial records as separate places.
        listed_dates_by_place.setdefault(place_id, set()).add(
            parsed_date.year
        )

    # Count each unique place once.
    for place_id, years in listed_dates_by_place.items():
        if len(years) > 1:
            print(
                f"WARNING: Place ID {place_id} has "
                f"multiple registration years: {sorted(years)}"
            )
            continue

        year = next(iter(years))
        year_counts[year] += 1

    write_counts(
        "listings_by_year.csv",
        "year",
        year_counts
    )

    print("\n--- Line chart data-quality summary ---")
    print(f"Distinct places counted: {sum(year_counts.values())}")
    print(f"Listed-place rows with missing IDs: {missing_id_rows}")
    print(f"Listed-place rows with missing dates: {missing_dates}")
    print(f"Listed-place rows with invalid dates: {invalid_dates}")

     # Donut chart: distinct listed heritage places by class
    class_by_place = {}
    missing_class_ids = 0

    for row in cleaned_rows:
        if row.get("status", "").strip() != "Listed place":
            continue

        place_id = row.get("place_id", "").strip()

        if not place_id:
            missing_class_ids += 1
            continue

        heritage_class = row.get("class", "").strip() or "Unknown"

        if place_id not in class_by_place:
            class_by_place[place_id] = heritage_class
        elif class_by_place[place_id] != heritage_class:
            print(
                f"WARNING: Place ID {place_id} has "
                f"multiple classes: {class_by_place[place_id]} "
                f"and {heritage_class}"
            )

    class_counts = Counter(class_by_place.values())

    write_counts(
        "listings_by_class.csv",
        "class",
        class_counts
    )

    print("\n--- Donut chart data summary ---")
    print(f"Distinct listed places counted: {sum(class_counts.values())}")
    print(f"Listed-place rows with missing IDs: {missing_class_ids}")



    
    # State or territory
    # Count each place once per state, while retaining places
    # that span multiple states.
    place_state_pairs = set()

    for row in cleaned_rows:
        place_id = row.get("place_id", "")
        state = row.get("state", "").strip() or "Unknown"

        if place_id:
            place_state_pairs.add((place_id, state))

    state_counts = Counter(
        state for place_id, state in place_state_pairs
    )

    write_counts(
        "listings_by_state.csv",
        "state",
        state_counts
    )


    # Waffle chart: distinct places by listing status
    included_statuses = {
        "Listed place",
        "Nominated place",
        "Within listed place"
    }

    status_counts = Counter(
        row.get("status", "").strip()
        for row in places
        if row.get("status", "").strip() in included_statuses
    )

    write_counts(
        "listing_status.csv",
        "status",
        status_counts
    )

    # Prepare waffle chart data
    waffle_path = DATA_DIR / "listing_status_waffle.csv"
    square_number = 1

    with open(waffle_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["status", "square"])

        for status, count in status_counts.items():
            for _ in range(count):
                writer.writerow([status, square_number])
                square_number += 1

    print(f"Created: {waffle_path.name}")
    print("Waffle chart status counts:")

    for status, count in status_counts.items():
        print(f"{status}: {count}")


    
    
    # Grant funding by funding round
    grant_rows = read_csv(DATA_DIR / "australian_heritage_grants.csv")

    funding_by_round = Counter()
    missing_funding = 0

    for row in grant_rows:
        grant_round = row.get("grant_round", "").strip() or "Unknown"
        raw_funding = row.get("funding_ex_gst", "").strip()

        # Skip blank or non-numeric funding values
        try:
            funding = float(raw_funding.replace(",", "").replace("$", ""))
        except ValueError:
            missing_funding += 1
            continue

        if funding < 0:
            print(
                f"WARNING: Negative funding amount in "
                f"{grant_round}: {funding}"
            )
            continue

        funding_by_round[grant_round] += funding

    # Sort grant rounds chronologically
    def round_start_year(item):
        round_name = item[0]
        try:
            return int(round_name[:4])
        except ValueError:
            return 9999

    sorted_rounds = sorted(
        funding_by_round.items(),
        key=round_start_year
    )

    grants_path = DATA_DIR / "grants_by_round.csv"

    with open(grants_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["grant_round", "funding", "round_order"])

        for order, (grant_round, funding) in enumerate(sorted_rounds):
            writer.writerow([
                grant_round,
                round(funding, 2),
                order
            ])

    print(f"Created: {grants_path.name}")
    print(f"Grant rounds included: {len(sorted_rounds)}")
    print(f"Rows with blank or invalid funding: {missing_funding}")
    print("Total funding by round:")
    for grant_round, funding in sorted_rounds:
        print(f"{grant_round}: ${funding:,.2f}")


    # Grant funding by state
    funding_by_state = Counter()

    for row in grant_rows:
        state = row.get("state", "").strip() or "Unknown"
        raw_funding = row.get("funding_inc_gst", "").strip()

        # Skip blank or non-numeric funding values
        try:
            funding = float(raw_funding.replace(",", "").replace("$", ""))
        except ValueError:
            continue

        funding_by_state[state] += funding

    funding_path = DATA_DIR / "funding_by_state.csv"

    with open(funding_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["state", "funding"])
        for state, funding in sorted(
            funding_by_state.items(),
            key=lambda item: item[1],
            reverse=True
        ):
            writer.writerow([state, round(funding, 2)])

    print(f"Created: {funding_path.name}")

    
    # Prepare hierarchical treemap data: Australia -> State -> Heritage site
    state_site_pairs = set()
    site_names = {}

    for row in cleaned_rows:
        place_id = row.get("place_id", "").strip()
        state = row.get("state", "").strip()
        name = row.get("name", "").strip() or place_id

        if place_id and state:
            state_site_pairs.add((state, place_id))
            site_names[place_id] = name

    treemap_rows = [
        {
            "id": "australia",
            "parent": None,
            "name": "Australia",
            "value": 0
        }
    ]

    states = sorted({state for state, _ in state_site_pairs})

    for state in states:
        treemap_rows.append({
            "id": f"state|{state}",
            "parent": "australia",
            "name": state,
            "value": 0
        })

    for state, place_id in sorted(state_site_pairs):
        treemap_rows.append({
            "id": f"site|{state}|{place_id}",
            "parent": f"state|{state}",
            "name": site_names.get(place_id, place_id),
            "value": 1
        })

    treemap_path = DATA_DIR / "heritage_treemap.json"

    with open(treemap_path, "w", encoding="utf-8") as file:
        json.dump(treemap_rows, file, ensure_ascii=False, indent=2)

    print(f"Created: {treemap_path.name}")

      # Graph 7: Funding by inferred heritage project type
    import re

    def classify_project(row):
        text = (
            row.get("project_title", "") + " " +
            row.get("project_description", "")
        ).lower()

        # Specific themes first, to reduce overlapping matches
        if any(word in text for word in [
            "indigenous", "aboriginal", "first nations",
            "traditional owner", "traditional owners"
        ]):
            return "Indigenous heritage"

        if any(word in text for word in [
            "conservation plan", "conservation management",
            "heritage management plan", "management plan"
        ]):
            return "Conservation planning"

        if any(word in text for word in [
            "restoration", "restore", "repair", "reconstruction",
            "stabilisation", "stabilization", "structural works"
        ]):
            return "Restoration and repair"

        if any(word in text for word in [
            "archaeology", "archaeological", "excavation",
            "archaeological survey"
        ]):
            return "Archaeology and research"

        if any(word in text for word in [
            "interpretation", "exhibition", "visitor centre",
            "visitor center", "signage", "education"
        ]):
            return "Interpretation and education"

        if any(word in text for word in [
            "recording", "documentation", "survey", "mapping",
            "digital"
        ]):
            return "Documentation and research"

        return "Other / needs review"

    funding_by_type = Counter()
    project_counts_by_type = Counter()

    for row in grant_rows:
        project_type = classify_project(row)
        raw_funding = row.get("funding_inc_gst", "").strip()

        try:
            funding = float(raw_funding.replace(",", "").replace("$", ""))
        except ValueError:
            continue

        if funding < 0:
            continue

        funding_by_type[project_type] += funding
        project_counts_by_type[project_type] += 1

    bubble_path = DATA_DIR / "funding_by_heritage_type.csv"

    with open(bubble_path, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["heritage_type", "funding", "project_count"])

        for project_type, funding in funding_by_type.items():
            writer.writerow([
                project_type,
                round(funding, 2),
                project_counts_by_type[project_type]
            ])

    print(f"Created: {bubble_path.name}")


    print("\nData preparation complete.")




if __name__ == "__main__":
    main()
