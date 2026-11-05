# Voter education update

Release: 20261101.education.1

Review date: November 1, 2026.

## Requested changes

The main data heading is now Louisiana voting statistics. Its navigation label is Voting statistics. The original early-voting anchor is retained for existing shared links. The displayed data cutoff remains October 27, 2026, and the report date remains October 28. Renaming the section is not a data refresh.

The page order is voting statistics, parish map, Senate research, District 6 research, other U.S. House races, registration, voting plan, and sources. Navigation follows the same order. The voting planner remains available through the mobile shortcuts even though its full section now follows registration.

The scenario calculator, statewide participation benchmark, calculator navigation link, and map button leading to the calculator are removed from the current page. Their event handlers, initialization and arithmetic functions are removed from the current dashboard script. Historical release documentation remains unchanged.

The new Other U.S. House races section immediately follows District 6. It covers Districts 1 through 5 with all 29 candidates listed in the reviewed official records. It is a ballot snapshot, not a polling panel, endorsement or election forecast.

## Primary sources

All candidate names and party labels come from the Louisiana Secretary of State candidate inquiry for the November 3, 2026 election, election identifier 344. November 1 is the review date, not a claimed publication date for the dynamic source pages.

Districts 1 and 2, Jefferson inquiry:
https://voterportal.sos.la.gov/CandidateInquiry/ParishCandidate/Print?electionDate=11%2F03%2F2026&electionId=344&parishId=27&parishName=JEFFERSON

District 3, Lafayette inquiry:
https://voterportal.sos.la.gov/CandidateInquiry/ParishCandidate/Print?electionDate=11%2F03%2F2026&electionId=344&parishId=29&parishName=LAFAYETTE

District 4, Bienville inquiry:
https://voterportal.sos.la.gov/CandidateInquiry/ParishCandidate/Print?electionDate=11%2F03%2F2026&electionId=344&parishId=8&parishName=BIENVILLE

District 5, Jackson inquiry:
https://voterportal.sos.la.gov/CandidateInquiry/ParishCandidate/Print?electionDate=11%2F03%2F2026&electionId=344&parishId=26&parishName=JACKSON

Election rules:
https://www.sos.la.gov/elections-voting/how-candidates-are-elected

Election calendar:
https://www.sos.la.gov/elections-voting/election-dates

Official voter lookup:
https://voterportal.sos.la.gov/Home/VoterLogin

A parish inquiry supplies the candidate list for a named congressional contest. It does not establish that the whole parish belongs to that district. Every voter should confirm their district and sample ballot through the official portal.

## Consistent publication treatment

Each district uses the same fields: district number, office, candidate count, candidate names, official party labels, and primary source link. The candidate order follows the official records, alphabetically by surname. Nickname quotation marks are retained. Names and parties use the same typography and neutral colors for every candidate. No candidate receives a campaign link, portrait, fundraising prompt, inferred vote share or ranking in these snapshots.

Candidate counts are 4 in District 1, 5 in District 2, 6 in District 3, 5 in District 4, and 9 in District 5.

The records include Republican, Democrat, Libertarian and No Party labels. No Party is not treated as undecided. Candidate addresses, telephone numbers, race and gender are not reproduced.

Secondary guides contained discrepancies. The official records reviewed here list Tia LeBrun as No Party and Oscar "Omar" Dantzler as Republican, and spell Priscilla Gonzalez with a final z. Those official labels and spelling are used. These discrepancies are also documented in the downloadable data.

The section explains the common November 3 U.S. House open primary rules and the December 12 election when needed. It does not apply that explanation to the Senate general election.

## Implementation and preservation

The House snapshot is static HTML so it remains available without JavaScript. The corresponding structured source record is data/processed/house_races_2026-11-01.json. Browser tests compare every displayed candidate name, party label and source link with that record.

The small voter education composition script runs after the existing modules. It moves the existing voting planner after registration without replacing its form handlers or privacy protections, aligns navigation, and updates section labels. A narrowly scoped observer aligns the Senate heading after its asynchronous render and then disconnects. It does not alter Senate survey data.

Participation files, registration files, district boundaries, District 6 polling data and Senate polling data are not changed in this release. The voting planner's data handling and export formats remain unchanged.

## Verification coverage

The updated browser regression suite checks page and navigation order, the renamed heading, removal of calculator controls, all 29 candidate names and party labels, official source links, and consistent candidate styling. It also retains parish map, keyboard, zoom, search, data export, all 64 organization packet selections, CSV protection, PDF printing, personal plan, directions and privacy checks. Mobile widths and a JavaScript disabled view are tested. Existing Senate research tests remain a separate workflow step.

Test results and screenshots are uploaded by the repository workflow. A passing workflow result is the record of completed validation; this document describes the checks rather than claiming an unobserved test result.
