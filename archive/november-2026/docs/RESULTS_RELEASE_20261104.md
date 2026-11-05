# November 4 results and runoff release

This release publishes the December 12 House runoffs first, followed by the November 3 congressional returns and SOS unofficial turnout. Results remain unofficial even with all expected precincts reporting. Candidate vote shares are the whole percentages shown by SOS. Totals are not summed across overlapping Senate and House contests.

## Evidence and retrieval

Results were retrieved at 2026-11-04T09:11:11.703682-06:00 from https://voterportal.sos.la.gov/graphical and checked against the official candidate and vote payloads preserved under data/sources/20261104. The source result timestamp is a 1900 placeholder, so no publication timestamp is inferred. The two leading candidates in Districts 5 and 6 advance under the open primary majority rule based on complete unofficial returns. This is not a certification claim.

Official rules: https://www.sos.la.gov/elections-voting/how-candidates-are-elected
Official calendar: https://www.sos.la.gov/elections-voting/election-dates

December 12 polls: 7 a.m. to 8 p.m. Central. Registration: November 12 in person or by mail, November 21 online. Early voting: November 28 through December 5, except November 29, 8:30 a.m. to 6 p.m. Ordinary absentee request: December 8 at 4:30 p.m.; receipt: December 11 at 4:30 p.m. Military and overseas exceptions apply.

## Early and absentee participation

The November 4 workbooks cover participation through November 3. The 64 parish totals, 6,314 detailed rows, statewide controls and every method, race and party column reconcile. Total 536,185; in person 448,587; absentee 87,598. The reported sex columns leave a residual of 278. This is not total Election Day turnout. The prior October 27 snapshot remains unchanged in data/processed/early_voting_2026.json. New data are stored in early_voting_2026-11-03.json and early_voting_parishes_2026-11-03.csv.

## Registration

The November 1 source explicitly uses Status Both and Office Congress, matching the October scope. Six congressional district summaries and their parish components reconcile with all statewide race and party controls. Statewide registrations: 2,984,520, a net increase of 6,377 from October 1. Black registrations: 936,512; outside District 2: 635,050, or 67.81%. This supersedes the dated October 67.79% finding without changing that historical record. The monthly registration total is not substituted for the SOS result portal's contest qualified voter denominator.

Source workbook: https://electionstatistics.sos.la.gov/Data/Registration_Statistics/statewide/2026_1101_sta_comb.xlsx

## Audited participation and preservation

The successfully retrieved official postelection statewide and parish indexes did not list a November 3 audited report. The display therefore uses the portal's explicitly unofficial turnout and does not invent audited parish turnout. The parish map remains an early and absentee ballot map. All October source datasets, polling records, original candidate lists and the backup branch remain untouched. District boundaries and legal status findings are not changed.

The planner now uses December 12 dates and correct Saturday hours. Prior November transportation offers are removed from current service claims. Every voter must check their actual December ballot and polling place. No voter identities, pickup addresses, party based targeting or candidate preferences are collected.

## Reproducibility

source_manifest.json records source checksums, retrieval details and validation. Data are built from the preserved official evidence, not media reports. GitHub source evidence runs: 41850427492 and 41854993575. Release build script: scripts/build_results_release_20261104.py.
