# Louisiana Election Intelligence

## Congressional Voter & Participation Dashboard

Independent research, spatial analysis and public data storytelling by Tia Fields / Provisional Consulting LLC.

[Open the public dashboard](https://tiandrafields-arch.github.io/redistricting-dashboard---LA/)

## Current release

Release `20261028.parish.2` puts early voting first and replaces the earlier pending display with a verified snapshot of the two supplied Louisiana Secretary of State workbooks. The observation covers the November 3, 2026 election through October 27, 2026. It is not a certified final election return.

| Measure | Reported count |
|:--|--:|
| Cumulative ballots | 520,942 |
| In person | 448,525 |
| Absentee | 72,417 |
| Parishes reconciled | 64 |

Both workbooks carry the print date October 28, 2026, 3:10:06 a.m. Their footers do not specify a timezone. Later absentee receipts and corrections are outside this snapshot.

## Functional dashboard

The page now includes a real interactive parish map using locally cached official Census geometry, a parish selector, party and race composition, voting method comparisons, a searchable table of all 64 parishes, a CSV export, and a statewide or parish participation scenario calculator. Map paths support pointer selection, keyboard activation, zoom, reset and mouse panning. The menu and table remain available when map rendering fails.

Republican registration uses red, Democratic registration blue, and No Party registration purple. Other parties and undecided survey responses use neutral gray but remain separate concepts. Race and voting method use their own scales. No party registration category is interpreted as candidate preference.

The page uses no external runtime JavaScript, map tiles, font services, analytics or tracking scripts. HTML, CSS, JavaScript, data and simplified boundaries are stored in this repository.

## Data and validation

`data/processed/early_voting_2026.json` is the published structured snapshot. Its status is `verified_snapshot`, not `final_verified`, because validation of a reporting snapshot is not election certification.

`data/processed/early_voting_2026_parishes.csv` contains the audited public parish aggregates and explicit SOS code to Census GEOID crosswalk. `scripts/build_early_voting_snapshot.py` builds the JSON and validates category totals and geographic joins. `scripts/validate_early_voting.py` checks the published output and cached boundary checksum.

All 6,869 detailed aggregate rows in the supplied parish workbook were reconciled to its parish summaries and the separate statewide workbook. All 64 parish totals, methods, race and party categories match. The sum of reported male and female counts is 266 below the statewide total. No gender category is inferred from this residual.

Only one observation date is authenticated by these uploads. The release does not fabricate a daily series, historical comparison or congressional district early voting allocation.

[Full source and methodology record](docs/EARLY_VOTING_METHODS.md)

## Boundaries

`data/louisiana_parishes_2026.geojson` is a verified cache of U.S. Census Bureau TIGERweb BAS 2026 parish geometry, vintage January 1, 2026. `data/boundary_source.json` records the precise query, retrieval timestamp and checksum. The display geometry is generalized at 0.005 degrees and uses EPSG:4326 coordinates. The client projects the coordinates for display; this is not an equal area analytical layer.

SOS parish codes are not Census FIPS codes. The explicit crosswalk was checked using normalized parish names and unique GEOIDs. Parish counts are never assigned to congressional districts.

## Registration and congressional research

The existing October 1, 2026 registration JSON remains unchanged: 2,978,143 statewide registrants and the six official congressional district subtotals. These counts are registration, not turnout. The baseline predates the final registration deadline and is not an election certified turnout denominator.

The October source correction remains: 632,478 of 933,052 Black registrants, or 67.79%, are outside District 2. The earlier whole parish estimate of 81% is withdrawn.

[Registration source record](docs/REGISTRATION_UPDATE_2026-10-01.md)

[Participation Lab and litigation research](https://tiandrafields-arch.github.io/louisiana-congressional-participation-lab/)

[Historical dashboard archive](archive/redistricting_dashboard_legacy_2026-10-21.html)

The congressional map and registration layers are not modified by this parish participation release.

## Polling research

The integrated District 6 polling panel retains the JMC survey as reported by WBRZ on October 9, 2026. It clearly discloses that the full pollster report and questionnaire are not archived here. Only explicitly reported categories are charted. The unattributed 419 respondent screenshot is excluded from quantitative comparison. Polling, administrative participation and registration are never combined into candidate predictions.

## Local checks

```sh
python scripts/validate_early_voting.py
node --check assets/dashboard-v20261028.js
python -m pip install playwright==1.55.0
python -m playwright install chromium
python tests/test_dashboard.py
python -m http.server 8000
```

The browser test starts its own local server and verifies real file loading, all 64 map paths, parish selection, calculator arithmetic, keyboard interactions, zoom, table search, CSV export and a phone viewport. GitHub Actions runs the same tests when interface or data files change.

## Commission and support links

The footer keeps two purposes distinct. [Commission Tia Fields](https://www.tiafields.com/engage) for policy research, spatial analysis, dashboard development and data storytelling. [Support CivicLens Data](https://civiclensdata.com/) to support the separate AI powered civic data platform. Platform support is not a campaign contribution.

## Governance

Only aggregate, nonidentifying information is published. Do not add individual voter records, walk lists, phone lists, addresses or private contact information. Raw workbook hashes establish the source files used; they do not imply that a newer online report was retrieved.

Copyright 2026 Tia Fields / Provisional Consulting LLC. Analysis under CC BY 4.0 unless otherwise stated. Third party data retain their original terms. This is independent descriptive research, not an official government publication, legal advice, a candidate forecast or certified election results.

## October 28 polling and Central Time update

The public Polling section includes the 419 respondent District 6 survey from a confidential source verified by Tia Fields, with a pull date of October 28, 2026. Pull date is distinct from the unspecified survey field dates. All ten initial ballot percentages are displayed separately from the JMC survey. Central Time is used across report labels and metadata. See `docs/POLLING_METHODS.md` for disclosure and interpretation rules.
