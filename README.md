# Louisiana Congressional Voter & Participation Dashboard

**Independent civic-data and spatial analysis by Tia Fields / Provisional Consulting LLC**

This repository began as the Louisiana Redistricting Equity Dashboard. On October 21, 2026, the live site was refocused toward a practical **congressional voter and participation tool** using Louisiana's enacted 2026 congressional districts and the latest Louisiana Secretary of State registration reports available to this project.

The legacy redistricting dashboard is preserved at:

`archive/redistricting_dashboard_legacy_2026-10-21.html`

**Live dashboard:** https://tiandrafields-arch.github.io/redistricting-dashboard---LA/

## Current Purpose

The live dashboard now prioritizes:

- current congressional-district registration composition;
- official election dates and voter resources;
- direct links to Louisiana's Voter Portal, sample ballots, and election information;
- a clear separation between registration, Census demographics, turnout, and election outcomes;
- a foundation for future historical-turnout analysis.

It does **not** currently publish a turnout forecast or candidate/party winner prediction.

## October 2026 Registration Snapshot

Source reports:

- `2026_1001_sta_comb.xls` — Louisiana Secretary of State statewide registered voters by party and race;
- `2026_1001_par_comb.xls` — parish workbook containing congressional-district subtotal rows;
- report date: **October 1, 2026**;
- report status: **Both**.

Statewide controls:

| Measure | October 1, 2026 |
|---|---:|
| Total registered | 2,978,143 |
| Black registered | 933,052 (31.33%) |
| Democratic | 1,060,252 (35.60%) |
| Republican | 1,067,827 (35.86%) |
| No Party | 825,562 (27.72%) |
| Other parties | 24,502 (0.82%) |

Official congressional-district subtotals:

| District | Total registered | Black registered | Black share | Democratic | Republican | No Party |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 515,235 | 64,317 | 12.48% | 125,197 | 223,647 | 161,292 |
| 2 | 500,285 | 300,574 | 60.08% | 297,200 | 62,577 | 135,863 |
| 3 | 495,905 | 135,492 | 27.32% | 158,548 | 195,962 | 137,864 |
| 4 | 482,573 | 146,048 | 30.26% | 156,503 | 193,517 | 129,103 |
| 5 | 484,102 | 161,950 | 33.45% | 168,228 | 191,221 | 121,670 |
| 6 | 500,043 | 124,671 | 24.93% | 154,576 | 200,903 | 139,770 |

The six district aggregates reconcile exactly to the statewide party-and-race control totals.

**Changed finding:** the former May-based estimate that 81% of Black registrants were outside District 2 is withdrawn. The October official district subtotals show **632,478 Black registrants — 67.79% of the statewide Black registration total — outside District 2**.

## Current Congressional Map

Louisiana's Legislature lists **Congress Act 2 (SB121)** among the enacted plans from the 2026 Regular Session and publishes the statewide map, reports, shapefile, and block-equivalency file.

Primary sources:

- Louisiana enacted redistricting plans: https://redist.legis.la.gov/
- Congress Act 2 materials: https://redist.legis.la.gov/2026_Files/2026CONGRESSACT2
- SB121 / Act 2: https://www.legis.la.gov/Legis/BillInfo.aspx?i=250004

## November 3, 2026 Election

The Louisiana Secretary of State lists November 3, 2026 as the **U.S. Senate General / Open U.S. Representative Primary / Open Primary Election**.

Current official voter resources:

- Election dates: https://www.sos.la.gov/elections-voting/election-dates
- Voter Portal: https://voterportal.sos.la.gov/
- Sample ballots: https://www.sos.la.gov/elections-voting/sample-ballots
- Voting information: https://www.sos.la.gov/elections-voting/ways-to-vote

As of October 21, 2026:

- early voting: October 20–27, excluding Sunday, October 25, 8:30 a.m.–6 p.m.;
- absentee-ballot request deadline: October 30 at 4:30 p.m.;
- absentee-ballot receipt deadline: November 2 at 4:30 p.m. for most voters;
- Election Day polls: November 3, 6 a.m.–8 p.m.;
- a U.S. Representative general election, if necessary, is scheduled for December 12, 2026.

## Data Layers — Kept Separate

Registration, Census VAP, turnout, political preference, and election results are different measures.

Where the archived redistricting analysis uses REI:

> **REI = District Black VAP percentage − statewide Black VAP percentage**

REI remains a descriptive demographic metric and is not a turnout or election-performance measure.

The live voter tool does not infer candidate preference from race or registration.

## Turnout Forecasting Status

**No turnout forecast is currently published.**

A defensible turnout model requires:

1. official historical election results across comparable cycles;
2. a reproducible precinct/VTD/block crosswalk to the 2026 congressional districts;
3. an election-appropriate turnout denominator;
4. out-of-sample back-testing;
5. published error metrics and uncertainty intervals.

The broader forecasting and historical participation work belongs in the related **Louisiana Congressional Representation & Participation Lab**:

https://github.com/tiandrafields-arch/louisiana-congressional-participation-lab

## Repository Data

Processed October registration files are stored under `data/processed/`.

The original SOS legacy XLS files are documented by filename and SHA-256 in `docs/REGISTRATION_UPDATE_2026-10-01.md`. The public repository does not need to duplicate every raw binary source when reproducible processed tables, checksums, and source documentation are available.

## Attribution and License

Copyright © 2026 Tia Fields, Provisional Consulting LLC.

Unless otherwise stated:

**Analysis by Tia Fields / Provisional Consulting LLC. Licensed under CC BY 4.0.**

Third-party source data retains its own source terms and is not automatically relicensed under CC BY 4.0.

## Disclaimer

This dashboard provides independent descriptive spatial and civic-data analysis using public data. It is not legal advice, an official government product, expert testimony, a legal determination, or an election forecast. Litigation, election administration, statutes, district boundaries, and voter-registration totals may change; users should verify current primary sources before relying on time-sensitive information.

## October 28, 2026 Early Voting Research Update

The dashboard now stages the reported October 27 statewide cumulative early voting snapshot of 520,942 ballots, including 448,525 in person and 72,417 absentee. The snapshot is explicitly marked **source reconciliation pending**, not `final_verified`. Its stated report printing timestamp is October 28, 2026, 3:10:06 a.m. Central. The Secretary of State's updating PDF endpoint is https://electionstatistics.sos.la.gov/Data/Early_Voting_Statistics/statewide/2026_1103_StatewideStats.pdf . Independent retrieval of that PDF and the complete 64 parish table was not achieved in this session. The date slider and final breakdown controls remain locked until the authoritative source and parish totals reconcile. The October 1 registration baseline and congressional map are unchanged. Absentee reporting can continue after the last day of in person early voting.
