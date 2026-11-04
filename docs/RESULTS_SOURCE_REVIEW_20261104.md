# November 4 official source review

This is a source review for the requested results update. It does not establish that the live dashboard has been updated.

## Retrieval and evidence

A Chromium browser successfully rendered the Louisiana Secretary of State public results portal with Tuesday November 3, 2026 selected. The source labels these returns Unofficial Results.

Retrieval started November 4, 2026 at 8:44:29 a.m. Central Standard Time. The congressional page capture was logged at 8:44:43 a.m. Central. The review completed at approximately 8:45 a.m. Central.

Primary portal: https://voterportal.sos.la.gov/graphical

Public candidate metadata fetched by the portal: https://voterportal.sos.la.gov/ElectionResults/ElectionResults/Data?blob=20261103/RacesCandidates_Multiparish.htm

Public vote data fetched by the portal: https://voterportal.sos.la.gov/ElectionResults/ElectionResults/Data?blob=20261103/Votes_Multiparish.htm

The captured vote payload has VersionDateTime 1900-01-01T00:00:00. This is not a usable source update timestamp. Candidate metadata WriteTime is not treated as the results update time. Use the actual retrieval time in the presentation.

Evidence run: https://github.com/tiandrafields-arch/redistricting-dashboard---LA/actions/runs/41850427492

Artifact identifier: 13336085270. Artifact name: sos-public-source-review. The artifact preserves rendered HTML, page text, screenshots, original network responses and downloaded early voting workbooks.

Candidate metadata SHA256: 71d09488b6e02028305f386d9fc81ce9850c784ead840322430fff58f625f08a

Vote data SHA256: 6d1d3bee6647da11f687aa7695d4d8e802a118943ff88b3f0aac03baa937cc6b

## Congressional totals and turnout displayed by SOS

The turnout rates below are copied from the rendered SOS page, where they are explicitly labeled Unofficial Turnout. The vote totals are totals for each contest, not a count of unique voters across different contests. Do not sum Senate and House votes to produce statewide turnout.

| Contest | Contest vote total | SOS unofficial turnout | Election Day precincts reporting | Early and absentee parishes reporting |
| :--- | ---: | ---: | :--- | :--- |
| U.S. Senate | 1,466,069 | 49.3% | 3,722 of 3,722 | 64 of 64 |
| House District 1 | 263,373 | 51.1% | 522 of 522 | 8 of 8 |
| House District 2 | 240,582 | 48.1% | 613 of 613 | 10 of 10 |
| House District 3 | 234,994 | 47.4% | 571 of 571 | 11 of 11 |
| House District 4 | 230,339 | 47.8% | 684 of 684 | 15 of 15 |
| House District 5 | 227,917 | 47.1% | 791 of 791 | 24 of 24 |
| House District 6 | 261,951 | 52.5% | 541 of 541 | 11 of 11 |

All seven displayed contest totals were checked against the sum of their candidate votes in the captured public JSON. Complete precinct reporting is not certification.

## Senate and runoff relevant candidate totals

The rendered SOS page displays candidate percentages rounded to whole percentages. Do not substitute media percentages or imply greater source precision.

U.S. Senate: Julia Letlow (REP), 745,963 votes, 51%; Jamie Davis (DEM), 720,106 votes, 49%.

House District 5: Patricia Pat Moore (DEM), 40,789 votes, 18%; Gabe Firment (REP), 39,131 votes, 17%. They are the two highest vote recipients in the complete reported count; neither has a majority.

House District 6: Chauna Banks (DEM), 50,878 votes, 19%; Blake Miguez (REP), 50,213 votes, 19%. They are the two highest vote recipients in the complete reported count; neither has a majority. Rick Edmonds is third with 49,241 votes, also displayed as 19% after rounding.

The runoff pairings follow from the complete unofficial SOS returns and the official open primary rule. Present them as based on unofficial SOS returns, not certified results.

Official election rules: https://www.sos.la.gov/elections-voting/how-candidates-are-elected

Official election calendar: https://www.sos.la.gov/elections-voting/election-dates

The calendar schedules the House general election for Saturday December 12, 2026. Polls are open 7 a.m. to 8 p.m. Early voting is November 28 through December 5, excluding Sunday November 29, from 8:30 a.m. to 6 p.m. The ordinary absentee request deadline is December 8 at 4:30 p.m.; ordinary receipt deadline is December 11 at 4:30 p.m. Military and overseas exceptions apply. Registration deadlines are November 12 in person or by mail and November 21 online.

## Latest early and absentee statistics

The official statewide workbook downloaded successfully from:
https://electionstatistics.sos.la.gov/Data/Early_Voting_Statistics/statewide/2026_1103_StatewideStats.xlsx

Its header covers the November 3 election with an end date of November 3, 2026. Its print footer says November 4, 2026, 3:10:08 a.m. The publication index identifies November 4 as Date Created.

State total: 536,185 reported early and absentee ballots.
In person: 448,587.
Absentee: 87,598.

The 64 parish rows sum to the state total in every numeric column. Voting methods, race categories and party categories reconcile within each row and statewide. The male and female columns total 278 fewer than the ballot total; do not assign the residual to an invented gender category.

Compared with the dashboard's October 27 snapshot of 520,942, the new total is 15,243 higher. The in person change is 62; absentee change is 15,181. These are administrative snapshot differences, not a daily voting series.

Statewide workbook SHA256: 21c9a2cebba310305e61e582a1be5d7f170c02d9ecd48ced69caf5b53444c495

The corresponding detailed parish workbook was also downloaded:
https://electionstatistics.sos.la.gov/Data/Early_Voting_Statistics/parish/2026_1103_ParishStats.xlsx

Parish workbook SHA256: 16b4da916920c4313168ad0485dfc6ea64a9c06968b0ee56ec74af4a1aac53ad

The detailed parish workbook still requires its separate cross workbook reconciliation before replacing the published parish dataset. The new early ballot total is not total Election Day participation.

## Audited postelection files

The official statewide and parish postelection indexes were successfully opened with 2026 selected. Neither listed a November 3, 2026 report at the retrieval time. The newest election listed in those indexes was June 27, 2026, with files created July 10.

Statewide index: https://electionstatistics.sos.la.gov/default.aspx?Stats=Post_Election_Statistics&Type=Statewide

Parish index: https://electionstatistics.sos.la.gov/default.aspx?Stats=Post_Election_Statistics&Type=Parish

This absence does not prevent displaying the SOS portal's current unofficial turnout and candidate returns. It prevents describing unavailable audited parish statistics as already published.

## Required presentation changes

Place December 12 House runoff information at the top, using equal presentation for Districts 5 and 6. Follow with current November 3 contest results and the SOS unofficial turnout rates. Keep the dated early voting history and preelection surveys separate and clearly labeled. Preserve the original October 27 snapshot and backup branch.

Use distinct records for candidate results, provisional contest turnout, and audited voter participation. Refresh parish early and absentee data only after reconciliation. Do not treat a party or race share of early ballots as a turnout rate or infer a district from whole parish totals.

Update the voting planner's dates and Saturday polling hours for December 12. Do not reuse November 3 transportation offers as verified December services. Maintain the user's requested placement of the voting planner after registration and before sources, with a top shortcut to it.
