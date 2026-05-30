# Louisiana Redistricting Equity Dashboard
**Policy Analysis & Research: Tia Fields | Provisional Consulting LLC**
Built in response to *Louisiana v. Callais*, 608 U.S. ___ (Apr. 29, 2026)

---

## What This Is
An independent spatial equity dashboard tracking Louisiana's SB 121 
(Act 2) redistricting plan — analyzing the 5R/1D cracking of Black 
voting power across all six congressional districts using Census PL 
94-171 data and Louisiana Secretary of State voter registration records.

**Live Dashboard:** https://tiandrafields-arch.github.io/redistricting-dashboard---LA/

---

## Key Findings
- **District 2 is the only majority Black VAP district** (58.24% Black VAP)
- **District 6 Black VAP: 24.58%** — not majority Black despite prior claims
- **74.3% of Black Louisiana residents** live outside District 2
- Representational deficit of approximately **0.33 seats** below proportional share

---

## Data Sources
| Source | File | Authority |
|--------|------|-----------|
| Act 2 (SB 121) enrolled shapefile | SB_121_Enrolled.shp | Legal boundary definition |
| Census PL 94-171 Segment 3 | la000032020.pl | Authoritative demographics |
| VTD assignment file | SB121_VTD_assignment.csv | 3,539 VTDs |
| LA Secretary of State registration | 2026_0501_sta_comb.xls | Provisional |

---

## Methodology
Representational Equity Index (REI):
- **REI_VAP** = District Black VAP% − Statewide Black VAP% (Census PL 94-171)
- **REI_REGISTRATION** = District Black Reg% − Statewide Black Reg% (SOS, provisional)
- Positive = PACKED | Negative = CRACKED
- |REI| > 8pp = severe dilution

---

## What This Project Does Not Contain
- No personally identifiable information (PII)
- No private or proprietary data
- All source data is public record

---

## Attribution & License
© 2026 Tia Fields — Provisional Consulting LLC
Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
Any use of this analysis must credit **Tia Fields / Provisional Consulting LLC**
