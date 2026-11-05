# Polling publication notes

## District 6 confidential source survey

Pull date: October 28, 2026, using Central Time (America/Chicago). No collection hour is supplied or invented. Pull date means the date the poll was obtained for this dashboard; survey interview dates remain unspecified.

Source: confidential source verified by Tia Fields, as attested by the publisher on October 28. The source requested anonymity. No name, email, contact details or identifying metadata are stored in the public record. This is source identity assurance from the publisher, not an independent audit of the pollster or survey methods.

The supplied executive summary describes 419 likely voters in Louisiana Congressional District 6, contacted by text message from the L2 voter file and weighted to the district's L2 likely voter profile. Its stated full sample margin of error is 4.8 percentage points and larger for subgroups. That is a reported measure, not a margin recalculated or independently validated here.

The chart displays Q13, initial ballot, all likely voters, weighted percentages: Miguez 19; Edmonds 16; Garcia 15; Forbes 11; Banks 10; Wagley 5; Larry Davis 2; Appeaning 2; Craig 2; undecided 18. These ten reported categories sum to 100. Candidate labels and party abbreviations are transcribed from the supplied image. No polling microdata are published.

Field dates, pollster, sponsor, complete questionnaire and full weighting details are not publicly supplied in this record. Unknown values are null in the JSON. The screenshot's narrative claims about a runoff or leaners are not converted into quantified forecasts or additional estimates.

## Comparability

The retained JMC chart is separately attributed to the existing WBRZ report. It is not combined with the confidential source chart into an average, trend, candidate forecast or estimate of counted votes. Common chart widths run from 0 to 100 percent. Only reported values are displayed. Republican labels use red, Democratic blue, No Party purple, and other party or undecided responses gray. Undecided is not a party registration category.

## Time convention

All dashboard reporting times use Central Time with the IANA zone America/Chicago. Date specific offsets are applied rather than a fixed UTC offset. October 28, 2026 uses UTC minus five hours. The publisher confirmed the local reporting timezone. Existing verification instants are preserved; a local representation is added without changing the instant.

[Official U.S. daylight saving rules](https://www.nist.gov/pml/time-and-frequency-division/popular-links/daylight-saving-time-dst)

## Reproducibility

`data/processed/polling_la6_2026-10-28.json` is the public transcription. `tests/test_polling_update.py` checks values, total, confidentiality metadata, time normalization and the published display. Existing data and browser tests continue to cover the 64 parish map and calculator.
