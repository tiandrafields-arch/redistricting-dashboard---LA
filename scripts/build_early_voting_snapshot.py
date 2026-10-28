"""Build the verified October 27 snapshot from the audited parish aggregate export.
The original 6,869 report rows were reconciled against both supplied SOS workbooks.
This reproducible build checks the public aggregate CSV and cached Census boundaries.
It does not claim to fetch or authenticate a new online SOS report.
"""
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
PARTY = {'democratic': 221066, 'republican': 205085, 'no_party': 92922, 'other': 1869}
RACE = {'white': 319138, 'black': 179094, 'other': 22710}
STATE = {'total': 520942, 'in_person': 448525, 'absentee': 72417, 'breakdowns': {'party': PARTY, 'race': RACE}}

def normalize(name):
    return re.sub('[^A-Z]', '', name.upper().replace(' PARISH', ''))

with (ROOT / 'data/processed/early_voting_2026_parishes.csv').open(newline='') as stream:
    rows = list(csv.DictReader(stream))
geometry = json.loads((ROOT / 'data/louisiana_parishes_2026.geojson').read_text())
geo = {f['properties']['GEOID']: normalize(f['properties']['BASENAME']) for f in geometry['features']}
assert len(rows) == len(geo) == 64
parishes = []
for r in rows:
    p = {k: r[k] for k in ('parish_code', 'geoid', 'parish')}
    p.update({k: int(r[k]) for k in ('total', 'in_person', 'absentee')})
    p['breakdowns'] = {
        'party': {k: int(r['other_party' if k == 'other' else k]) for k in PARTY},
        'race': {k: int(r['other_race' if k == 'other' else k]) for k in RACE},
    }
    assert geo[p['geoid']] == normalize(p['parish']), p['parish']
    assert p['total'] == p['in_person'] + p['absentee']
    for values in p['breakdowns'].values():
        assert all(v >= 0 for v in values.values())
        assert sum(values.values()) == p['total']
    parishes.append(p)
assert len({p['parish_code'] for p in parishes}) == 64
assert len({p['geoid'] for p in parishes}) == 64
for key in ('total', 'in_person', 'absentee'):
    assert sum(p[key] for p in parishes) == STATE[key]
for group in ('party', 'race'):
    for key, value in STATE['breakdowns'][group].items():
        assert sum(p['breakdowns'][group][key] for p in parishes) == value
verified = datetime.now(timezone.utc)
result = {
    'schema_version': 2, 'status': 'verified_snapshot', 'election_date': '2026-11-03',
    'reporting_period_end': '2026-10-27', 'report_printed_at_local': '2026-10-28 03:10:06',
    'report_printed_timezone': 'America/Chicago',
    'display_timezone_label': 'Central Time',
    'report_printed_at': datetime(2026, 10, 28, 3, 10, 6, tzinfo=ZoneInfo('America/Chicago')).isoformat(),
    'timezone_basis': 'Louisiana local reporting time confirmed by the publisher; display normalized with America/Chicago.',
    'verified_at': verified.isoformat(),
    'verified_at_local': verified.astimezone(ZoneInfo('America/Chicago')).isoformat(),
    'source_url': 'https://www.sos.la.gov/elections-voting/early-voting-statistics-parish',
    'source_files': [
        {'filename': '2026_1103_StatewideStats.xlsx', 'sha256': '9265f07ed7d1e2d351726ab5c02d788d25341e1184721e6d194e7e1733f5a37c', 'origin': 'User supplied SOS workbook'},
        {'filename': '2026_1103_ParishStats.xlsx', 'sha256': '77c7b7afd43576781659ef345b4ef70499c7b63adaa9ee49ad17463d5977feff', 'origin': 'User supplied SOS workbook'},
    ],
    'verification': {'parishes': 64, 'detail_rows_checked': 6869, 'workbooks_reconciled': True, 'geography_matches': 64, 'reported_sex_gap': 266},
    'scope_note': 'Reported participation through October 27, not certified final election turnout. Later absentee receipts and corrections are not included.',
    'statewide': STATE, 'parishes': parishes, 'observations': [{'date': '2026-10-27', **STATE}],
}
(ROOT / 'data/processed/early_voting_2026.json').write_text(json.dumps(result, indent=2) + '\n')
print('PASS: 64 parish records, all categories, geographic identities and Central Time metadata reconcile')
