# Changelog

## October 28, 2026: Verified parish release

Release `20261028.parish.2` supersedes the earlier pending snapshot below.

Published all 64 parish aggregates after reconciling both supplied SOS workbooks and 6,869 detailed report rows. The snapshot records 520,942 reported ballots through October 27, comprising 448,525 in person and 72,417 absentee. It is a verified administrative reporting snapshot, not certified final election turnout.

Rebuilt the interface with early voting first in the actual HTML, a consistent navy and white design, Republican red, Democratic blue and No Party purple. Added official cached Census parish geometry, interactive map metrics and selection, accessible keyboard controls, zoom and reset, a searchable parish table and CSV export. Added statewide and parish scenario calculations with explicit assumptions, while retaining the separate registration benchmark.

Preserved the registration JSON, congressional geography, archival analysis and polling publication safeguards. Added distinct footer links for commissioning Tia Fields and supporting CivicLens Data. Added reproducible data validation, browser regression checks and public deployment verification.

See [the release record](docs/RELEASE_2026_10_28.md) and [source methodology](docs/EARLY_VOTING_METHODS.md).

## October 28, 2026: Earlier staging release

Staged the reported October 27 statewide early voting snapshot with `source_reconciliation_pending` status. At that time, official source reconciliation was incomplete. This pending state was replaced by the verified parish release above after processing the supplied workbooks.

## October 21, 2026: Voter tool pivot and registration refresh

Archived the prior redistricting focused public dashboard. Refocused the live site toward current congressional voter information and participation. Replaced the May whole parish approximation with October 1 official congressional district subtotal rows.

Statewide registration was updated to 2,978,143, including 933,052 Black registrants. Party controls are 1,060,252 Democratic, 1,067,827 Republican, 825,562 No Party and 24,502 other parties.

The earlier estimate that 81% of Black registrants were outside District 2 was withdrawn. Official October subtotals show 632,478, or 67.79%, outside District 2. District 2 contains 300,574 Black registrants, or 60.08% of district registration.

Official voter resource links and election timing were added. Registration wording implying candidate preferences or turnout was removed. Census 2020 VAP analysis, the demographic REI measure and historical legal narrative remain in the archive rather than being presented as current turnout measures.

No candidate or turnout forecast is published. Any future predictive research requires verified historical inputs, geographic crosswalks, comparable election definitions and documented testing.

## October 28, 2026: confidential survey and Central Time

Added all ten reported District 6 initial ballot percentages from the confidential source survey, with publisher attested source verification and October 28 pull date. Replaced the prior survey exclusion with a chart and transparent methodology disclosures. Normalized timestamps to America/Chicago, removed the timezone uncertainty wording, and added regression tests. Early voting counts, parish boundaries, the calculator, registration baseline and commissioning links are unchanged.
