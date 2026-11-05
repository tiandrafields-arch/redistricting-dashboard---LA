# Voting planner release

Release: 20261101.plan.1

Planning guidance reviewed November 1, 2026. Election date: November 3, 2026. The existing participation dataset still covers October 27, 2026. This release does not refresh participation, registration, district boundaries or legal status data.

## User paths

The homepage loads assets/voting-plan-20261101.js after the existing dashboard script. The new section appears above the early voting data, with a Voting plan navigation link and mobile shortcuts.

For voters: open the official voter lookup, enter the confirmed polling address, select a departure time and travel method, and explicitly confirm the assignment. The planner can open directions, share or copy the plan, and print it. Saving a PDF uses the browser print destination or device sharing controls. Editing the parish, precinct or address invalidates the prior confirmation.

For organizations: select one of 64 parishes and optionally enter an organization name. Generate a packet with election hours, the parish's dated ballot count when available, official information links, transportation cautions and ten volunteer coordination tasks. Download an editable CSV checklist or print the packet and save it as a PDF. The spreadsheet export is a CSV, not a native XLSX workbook.

A parish selection does not establish a voter's assigned precinct. No individual voter file, home address, birth date, phone number or pickup address is requested. Organizations must arrange and confirm transportation directly with a provider. This tool is not a ride booking or dispatch service.

## Sources

Louisiana Secretary of State election dates:
https://www.sos.la.gov/elections-voting/election-dates

Official voting hours, identification, voter rights and transportation guidance:
https://www.sos.la.gov/elections-voting/voting-on-election-day-faqs

Official election rules:
https://www.sos.la.gov/elections-voting/how-candidates-are-elected

Official polling location information:
https://www.sos.la.gov/elections-voting/polling-locations

Official voter lookup:
https://voterportal.sos.la.gov/Home/VoterLogin

Official address lookup:
https://voterportal.sos.la.gov/Home/AddressLogin

Official parish information:
https://voterportal.sos.la.gov/Home/ParishLogin

Official registrar directory:
https://voterportal.sos.la.gov/Registrar

National Archives Electoral College explanation:
https://www.archives.gov/electoral-college/about

Power Coalition external ride request resource:
https://powercoalition.org/powerrides/

The provider page includes older notices alongside current information. The planner uses current SOS hours and does not promise service coverage or availability. Voters must confirm coverage, service hours, accessibility, pickup and return arrangements directly. An external request is not a confirmed ride.

New Orleans RTA announcement dated October 23, 2026:
https://www.norta.com/news-list/rta-providing-fare-free-transportation-for-early-voting-and-election-day

The RTA notice appears only when Orleans is selected. It describes RTA buses, streetcars and ferries on November 3, not transportation throughout Louisiana. The planner directs users to verify current service and accessibility.

Participation source: data/processed/early_voting_2026.json. The planner requires a verified snapshot, 64 unique parish codes, nonnegative integer counts, a dated cutoff and reconciliation with the statewide count. A data loading failure does not disable official lookup links or checklist generation.

## Privacy and safety

Form entries are held in the current page. No database submission, localStorage or sessionStorage write is implemented. Printing, downloading, sharing or opening directions sends information to the destination selected by the user. External services have separate privacy policies.

User supplied text is escaped for HTML. CSV fields are quoted and potential spreadsheet formula prefixes are neutralized. The print layout excludes the rest of the dashboard. The planner displays an archive notice after the November 3 election closes. It does not infer candidate support, prioritize groups by race or party, or describe small ballot counts as low turnout rates.

## Validation

The isolated planner browser test completed 101 checks using Chromium, including all 64 parish packet selections, required fields, assignment confirmation, stale confirmation invalidation, directions, two page PDF output, CSV export, formula injection protection, HTML escaping, Orleans specific transportation information, archive notice, mobile widths and graceful data failure. The tested module blob is 5dffcea5f4ac9304fd9767ef9b9f0ad0759ab7cb, matching the committed module.

PDF pages and mobile screenshots were visually inspected. The isolated tests used a fixture matching the published parish totals. Existing full dashboard regression checks are separate and run through the repository's GitHub Actions workflow. Native iOS share sheets, printer dialogs and real transportation availability require device or provider verification.

No existing participation data, survey data, registration files or boundary files were changed by this release.
