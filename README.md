# Louisiana Redistricting Equity Dashboard
**Policy Analysis and Research: Tia Fields | Provisional Consulting LLC**
Built in response to *Louisiana v. Callais*, No. 24-109, ___ U.S. ___ (Apr. 29, 2026)

---

## What This Is
An independent spatial equity dashboard tracking Louisiana's SB 121
(Act 2 of 2026, Sen. Morris) congressional map. It analyzes the 5R/1D cracking
of Black voting power across all six congressional districts using Census PL
94-171 Voting Age Population data and Louisiana Secretary of State voter
registration records, kept as two separate and clearly labeled layers.

**Live Dashboard:** https://tiandrafields-arch.github.io/redistricting-dashboard---LA/

---

## Active Litigation (status as of August 2026)
Act 2 of 2026 was heard by a federal three-judge panel on **June 17, 2026** in
*Callais v. Landry*, U.S. District Court for the Western District of Louisiana,
Shreveport. Panel: Judges Carl E. Stewart, David C. Joseph, and Robert R. Summerhays.
Opening briefs were filed June 5 and responses June 12. The enacted Act 2 map remains
in effect for the **November 3, 2026 election** while the challenge proceeds to full
evidentiary review, expected to extend into 2027. Confirm the current docket before
relying on this summary.

---

## Key Findings (Census 2020 PL 94-171, certified spatial join)
- **District 2 is the only majority Black VAP district** at 58.24 percent Black VAP.
- **District 6 Black VAP is 24.58 percent**, not majority Black despite prior claims.
- **District 1 is the most cracked** at 13.36 percent Black VAP, an REI of minus 17.88 points.
- **68.8 percent of Louisiana's Black VAP lives outside District 2** (767,141 of 1,115,306).
- On the provisional SOS registration layer, **81 percent of Black registered voters
  (749,661 of 925,657) sit outside District 2.**
- At 31.24 percent statewide Black VAP, proportional representation supports roughly
  **2 of 6 majority-Black seats**; Act 2 provides 1, a deficit of about 0.87 seats.
- Population deviation range is **0.9123 percent**, within constitutional tolerance
  under *Karcher v. Daggett*. The one person one vote theory is not the winning pathway;
  racial gerrymandering and discriminatory intent are.

---

## Data Notes (updated August 2026)
- **Black VAP definition.** The Black VAP figures above are Any Part Black (Black alone
  or in combination), consistent with the illustrative-district analysis in *Robinson v.
  Ardoin*. The Redistricting Data Hub's published 120th-plan figures use Black alone
  (single race) and run about 1 to 2 points lower (for example D2 at 55.9 percent). The
  dashboard now shows both bases side by side. District 2 is majority Black, and the
  other five fall short, under either definition.
- **Change analysis.** The dashboard now incorporates the RDH 119th to 120th change
  analysis: the Removed, Retained, and Added composition of each district, with VAP,
  Black share, and 2024 presidential two-party Democratic share. District 6 is the clearest
  case: it shed territory that was 56.5 percent Black and 59.5 percent Democratic and took
  on territory that was 16.5 percent Black and 27.0 percent Democratic.

---

## Two Data Layers, Never Mixed
| Layer | Source | File | Role |
|-------|--------|------|------|
| Population and VAP | Census 2020 PL 94-171 | la000032020.pl + validated VTD shapefile | Legally authoritative demographics and REI baseline (31.24 percent) |
| District geometry | Act 2 (SB 121) enrolled | SB_121_Enrolled.shp | Legal boundary definition, R.S. 18:1276 |
| VTD assignment | Certified spatial join | SB121_VTD_assignment.csv | 3,536 of 3,539 VTDs matched |
| Voter registration | LA Secretary of State 5/1/2026 | 2026_0501_sta_comb.xls | Provisional, parish level, not reconciled to Act 2 precincts |

The Representational Equity Index used throughout the dashboard is VAP based
(District Black VAP percent minus 31.24 percent). The SOS registration share
(31.2 percent) appears only as provisional context and is never substituted into the REI.

---

## Provisional Parish Note
District level registration rollups assign each parish whole to the district holding
the majority of its precincts under enrolled Act 2. For split parishes this is an
approximation. In the June 2026 build, Lafourche and Tangipahoa were aligned to the
enacted map's majority coloring (Lafourche to D1, Tangipahoa to D5). VAP figures are
unaffected because they derive from the certified VTD spatial join, not parish rollups.

---

## What This Project Does Not Contain
- No personally identifiable information.
- No private or proprietary data.
- All source data is public record.

---

## Attribution and License
(c) 2026 Tia Fields, Provisional Consulting LLC.
Licensed under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/).
Any use of this analysis must credit **Tia Fields / Provisional Consulting LLC**.
