# Louisiana U.S. Senate survey research

Release: 20261101.senate.1. Research reviewed November 1, 2026. Election date: November 3, 2026.

This is a dated research collection, not a live feed, polling average, prediction or election return. The statewide Senate contest is separate from the U.S. House District 6 research immediately below it. No participation, registration, boundary or District 6 survey data are changed.

## Louisiana survey inventory

| Pollster | Interviews in 2026 | Population | Sample | Davis | Letlow | Not sure or undecided | Reported margin of error |
| :--- | :--- | :--- | ---: | ---: | ---: | ---: | :--- |
| Hart Research Associates | October 28 to 29 | Likely Louisiana voters | 502 | 45% | 45% | 10% | ±4.5 percentage points |
| Hart Research Associates | September 17 to 19 | Likely Louisiana voters | 500 | 44% | 48% | 8% | ±4.5 percentage points |
| Public Policy Polling | July 21 to 22 | Registered Louisiana voters | 518 | 37% | 41% | 22% | Not supplied in the reviewed source |

All three surveys were commissioned by Jamie Davis's campaign. No independently sponsored Louisiana general election survey was located in this review. This is a search finding, not proof that no other survey exists. Repeated articles and aggregator entries about the same survey are counted once.

The October Hart memo is dated October 30. Its first paragraph specifies 502 interviews, resolving a news report describing 500. The September memo is dated September 22. The July PPP reporting is dated August 14; that is a source publication date, not an interview date or independently established first release date.

The two Hart memos are original pollster documents hosted by The Bayou Progressive. Their initial ballot charts and sample statements were inspected visually. The PPP entry relies on original reporting by The Bayou Progressive, which states it received a three page report from the campaign. That underlying report was not retrieved in this review. The dashboard identifies this evidence limitation rather than claiming an independent inspection.

Hart used landline, cell phone and text to web interviews. The July report describes 33% landline and 67% text to web interviews. The campaign told the reporting outlet it had not received a margin of error, detailed weighting or demographic crosstabs for that survey.

Only initial ballot preferences are compared. Results after candidate descriptions and results that include initially undecided people pressed for a preference are not substituted for the initial question. Likely voters and registered voters are different survey populations. No average, trend line, candidate win probability or parish projection is computed.

A poll's reported margin of error does not directly describe uncertainty in the difference between two candidates. Sampling error is not the only uncertainty. Sponsor, question wording, coverage, weighting, nonresponse and turnout assumptions also matter. A tied sample does not predict a tied election.

## National context

Emerson College Polling interviewed 1,000 U.S. likely voters October 24 to 26. Its October 30 release reports a generic congressional ballot of 52% Democratic and 42% Republican, with a reported credibility interval of ±3 percentage points. It used text to web panel contacts and additional online panel interviews. The displayed figures are rounded release figures.

NPR / PBS News / Marist interviewed 1,289 registered voters October 19 to 20. Its October 27 release reports 52% Democratic and 44% Republican using likely voter weights. The likely voter margin of error is ±3.8 percentage points. The registered voter interview count is not mislabeled as a separate likely voter sample. The original methodology and ballot table were inspected on pages 1 and 7.

These are national generic congressional ballot measures, not Louisiana Senate polls. They are not assigned to Louisiana, converted to Senate seats, or combined with candidate preferences. Other response categories are not reconstructed or rescaled.

## National assessments of the Louisiana race

Cook Political Report displayed Solid Republican when checked November 1. Its race page labels the last rating update February 11, 2025. The dashboard preserves that date and does not suggest a new November rating.

The Hill / Decision Desk HQ classified the race as Likely Republican in a model update dated October 31, 2026, 1:26 p.m. Eastern Daylight Time. This is a forecast, not an additional poll. Its model probability is not displayed as vote share.

These assessments use evidence beyond the campaign survey results. They are displayed separately from polling and do not establish an election outcome.

## Source register

Original October Hart memo:
https://cms.bayouprogressive.com/wp-content/uploads/2026/10/10.30-Poll-memo.pdf

Original September Hart memo:
https://cms.bayouprogressive.com/wp-content/uploads/2026/09/JDavispollingmemo9_22.pdf

Original reporting on the July PPP survey:
https://bayouprogressive.com/2026/08/new-poll-puts-jamie-davis-four-points-behind-julia-letlow-as-1-in-5-voters-remain-undecided/

Emerson national release:
https://emersoncollegepolling.com/october-2026-national-poll-democrats-hold-10-point-midterm-advantage/

Marist national release:
https://maristpoll.marist.edu/polls/u-s-midterm-elections-october-2026/

Marist methodology and tables:
https://maristpoll.marist.edu/wp-content/uploads/2026/10/NPR_PBS-News_Marist-Poll_USA-NOS-and-Tables_202610211808AS.pdf

Cook Political Report:
https://www.cookpolitical.com/senate/race/488591

The Hill / Decision Desk HQ:
https://elections2026.thehill.com/forecast/2026/senate/louisiana/

Official candidate listing, statewide Senate contest within the parish inquiry:
https://voterportal.sos.la.gov/CandidateInquiry/ParishCandidate/Print?electionDate=11%2F03%2F2026&electionId=344&parishId=8&parishName=BIENVILLE

Official election rules:
https://www.sos.la.gov/elections-voting/how-candidates-are-elected

Independent reporting about the October campaign poll, not a separate survey:
https://www.wwno.org/2026-10-30/jamie-davis-julia-letlow-tied-heading-into-nov-3-senate-election-new-poll-shows

## Implementation and validation

The module assets/senate-research-20261101.js inserts the section immediately before polling-research and adds Senate polling to navigation. District 6 retains its existing content and is labeled 03B. The Senate section is labeled 03A. A static summary and primary source links remain available when JavaScript is disabled.

The JSON dataset supplies source provenance, interview dates, publication dates, sample definitions, sponsorship and limitations. The interface uses a shared 0 to 100% bar scale, an accessible survey selector, keyboard operated tabs, a comparison table and a downloadable research JSON. Validation rejects missing source references, invalid percentages and Louisiana ballot categories that do not sum to 100.

An isolated Chromium component test using the actual research JSON and a mocked fetch passed survey selection, numeric bars, section placement, national views, keyboard tabs, export, data loading failure and widths of 320, 390 and 768 pixels. Desktop and mobile screenshots were visually inspected. This isolated check is not a full live website integration test.

The repository test tests/test_senate_research.py serves actual repository files and checks integration, chart values, methods, downloads, keyboard navigation, mobile layout, loading failures and the archive notice. Full dashboard regression tests remain separate. Current GitHub Actions results are the authority for the integrated test outcome.

No personal voter records are collected. Poll responses are not combined with race, party registration, parish totals, early voting or the participation calculator to infer candidate support. Data and guidance dates remain separate.
