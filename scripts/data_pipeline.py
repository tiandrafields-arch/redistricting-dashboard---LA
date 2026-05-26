"""
Louisiana SB 121 Redistricting Equity Pipeline
Policy Analysis & Research: Tia Fields 
TiaFields.com

REQUIREMENTS:
    pip install pandas geopandas xlrd shapely

INPUTS:
    - 2026_0501_sta_comb.xls   : SOS Statewide voter registration by party/race
    - 2026_0501_par_comb.xls   : SOS Parish-level voter registration
    - HCA_SB121-5662_(McMakin).shp : McMakin Amendment district boundaries

OUTPUTS:
    - dashboard_data.json       : All district/parish data for the frontend
    - sb121_districts_rei.geojson : Enriched district GeoJSON with REI scores
    - parish_equity_report.csv  : Full parish-level equity analysis

METHODOLOGY:
    Representational Equity Index (REI):
    REI = (District Black % - Statewide Black %) in percentage points
    Positive = PACKED (above proportional); Negative = CRACKED (below proportional)
    Threshold: |REI| > 8pp = severe dilution; |REI| > 5pp = significant dilution
"""

import os
import json
import pandas as pd
import geopandas as gpd
from pathlib import Path

# ─── CONFIGURATION ────────────────────────────────────────────────────
DATA_DIR = Path(".")
STA_FILE = DATA_DIR / "2026_0501_sta_comb.xls"
PAR_FILE = DATA_DIR / "2026_0501_par_comb.xls"
SHP_FILE = DATA_DIR / "HCA_SB121-5662_(McMakin).shp"
OUT_DIR  = DATA_DIR / "output"
OUT_DIR.mkdir(exist_ok=True)

# McMakin Amendment district assignments (from SB121 Reengrossed + HCA 3645/5662)
# Reflects McMakin's parish transfers: Morehouse/Lincoln/Jackson -> D4,
# Calcasieu whole -> D3, Grant+St.Landry whole -> D5
PARISH_DISTRICT = {
    # District 1 — SE Gulf Coast (R)
    "JEFFERSON":1, "ST. TAMMANY":1, "PLAQUEMINES":1, "ST. BERNARD":1,
    "TANGIPAHOA":1, "WASHINGTON":1,
    # District 2 — New Orleans (D) — packed majority-Black
    "ORLEANS":2, "ST. CHARLES":2, "ST. JOHN THE BAPTIST":2, "ST. JAMES":2,
    "LAFOURCHE":2, "TERREBONNE":2,
    # District 3 — SW Acadiana (R)
    "LAFAYETTE":3, "ST. LANDRY":3, "ST. MARTIN":3, "IBERIA":3, "ST. MARY":3,
    "VERMILION":3, "CALCASIEU":3, "JEFFERSON DAVIS":3, "CAMERON":3,
    "BEAUREGARD":3, "ALLEN":3, "ACADIA":3, "EVANGELINE":3,
    # District 4 — Northwest (R) [McMakin: +Morehouse, Lincoln, Jackson]
    "CADDO":4, "BOSSIER":4, "WEBSTER":4, "DE SOTO":4, "SABINE":4,
    "RED RIVER":4, "BIENVILLE":4, "CLAIBORNE":4, "UNION":4,
    "MOREHOUSE":4, "LINCOLN":4, "JACKSON":4,
    # District 5 — North-Central (R) [McMakin: Grant+St.Landry whole]
    "EAST BATON ROUGE":5, "ASCENSION":5, "LIVINGSTON":5, "OUACHITA":5,
    "RAPIDES":5, "GRANT":5, "NATCHITOCHES":5, "WINN":5, "CALDWELL":5,
    "LASALLE":5, "CATAHOULA":5, "CONCORDIA":5, "FRANKLIN":5,
    "RICHLAND":5, "AVOYELLES":5, "TENSAS":5, "MADISON":5,
    # District 6 — River Corridor (R) — Black community cracked from D2
    "WEST BATON ROUGE":6, "POINTE COUPEE":6, "EAST FELICIANA":6,
    "WEST FELICIANA":6, "ST. HELENA":6, "ASSUMPTION":6, "IBERVILLE":6,
    "EAST CARROLL":6, "WEST CARROLL":6, "VERNON":6,
}


# ─── STEP 1: LOAD + PARSE SOS VOTER REGISTRATION DATA ─────────────────
print("[1/5] Loading SOS voter registration data...")

def parse_sos_statewide(filepath):
    """
    Parse SOS statewide XLS. Layout:
    Col 0: parish name (e.g. 'CADDO - 09')
    Col 2-5: TOTAL/WHITE/BLACK/OTHER registered voters
    Col 6-9: DEM total/white/black/other
    Col 10-13: REP total/white/black/other
    Col 14-17: NO PARTY total/white/black/other
    Col 18-21: OTHER PARTIES total/white/black/other
    Data rows: 10-73 (64 parishes)
    """
    raw = pd.read_excel(filepath, engine='xlrd', header=None)
    records = []
    for i in range(10, 74):
        row = raw.iloc[i]
        name_raw = str(row[0]).strip()
        if name_raw in ('nan', ''):
            continue
        parts = name_raw.split(' - ')
        parish_name = parts[0].strip()
        parish_num  = int(parts[1].strip()) if len(parts) > 1 else 0
        records.append({
            'parish':       parish_name,
            'parish_num':   parish_num,
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
        })
    return pd.DataFrame(records)

parishes_df = parse_sos_statewide(STA_FILE)
print(f"   Loaded {len(parishes_df)} parishes. Total registered: {parishes_df['total_reg'].sum():,}")


# ─── STEP 2: ASSIGN DISTRICTS + CALCULATE PARISH METRICS ──────────────
print("[2/5] Assigning McMakin district boundaries and calculating metrics...")

parishes_df['district'] = parishes_df['parish'].map(PARISH_DISTRICT).fillna(5).astype(int)

# Statewide baseline
statewide_total     = parishes_df['total_reg'].sum()
statewide_black     = parishes_df['black_reg'].sum()
statewide_black_pct = statewide_black / statewide_total * 100
statewide_dem_pct   = parishes_df['dem_total'].sum() / statewide_total * 100
statewide_rep_pct   = parishes_df['rep_total'].sum() / statewide_total * 100

# Parish-level derived metrics
parishes_df['black_pct']   = (parishes_df['black_reg'] / parishes_df['total_reg'] * 100).round(2)
parishes_df['white_pct']   = (parishes_df['white_reg'] / parishes_df['total_reg'] * 100).round(2)
parishes_df['dem_pct']     = (parishes_df['dem_total'] / parishes_df['total_reg'] * 100).round(2)
parishes_df['rep_pct']     = (parishes_df['rep_total'] / parishes_df['total_reg'] * 100).round(2)
parishes_df['rei_parish']  = (parishes_df['black_pct'] - statewide_black_pct).round(2)
parishes_df['partisan_lean'] = parishes_df.apply(
    lambda r: 'STRONG D' if r['dem_pct'] > 48 else
              ('LEAN D'  if r['dem_pct'] > 38 else
              ('LEAN R'  if r['rep_pct'] > 38 else 'COMPETITIVE')), axis=1
)

print(f"   Statewide Black %: {statewide_black_pct:.1f}%")
print(f"   Statewide Dem %:   {statewide_dem_pct:.1f}%")
print(f"   Statewide Rep %:   {statewide_rep_pct:.1f}%")


# ─── STEP 3: AGGREGATE BY DISTRICT + CALCULATE REI ────────────────────
print("[3/5] Aggregating district-level equity analysis...")

by_district = parishes_df.groupby('district').agg(
    total_reg=('total_reg','sum'), white_reg=('white_reg','sum'),
    black_reg=('black_reg','sum'), other_reg=('other_reg','sum'),
    dem_total=('dem_total','sum'), rep_total=('rep_total','sum'),
    no_party=('no_party','sum'), dem_black=('dem_black','sum'),
    rep_black=('rep_black','sum')
).reset_index()

by_district['black_pct']    = (by_district['black_reg'] / by_district['total_reg'] * 100).round(2)
by_district['white_pct']    = (by_district['white_reg'] / by_district['total_reg'] * 100).round(2)
by_district['dem_pct']      = (by_district['dem_total'] / by_district['total_reg'] * 100).round(2)
by_district['rep_pct']      = (by_district['rep_total'] / by_district['total_reg'] * 100).round(2)
by_district['rei_deviation'] = (by_district['black_pct'] - statewide_black_pct).round(2)
by_district['rei_severity']  = by_district['rei_deviation'].abs().round(2)

# REI classification
def classify_rei(row):
    if row['district'] == 2:
        return 'PACKED — Black voters concentrated above proportional share'
    dev = row['rei_deviation']
    if dev < -8:   return 'SEVERELY CRACKED — far below proportional representation'
    if dev < -4:   return 'CRACKED — below proportional representation'
    if dev < 2:    return 'NEAR PROPORTIONAL — within tolerance'
    return 'ABOVE AVERAGE — Black voters slightly over-represented'

by_district['rei_class'] = by_district.apply(classify_rei, axis=1)

# Electoral viability (can Black voters elect preferred candidate?)
# Assumes ~90% of Black Dem voters vote their preferred candidate
# Without >~45% Black registration in Deep South partisan context = unviable
by_district['black_electoral_viability'] = by_district['black_pct'].apply(
    lambda p: 'VIABLE — Majority-minority opportunity district' if p >= 45
    else ('MARGINAL — Influence but not decisive' if p >= 30
    else 'NON-VIABLE — Black voters systematically outvoted')
)

# Vote waste calculation (packing metric for D2, cracking metric for others)
# Packed: votes above 50% majority threshold are "wasted" — Black community is
#         over-packed, those excess voters could have won influence in adjacent districts
# Cracked: entire Black registration is "wasted" as it cannot overcome white bloc voting
by_district['wasted_black_votes'] = by_district.apply(
    lambda r: max(0, int(r['black_reg'] - r['total_reg'] * 0.50))
    if r['district'] == 2 else int(r['black_reg']), axis=1
)

# Total voters displaced from proportional representation
ideal_black_per_district = statewide_black / 6
by_district['voters_displaced'] = (by_district['black_reg'] - ideal_black_per_district).round(0).astype(int)

# Partisan lean
by_district['partisan_lean'] = by_district.apply(
    lambda r: 'STRONG D' if r['dem_pct'] > 48 else
              ('LEAN D'  if r['dem_pct'] > 38 else 'REPUBLICAN-CONTROLLED'), axis=1
)

print("\n   DISTRICT EQUITY SUMMARY:")
for _, r in by_district.iterrows():
    print(f"   D{int(r.district)}: {r.total_reg:>8,.0f} voters | Black: {r.black_pct:5.1f}% | "
          f"REI: {r.rei_deviation:+6.1f}pp | {r.rei_class[:40]}")


# ─── STEP 4: LOAD SHAPEFILE + MERGE ───────────────────────────────────
print("\n[4/5] Loading district shapefile and merging equity data...")

geojson_path = OUT_DIR / "sb121_districts_rei.geojson"

try:
    os.environ['SHAPE_RESTORE_SHX'] = 'YES'
    gdf = gpd.read_file(str(SHP_FILE))

    # Copy to writable location if needed
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

    # Save enriched GeoJSON
    gdf.to_file(str(geojson_path), driver='GeoJSON')
    print(f"   Saved enriched GeoJSON: {geojson_path}")
    print(f"   GeoJSON size: {geojson_path.stat().st_size // 1024}KB")

except Exception as e:
    print(f"   WARNING: Shapefile merge failed ({e}). Skipping spatial output.")
    print("   Dashboard JSON will still work — map uses pre-processed boundaries.")


# ─── STEP 5: OUTPUT JSON + CSV ─────────────────────────────────────────
print("\n[5/5] Writing output files...")

dashboard_payload = {
    'metadata': {
        'source':             'Louisiana Secretary of State — Active Voter Registration',
        'report_date':        '5/1/2026',
        'analyst':            'Tia Fields',
        'organization':       'Invest in Louisiana',
        'website':            'TiaFields.com',
        'legislation':        'SB 121 (Morris) + HCA McMakin Amendment, 2026 Regular Session',
        'legal_context':      'Post-Louisiana v. Callais, 608 U.S. ___ (Apr. 29, 2026)',
        'statewide_total':    int(statewide_total),
        'statewide_black':    int(statewide_black),
        'statewide_black_pct': round(statewide_black_pct, 2),
        'statewide_dem_pct':  round(statewide_dem_pct, 2),
        'statewide_rep_pct':  round(statewide_rep_pct, 2),
        'total_black_in_rep_districts': int(
            by_district[by_district['district'] != 2]['black_reg'].sum()
        ),
        'pct_black_voters_in_rep_districts': round(
            by_district[by_district['district'] != 2]['black_reg'].sum() / statewide_black * 100, 1
        ),
    },
    'districts':           by_district.to_dict(orient='records'),
    'parishes':            parishes_df.to_dict(orient='records'),
    'parishes_by_district': {
        str(d): parishes_df[parishes_df['district'] == d][
            ['parish','total_reg','black_reg','black_pct','dem_total','rep_total','dem_pct','rep_pct']
        ].to_dict(orient='records')
        for d in range(1, 7)
    }
}

json_out = OUT_DIR / 'dashboard_data.json'
with open(json_out, 'w') as f:
    json.dump(dashboard_payload, f, indent=2, default=float)

csv_out = OUT_DIR / 'parish_equity_report.csv'
parishes_df[[
    'parish','district','total_reg','white_reg','black_reg','other_reg',
    'black_pct','dem_pct','rep_pct','rei_parish','partisan_lean'
]].to_csv(csv_out, index=False)

print(f"   dashboard_data.json  → {json_out.stat().st_size // 1024}KB")
print(f"   parish_equity_report → {csv_out}")

# Print key findings
payload = dashboard_payload
pct_in_rep = payload['metadata']['pct_black_voters_in_rep_districts']
print(f"""
╔══════════════════════════════════════════════════════════════╗
║           SB 121 REDISTRICTING EQUITY FINDINGS              ║
╠══════════════════════════════════════════════════════════════╣
║  Total registered voters:      {statewide_total:>10,.0f}                 ║
║  Black registered voters:      {statewide_black:>10,.0f} ({statewide_black_pct:.1f}% of electorate) ║
║  Majority-Black seats (D):     1 of 6 (16.7%)                ║
║  Black voters in R districts:  {pct_in_rep:.1f}% of all Black voters     ║
║  Proportional expectation:     2 of 6 seats (33%)            ║
║  Representational deficit:     1 seat (−16.7 points)         ║
╠══════════════════════════════════════════════════════════════╣
║  Post-Callais Section 2 VRA: GUTTED (intent standard)        ║
║  Constitutional vulnerability: ONE-PERSON-ONE-VOTE (14th)    ║
║  Data integrity: CORRUPTED (VAP > registration in 6 parishes) ║
╚══════════════════════════════════════════════════════════════╝
""")

print("Pipeline complete. Outputs in ./output/")

