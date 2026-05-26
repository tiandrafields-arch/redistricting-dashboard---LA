"""
Louisiana SB 121 Redistricting Equity Pipeline
Policy Analysis & Research: Tia Fields
TiaFields.com

PURPOSE:
    Merges Louisiana Secretary of State active voter registration data against
    SB 121 (Morris) + McMakin Amendment (HCA 3645/5662) district boundaries
    to calculate representational equity metrics, document racial vote dilution
    patterns, and produce output files for the TiaFields.com redistricting
    equity dashboard.

    All voter data sourced from: Louisiana Secretary of State — Active Voter
    Registration File, Report Date 5/1/2026.

    All district boundaries sourced from: SB 121 Reengrossed (Morris) +
    House Committee Amendment HCA 3645/5662 (McMakin), 2026 Regular Session.
    Shapefile: HCA_SB121-5662_(McMakin).shp

LEGISLATIVE STATUS:
    House Floor Vote Scheduled: Thursday, May 28, 2026 — 9:00 AM
    Post-Louisiana v. Callais, 608 U.S. ___ (Apr. 29, 2026)

REQUIREMENTS:
    pip install pandas geopandas xlrd shapely

INPUTS:
    - 2026_0501_sta_comb.xls        SOS statewide voter registration by party/race
                                    Source: Louisiana Secretary of State, 5/1/2026
    - 2026_0501_par_comb.xls        SOS parish-level voter registration
                                    Source: Louisiana Secretary of State, 5/1/2026
    - HCA_SB121-5662_(McMakin).shp  McMakin Amendment district boundaries
                                    Source: SB 121, 2026 Regular Session (HCA 3645/5662)

OUTPUTS:
    - output/dashboard_data.json        District + parish equity data for the dashboard
    - output/sb121_districts_rei.geojson  SB 121 district GeoJSON enriched with REI scores
    - output/parish_equity_report.csv   Full parish-level equity analysis

METHODOLOGY — Representational Equity Index (REI):
    REI = (District Black % - Statewide Black %) in percentage points
    Positive = PACKED  (Black voters over-concentrated above proportional share)
    Negative = CRACKED (Black voters dispersed below decisive electoral threshold)
    |REI| > 8pp = severe dilution
    |REI| > 5pp = significant dilution

DATA INTEGRITY NOTE:
    SB 121 Reengrossed (Morris), Page 12 contains impossible VAP metrics:
    voter registration totals exceed stated voting-age population in 6+ parishes
    (e.g. Jefferson Parish D1 segment: 146.7% registration rate). District 1
    parish VAPs sum to 477,567 but the bill declares D1 VAP = 601,847 —
    a gap of 124,280 phantom residents. Source: SB 121 Reengrossed, Pages 11-12.
    Identified by Rep. C. Denise Marcelle (D-Baton Rouge), May 21, 2026.
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

# Louisiana Secretary of State — Active Voter Registration, 5/1/2026
STA_FILE = DATA_DIR / "2026_0501_sta_comb.xls"
PAR_FILE = DATA_DIR / "2026_0501_par_comb.xls"

# SB 121 (Morris) + McMakin Amendment (HCA 3645/5662) — district boundary shapefile
SHP_FILE = DATA_DIR / "HCA_SB121-5662_(McMakin).shp"

# Legislative tracking
FLOOR_VOTE_DATE     = "Thursday, May 28, 2026"
FLOOR_VOTE_TIME     = "9:00 AM"
FLOOR_VOTE_DATETIME = f"{FLOOR_VOTE_DATE} at {FLOOR_VOTE_TIME}"
CALLAIS_DECIDED     = "April 29, 2026"
SOS_REPORT_DATE     = "5/1/2026"
SOS_SOURCE_LABEL    = "Louisiana Secretary of State — Active Voter Registration"
SB121_SOURCE_LABEL  = "SB 121 (Morris) + HCA McMakin Amendment (3645/5662), 2026 Regular Session"

# ─── PARISH → DISTRICT MAP ────────────────────────────────────────────────────
# Source: SB 121 Reengrossed (Morris) + McMakin Amendment parish transfers:
#   Morehouse, Lincoln, Jackson  →  District 4
#   Calcasieu (whole)            →  District 3
#   Grant, St. Landry (whole)   →  District 5

PARISH_DISTRICT = {
    # District 1 — SE Gulf Coast (R)
    "JEFFERSON": 1, "ST. TAMMANY": 1, "PLAQUEMINES": 1, "ST. BERNARD": 1,
    "TANGIPAHOA": 1, "WASHINGTON": 1,

    # District 2 — New Orleans Metro (D) — packed majority-Black
    "ORLEANS": 2, "ST. CHARLES": 2, "ST. JOHN THE BAPTIST": 2, "ST. JAMES": 2,
    "LAFOURCHE": 2, "TERREBONNE": 2,

    # District 3 — SW Acadiana (R) — McMakin: Calcasieu made whole
    "LAFAYETTE": 3, "ST. LANDRY": 3, "ST. MARTIN": 3, "IBERIA": 3, "ST. MARY": 3,
    "VERMILION": 3, "CALCASIEU": 3, "JEFFERSON DAVIS": 3, "CAMERON": 3,
    "BEAUREGARD": 3, "ALLEN": 3, "ACADIA": 3, "EVANGELINE": 3,

    # District 4 — Northwest (R) — McMakin: +Morehouse, Lincoln, Jackson
    "CADDO": 4, "BOSSIER": 4, "WEBSTER": 4, "DE SOTO": 4, "SABINE": 4,
    "RED RIVER": 4, "BIENVILLE": 4, "CLAIBORNE": 4, "UNION": 4,
    "MOREHOUSE": 4, "LINCOLN": 4, "JACKSON": 4,

    # District 5 — North-Central (R) — McMakin: Grant + St. Landry whole
    "EAST BATON ROUGE": 5, "ASCENSION": 5, "LIVINGSTON": 5, "OUACHITA": 5,
    "RAPIDES": 5, "GRANT": 5, "NATCHITOCHES": 5, "WINN": 5, "CALDWELL": 5,
    "LASALLE": 5, "CATAHOULA": 5, "CONCORDIA": 5, "FRANKLIN": 5,
    "RICHLAND": 5, "AVOYELLES": 5, "TENSAS": 5, "MADISON": 5,

    # District 6 — River Corridor (R) — Black community cracked from D2
    "WEST BATON ROUGE": 6, "POINTE COUPEE": 6, "EAST FELICIANA": 6,
    "WEST FELICIANA": 6, "ST. HELENA": 6, "ASSUMPTION": 6, "IBERVILLE": 6,
    "EAST CARROLL": 6, "WEST CARROLL": 6, "VERNON": 6,
}


# ─── STEP 1: LOAD SOS VOTER REGISTRATION ──────────────────────────────────────
print(f"[1/5] Loading SOS voter registration data...")
print(f"      Source: {SOS_SOURCE_LABEL}")
print(f"      File:   {STA_FILE.name} — Report Date {SOS_REPORT_DATE}")

def parse_sos_statewide(filepath):
    """
    Parse Louisiana SOS statewide voter registration XLS.
    Source: Louisiana Secretary of State, Active Voter Registration, 5/1/2026.

    Column layout (0-indexed):
        0:  Parish name — format 'PARISH NAME - ##'
        2:  Total registered (all parties, all races)
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
    Data rows: 10–73 (64 Louisiana parishes)
    """
    raw = pd.read_excel(filepath, engine='xlrd', header=None)
    records = []
    for i in range(10, 74):
        row = raw.iloc[i]
        name_raw = str(row[0]).strip()
        if name_raw in ('nan', ''):
            continue
        parts = name_raw.split(' - ')
        parish_name = parts[0].strip().upper()
        parish_num  = int(parts[1].strip()) if len(parts) > 1 else 0
        records.append({
            'parish':       parish_name,
            'parish_num':   parish_num,
            # SOS data columns — Source: SOS Active Voter File, 5/1/2026
            'total_reg':    int(row[2]),
            'white_reg':    int(row[3]),
            'black_reg':    int(row[4]),
            'other_reg':    int(row[5]),
            'dem_total':    int(row[6]),
            'dem_white':    int(row[7]),
            'dem_black':    int(row[8]),
            'dem_other':    int(row[9]),
            'rep_total':    int(row[10]),
            'rep_white':    int(row[11]),
            'rep_black':    int(row[12]),
            'rep_other':    int(row[13]),
            'no_party':     int(row[14]),
            'other_party':  int(row[18]),
            # Data source tag — carried into all outputs
            'data_source':  f"{SOS_SOURCE_LABEL} · {SOS_REPORT_DATE}",
        })
    return pd.DataFrame(records)

parishes_df = parse_sos_statewide(STA_FILE)
print(f"   ✓ Loaded {len(parishes_df)} parishes")
print(f"   ✓ Total registered voters: {parishes_df['total_reg'].sum():,}  [SOS {SOS_REPORT_DATE}]")


# ─── STEP 2: ASSIGN SB 121 DISTRICTS + CALCULATE PARISH METRICS ───────────────
print(f"\n[2/5] Assigning SB 121 McMakin district boundaries...")
print(f"      Source: {SB121_SOURCE_LABEL}")

parishes_df['district'] = parishes_df['parish'].map(PARISH_DISTRICT)
unmapped = parishes_df[parishes_df['district'].isna()]['parish'].tolist()
if unmapped:
    print(f"   WARNING: Unmapped parishes (defaulting to District 5): {unmapped}")
parishes_df['district'] = parishes_df['district'].fillna(5).astype(int)

# Add SB 121 boundary source tag to each parish row
parishes_df['boundary_source'] = SB121_SOURCE_LABEL

# Statewide baselines — Source: SOS Active Voter File, 5/1/2026
statewide_total     = parishes_df['total_reg'].sum()
statewide_black     = parishes_df['black_reg'].sum()
statewide_black_pct = statewide_black / statewide_total * 100
statewide_dem_pct   = parishes_df['dem_total'].sum() / statewide_total * 100
statewide_rep_pct   = parishes_df['rep_total'].sum() / statewide_total * 100

# Parish-level derived metrics
parishes_df['black_pct']     = (parishes_df['black_reg'] / parishes_df['total_reg'] * 100).round(2)
parishes_df['white_pct']     = (parishes_df['white_reg'] / parishes_df['total_reg'] * 100).round(2)
parishes_df['dem_pct']       = (parishes_df['dem_total'] / parishes_df['total_reg'] * 100).round(2)
parishes_df['rep_pct']       = (parishes_df['rep_total'] / parishes_df['total_reg'] * 100).round(2)
parishes_df['rei_parish']    = (parishes_df['black_pct'] - statewide_black_pct).round(2)
parishes_df['partisan_lean'] = parishes_df.apply(
    lambda r: 'STRONG D' if r['dem_pct'] > 48 else
              ('LEAN D'   if r['dem_pct'] > 38 else
              ('LEAN R'   if r['rep_pct'] > 38 else 'COMPETITIVE')), axis=1
)

print(f"   ✓ Statewide Black %:  {statewide_black_pct:.1f}%  [SOS {SOS_REPORT_DATE}]")
print(f"   ✓ Statewide Dem %:    {statewide_dem_pct:.1f}%  [SOS {SOS_REPORT_DATE}]")
print(f"   ✓ Statewide Rep %:    {statewide_rep_pct:.1f}%  [SOS {SOS_REPORT_DATE}]")


# ─── STEP 3: AGGREGATE BY SB 121 DISTRICT + CALCULATE REI ─────────────────────
print(f"\n[3/5] Aggregating district-level equity analysis...")
print(f"      SOS data × SB 121 McMakin district boundaries")

by_district = parishes_df.groupby('district').agg(
    total_reg   = ('total_reg',  'sum'),
    white_reg   = ('white_reg',  'sum'),
    black_reg   = ('black_reg',  'sum'),
    other_reg   = ('other_reg',  'sum'),
    dem_total   = ('dem_total',  'sum'),
    rep_total   = ('rep_total',  'sum'),
    no_party    = ('no_party',   'sum'),
    dem_black   = ('dem_black',  'sum'),
    rep_black   = ('rep_black',  'sum'),
).reset_index()

by_district['black_pct']     = (by_district['black_reg'] / by_district['total_reg'] * 100).round(2)
by_district['white_pct']     = (by_district['white_reg'] / by_district['total_reg'] * 100).round(2)
by_district['dem_pct']       = (by_district['dem_total'] / by_district['total_reg'] * 100).round(2)
by_district['rep_pct']       = (by_district['rep_total'] / by_district['total_reg'] * 100).round(2)

# REI: deviation from proportional Black representation
# Formula: REI = District Black % − Statewide Black % (SOS 5/1/2026: 31.2%)
by_district['rei_deviation']  = (by_district['black_pct'] - statewide_black_pct).round(2)
by_district['rei_severity']   = by_district['rei_deviation'].abs().round(2)

def classify_rei(row):
    """
    Classify district gerrymandering effect under SB 121 McMakin boundaries.
    Baseline: 31.2% Black statewide (SOS Active Voter File, 5/1/2026).
    """
    if row['district'] == 2:
        return 'PACKED — Black voters concentrated above proportional share (SB 121 D2)'
    dev = row['rei_deviation']
    if dev < -8:  return 'SEVERELY CRACKED — far below proportional representation (SB 121)'
    if dev < -4:  return 'CRACKED — below proportional representation (SB 121)'
    if dev < 2:   return 'NEAR PROPORTIONAL — within tolerance'
    return 'ABOVE AVERAGE — Black voters slightly over-represented'

by_district['rei_class'] = by_district.apply(classify_rei, axis=1)

def classify_viability(black_pct):
    """Electoral viability under Deep South partisan polarization context."""
    if black_pct >= 45: return 'VIABLE — Majority-minority opportunity district'
    if black_pct >= 30: return 'MARGINAL — Influence but not decisive'
    return 'NON-VIABLE — Black voters systematically outvoted'

by_district['black_electoral_viability'] = by_district['black_pct'].apply(classify_viability)

# Wasted votes:
#   D2 (packed): excess above 50% threshold — structurally wasted concentration
#   All others (cracked): entire Black registration wasted under bloc-voting conditions
by_district['wasted_black_votes'] = by_district.apply(
    lambda r: max(0, int(r['black_reg'] - r['total_reg'] * 0.50))
    if r['district'] == 2 else int(r['black_reg']), axis=1
)

ideal_black_per_district = statewide_black / 6
by_district['voters_displaced'] = (
    by_district['black_reg'] - ideal_black_per_district
).round(0).astype(int)

by_district['partisan_lean'] = by_district.apply(
    lambda r: 'STRONG D' if r['dem_pct'] > 48 else
              ('LEAN D'   if r['dem_pct'] > 38 else 'REPUBLICAN-CONTROLLED'), axis=1
)

# Carry both source labels into district records
by_district['sos_source']      = f"{SOS_SOURCE_LABEL} · {SOS_REPORT_DATE}"
by_district['boundary_source'] = SB121_SOURCE_LABEL

print("\n   DISTRICT EQUITY SUMMARY  [SOS 5/1/2026 × SB 121 McMakin Boundaries]")
print(f"   {'Dist':<6} {'Total Reg':>10}  {'Black %':>8}  {'Dem %':>7}  {'Rep %':>7}  {'REI':>7}  Classification")
print(f"   {'─'*6} {'─'*10}  {'─'*8}  {'─'*7}  {'─'*7}  {'─'*7}  {'─'*38}")
for _, r in by_district.iterrows():
    print(f"   D{int(r.district):<5} {int(r.total_reg):>10,}  {r.black_pct:>7.1f}%  "
          f"{r.dem_pct:>6.1f}%  {r.rep_pct:>6.1f}%  {r.rei_deviation:>+6.1f}pp  "
          f"{r.rei_class[:38]}")


# ─── STEP 4: LOAD SB 121 SHAPEFILE + MERGE ────────────────────────────────────
print(f"\n[4/5] Loading SB 121 district shapefile...")
print(f"      Source: {SB121_SOURCE_LABEL}")

geojson_path = OUT_DIR / "sb121_districts_rei.geojson"

try:
    os.environ['SHAPE_RESTORE_SHX'] = 'YES'

    import shutil, tempfile
    tmp = Path(tempfile.mkdtemp())
    for f in Path(SHP_FILE).parent.glob(Path(SHP_FILE).stem + '*'):
        shutil.copy(f, tmp / f.name)
    gdf = gpd.read_file(str(tmp / Path(SHP_FILE).name))

    if gdf.crs is None:
        gdf = gdf.set_crs('EPSG:4326')
    else:
        gdf = gdf.to_crs('EPSG:4326')

    gdf['district'] = range(1, len(gdf) + 1)
    gdf = gdf.merge(by_district, on='district', how='left')
    gdf['geometry'] = gdf.geometry.simplify(0.001, preserve_topology=True)

    # Embed source attribution in GeoJSON properties
    gdf['sos_source']      = f"{SOS_SOURCE_LABEL} · {SOS_REPORT_DATE}"
    gdf['boundary_source'] = SB121_SOURCE_LABEL
    gdf['floor_vote']      = FLOOR_VOTE_DATETIME

    gdf.to_file(str(geojson_path), driver='GeoJSON')
    print(f"   ✓ Saved enriched GeoJSON: {geojson_path}")
    print(f"   ✓ GeoJSON size: {geojson_path.stat().st_size // 1024}KB")

except Exception as e:
    print(f"   WARNING: Shapefile merge failed ({e})")
    print("   Dashboard JSON will still work — map uses pre-processed boundaries.")


# ─── STEP 5: WRITE OUTPUT FILES ────────────────────────────────────────────────
print(f"\n[5/5] Writing output files...")

black_in_rep  = int(by_district[by_district['district'] != 2]['black_reg'].sum())
pct_in_rep    = round(black_in_rep / statewide_black * 100, 1)
prop_expected = round((statewide_black_pct / 100) * 6, 2)

dashboard_payload = {
    'metadata': {
        # ── Attribution ──────────────────────────────────────────────────────
        'analyst':                          'Tia Fields',
        'website':                          'TiaFields.com',
        'project':                          'Louisiana Redistricting Equity Dashboard',

        # ── SOS voter data source ─────────────────────────────────────────────
        'sos_source':                       SOS_SOURCE_LABEL,
        'sos_report_date':                  SOS_REPORT_DATE,
        'sos_file_statewide':               '2026_0501_sta_comb.xls',
        'sos_file_parish':                  '2026_0501_par_comb.xls',
        'sos_note':                         'Active voters only. Inactive registrations excluded.',

        # ── SB 121 boundary source ────────────────────────────────────────────
        'sb121_source':                     SB121_SOURCE_LABEL,
        'sb121_shapefile':                  'HCA_SB121-5662_(McMakin).shp',
        'sb121_author':                     'Sen. Jay Morris (R-West Monroe)',
        'sb121_amendment_author':           'Rep. Dixon McMakin (R-Baton Rouge)',
        'sb121_amendment_adopted':          'May 21, 2026 — House & Governmental Affairs Committee, 10-7',
        'sb121_floor_vote':                 FLOOR_VOTE_DATETIME,

        # ── Legal context ─────────────────────────────────────────────────────
        'legal_context':                    'Post-Louisiana v. Callais, 608 U.S. ___ (Apr. 29, 2026) — Section 2 VRA gutted',
        'callais_decided':                  CALLAIS_DECIDED,
        'constitutional_vulnerability':     '14th Amendment — One-person, one-vote (VAP anomalies in SB 121, Pages 11-12)',
        'data_integrity_note':              'SB 121 Reengrossed Page 12: Jefferson Parish D1 segment lists 196,528 registered voters against a stated VAP of 133,984 (146.7% rate). Six parishes show this pattern. D1 parish VAPs sum to 477,567 but bill declares 601,847 — gap of 124,280 phantom residents.',

        # ── Statewide equity metrics (SOS 5/1/2026) ──────────────────────────
        'statewide_total_reg':              int(statewide_total),
        'statewide_black_reg':              int(statewide_black),
        'statewide_black_pct':              round(statewide_black_pct, 2),
        'statewide_dem_pct':                round(statewide_dem_pct, 2),
        'statewide_rep_pct':                round(statewide_rep_pct, 2),
        'black_in_republican_districts':    black_in_rep,
        'pct_black_in_republican_districts': pct_in_rep,
        'majority_black_districts_sb121':   int((by_district['black_pct'] >= 50).sum()),
        'opportunity_districts_45plus':     int((by_district['black_pct'] >= 45).sum()),
        'proportional_seat_expectation':    prop_expected,
        'representational_deficit_seats':   round(prop_expected - 1, 2),
    },
    'districts':            by_district.to_dict(orient='records'),
    'parishes':             parishes_df.to_dict(orient='records'),
    'parishes_by_district': {
        str(d): parishes_df[parishes_df['district'] == d][[
            'parish', 'total_reg', 'black_reg', 'black_pct',
            'dem_total', 'rep_total', 'dem_pct', 'rep_pct',
            'data_source', 'boundary_source'
        ]].to_dict(orient='records')
        for d in range(1, 7)
    },
}

json_out = OUT_DIR / 'dashboard_data.json'
with open(json_out, 'w') as f:
    json.dump(dashboard_payload, f, indent=2, default=float)

csv_out = OUT_DIR / 'parish_equity_report.csv'
parishes_df[[
    'parish', 'district', 'total_reg', 'white_reg', 'black_reg', 'other_reg',
    'black_pct', 'dem_pct', 'rep_pct', 'rei_parish', 'partisan_lean',
    'data_source', 'boundary_source'
]].to_csv(csv_out, index=False)

print(f"   ✓ dashboard_data.json        → {json_out.stat().st_size // 1024}KB")
print(f"   ✓ parish_equity_report.csv   → {csv_out}")

# ─── FINAL SUMMARY ────────────────────────────────────────────────────────────
print(f"""
╔══════════════════════════════════════════════════════════════════════════╗
║              SB 121 REDISTRICTING EQUITY FINDINGS                       ║
╠══════════════════════════════════════════════════════════════════════════╣
║  DATA SOURCES                                                            ║
║  Voter data:   {SOS_SOURCE_LABEL:<54} ║
║                Report Date: {SOS_REPORT_DATE:<46} ║
║  Boundaries:   SB 121 (Morris) + HCA McMakin Amendment (3645/5662)      ║
║  Floor Vote:   {FLOOR_VOTE_DATETIME:<54} ║
╠══════════════════════════════════════════════════════════════════════════╣
║  EQUITY METRICS  [SOS {SOS_REPORT_DATE}]                                        ║
║  Total registered voters:        {int(statewide_total):>10,}                     ║
║  Black registered voters:        {int(statewide_black):>10,}  ({statewide_black_pct:.1f}% of electorate) ║
║  Majority-Black seats under SB 121:  1 of 6  (16.7%)                   ║
║  Black voters in Republican districts: {pct_in_rep:.1f}% of all Black voters  ║
║  Proportional seat expectation:      {prop_expected:.2f} of 6 seats               ║
║  Representational deficit:           {round(prop_expected-1,2):.2f} seats                       ║
╠══════════════════════════════════════════════════════════════════════════╣
║  LEGAL STATUS  [Post-Callais, Apr. 29, 2026]                            ║
║  Section 2 VRA:     GUTTED — intent standard reinstated                 ║
║  14th Amendment:    VIABLE — VAP anomalies in SB 121 Pages 11-12        ║
║  Data integrity:    CORRUPTED — 124,280 phantom residents in D1 VAP     ║
╚══════════════════════════════════════════════════════════════════════════╝
""")

print("Pipeline complete. Outputs in ./output/")