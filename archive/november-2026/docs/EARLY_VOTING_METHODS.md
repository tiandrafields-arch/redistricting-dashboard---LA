# Early voting source and methodology record

## Release and scope

Release: `20261028.poll.3`, October 28, 2026.

Election: November 3, 2026. Reporting cutoff: October 27, 2026. Statewide reported participation: 520,942, comprising 448,525 in person and 72,417 absentee.

These are cumulative administrative participation records through the final day of the in person early voting period. They do not include all later absentee receipts or corrections and are not certified election returns. `verified_snapshot` means the supplied files passed coverage, arithmetic and geographic checks. It does not mean every aspect of the election has been certified.

## Source artifacts

The source was the two user supplied Louisiana Secretary of State workbooks, not an independently downloaded new PDF. Their headers identify the November 3 election and an end date of October 27. The print footer is displayed as October 28, 2026, 3:10:06 a.m. Central Time. The publisher confirmed Louisiana local reporting time. The dashboard uses America/Chicago and the corresponding offset for each date.

| Workbook | SHA256 |
|:--|:--|
| `2026_1103_StatewideStats.xlsx` | `9265f07ed7d1e2d351726ab5c02d788d25341e1184721e6d194e7e1733f5a37c` |
| `2026_1103_ParishStats.xlsx` | `77c7b7afd43576781659ef345b4ef70499c7b63adaa9ee49ad17463d5977feff` |

[Official SOS publication page](https://www.sos.la.gov/elections-voting/early-voting-statistics-parish)

## Workbook reconciliation

The statewide report supplies one row for each of 64 parishes and a STATE TOTAL control. The detailed parish workbook contains 64 parish sheets and a statewide total sheet. Each parish sheet has detailed aggregate rows and a SUM row.

All 6,869 detailed rows were summed within their own sheet. Every reported numeric column was compared with the parish SUM, then with the corresponding statewide report row. All 64 records matched. Across parishes, the voting method, party and race categories reconcile exactly to the statewide controls.

Voting method identity: `total = in_person + absentee`.

Party categories: Democratic, Republican, No Party and Other parties.

Race categories: White, Black and Other as reported by SOS. These categories are not treated as political preferences.

The male total is 218,966 and the female total is 301,710. Their sum is 266 below 520,942. This residual is not reclassified as another gender and no complete gender chart is published.

The public CSV and JSON contain parish aggregates only. The detailed workbook rows were used for validation, not published as individual voter records or automatically allocated to congressional districts.

## Geographic join and display

[Official Census layer](https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/19)

The cache uses TIGERweb BAS 2026 county equivalents for Louisiana, vintage January 1, 2026. The query selects STATE 22 and returns GEOID, STATE, COUNTY, BASENAME and NAME, with EPSG:4326 geometry. It requests four decimal places and a 0.005 degree generalization for display. Exact query, retrieval time and SHA256 are in `data/boundary_source.json`.

SOS numeric parish codes and Census county FIPS codes are separate identifiers. A name normalized crosswalk links them explicitly. Both sets contain 64 unique records, with 64 name matches and no unmatched features. LaSalle naming differences are normalized without changing either source identity.

The client renders the stored polygons as SVG with a Mercator projection. This is a general reference display, not an equal area measurement surface or a legal boundary certification. No area based allocation is performed.

Count map classes are under 2,500; 2,500 to 4,999; 5,000 to 9,999; 10,000 to 19,999; and 20,000 or more. Percentage map classes use 20 percentage point intervals. Every share uses that parish's reported ballot total as the denominator. None is a turnout rate against eligible or registered voters.

Republican registration uses red, Democratic blue, No Party purple. Other party records use gray. Separate sequential colors are used for total volume, race and voting method. Map colors are not electoral winners or candidate support.

## Time and comparability

Only the October 27 cutoff is authenticated by these uploads. The interface does not infer earlier daily observations from cumulative totals, interpolate missing days, or attach unsupported prior cycle benchmarks. A historical date slider requires independently authenticated observations for each date.

The October 1 registration baseline is preserved unchanged. It predates the final registration deadline. The dashboard does not divide parish ballots by a missing or guessed parish registration denominator. It does not apply whole parish counts to congressional districts.

## Calculator formulas

For a selected geography with observed count E and a user chosen additional percentage r:

`additional = round(E × r / 100)`

`scenario_total = E + additional`

The additional count includes hypothetical Election Day ballots and later absentee receipts together. It is not a modeled probability or forecast and is not broken down into candidate support. Scenario totals can exceed an eligible electorate because no current parish eligibility denominator is loaded. This limitation is visible next to the controls.

A separate retained benchmark uses the October 1 statewide registration count N = 2,978,143:

`illustrative_total = round(N × assumed_percentage / 100)`

This is arithmetic using an older registration snapshot, not certified turnout. JavaScript Math.round is used consistently for displayed whole ballots.

## Polling publication rules

The existing JMC panel is attributed to WBRZ reporting dated October 9, 2026. It is labeled as a September 19 to 21 survey of 790 likely voters, with the reported full sample margin of error of 3.5 percentage points and the named funder. The full questionnaire and original technical report are not archived here. Only percentages explicitly reported by the cited article appear in the chart. The chart uses a common 0 to 100 scale and does not reconstruct omitted categories.

The 419 respondent survey is published separately with a pull date of October 28, 2026, following source verification attested by Tia Fields. The source requested anonymity. Field dates remain unspecified; the pull date is not an interview date. The chart transcribes all ten initial ballot categories without inferring leaner results, probabilities or a trend. See `docs/POLLING_METHODS.md`. No Party administrative registration is not the same as an undecided survey response. Polling, administrative voting records and registration are separate populations and measures.

## Reproducibility and tests

`python scripts/build_early_voting_snapshot.py` reconstructs the JSON from the audited CSV and validates the explicit geographic join. `python scripts/validate_early_voting.py` verifies the published data and boundary checksum. Both fail on inconsistencies rather than marking an unresolved source final.

`node --check assets/dashboard-v20261028.js` checks syntax. `python tests/test_dashboard.py` uses a real local HTTP server and Playwright to test data loading, all 64 paths, selection, calculator arithmetic, map keyboard selection, zoom, search, CSV export, commissioning links and phone layout. Screenshots and a machine readable test summary are produced under `test-output/`.

No external runtime libraries, fonts, map tile servers or analytics are needed. Personal voter records are not published. Source snapshots and verification times are dated rather than represented as a live election feed.
