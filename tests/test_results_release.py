"""Check sourced results against rendered pages without external data mocks."""
import csv,json,threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
R=Path(__file__).resolve().parents[1]; O=R/'test-output';O.mkdir(exist_ok=True)
d=json.loads((R/'data/processed/election_results_2026-11-03.json').read_text())
e=json.loads((R/'data/processed/early_voting_2026-11-03.json').read_text())
r=json.loads((R/'data/processed/registration_snapshot_2026-11-01.json').read_text())
assert not d['certified'] and len(d['races'])==7
assert sum(len(x['candidates']) for x in d['races'])==41
assert [x['district'] for x in d['races'] if x['runoff_based_on_complete_unofficial_returns']]==[5,6]
for race in d['races']:
    assert sum(c['votes'] for c in race['candidates'])==race['candidate_total']
    assert race['precincts_reporting']==race['precincts_expected']
    assert race['early_absentee_parishes_reporting']==race['early_absentee_parishes_expected']
assert e['statewide']['total']==536185 and sum(p['total'] for p in e['parishes'])==536185
assert r['statewide']['total_registered']==2984520
assert sum(p['total_registered'] for p in r['districts'])==2984520
assert r['derived']['pct_black_registered_outside_district_2']==67.81
assert json.loads((R/'data/processed/early_voting_2026.json').read_text())['statewide']['total']==520942
assert json.loads((R/'data/processed/registration_snapshot_2026-10-01.json').read_text())['statewide']['total_registered']==2978143
class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Handler,directory=str(R)))
threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/'
try:
    with sync_playwright() as p:
        browser=p.chromium.launch()
        for width in [1440,390,320,768]:
            page=browser.new_page(viewport={'width':width,'height':900},accept_downloads=True)
            errors=[];page.on('pageerror',lambda err:errors.append(str(err)))
            page.goto(url,wait_until='networkidle');page.wait_for_selector('html[data-map-ready="true"]')
            assert page.locator('#main > section').first.get_attribute('id')=='runoffs'
            assert page.locator('#runoffs .runoff-card').count()==2
            assert page.locator('#election-results .turnout-card').count()==7
            assert '49.3%' in page.locator('#election-results').inner_text()
            assert page.locator('#election-results tbody tr').count()==41
            for race in d['races']:
                suffix='senate' if race['district'] is None else 'district-'+str(race['district'])
                panel=page.locator('#results-'+suffix);panel.locator('summary').click()
                for c in race['candidates']:
                    assert f"{c['votes']:,}" in panel.inner_text()
                    assert c['name'] in panel.inner_text()
                panel.locator('summary').click()
            assert '2,984,520' in page.locator('#registration').inner_text()
            assert '67.81%' in page.locator('#registration').text_content()
            assert 'Saturday, December 12, 2026' in page.locator('#voting-plan .vp-hero').inner_text()
            assert '7 a.m. to 8 p.m.' in page.locator('#voting-plan .vp-hero').inner_text()
            assert page.locator('#vp-expired').is_hidden()
            page.click('#vp-tab-org');page.select_option('#vp-org-parish','36');page.locator('#vp-org-form button[type="submit"]').click()
            packet=page.locator('#vp-org-preview').inner_text()
            assert 'December 12, 2026' in packet and '7 a.m. to 8 p.m.' in packet
            assert 'No December transportation service has been verified' in packet
            assert 'RTA announced no fares' not in packet
            assert 'Historical November election' in packet
            assert page.locator('#vp-rta').is_hidden()
            with page.expect_download() as event:page.click('#vp-csv')
            dl=event.value;assert '20261212' in dl.suggested_filename
            with open(dl.path(),encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
            assert all(row[2]=='Saturday, December 12, 2026' for row in rows[1:])
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'),width
            page.locator('#runoffs').screenshot(path=str(O/f'runoffs-{width}.png'))
            if width in [1440,390]:page.locator('#election-results').screenshot(path=str(O/f'results-{width}.png'))
            assert not errors,errors
            page.close()
        plain=browser.new_page(java_script_enabled=False)
        plain.goto(url,wait_until='networkidle')
        assert plain.locator('#runoffs').is_visible()
        assert plain.locator('#election-results .turnout-card').count()==7
        assert 'December 12, 2026' in plain.locator('#voting-plan').inner_text()
        assert 'November 3, 2026. Polls open 6 a.m.' not in plain.locator('#voting-plan').inner_text()
        assert plain.locator('h1').count()==1
        browser.close()
finally:server.shutdown()
report={'results':'PASS','races':7,'candidates':41,'runoff_districts':[5,6],'registration_total':2984520,'early_absentee_total':536185,'historical_snapshots':'PRESERVED','december_planner':'PASS','mobile_widths':[320,390,768],'no_javascript':'PASS'}
(O/'results-release-checks.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
