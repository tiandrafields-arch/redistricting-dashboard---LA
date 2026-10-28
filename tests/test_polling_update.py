"""Validate the public survey transcription and publisher confirmed local time."""
import json
from datetime import datetime, timedelta
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
poll = json.loads((ROOT / 'data/processed/polling_la6_2026-10-28.json').read_text())
expected = [19, 16, 15, 11, 10, 5, 2, 2, 2, 18]
assert [r['percent'] for r in poll['results']] == expected
assert sum(expected) == 100 and len(poll['results']) == 10
assert poll['sample_size'] == 419
assert poll['pull_date'] == '2026-10-28' and poll['field_dates'] is None
assert poll['source']['identity_withheld'] is True
assert poll['source']['verified_by'] == 'Tia Fields'
assert poll['source']['public_source_url'] is None
assert not any(k in poll['source'] for k in ['name', 'email', 'phone', 'contact'])
html = (ROOT / 'index.html').read_text()
class IDs(HTMLParser):
    def __init__(self):
        super().__init__(); self.ids = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs: self.ids.append(attrs['id'])
parser = IDs(); parser.feed(html)
assert len(parser.ids) == len(set(parser.ids)), 'Duplicate HTML IDs'
assert html.count('data-response=') == 10
assert 'Pull date:' in html and 'October 28, 2026' in html
assert 'Source verified by Tia Fields' in html
assert 'Identity withheld at the source’s request' in html
assert 'Unverified survey excluded' not in html
assert 'The workbook does not state a timezone' not in html
assert 'timezone is not stated' not in html
assert 'id="poll-bars"' in html
assert 'Central Time' in html
assert html.index('id="early-voting"') < html.index('id="parish-map"') < html.index('id="polling-research"')
assert 'https://www.tiafields.com/engage' in html and 'https://civiclensdata.com/' in html
for r in poll['results']:
    assert f'data-response="{r["label"]}"' in html
state = json.loads((ROOT / 'data/processed/early_voting_2026.json').read_text())
assert state['report_printed_timezone'] == 'America/Chicago'
assert state['display_timezone_label'] == 'Central Time'
assert datetime.fromisoformat(state['report_printed_at']).utcoffset() == timedelta(hours=-5)
assert datetime.fromisoformat(state['verified_at_local']) == datetime.fromisoformat(state['verified_at'])
assert state['statewide']['total'] == 520942 and len(state['parishes']) == 64
builder = (ROOT / 'scripts/build_early_voting_snapshot.py').read_text()
assert "'report_printed_timezone': 'America/Chicago'" in builder
assert 'Not stated in workbook' not in builder
methods = (ROOT / 'docs/EARLY_VOTING_METHODS.md').read_text()
assert 'No timezone is stated' not in methods
assert 'screenshot is excluded' not in methods
print('PASS: 10 responses, 100 percent, source privacy, pull date and Central Time')
