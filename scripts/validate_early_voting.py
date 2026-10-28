"""Fail closed if the published snapshot or its geographic join is inconsistent."""
import hashlib
import json
from datetime import datetime
from pathlib import Path
R = Path(__file__).resolve().parents[1]
d = json.loads((R / 'data/processed/early_voting_2026.json').read_text())
g = json.loads((R / 'data/louisiana_parishes_2026.geojson').read_text())
m = json.loads((R / 'data/boundary_source.json').read_text())
assert d['status'] == 'verified_snapshot', 'Publication requires a verified snapshot'
assert d['reporting_period_end'] == '2026-10-27'
datetime.fromisoformat(d['verified_at'])
assert len(d['parishes']) == 64
assert len({p['parish_code'] for p in d['parishes']}) == 64
assert len({p['geoid'] for p in d['parishes']}) == 64
assert {p['geoid'] for p in d['parishes']} == {f['properties']['GEOID'] for f in g['features']}
assert hashlib.sha256((R / 'data/louisiana_parishes_2026.geojson').read_bytes()).hexdigest() == m['sha256']
state = d['statewide']
for p in [state, *d['parishes']]:
    assert all(type(p[k]) is int and p[k] >= 0 for k in ('total', 'in_person', 'absentee'))
    assert p['total'] == p['in_person'] + p['absentee']
    for group in ('party', 'race'):
        assert all(type(v) is int and v >= 0 for v in p['breakdowns'][group].values())
        assert sum(p['breakdowns'][group].values()) == p['total']
for key in ('total', 'in_person', 'absentee'):
    assert sum(p[key] for p in d['parishes']) == state[key]
for group in ('party', 'race'):
    for key, value in state['breakdowns'][group].items():
        assert sum(p['breakdowns'][group][key] for p in d['parishes']) == value
assert len(d['observations']) == 1 and d['observations'][0]['date'] == '2026-10-27'
print('PASS: source scope, counts, category sums, geography and boundary checksum')
