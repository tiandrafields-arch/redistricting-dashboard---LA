"""
Louisiana Redistricting Equity Pipeline
Policy Analysis & Research: Tia Fields
TiaFields.com

PURPOSE:
    Merges Louisiana Secretary of State active voter registration data against
    Act 2 (SB 121, Morris) district boundaries to calculate representational
    equity metrics, document racial
    vote dilution patterns, and produce output files for the TiaFields.com
    redistricting equity dashboard.

    Voter data sourced from:
        Louisiana Secretary of State -- Active Voter Registration File,
        Report Date 5/1/2026.

    District boundaries sourced from:
        Act 2 (SB 121, Morris), 2026 Regular Session -- enrolled shapefile
        SB_121_Enrolled.shp
        Effective for 2026 congressional elections upon Governor's signature.
        Full statutory effectiveness: noon, January 3, 2027.
        Enacts R.S. 18:1276.

    VTD-level Census and registration data sourced from:
        SB121_VTD_assignment.csv -- 3,539 VTDs with Census PL 94-171
        population and VAP columns joined to Act 2 district assignments
        and SOS active voter registration from 5/1/2026.

    PL 94-171 data sourced from:
        la000032020.pl -- U.S. Census Bureau 2020 Redistricting Data
        (Public Law 94-171) Segment 3, Louisiana.
        Census VTD geometry from:
        Census_2020_TigerLine_VTD_Shapefile_Layer_as_Validated_by_the_LA_Legislature.shp

LEGISLATIVE STATUS:
    SB 121 signed by Governor Landry and enrolled as Act 2.
    Effective for 2026 congressional elections.
    Full statutory effectiveness: noon, January 3, 2027.
    Enacts R.S. 18:1276.
    Post-Louisiana v. Callais, 608 U.S. ___ (Apr. 29, 2026).

DATA SOURCE HIERARCHY (order of legal authority):
    1. Act 2 enrolled district geometry (SB_121_Enrolled.shp)
    2. Census PL 94-171 population and VAP (la000032020.pl + VTD shapefile)
    3. VTD assignment outputs (SB121_VTD_assignment.csv)
    4. Louisiana SOS active voter registration (2026_0501_sta_comb.xls)
    5. Derived analysis (REI, PACKED/CRACKED, wasted-vote estimates)

DATA INTEGRITY NOTE -- REGISTRATION VS. VAP:
    Census PL 94-171 VAP and SOS voter registration are conceptually distinct.
    VAP counts all residents 18+. Registration counts only enrolled voters.
    These datasets produce different racial composition percentages.
    This pipeline tracks both and never equates them.

    SOS registration data in this file was reported prior to official SOS
    re-tabulation by Act 2 district geography. District-level registration
    aggregates derived here are analytical approximations, not certified
    Act 2 district statistics. Label all registration-derived outputs
    as provisional.

    Pre-enrollment data integrity anomalies (SB 121 Reengrossed, Pages 11-12):
    Jefferson Parish D1 segment: 196,528 registered voters against stated
    VAP of 133,984 (146.7% rate). D1 parish VAPs sum to 477,567 but
    reengrossed bill declared 601,847 -- gap of 124,280.
    Identified by Rep. C. Denise Marcelle (D-Baton Rouge), May 21, 2026.
    These anomalies were in the pre-enrollment text; verify against
    enrolled Act 2 before treating as confirmed defects.

REQUIREMENTS:
    pip install pandas geopandas xlrd shapely

INPUTS:
    - 2026_0501_sta_comb.xls
          SOS statewide voter registration by party/race
          Source: Louisiana Secretary of State, 5/1/2026 (provisional --
          not yet re-tabulated by Act 2 district geography)
    - 2026_0501_par_comb.xls
          SOS parish-level voter registration
          Source: Louisiana Secretary of State, 5/1/2026 (provisional)
    - SB_121_Enrolled.shp
          Act 2 (SB 121) enrolled district boundary shapefile
          Source: Louisiana Legislature, 2026 Regular Session
          Legal boundary definition for R.S. 18:1276
    - SB121_VTD_assignment.csv
          VTD-level Census PL 94-171 population, VAP, and SOS registration
          joined to Act 2 district assignments (3,539 VTDs)
          Columns: GEOID20, COUNTYFP20, VTDST20, NAME20, district,
                   TOT_POP, TOT_BLACK, TOT_WHITE, TOT_HISPAN,
                   VAP_TOTAL, VAP_BLACK, VAP_WHITE,
                   RVTOTAL, RVBLACK, RVDEMTOTAL, RVREPTOTAL
    - la000032020.pl
          U.S. Census Bureau 2020 PL 94-171 Segment 3, Louisiana
          (block/VTD-level population by race)
    - Census_2020_TigerLine_VTD_Shapefile_Layer_as_Validated_by_the_LA_Legislature.shp
          Census VTD geometry validated by Louisiana Legislature

OUTPUTS:
    - output/dashboard_data.json
          District + parish equity data for the dashboard.
          Includes both Census VAP and SOS registration metrics,
          clearly labeled and not conflated.
    - output/act2_districts_rei.geojson
          Act 2 district GeoJSON enriched with REI scores and
          Census VAP / SOS registration metrics.
    - output/vtd_equity_report.csv
          VTD-level equity analysis with Census and registration columns.
    - output/parish_equity_report.csv
          Parish-level equity analysis (registration-based, provisional).

METHODOLOGY -- Representational Equity Index (REI):
    REI is calculated separately for Census VAP and SOS registration.

    REI_VAP         = District Black VAP %    - Statewide Black VAP %
    REI_REGISTRATION = District Black Reg %    - Statewide Black Reg % (SOS)

    Positive = PACKED  (Black voters/residents over-concentrated)
    Negative = CRACKED (Black voters/residents dispersed below threshold)
    |REI| > 8pp = severe dilution
    |REI| > 5pp = significant dilution

    All REI values are labeled with their source (VAP or registration).
    District 2 is the only majority Black VAP district (58.24% Black VAP
    per Census PL 94-171 and confirmed by VTD assignment file).
    District 6 Black VAP is 24.58% -- not majority Black.
"""

import os
import json
import pandas as pd
import geopandas as gpd
from pathlib import Path

# ─── CONFIGURATION ────────────────────────────────────────────────────────────

DATA_DIR = Path(".")
OUT_DIR  = DATA_DIR / "output"
OUT_DIR.mkdir(exist_ok=True)

# SOS voter registration inputs (provisional -- not re-tabulated by Act 2 geography)
STA_FILE = DATA_DIR / "2026_0501_sta_comb.xls"
PAR_FILE = DATA_DIR / "2026_0501_par_comb.xls"

# Act 2 (SB 121) enrolled district boundary shapefile (legal authority)
SHP_FILE = DATA_DIR / "SB_121_Enrolled.shp"

# VTD-level data: Census PL 94-171 + SOS registration + Act 2 district assignments
VTD_FILE = DATA_DIR / "SB121_VTD_assignment.csv"

# Census PL 94-171 Segment 3 (block/VTD-level population by race)
PL_FILE  = DATA_DIR / "la000032020.pl"

# Census VTD geometry (Louisiana Legislature validated)
VTD_SHP  = DATA_DIR / "Census_2020_TigerLine_VTD_Shapefile_Layer_as_Validated_by_the_LA_Legislature.shp"

# ─── SOURCE LABELS ────────────────────────────────────────────────────────────

SOS_REPORT_DATE    = "5/1/2026"
SOS_SOURCE_LABEL   = "Louisiana Secretary of State -- Active Voter Registration (provisional; not re-tabulated by Act 2 district geography)"
ACT2_SOURCE_LABEL  = "Act 2 (SB 121, Morris), 2026 Regular Session -- enrolled. Enacts R.S. 18:1276."
VTD_SOURCE_LABEL   = "SB121_VTD_assignment.csv -- Census PL 94-171 VAP + SOS registration joined to Act 2 district assignments"
PL_SOURCE_LABEL    = "U.S. Census Bureau 2020 PL 94-171 Segment 3 (la000032020.pl)"

# ─── LEGISLATIVE STATUS ───────────────────────────────────────────────────────

ACT2_STATUS = {
    "bill":                 "SB 121 (Morris)",
    "house_passed":         "May 28, 2026",
    "governor_signed":      "May 2026",
    "enrolled_as":          "Act 2",
    "statute":              "R.S. 18:1276",
    "effective_elections":  "Effective for 2026 congressional elections upon Governor signature",
    "effective_full":       "Noon, January 3, 2027",
    "callais_decided":      "April 29, 2026",
    "legal_context":        "Post-Louisiana v. Callais, 608 U.S. ___ (Apr. 29, 2026)",
}

# ─── PARISH TO DISTRICT MAP ───────────────────────────────────────────────────
# Source: Act 2 (SB 121) enrolled text and district parish assignments.
# Note: sub-parish splits are not reflected here -- whole-parish assignment
# is an approximation. VTD_FILE contains the authoritative VTD-level
# district assignments for sub-parish precision.

PARISH_DISTRICT = {
    # District 1 -- SE Gulf Coast
    "JEFFERSON": 1, "ST. TAMMANY": 1, "PLAQUEMINES": 1, "ST. BERNARD": 1,
    "TANGIPAHOA": 1, "WASHINGTON": 1,

    # District 2 -- New Orleans Metro (only majority Black VAP district)
    # Census PL 94-171 Black VAP: 58.24% (VTD file confirms)
    "ORLEANS": 2, "ST. CHARLES": 2, "ST. JOHN THE BAPTIST": 2, "ST. JAMES": 2,
    "LAFOURCHE": 2, "TERREBONNE": 2,

    # District 3 -- SW Acadiana
    "LAFAYETTE": 3, "ST. LANDRY": 3, "ST. MARTIN": 3, "IBERIA": 3, "ST. MARY": 3,
    "VERMILION": 3, "CALCASIEU": 3, "JEFFERSON DAVIS": 3, "CAMERON": 3,
    "BEAUREGARD": 3, "ALLEN": 3, "ACADIA": 3, "EVANGELINE": 3,

    # District 4 -- Northwest
    "CADDO": 4, "BOSSIER": 4, "WEBSTER": 4, "DE SOTO": 4, "SABINE": 4,
    "RED RIVER": 4, "BIENVILLE": 4, "CLAIBORNE": 4, "UNION": 4,
    "MOREHOUSE": 4, "LINCOLN": 4, "JACKSON": 4,

    # District 5 -- North-Central
    "EAST BATON ROUGE": 5, "ASCENSION": 5, "LIVINGSTON": 5, "OUACHITA": 5,
    "RAPIDES": 5, "GRANT": 5, "NATCHITOCHES": 5, "WINN": 5, "CALDWELL": 5,
    "LASALLE": 5, "CATAHOULA": 5, "CONCORDIA": 5, "FRANKLIN": 5,
    "RICHLAND": 5, "AVOYELLES": 5, "TENSAS": 5, "MADISON": 5,

    # District 6 -- River Corridor
    # Black VAP 24.58% (Census PL 94-171) -- NOT a majority Black district
    "WEST BATON ROUGE": 6, "POINTE COUPEE": 6, "EAST FELICIANA": 6,
    "WEST FELICIANA": 6, "ST. HELENA": 6, "ASSUMPTION": 6, "IBERVILLE": 6,
    "EAST CARROLL": 6, "WEST CARROLL": 6, "VERNON": 6,
}


# ─── STEP 1: LOAD VTD-LEVEL CENSUS AND REGISTRATION DATA ─────────────────────
print("[1/6] Loading VTD-level Census PL 94-171 + SOS registration data...")
print(f"      Source: {VTD_SOURCE_LABEL}")

vtd_df = pd.read_csv(VTD_FILE, dtype={"GEOID20": str, "VTDST20": str})

print(f"   OK  Loaded {len(vtd_df):,} VTDs across {vtd_df['district'].nunique()} districts")
print(f"   OK  Columns: {list(vtd_df.columns)}")

# VTD-level derived metrics
vtd_df["pct_black_vap"]  = (vtd_df["VAP_BLACK"]  / vtd_df["VAP_TOTAL"].replace(0, 1) * 100).round(2)
vtd_df["pct_black_rv"]   = (vtd_df["RVBLACK"]    / vtd_df["RVTOTAL"].replace(0, 1)   * 100).round(2)
vtd_df["pct_dem_rv"]     = (vtd_df["RVDEMTOTAL"] / vtd_df["RVTOTAL"].replace(0, 1)   * 100).round(2)
vtd_df["pct_rep_rv"]     = (vtd_df["RVREPTOTAL"] / vtd_df["RVTOTAL"].replace(0, 1)   * 100).round(2)

vtd_df["vap_source"]   = PL_SOURCE_LABEL
vtd_df["rv_source"]    = SOS_SOURCE_LABEL
vtd_df["boundary_source"] = ACT2_SOURCE_LABEL


# ─── STEP 2: DISTRICT-LEVEL CENSUS VAP AGGREGATION ────────────────────────────
print("\n[2/6] Aggregating Census PL 94-171 VAP by Act 2 district...")
print(f"      Source: {PL_SOURCE_LABEL} via VTD assignment file")

by_district_vap = vtd_df.groupby("district").agg(
    tot_pop       = ("TOT_POP",    "sum"),
    tot_black     = ("TOT_BLACK",  "sum"),
    tot_white     = ("TOT_WHITE",  "sum"),
    tot_hispan    = ("TOT_HISPAN", "sum"),
    vap_total     = ("VAP_TOTAL",  "sum"),
    vap_black     = ("VAP_BLACK",  "sum"),
    vap_white     = ("VAP_WHITE",  "sum"),
    rv_total      = ("RVTOTAL",    "sum"),
    rv_black      = ("RVBLACK",    "sum"),
    rv_dem        = ("RVDEMTOTAL", "sum"),
    rv_rep        = ("RVREPTOTAL", "sum"),
    vtd_count     = ("GEOID20",    "count"),
).reset_index()

# Census VAP percentages (primary demographic authority)
by_district_vap["pct_black_vap"]  = (by_district_vap["vap_black"] / by_district_vap["vap_total"] * 100).round(2)
by_district_vap["pct_white_vap"]  = (by_district_vap["vap_white"] / by_district_vap["vap_total"] * 100).round(2)

# SOS registration percentages (provisional -- labeled separately)
by_district_vap["pct_black_rv"]   = (by_district_vap["rv_black"] / by_district_vap["rv_total"].replace(0, 1) * 100).round(2)
by_district_vap["pct_dem_rv"]     = (by_district_vap["rv_dem"]   / by_district_vap["rv_total"].replace(0, 1) * 100).round(2)
by_district_vap["pct_rep_rv"]     = (by_district_vap["rv_rep"]   / by_district_vap["rv_total"].replace(0, 1) * 100).round(2)

# Majority Black VAP flag -- based solely on Census PL 94-171
by_district_vap["majority_black_vap"] = by_district_vap["pct_black_vap"] >= 50.0

statewide_vap_total = by_district_vap["vap_total"].sum()
statewide_vap_black = by_district_vap["vap_black"].sum()
statewide_black_vap_pct = statewide_vap_black / statewide_vap_total * 100

print(f"   OK  Statewide Black VAP: {statewide_black_vap_pct:.2f}%  [Census PL 94-171]")
print(f"   OK  Majority Black VAP districts: {by_district_vap['majority_black_vap'].sum()} of 6")
print(f"       (District 2 only -- {by_district_vap.loc[by_district_vap['district']==2,'pct_black_vap'].values[0]:.2f}% Black VAP)")

print("\n   DISTRICT VAP SUMMARY  [Census PL 94-171 via VTD assignment]")
print(f"   {'Dist':<6} {'Tot Pop':>10}  {'Black VAP%':>11}  {'Majority?':>10}  {'VAP Source'}")
print(f"   {'--'*40}")
for _, r in by_district_vap.iterrows():
    flag = "YES -- D2 only" if r["majority_black_vap"] else "no"
    print(f"   D{int(r.district):<5} {int(r.tot_pop):>10,}  {r.pct_black_vap:>10.2f}%  {flag:>10}")


# ─── STEP 3: LOAD SOS PARISH REGISTRATION + ASSIGN DISTRICTS ──────────────────
print(f"\n[3/6] Loading SOS parish registration data...")
print(f"      Source: {SOS_SOURCE_LABEL}")
print(f"      NOTE: district-level aggregates from this step are provisional.")
print(f"            SOS has not officially re-tabulated by Act 2 geography.")

def parse_sos_statewide(filepath):
    """
    Parse Louisiana SOS statewide voter registration XLS.
    Source: Louisiana Secretary of State, Active Voter Registration, 5/1/2026.
    PROVISIONAL: data reported under prior district geography.

    Column layout (0-indexed):
        0:  Parish name -- format 'PARISH NAME - ##'
        2:  Total registered
        3:  White registered
        4:  Black registered
        5:  Other race registered
        6:  Democrat total
        7:  Democrat white
        8:  Democrat Black
        9:  Democrat other
        10: Republican total
        11: Republican white
        12: Republican Black
        13: Republican other
        14: No Party total
        18: Other parties total
    Data rows: 10-73 (64 Louisiana parishes)
    """
    raw = pd.read_excel(filepath, engine="xlrd", header=None)
    records = []
    for i in range(10, 74):
        row = raw.iloc[i]
        name_raw = str(row[0]).strip()
        if name_raw in ("nan", ""):
            continue
        parts = name_raw.split(" - ")
        parish_name = parts[0].strip().upper()
        parish_num  = int(parts[1].strip()) if len(parts) > 1 else 0
        records.append({
            "parish":       parish_name,
            "parish_num":   parish_num,
            "total_reg":    int(row[2]),
            "white_reg":    int(row[3]),
            "black_reg":    int(row[4]),
            "other_reg":    int(row[5]),
            "dem_total":    int(row[6]),
            "dem_white":    int(row[7]),
            "dem_black":    int(row[8]),
            "dem_other":    int(row[9]),
            "rep_total":    int(row[10]),
            "rep_white":    int(row[11]),
            "rep_black":    int(row[12]),
            "rep_other":    int(row[13]),
            "no_party":     int(row[14]),
            "other_party":  int(row[18]),
            "rv_source":    f"{SOS_SOURCE_LABEL} -- Report Date {SOS_REPORT_DATE}",
        })
    return pd.DataFrame(records)

parishes_df = parse_sos_statewide(STA_FILE)
parishes_df["district"] = parishes_df["parish"].map(PARISH_DISTRICT)

unmapped = parishes_df[parishes_df["district"].isna()]["parish"].tolist()
if unmapped:
    print(f"   WARNING: Unmapped parishes (defaulting to District 5): {unmapped}")
parishes_df["district"] = parishes_df["district"].fillna(5).astype(int)

parishes_df["boundary_source"] = ACT2_SOURCE_LABEL
parishes_df["rv_provisional"]  = True   # flag: registration not re-tabulated by Act 2 geography

statewide_total     = parishes_df["total_reg"].sum()
statewide_black_rv  = parishes_df["black_reg"].sum()
statewide_black_pct = statewide_black_rv / statewide_total * 100

parishes_df["black_pct"] = (parishes_df["black_reg"] / parishes_df["total_reg"] * 100).round(2)
parishes_df["white_pct"] = (parishes_df["white_reg"] / parishes_df["total_reg"] * 100).round(2)
parishes_df["dem_pct"]   = (parishes_df["dem_total"] / parishes_df["total_reg"] * 100).round(2)
parishes_df["rep_pct"]   = (parishes_df["rep_total"] / parishes_df["total_reg"] * 100).round(2)

# REI calculated against SOS registration baseline (labeled explicitly)
parishes_df["rei_registration"] = (parishes_df["black_pct"] - statewide_black_pct).round(2)
parishes_df["rei_source"]       = f"SOS registration-based REI. Baseline: {statewide_black_pct:.1f}% (SOS 5/1/2026). NOT Census VAP-based."

parishes_df["partisan_lean"] = parishes_df.apply(
    lambda r: "STRONG D" if r["dem_pct"] > 48 else
              ("LEAN D"   if r["dem_pct"] > 38 else
              ("LEAN R"   if r["rep_pct"] > 38 else "COMPETITIVE")), axis=1
)

print(f"   OK  Loaded {len(parishes_df)} parishes")
print(f"   OK  Statewide total registered: {statewide_total:,}  [SOS {SOS_REPORT_DATE}, provisional]")
print(f"   OK  Statewide Black % (registration): {statewide_black_pct:.1f}%  [SOS -- NOT Census VAP]")


# ─── STEP 4: DISTRICT-LEVEL REGISTRATION AGGREGATION (PROVISIONAL) ────────────
print(f"\n[4/6] Aggregating SOS registration by Act 2 district (provisional)...")
print(f"      CAUTION: Whole-parish assignment -- sub-parish splits not reflected.")
print(f"               Do not treat these totals as certified Act 2 district statistics.")

by_district_rv = parishes_df.groupby("district").agg(
    total_reg  = ("total_reg", "sum"),
    white_reg  = ("white_reg", "sum"),
    black_reg  = ("black_reg", "sum"),
    other_reg  = ("other_reg", "sum"),
    dem_total  = ("dem_total", "sum"),
    rep_total  = ("rep_total", "sum"),
    no_party   = ("no_party",  "sum"),
    dem_black  = ("dem_black", "sum"),
    rep_black  = ("rep_black", "sum"),
).reset_index()

by_district_rv["black_pct_rv"] = (by_district_rv["black_reg"] / by_district_rv["total_reg"] * 100).round(2)
by_district_rv["white_pct_rv"] = (by_district_rv["white_reg"] / by_district_rv["total_reg"] * 100).round(2)
by_district_rv["dem_pct_rv"]   = (by_district_rv["dem_total"] / by_district_rv["total_reg"] * 100).round(2)
by_district_rv["rep_pct_rv"]   = (by_district_rv["rep_total"] / by_district_rv["total_reg"] * 100).round(2)

# REI against SOS registration baseline (NOT Census VAP baseline)
by_district_rv["rei_registration"]  = (by_district_rv["black_pct_rv"] - statewide_black_pct).round(2)
by_district_rv["rei_severity_rv"]   = by_district_rv["rei_registration"].abs().round(2)
by_district_rv["rv_provisional"]    = True
by_district_rv["rv_source"]         = f"{SOS_SOURCE_LABEL} -- {SOS_REPORT_DATE}"

# Merge VAP and registration district tables
by_district = by_district_vap.merge(by_district_rv, on="district", how="left")

# REI against Census VAP baseline (authoritative)
by_district["rei_vap"] = (by_district["pct_black_vap"] - statewide_black_vap_pct).round(2)
by_district["rei_severity_vap"] = by_district["rei_vap"].abs().round(2)
by_district["vap_baseline_pct"] = round(statewide_black_vap_pct, 2)
by_district["rv_baseline_pct"]  = round(statewide_black_pct, 2)

def classify_rei(dev, district_id, source="VAP"):
    """
    Classify district gerrymandering effect under Act 2 boundaries.
    Source label distinguishes VAP-based from registration-based classification.
    """
    if district_id == 2:
        return f"PACKED -- Black residents/voters concentrated above proportional share (Act 2 D2) [{source}-based]"
    if dev < -8:  return f"SEVERELY CRACKED -- far below proportional [{source}-based]"
    if dev < -4:  return f"CRACKED -- below proportional [{source}-based]"
    if dev < 2:   return f"NEAR PROPORTIONAL -- within tolerance [{source}-based]"
    return f"ABOVE AVERAGE -- over-represented [{source}-based]"

by_district["rei_class_vap"] = by_district.apply(
    lambda r: classify_rei(r["rei_vap"], r["district"], "VAP"), axis=1
)
by_district["rei_class_rv"] = by_district.apply(
    lambda r: classify_rei(r["rei_registration"], r["district"], "SOS registration"), axis=1
)

def classify_viability_vap(black_vap_pct):
    """
    Electoral viability based on Census PL 94-171 Black VAP percentage.
    D2 is the ONLY majority Black VAP district under Act 2.
    D6 Black VAP is 24.58% -- not majority Black.
    """
    if black_vap_pct >= 50:  return "VIABLE -- Majority-minority VAP district (Census PL 94-171)"
    if black_vap_pct >= 30:  return "MARGINAL -- Influence district, below VAP majority"
    return "NON-VIABLE -- Black VAP below decisive threshold"

by_district["viability_vap"] = by_district["pct_black_vap"].apply(classify_viability_vap)

# Wasted votes estimate (analytical construct -- labeled as such)
by_district["wasted_black_votes_est"] = by_district.apply(
    lambda r: max(0, int(r["vap_black"] - r["vap_total"] * 0.50))
    if r["district"] == 2 else int(r["vap_black"]), axis=1
)
by_district["wasted_votes_source"] = "Analytical estimate based on Census VAP. Not a certified metric."

ideal_black_vap_per_district = statewide_vap_black / 6
by_district["vap_displaced"] = (
    by_district["vap_black"] - ideal_black_vap_per_district
).round(0).astype(int)

by_district["partisan_lean"] = by_district.apply(
    lambda r: "STRONG D" if r["dem_pct_rv"] > 48 else
              ("LEAN D"   if r["dem_pct_rv"] > 38 else "REPUBLICAN-CONTROLLED"), axis=1
)

by_district["sos_source"]      = f"{SOS_SOURCE_LABEL} -- {SOS_REPORT_DATE}"
by_district["boundary_source"] = ACT2_SOURCE_LABEL
by_district["vap_source"]      = PL_SOURCE_LABEL

print("\n   DISTRICT EQUITY SUMMARY")
print(f"   {'Dist':<6} {'Black VAP%':>11} {'Maj?':>6}  {'Black RV%':>10} {'REI_VAP':>9}  {'REI_RV':>7}")
print(f"   {'--'*50}")
for _, r in by_district.iterrows():
    maj = "YES" if r["majority_black_vap"] else "no"
    print(f"   D{int(r.district):<5} {r.pct_black_vap:>10.2f}% {maj:>6}  "
          f"{r.black_pct_rv:>9.2f}% {r.rei_vap:>+8.2f}pp  {r.rei_registration:>+6.2f}pp")


# ─── STEP 5: LOAD ACT 2 SHAPEFILE + MERGE ────────────────────────────────────
print(f"\n[5/6] Loading Act 2 (SB 121) enrolled district shapefile...")
print(f"      Source: {ACT2_SOURCE_LABEL}")

geojson_path = OUT_DIR / "act2_districts_rei.geojson"

try:
    os.environ["SHAPE_RESTORE_SHX"] = "YES"

    import shutil, tempfile
    tmp = Path(tempfile.mkdtemp())
    for f in Path(SHP_FILE).parent.glob(Path(SHP_FILE).stem + "*"):
        shutil.copy(f, tmp / f.name)
    gdf = gpd.read_file(str(tmp / Path(SHP_FILE).name))

    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    else:
        gdf = gdf.to_crs("EPSG:4326")

    # Assign district numbers to shapefile rows
    if "district" not in gdf.columns:
        gdf["district"] = range(1, len(gdf) + 1)

    gdf = gdf.merge(by_district, on="district", how="left")
    gdf["geometry"] = gdf.geometry.simplify(0.001, preserve_topology=True)

    # Embed full source attribution
    gdf["sos_source"]       = f"{SOS_SOURCE_LABEL} -- {SOS_REPORT_DATE}"
    gdf["boundary_source"]  = ACT2_SOURCE_LABEL
    gdf["vap_source"]       = PL_SOURCE_LABEL
    gdf["act2_status"]      = "Signed by Governor Landry -- enrolled as Act 2 -- R.S. 18:1276"
    gdf["act2_effective"]   = "2026 congressional elections (immediate); full statutory: noon Jan 3, 2027"
    gdf["rv_provisional"]   = True
    gdf["rv_note"]          = "SOS registration not re-tabulated by Act 2 geography. District totals are provisional."
    gdf["majority_black_note"] = "District 2 is the only majority Black VAP district (58.24% Black VAP, Census PL 94-171). District 6 Black VAP is 24.58% -- not majority Black."

    gdf.to_file(str(geojson_path), driver="GeoJSON")
    print(f"   OK  Saved enriched GeoJSON: {geojson_path}")
    print(f"   OK  GeoJSON size: {geojson_path.stat().st_size // 1024}KB")

except Exception as e:
    print(f"   WARNING: Shapefile merge failed ({e})")
    print("   Dashboard JSON will still work -- map can use pre-processed boundaries.")


# ─── STEP 6: WRITE OUTPUT FILES ────────────────────────────────────────────────
print(f"\n[6/6] Writing output files...")

# Statewide equity metrics
black_in_non_d2_vap = int(by_district[by_district["district"] != 2]["vap_black"].sum())
pct_in_non_d2_vap   = round(black_in_non_d2_vap / statewide_vap_black * 100, 1)

black_in_non_d2_rv  = int(by_district[by_district["district"] != 2]["black_reg"].sum())
pct_in_non_d2_rv    = round(black_in_non_d2_rv / statewide_black_rv * 100, 1)

prop_seats_vap      = round((statewide_black_vap_pct / 100) * 6, 2)
prop_seats_rv       = round((statewide_black_pct / 100) * 6, 2)

dashboard_payload = {
    "metadata": {
        # ── Attribution ──────────────────────────────────────────────────────
        "analyst":              "Tia Fields",
        "website":              "TiaFields.com",
        "project":              "Louisiana Redistricting Equity Dashboard",

        # ── Act 2 legal status ────────────────────────────────────────────────
        "act2_status":          ACT2_STATUS,
        "boundary_source":      ACT2_SOURCE_LABEL,
        "boundary_shapefile":   "SB_121_Enrolled.shp",

        # ── Census VAP source (authoritative for demographics) ─────────────────
        "vap_source":           PL_SOURCE_LABEL,
        "vtd_source":           VTD_SOURCE_LABEL,
        "vap_note":             "Census PL 94-171 VAP is the authoritative population source. Distinct from SOS registration.",

        # ── SOS registration source (provisional) ────────────────────────────
        "sos_source":           SOS_SOURCE_LABEL,
        "sos_report_date":      SOS_REPORT_DATE,
        "sos_file_statewide":   "2026_0501_sta_comb.xls",
        "sos_file_parish":      "2026_0501_par_comb.xls",
        "sos_provisional_note": "SOS registration not yet re-tabulated by Act 2 district geography. All district-level registration statistics are provisional and must not be treated as final Act 2 district totals.",

        # ── Data integrity note ───────────────────────────────────────────────
        "data_integrity_note":  (
            "VAP anomalies identified in pre-enrollment SB 121 Reengrossed text (Pages 11-12): "
            "Jefferson Parish D1 segment shows 146.7% registration rate against stated VAP. "
            "D1 parish VAPs summed to 477,567 but reengrossed bill declared 601,847 (gap: 124,280). "
            "Source: SB 121 Reengrossed, Pages 11-12. Identified by Rep. C. Denise Marcelle (D-Baton Rouge), "
            "May 21, 2026. Verify against enrolled Act 2 before treating as confirmed defect."
        ),

        # ── Census VAP statewide metrics ──────────────────────────────────────
        "statewide_vap_total":              int(statewide_vap_total),
        "statewide_vap_black":              int(statewide_vap_black),
        "statewide_black_vap_pct":          round(statewide_black_vap_pct, 2),
        "majority_black_vap_districts":     int(by_district["majority_black_vap"].sum()),
        "majority_black_vap_note":          "District 2 only (58.24% Black VAP). District 6 is 24.58% Black VAP -- not majority Black.",
        "proportional_seats_vap":           prop_seats_vap,
        "representational_deficit_vap":     round(prop_seats_vap - 1, 2),
        "black_vap_outside_d2":             black_in_non_d2_vap,
        "pct_black_vap_outside_d2":         pct_in_non_d2_vap,

        # ── SOS registration statewide metrics (provisional) ──────────────────
        "statewide_total_reg":              int(statewide_total),
        "statewide_black_reg":              int(statewide_black_rv),
        "statewide_black_pct_rv":           round(statewide_black_pct, 2),
        "statewide_dem_pct_rv":             round(parishes_df["dem_total"].sum() / statewide_total * 100, 2),
        "statewide_rep_pct_rv":             round(parishes_df["rep_total"].sum() / statewide_total * 100, 2),
        "proportional_seats_rv":            prop_seats_rv,
        "black_rv_outside_d2":              black_in_non_d2_rv,
        "pct_black_rv_outside_d2":          pct_in_non_d2_rv,
        "rv_provisional":                   True,

        # ── REI methodology note ───────────────────────────────────────────────
        "rei_methodology": (
            "REI_VAP = District Black VAP% - Statewide Black VAP% (Census PL 94-171). "
            "REI_REGISTRATION = District Black Reg% - Statewide Black Reg% (SOS 5/1/2026, provisional). "
            "Both are reported. They are not compared to each other. "
            "Positive = PACKED. Negative = CRACKED. |REI| > 8pp = severe dilution."
        ),
    },

    # Districts include both VAP and registration metrics, clearly labeled
    "districts":            by_district.to_dict(orient="records"),

    # Parishes are registration-based only (provisional)
    "parishes":             parishes_df.to_dict(orient="records"),

    "parishes_by_district": {
        str(d): parishes_df[parishes_df["district"] == d][[
            "parish", "total_reg", "black_reg", "black_pct",
            "dem_total", "rep_total", "dem_pct", "rep_pct",
            "rv_source", "boundary_source", "rv_provisional"
        ]].to_dict(orient="records")
        for d in range(1, 7)
    },

    # VTD-level: Census VAP and registration joined (most granular)
    "vtd_summary_by_district": {
        str(d): vtd_df[vtd_df["district"] == d][[
            "GEOID20", "COUNTYFP20", "VTDST20", "NAME20",
            "TOT_POP", "TOT_BLACK", "VAP_TOTAL", "VAP_BLACK",
            "pct_black_vap", "RVTOTAL", "RVBLACK", "pct_black_rv",
            "vap_source", "rv_source"
        ]].to_dict(orient="records")
        for d in range(1, 7)
    },
}

json_out = OUT_DIR / "dashboard_data.json"
with open(json_out, "w") as f:
    json.dump(dashboard_payload, f, indent=2, default=float)

# VTD-level equity report (new -- Census VAP + registration both included)
vtd_out = OUT_DIR / "vtd_equity_report.csv"
vtd_df[[
    "GEOID20", "COUNTYFP20", "VTDST20", "NAME20", "district",
    "TOT_POP", "TOT_BLACK", "VAP_TOTAL", "VAP_BLACK", "VAP_WHITE",
    "pct_black_vap", "RVTOTAL", "RVBLACK", "RVDEMTOTAL", "RVREPTOTAL",
    "pct_black_rv", "pct_dem_rv", "pct_rep_rv",
    "vap_source", "rv_source", "boundary_source"
]].to_csv(vtd_out, index=False)

# Parish-level report (registration-based, provisional)
csv_out = OUT_DIR / "parish_equity_report.csv"
parishes_df[[
    "parish", "district", "total_reg", "white_reg", "black_reg", "other_reg",
    "black_pct", "dem_pct", "rep_pct", "rei_registration",
    "partisan_lean", "rv_source", "boundary_source", "rv_provisional"
]].to_csv(csv_out, index=False)

print(f"   OK  dashboard_data.json       -> {json_out.stat().st_size // 1024}KB")
print(f"   OK  vtd_equity_report.csv     -> {vtd_out}")
print(f"   OK  parish_equity_report.csv  -> {csv_out}")


# ─── FINAL SUMMARY ────────────────────────────────────────────────────────────
print(f"""
+------------------------------------------------------------------------------+
|                    ACT 2 (SB 121) REDISTRICTING EQUITY FINDINGS             |
+------------------------------------------------------------------------------+
|  LEGAL STATUS                                                                |
|  Bill:         SB 121 (Morris) enrolled as Act 2                            |
|  Enacted:      Act 2 -- signed by Governor Landry                           |
|  Statute:      R.S. 18:1276                                                  |
|  Effective:    2026 congressional elections (immediate upon signature)       |
|  Full effect:  Noon, January 3, 2027                                        |
+------------------------------------------------------------------------------+
|  DATA SOURCES (in order of authority)                                        |
|  1. Act 2 enrolled geometry:  SB_121_Enrolled.shp                           |
|  2. Census PL 94-171 VAP:     la000032020.pl (authoritative demographics)   |
|  3. VTD assignment:           SB121_VTD_assignment.csv (3,539 VTDs)         |
|  4. SOS registration:         2026_0501_sta_comb.xls  PROVISIONAL           |
|  5. Derived analysis:         REI, PACKED/CRACKED (analytical constructs)   |
+------------------------------------------------------------------------------+
|  CENSUS VAP METRICS  [PL 94-171 -- authoritative]                           |
|  Statewide Black VAP:              {statewide_black_vap_pct:.2f}%                               |
|  Majority Black VAP districts:     1 of 6  (District 2 only, 58.24%)       |
|  D6 Black VAP:                     24.58%  (NOT majority Black)             |
|  Black VAP outside District 2:     {pct_in_non_d2_vap:.1f}% of all Black residents (VAP)  |
|  Proportional seat expectation:    {prop_seats_vap:.2f} of 6 seats (Census VAP basis)   |
|  Representational deficit (VAP):   {round(prop_seats_vap-1,2):.2f} seats                            |
+------------------------------------------------------------------------------+
|  SOS REGISTRATION METRICS  [5/1/2026 -- PROVISIONAL]                        |
|  Statewide Black Reg %:            {statewide_black_pct:.1f}%  (registration, NOT Census VAP) |
|  Black reg outside District 2:     {pct_in_non_d2_rv:.1f}% of all Black registrants        |
|  NOTE: Registration not re-tabulated by Act 2 geography.                    |
|        District-level totals are analytical approximations only.            |
+------------------------------------------------------------------------------+
|  DATA INTEGRITY  [Pre-enrollment anomalies -- verify against enrolled Act 2] |
|  D1 VAP gap in reengrossed text:   124,280 phantom residents                |
|  Identified:                       Rep. C. Denise Marcelle, May 21, 2026    |
+------------------------------------------------------------------------------+
""")

print("Pipeline complete. Outputs in ./output/")
