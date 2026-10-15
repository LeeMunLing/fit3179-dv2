
import pandas as pd
import re

# Load the original grants dataset
grants = pd.read_csv("data/australian_heritage_grants.csv")

# Clean column values
grants["state"] = grants["state"].astype("string").str.strip().str.upper()
grants["grant_round"] = grants["grant_round"].astype("string").str.strip()

# Extract a four-digit year from grant_round
grants["year"] = grants["grant_round"].str.extract(
    r"\b(20\d{2})\b"
)

# Convert funding to numeric values
grants["funding_inc_gst"] = pd.to_numeric(
    grants["funding_inc_gst"]
        .astype("string")
        .str.replace(r"[$,\s]", "", regex=True),
    errors="coerce"
)

# Keep valid years, states and funding values
valid_states = ["WA", "NT", "SA", "QLD", "NSW", "ACT", "VIC", "TAS"]

grants = grants[
    grants["year"].notna()
    & grants["state"].isin(valid_states)
    & grants["funding_inc_gst"].notna()
    & (grants["funding_inc_gst"] >= 0)
].copy()

# Convert year to integer
grants["year"] = grants["year"].astype(int)

# Aggregate funding and count grant records by state and year
summary = (
    grants.groupby(["year", "state"], as_index=False)
    .agg(
        total_funding=("funding_inc_gst", "sum"),
        grant_count=("project_title", "count")
    )
)

# Sort the results
summary = summary.sort_values(["year", "state"])

# Save the heatmap dataset
summary.to_csv("data/funding_by_state_year.csv", index=False)

print("Created: data/funding_by_state_year.csv")
print(summary.to_string(index=False))
print("\nRows included:", len(grants))
print("Rows excluded:", len(pd.read_csv("data/australian_heritage_grants.csv")) - len(grants))
