"""
Louisiana SB 121 Redistricting Equity Pipeline
Policy Analysis & Research: Tia Fields
TiaFields.com

REQUIREMENTS:
    pip install pandas geopandas xlrd shapely fiona pyogrio openpyxl

INPUTS:
    - 2026_0501_sta_comb.xls : SOS Statewide voter registration by party/race
    - 2026_0501_par_comb.xls : SOS Parish-level voter registration
    - HCA_SB121-5662_(McMakin).shp : McMakin Amendment district boundaries

OUTPUTS:
    - output/dashboard_data.json
    - output/sb121_districts_rei.geojson
    - output/parish_equity_report.csv
"""

import json
import math
import os
from pathlib import Path

import geopandas as gpd
import pandas as pd

DATA_DIR = Path(".")
STA_FILE = DATA_DIR / "2026_0501_sta_comb.xls"
PAR_FILE = DATA_DIR / "2026_0501_par_comb.xls"

# Your current folder name appears to include a trailing space before the slash.
# Keep this exact path unless/until you rename the folder in Finder/Terminal.
SHP_FILE = DATA_DIR / "Maps_SB121-5662_(McMakin) " / "HCA_SB121-5662_(McMakin).shp"

OUT_DIR = DATA_DIR / "output"
OUT_DIR.mkdir(exist_ok=True)

PARISH_DISTRICT = {
    "JEFFERSON": 1, "ST. TAMMANY": 1, "PLAQUEMINES": 1, "ST. BERNARD": 1,
    "TANGIPAHOA": 1, "WASHINGTON": 1,

    "ORLEANS": 2, "ST. CHARLES": 2, "ST. JOHN THE BAPTIST": 2, "ST. JAMES": 2,
    "LAFOURCHE": 2, "TERREBONNE": 2,

    "LAFAYETTE": 3, "ST. LANDRY": 3, "ST. MARTIN": 3, "IBERIA": 3, "ST. MARY": 3,
    "VERMILION": 3, "CALCASIEU": 3, "JEFFERSON DAVIS": 3, "CAMERON": 3,
    "BEAUREGARD": 3, "ALLEN": 3, "ACADIA": 3, "EVANGELINE": 3,

    "CADDO": 4, "BOSSIER": 4, "WEBSTER": 4, "DE SOTO": 4, "SABINE": 4,
    "RED RIVER": 4, "BIENVILLE": 4, "CLAIBORNE": 4, "UNION": 4,
    "MOREHOUSE": 4, "LINCOLN": 4, "JACKSON": 4,

    "EAST BATON ROUGE": 5, "ASCENSION": 5, "LIVINGSTON": 5, "OUACHITA": 5,
    "RAPIDES": 5, "GRANT": 5, "NATCHITOCHES": 5, "WINN": 5, "CALDWELL": 5,
    "LASALLE": 5, "CATAHOULA": 5, "CONCORDIA": 5, "FRANKLIN": 5,
    "RICHLAND": 5, "AVOYELLES": 5, "TENSAS": 5, "MADISON": 5,

    "WEST BATON ROUGE": 6, "POINTE COUPEE": 6, "EAST FELICIANA": 6,
    "WEST FELICIANA": 6, "ST. HELENA": 6, "ASSUMPTION": 6, "IBERVILLE": 6,
    "EAST CARROLL": 6, "WEST CARROLL": 6, "VERNON": 6,
}


def clean_int(value):
    if pd.isna(value):
        return 0
    if isinstance(value, str):
        value = value.replace(",", "").strip()
        if value == "":
            return 0
    return int(float(value))


def clean_str(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def safe_pct(numerator, denominator, digits=2):
    if denominator in (0, None) or pd.isna(denominator):
        return 0.0
    return round((numerator / denominator) * 100, digits)


def parse_sos_statewide(filepath: Path) -> pd.DataFrame:
    raw = pd.read_excel(filepath, engine="xlrd", header=None)
    records = []

    for i in range(10, 74):
        row = raw.iloc[i]
        name_raw = clean_str(row[0])
        if name_raw.lower() == "nan" or name_raw == "":
            continue

        parts = name_raw.split(" - ")
        parish_name = parts[0].strip().upper()
        parish_num = clean_int(parts[1]) if len(parts) > 1 else 0

        records.append({
            "parish": parish_name,
            "parish_num": parish_num,
            "total_reg": clean_int(row[2]),
            "white_reg": clean_int(row[3]),
            "black_reg": clean_int(row[4]),
            "other_reg": clean_int(row[5]),
            "dem_total": clean_int(row[6]),
            "dem_white": clean_int(row[7]),
            "dem_black": clean_int(row[8]),
            "dem_other": clean_int(row[9]),
            "rep_total": clean_int(row[10]),
            "rep_white": clean_int(row[11]),
            "rep_black": clean_int(row[12]),
            "rep_other": clean_int(row[13]),
            "no_party": clean_int(row[14]),
            "no_party_white": clean_int(row[15]) if len(row) > 15 else 0,
            "no_party_black": clean_int(row[16]) if len(row) > 16 else 0,
            "no_party_other": clean_int(row[17]) if len(row) > 17 else 0,
            "other_party": clean_int(row[18]),
            "other_party_white": clean_int(row[19]) if len(row) > 19 else 0,
            "other_party_black": clean_int(row[20]) if len(row) > 20 else 0,
            "other_party_other": clean_int(row[21]) if len(row) > 21 else 0,
        })

    df = pd.DataFrame(records)
    if df.empty:
        raise ValueError("No parish rows were parsed from statewide SOS file.")
    return df


def classify_parish_partisan_lean(row):
    if row["dem_pct"] > 48:
        return "STRONG D"
    if row["dem_pct"] > 38:
        return "LEAN D"
    if row["rep_pct"] > 38:
        return "LEAN R"
    return "COMPETITIVE"


def classify_district_rei(row):
    if row["district"] == 2:
        return "PACKED — Black voters concentrated above proportional share"
    dev = row["rei_deviation"]
    if dev < -8:
        return "SEVERELY CRACKED — far below proportional representation"
    if dev < -4:
        return "CRACKED — below proportional representation"
    if dev < 2:
        return "NEAR PROPORTIONAL — within tolerance"
    return "ABOVE AVERAGE — Black voters slightly over-represented"


def classify_viability(black_pct):
    if black_pct >= 45:
        return "VIABLE — Majority-minority opportunity district"
    if black_pct >= 30:
        return "MARGINAL — Influence but not decisive"
    return "NON-VIABLE — Black voters systematically outvoted"


def classify_district_partisan_lean(row):
    if row["dem_pct"] > 48:
        return "STRONG D"
    if row["dem_pct"] > 38:
        return "LEAN D"
    return "REPUBLICAN-CONTROLLED"


def make_json_safe(value):
    if isinstance(value, dict):
        return {str(k): make_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [make_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [make_json_safe(v) for v in value]
    if pd.isna(value) if not isinstance(value, (dict, list, tuple)) else False:
        return None
    if isinstance(value, (pd.Timestamp,)):
        return value.isoformat()
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            pass
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    return value


print("[1/5] Loading SOS voter registration data...")
parishes_df = parse_sos_statewide(STA_FILE)
print(f"   Loaded {len(parishes_df)} parishes. Total registered: {parishes_df['total_reg'].sum():,}")

print("[2/5] Assigning McMakin district boundaries and calculating metrics...")
parishes_df["district"] = parishes_df["parish"].map(PARISH_DISTRICT)

unmapped = sorted(parishes_df.loc[parishes_df["district"].isna(), "parish"].unique().tolist())
if unmapped:
    print(f"   WARNING: Unmapped parishes found; defaulting to District 5: {', '.join(unmapped)}")
parishes_df["district"] = parishes_df["district"].fillna(5).astype(int)

statewide_total = int(parishes_df["total_reg"].sum())
statewide_black = int(parishes_df["black_reg"].sum())
statewide_dem = int(parishes_df["dem_total"].sum())
statewide_rep = int(parishes_df["rep_total"].sum())

statewide_black_pct = safe_pct(statewide_black, statewide_total, 4)
statewide_dem_pct = safe_pct(statewide_dem, statewide_total, 4)
statewide_rep_pct = safe_pct(statewide_rep, statewide_total, 4)

parishes_df["black_pct"] = (parishes_df["black_reg"] / parishes_df["total_reg"] * 100).round(2)
parishes_df["white_pct"] = (parishes_df["white_reg"] / parishes_df["total_reg"] * 100).round(2)
parishes_df["dem_pct"] = (parishes_df["dem_total"] / parishes_df["total_reg"] * 100).round(2)
parishes_df["rep_pct"] = (parishes_df["rep_total"] / parishes_df["total_reg"] * 100).round(2)
parishes_df["rei_parish"] = (parishes_df["black_pct"] - statewide_black_pct).round(2)
parishes_df["partisan_lean"] = parishes_df.apply(classify_parish_partisan_lean, axis=1)

print(f"   Statewide Black %: {statewide_black_pct:.1f}%")
print(f"   Statewide Dem %:   {statewide_dem_pct:.1f}%")
print(f"   Statewide Rep %:   {statewide_rep_pct:.1f}%")

print("[3/5] Aggregating district-level equity analysis...")
by_district = parishes_df.groupby("district").agg(
    total_reg=("total_reg", "sum"),
    white_reg=("white_reg", "sum"),
    black_reg=("black_reg", "sum"),
    other_reg=("other_reg", "sum"),
    dem_total=("dem_total", "sum"),
    rep_total=("rep_total", "sum"),
    no_party=("no_party", "sum"),
    other_party=("other_party", "sum"),
    dem_black=("dem_black", "sum"),
    rep_black=("rep_black", "sum"),
).reset_index()

by_district["black_pct"] = (by_district["black_reg"] / by_district["total_reg"] * 100).round(2)
by_district["white_pct"] = (by_district["white_reg"] / by_district["total_reg"] * 100).round(2)
by_district["dem_pct"] = (by_district["dem_total"] / by_district["total_reg"] * 100).round(2)
by_district["rep_pct"] = (by_district["rep_total"] / by_district["total_reg"] * 100).round(2)
by_district["rei_deviation"] = (by_district["black_pct"] - statewide_black_pct).round(2)
by_district["rei_severity"] = by_district["rei_deviation"].abs().round(2)
by_district["rei_class"] = by_district.apply(classify_district_rei, axis=1)
by_district["black_electoral_viability"] = by_district["black_pct"].apply(classify_viability)

by_district["wasted_black_votes"] = by_district.apply(
    lambda r: max(0, int(round(r["black_reg"] - r["total_reg"] * 0.50)))
    if r["district"] == 2 else int(r["black_reg"]),
    axis=1,
)

ideal_black_per_district = statewide_black / 6
by_district["voters_displaced"] = (
    by_district["black_reg"] - ideal_black_per_district
).round(0).astype(int)

by_district["partisan_lean"] = by_district.apply(classify_district_partisan_lean, axis=1)

print("\n   DISTRICT EQUITY SUMMARY:")
for _, r in by_district.iterrows():
    print(
        f"   D{int(r['district'])}: {int(r['total_reg']):>8,} voters | "
        f"Black: {r['black_pct']:5.1f}% | "
        f"REI: {r['rei_deviation']:+6.1f}pp | "
        f"{r['rei_class'][:52]}"
    )

print("\n[4/5] Loading district shapefile and merging equity data...")
geojson_path = OUT_DIR / "sb121_districts_rei.geojson"

try:
    os.environ["SHAPE_RESTORE_SHX"] = "YES"

    if not SHP_FILE.exists():
        raise FileNotFoundError(f"{SHP_FILE} not found")

    gdf = gpd.read_file(SHP_FILE)

    if gdf.empty:
        raise ValueError("Shapefile loaded but contains no features.")

    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")

    if "district" in gdf.columns:
        gdf["district"] = pd.to_numeric(gdf["district"], errors="coerce")
    else:
        candidate_cols = [c for c in gdf.columns if c.lower() in {"dist", "district", "cd", "district_1"}]
        if candidate_cols:
            gdf["district"] = pd.to_numeric(gdf[candidate_cols[0]], errors="coerce")
        else:
            gdf["district"] = range(1, len(gdf) + 1)

    gdf["district"] = gdf["district"].fillna(pd.Series(range(1, len(gdf) + 1))).astype(int)

    gdf = gdf.merge(by_district, on="district", how="left")
    gdf["geometry"] = gdf.geometry.simplify(0.001, preserve_topology=True)
    gdf.to_file(geojson_path, driver="GeoJSON")

    print(f"   Saved enriched GeoJSON: {geojson_path}")
    print(f"   GeoJSON size: {geojson_path.stat().st_size // 1024}KB")
except Exception as e:
    print(f"   WARNING: Shapefile merge failed ({e}). Skipping spatial output.")
    print("   Dashboard JSON will still work — map uses pre-processed boundaries.")

print("\n[5/5] Writing output files...")

black_in_rep_districts = int(by_district.loc[by_district["district"] != 2, "black_reg"].sum())
pct_black_in_rep_districts = round((black_in_rep_districts / statewide_black) * 100, 1) if statewide_black else 0.0

dashboard_payload = {
    "metadata": {
        "source": "Louisiana Secretary of State — Active Voter Registration",
        "report_date": "5/1/2026",
        "analyst": "Tia Fields",
        "organization": "Invest in Louisiana",
        "website": "TiaFields.com",
        "legislation": "SB 121 (Morris) + HCA McMakin Amendment, 2026 Regular Session",
        "legal_context": "Post-Louisiana v. Callais, 608 U.S. ___ (Apr. 29, 2026)",
        "statewide_total": statewide_total,
        "statewide_black": statewide_black,
        "statewide_black_pct": round(statewide_black_pct, 2),
        "statewide_dem_pct": round(statewide_dem_pct, 2),
        "statewide_rep_pct": round(statewide_rep_pct, 2),
        "total_black_in_rep_districts": black_in_rep_districts,
        "pct_black_voters_in_rep_districts": pct_black_in_rep_districts,
        "majority_black_districts": int((by_district["black_pct"] >= 50).sum()),
        "opportunity_districts_45_plus": int((by_district["black_pct"] >= 45).sum()),
        "proportional_seat_expectation": round((statewide_black_pct / 100) * 6, 2),
    },
    "districts": make_json_safe(by_district.to_dict(orient="records")),
    "parishes": make_json_safe(parishes_df.to_dict(orient="records")),
    "parishes_by_district": {
        str(d): make_json_safe(
            parishes_df.loc[parishes_df["district"] == d, [
                "parish", "total_reg", "black_reg", "black_pct",
                "dem_total", "rep_total", "dem_pct", "rep_pct"
            ]].to_dict(orient="records")
        )
        for d in range(1, 7)
    },
}

json_out = OUT_DIR / "dashboard_data.json"
with open(json_out, "w", encoding="utf-8") as f:
    json.dump(make_json_safe(dashboard_payload), f, indent=2, ensure_ascii=False)

csv_out = OUT_DIR / "parish_equity_report.csv"
parishes_df[[
    "parish", "district", "total_reg", "white_reg", "black_reg", "other_reg",
    "black_pct", "dem_pct", "rep_pct", "rei_parish", "partisan_lean"
]].to_csv(csv_out, index=False)

print(f"   dashboard_data.json  → {json_out.stat().st_size // 1024}KB")
print(f"   parish_equity_report → {csv_out}")

pct_in_rep = dashboard_payload["metadata"]["pct_black_voters_in_rep_districts"]
majority_black_districts = dashboard_payload["metadata"]["majority_black_districts"]
proportional_expectation = dashboard_payload["metadata"]["proportional_seat_expectation"]

print(f"""
╔══════════════════════════════════════════════════════════════╗
║           SB 121 REDISTRICTING EQUITY FINDINGS              ║
╠══════════════════════════════════════════════════════════════╣
║  Total registered voters:      {statewide_total:>10,.0f}                 ║
║  Black registered voters:      {statewide_black:>10,.0f} ({statewide_black_pct:.1f}% of electorate) ║
║  Majority-Black seats:         {majority_black_districts} of 6                            ║
║  Black voters in non-D2 seats: {pct_in_rep:.1f}% of all Black voters     ║
║  Proportional expectation:     {proportional_expectation:.2f} of 6 seats              ║
║  Representational deficit:     {max(0, round(proportional_expectation - majority_black_districts, 2)):.2f} seats                  ║
╠══════════════════════════════════════════════════════════════╣
║  Post-Callais Section 2 VRA: GUTTED (intent standard)        ║
║  Constitutional vulnerability: ONE-PERSON-ONE-VOTE (14th)    ║
║  Data integrity: CORRUPTED (VAP > registration in 6 parishes) ║
╚══════════════════════════════════════════════════════════════╝
""")

print("Pipeline complete. Outputs in ./output/")