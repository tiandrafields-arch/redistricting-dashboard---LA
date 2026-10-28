"""Apply the publisher authorized confidential poll and Central Time display update.
Only public aggregate survey values are stored; no source identity is collected.
"""
import json
import re
from datetime import datetime
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
RELEASE = '20261028-poll3'
poll = json.loads((ROOT / 'data/processed/polling_la6_2026-10-28.json').read_text())
assert poll['pull_date'] == '2026-10-28' and poll['field_dates'] is None
assert poll['sample_size'] == 419 and len(poll['results']) == 10
assert sum(r['percent'] for r in poll['results']) == 100
colors = {'R': '#d92d3a', 'D': '#2563eb', 'NP': '#8054b8', 'L': '#6b7280', 'U': '#6b7280'}
rows = []
for r in poll['results']:
    label = escape(r['label'])
    value = r['percent']
    rows.append(f'<div class="bar-row" data-response="{label}"><div class="bar-label"><span>{label}</span><strong>{value}%</strong></div><div class="bar-track" aria-hidden="true"><span class="bar-fill" style="width:{value}%;background:{colors[r["party"]]}"></span></div></div>')
chart = '\n'.join(rows)
index = ROOT / 'index.html'
html = index.read_text()
start = html.index('<section id="polling-research"')
end = html.index('<section id="registration"', start)
section = '''<section id="polling-research" class="section" aria-labelledby="polling-title">
<div class="section-heading"><div><p class="eyebrow">03 / SURVEY RESEARCH</p><h2 id="polling-title">A separate lens on District 6</h2></div><span class="badge neutral">Surveys, not ballots</span></div>
<p class="section-intro">Explore two distinct survey snapshots. A pull date records when a poll was obtained for this dashboard, not when respondents were interviewed. The polls are not combined into an average or a trend.</p>
<div class="poll-grid">
<article class="panel" id="poll-confidential" aria-labelledby="poll-confidential-title">
<p class="eyebrow">CONFIDENTIAL SOURCE / INITIAL BALLOT</p><h3 id="poll-confidential-title">District 6 survey</h3>
<p class="fine"><strong>Pull date: <time datetime="2026-10-28">October 28, 2026</time> · Central Time</strong></p>
<p class="fine" id="poll-confidential-source">Source verified by Tia Fields. Identity withheld at the source’s request.</p>
<p class="fine">419 likely voters · text message survey · L2 voter file sample · weighted to the district’s L2 likely voter profile.</p>
<p class="fine">Reported full sample margin of error: ±4.8 percentage points; larger for subgroups.</p>
<div id="poll-confidential-bars" class="bar-list poll-bars" aria-label="District 6 initial ballot survey results from the confidential source">
''' + chart + '''
</div>
<p class="fine">Q13, initial ballot. Weighted percentages for all likely voters. All ten reported responses are displayed on a 0 to 100% scale. No Party and undecided are different categories.</p>
<details><summary>Source and methodology disclosures</summary><p class="fine">This chart transcribes the supplied executive summary. Source verification is the publisher’s attestation, not an independent audit of the survey. Field dates, the pollster, sponsor, complete questionnaire and full weighting details are not publicly supplied here. The pull date must not be read as the interview date. No candidate probabilities, runoff guarantees or subgroup estimates are inferred.</p><p><a href="data/processed/polling_la6_2026-10-28.json">Download this survey record</a> · <a href="docs/POLLING_METHODS.md">Polling publication notes</a></p></details>
</article>
<article class="panel" aria-labelledby="poll-jmc-title"><p class="eyebrow">PUBLICLY ATTRIBUTED / SEPTEMBER SURVEY</p><h3 id="poll-jmc-title">JMC Analytics and Polling</h3><p class="fine">September 19 to 21, 2026 · 790 likely voters · reported full sample margin of error ±3.5 percentage points.</p><p class="fine">Funded by the Greater Baton Rouge Economic Foundation, according to WBRZ. Likely voters were defined as registered voters who had voted at least once since November 2024.</p><div id="poll-bars" class="bar-list poll-bars" aria-label="Reported JMC District 6 survey preferences"></div><p class="fine">Bar widths use a common 0 to 100% scale. Only categories with specific percentages in the cited article are shown. The remaining candidates are not reconstructed.</p><a href="https://www.wbrz.com/news/wbrz-to-host-6th-district-congressional-debate-in-october/" target="_blank" rel="noopener noreferrer">Read WBRZ source, October 9, 2026 ↗</a></article>
</div>
<div class="poll-context"><h3>Read the evidence correctly</h3><p>Survey samples, interview dates and methods differ. The confidential survey’s field dates are not supplied, so differences between these charts are not evidence of movement over time. Source identity verification does not establish methodological quality. Close estimates do not establish a statistically meaningful lead.</p><div class="party-key"><span class="key rep">Republican</span><span class="key dem">Democratic</span><span class="key nop">No Party</span><span class="key gray">Other or undecided</span></div><p class="fine">Libertarian and undecided responses use gray. Administrative participation, voter registration and survey preferences have different populations and units. They are not combined to estimate candidate support.</p></div>
</section>
'''
html = html[:start] + section + html[end:]
html = html.replace('content="20261028-parish-v2"', f'content="{RELEASE}"')
html = html.replace('Release 20261028.parish.2', 'Release 20261028.poll.3')
html = html.replace('Updated October 28, 2026<br>', 'Updated October 28, 2026 · Central Time<br>')
html = html.replace('SOS report printed October 28 at 3:10:06 a.m. The workbook does not state a timezone.', 'SOS report printed October 28 at 3:10:06 a.m. Central Time.')
html = html.replace('Their print footers read October 28, 2026, 3:10:06 a.m.; timezone is not stated.', 'Their print footers are displayed as October 28, 2026, 3:10:06 a.m. Central Time, using the publisher’s confirmed Louisiana reporting timezone.')
html = re.sub(r'assets/dashboard-v20261028\.(css|js)(?:\?[^" ]*)?', lambda m: f'assets/dashboard-v20261028.{m.group(1)}?v={RELEASE}', html)
assert 'Unverified survey excluded' not in html and 'timezone is not stated' not in html
assert html.count('id="poll-bars"') == html.count('id="poll-confidential-bars"') == 1
assert html.index('id="early-voting"') < html.index('id="parish-map"') < html.index('id="polling-research"')
index.write_text(html)

path = ROOT / 'data/processed/early_voting_2026.json'
data = json.loads(path.read_text())
original_counts = json.dumps({k: data[k] for k in ['statewide', 'parishes', 'observations']}, sort_keys=True)
central = ZoneInfo('America/Chicago')
data['report_printed_timezone'] = 'America/Chicago'
data['display_timezone_label'] = 'Central Time'
data['report_printed_at'] = datetime(2026, 10, 28, 3, 10, 6, tzinfo=central).isoformat()
data['timezone_basis'] = 'Louisiana local reporting time confirmed by the publisher; display normalized with America/Chicago.'
data['verified_at_local'] = datetime.fromisoformat(data['verified_at']).astimezone(central).isoformat()
assert json.dumps({k: data[k] for k in ['statewide', 'parishes', 'observations']}, sort_keys=True) == original_counts
path.write_text(json.dumps(data, indent=2) + '\n')

path = ROOT / 'scripts/build_early_voting_snapshot.py'
text = path.read_text().replace("'report_printed_timezone': 'Not stated in workbook',", "'report_printed_timezone': 'America/Chicago',\n    'display_timezone_label': 'Central Time',\n    'report_printed_at': '2026-10-28T03:10:06-05:00',\n    'timezone_basis': 'Louisiana local reporting time confirmed by the publisher; display normalized with America/Chicago.',")
path.write_text(text)

path = ROOT / 'docs/EARLY_VOTING_METHODS.md'
text = path.read_text().replace('Release: `20261028.parish.2`', 'Release: `20261028.poll.3`')
text = text.replace('The print footer in both reports reads October 28, 2026, 3:10:06 a.m. No timezone is stated in that footer.', 'The print footer is displayed as October 28, 2026, 3:10:06 a.m. Central Time. The publisher confirmed Louisiana local reporting time. The dashboard uses America/Chicago and the corresponding offset for each date.')
text = text.replace('The unattributed 419 respondent screenshot is excluded from quantitative comparison.', 'The 419 respondent survey is published separately with a pull date of October 28, 2026, following source verification attested by Tia Fields. The source requested anonymity. Field dates remain unspecified; the pull date is not an interview date. The chart transcribes all ten initial ballot categories without inferring leaner results, probabilities or a trend. See `docs/POLLING_METHODS.md`.')
path.write_text(text)

notes = '''# Polling publication notes

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
'''
(ROOT / 'docs/POLLING_METHODS.md').write_text(notes)
for filename, heading, body in [
    ('README.md', '## October 28 polling and Central Time update', 'The public Polling section includes the 419 respondent District 6 survey from a confidential source verified by Tia Fields, with a pull date of October 28, 2026. Pull date is distinct from the unspecified survey field dates. All ten initial ballot percentages are displayed separately from the JMC survey. Central Time is used across report labels and metadata. See `docs/POLLING_METHODS.md` for disclosure and interpretation rules.'),
    ('CHANGELOG.md', '## October 28, 2026: confidential survey and Central Time', 'Added all ten reported District 6 initial ballot percentages from the confidential source survey, with publisher attested source verification and October 28 pull date. Replaced the prior survey exclusion with a chart and transparent methodology disclosures. Normalized timestamps to America/Chicago, removed the timezone uncertainty wording, and added regression tests. Early voting counts, parish boundaries, the calculator, registration baseline and commissioning links are unchanged.')]:
    p = ROOT / filename
    text = p.read_text()
    if heading not in text:
        p.write_text(text + '\n' + heading + '\n\n' + body + '\n')

path = ROOT / '.github/workflows/dashboard-checks.yml'
text = path.read_text()
if 'python tests/test_polling_update.py' not in text:
    text = text.replace('          python scripts/validate_early_voting.py\n', '          python scripts/validate_early_voting.py\n          python tests/test_polling_update.py\n')
path.write_text(text)

path = ROOT / 'tests/test_dashboard.py'
text = path.read_text()
if '# Confidential poll regression' not in text:
    extra = '''        # Confidential poll regression
        assert page.locator('#poll-confidential-bars .bar-row').count() == 10
        assert page.locator('#poll-bars .bar-row').count() == 6
        assert 'Pull date: October 28, 2026' in page.locator('#poll-confidential').inner_text()
        assert 'Source verified by Tia Fields' in page.locator('#poll-confidential-source').inner_text()
        assert 'Central Time' in page.locator('.snapshot-line').inner_text()
        page.locator('#polling-research').screenshot(path=str(OUT / 'polling-desktop.png'))
'''
    text = text.replace('        assert not errors, errors', extra + '        assert not errors, errors')
    mobile = '''        assert phone.locator('#poll-confidential-bars .bar-row').count() == 10
        phone.locator('#poll-confidential').screenshot(path=str(OUT / 'polling-mobile.png'))
'''
    text = text.replace("        phone.evaluate(\"document.documentElement.style.scrollBehavior='auto';window.scrollTo(0,0)\")", mobile + "        phone.evaluate(\"document.documentElement.style.scrollBehavior='auto';window.scrollTo(0,0)\")")
    path.write_text(text)
print('PASS: added 10 survey responses; counts unchanged; Central Time normalized')
