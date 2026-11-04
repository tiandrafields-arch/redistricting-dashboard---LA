"""Browser regression tests against real repository files, with no mocked data responses."""
import csv
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test-output'
OUT.mkdir(exist_ok=True)

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass

server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}/'
results = {}
order = ['runoffs', 'election-results', 'early-voting', 'parish-map', 'senate-research', 'polling-research', 'house-races', 'registration', 'voting-plan', 'methodology']
races = json.loads((ROOT / 'data/processed/house_races_2026-11-01.json').read_text())
assert [r['district'] for r in races['races']] == [1, 2, 3, 4, 5]
assert [len(r['candidates']) for r in races['races']] == [4, 5, 6, 5, 9]
assert sum(r['candidate_count'] for r in races['races']) == 29

def check_house(page):
    assert page.locator('#house-races .house-snapshot').count() == 5
    assert page.locator('#house-races .house-candidates li').count() == 29
    for race in races['races']:
        card = page.locator('#house-district-' + str(race['district']))
        names = card.locator('.house-candidates strong').all_text_contents()
        parties = card.locator('.house-party').all_text_contents()
        assert names == [c['name'] for c in race['candidates']]
        assert parties == [c['party'] for c in race['candidates']]
        assert card.locator('.house-source a').get_attribute('href') == race['source_url']
    assert len(set(page.locator('.house-party').evaluate_all('(items) => items.map(e => getComputedStyle(e).color)'))) == 1

try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
        errors = []
        failures = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('response', lambda r: failures.append(f'{r.status} {r.url}') if r.status >= 400 and 'favicon' not in r.url else None)
        page.goto(url, wait_until='networkidle')
        page.wait_for_selector('html[data-map-ready="true"][data-education-ready="true"]')
        page.wait_for_selector('#senate-research[data-ready="true"]')
        assert page.locator('#main > section').evaluate_all('(items) => items.map(e => e.id)') == order
        assert page.locator('.nav-inner a').evaluate_all('(items) => items.map(e => e.getAttribute("href").slice(1))') == order
        assert page.locator('#page-title').inner_text() == 'Early and absentee voting statistics'
        assert page.locator('.nav-inner a[href="#early-voting"]').inner_text() == 'Early ballot statistics'
        assert page.locator('#calculator, #use-in-calculator, #ev-scenario, a[href="#calculator"]').count() == 0
        assert 'assumptions' not in page.locator('#early-voting .intro').inner_text()
        assert 'calculator' not in page.locator('main').inner_text().lower()
        assert page.locator('#senate-research .eyebrow').first.inner_text() == '02 / SENATE SURVEY RESEARCH'
        check_house(page)
        page.locator('#house-races').screenshot(path=str(OUT / 'house-races-desktop.png'))
        assert page.locator('#map-shapes path').count() == 64
        assert page.locator('#district-cards .district-card').count() == 6
        assert page.locator('#ev-total').inner_text() == '536,185'
        page.select_option('#parish-select', '17')
        assert page.locator('#selected-total').inner_text() == '55,853'
        page.select_option('#map-metric', 'republican')
        assert 'Republican registration share' in page.locator('#metric-description').inner_text()
        before = page.locator('#map-svg').get_attribute('viewBox')
        page.click('#zoom-in')
        assert page.locator('#map-svg').get_attribute('viewBox') != before
        page.click('#map-reset')
        page.locator('#map-shapes path[data-code="36"]').focus()
        page.keyboard.press('Enter')
        assert page.locator('#selected-total').inner_text() == '49,250'
        page.locator('.table-details > summary').click()
        page.fill('#parish-search', 'Baton Rouge')
        assert page.locator('#parish-table tr').count() == 2
        with page.expect_download() as event:
            page.click('#download-data')
        event.value.save_as(OUT / 'export.csv')
        assert len((OUT / 'export.csv').read_text(encoding='utf-8-sig').splitlines()) == 65
        assert page.locator('#commission a[href="https://www.tiafields.com/engage"]').count() == 1
        assert page.locator('#commission a[href="https://civiclensdata.com/"]').count() == 1
        assert page.locator('#poll-confidential-bars .bar-row').count() == 10
        assert page.locator('#poll-bars .bar-row').count() == 6
        assert 'Pull date: October 28, 2026' in page.locator('#poll-confidential').inner_text()
        assert 'Source verified by Tia Fields' in page.locator('#poll-confidential-source').inner_text()
        assert 'Central Time' in page.locator('.snapshot-line').inner_text()
        page.locator('#polling-research').screenshot(path=str(OUT / 'polling-desktop.png'))
        # Planner integration uses the actual published snapshot, not a fixture.
        assert page.locator('#voting-plan').count() == 1
        assert page.locator('.nav-inner a[href="#voting-plan"]').count() == 1
        assert page.locator('#vp-org-parish option').count() == 65
        assert page.locator('.mini-heading h4').inner_text() == 'Who voted early or absentee'
        page.click('#vp-tab-org')
        snapshot = json.loads((ROOT / 'data/processed/early_voting_2026-11-03.json').read_text())
        for parish in snapshot['parishes']:
            page.select_option('#vp-org-parish', parish['parish_code'])
            page.locator('#vp-org-form button[type="submit"]').click()
            assert f"{parish['total']:,} reported early ballots" in page.locator('#vp-org-preview').inner_text()
            assert 'not a turnout rate' in page.locator('#vp-org-preview').inner_text()
        page.select_option('#vp-org-parish', '36')
        page.locator('#vp-org-form button[type="submit"]').click()
        assert page.locator('#vp-rta').is_hidden()
        assert 'No December transportation service has been verified' in page.locator('#vp-org-preview').inner_text()
        page.select_option('#vp-org-parish', '17')
        page.fill('#vp-org-name', 'Example community organization')
        page.locator('#vp-org-form button[type="submit"]').click()
        assert page.locator('#vp-rta').is_hidden()
        assert page.locator('#vp-org-preview tbody tr').count() == 10
        with page.expect_download() as event:
            page.click('#vp-csv')
        event.value.save_as(OUT / 'East_Baton_Rouge_Organization_Checklist.csv')
        with (OUT / 'East_Baton_Rouge_Organization_Checklist.csv').open(encoding='utf-8-sig', newline='') as handle:
            rows = list(csv.reader(handle))
        assert len(rows) == 14 and all(len(row) == 9 for row in rows)
        assert rows[1][0] == 'Example community organization' and rows[1][1] == 'East Baton Rouge'
        page.evaluate("window.print = () => { window.__plannerPrint = true; }")
        page.click('#vp-print-org')
        assert page.evaluate('window.__plannerPrint === true')
        page.pdf(path=str(OUT / 'East_Baton_Rouge_Organization_Plan.pdf'), prefer_css_page_size=True, print_background=True)
        page.evaluate("document.body.classList.remove('vp-printing')")
        page.fill('#vp-org-name', '=1+1')
        page.locator('#vp-org-form button[type="submit"]').click()
        with page.expect_download() as event:
            page.click('#vp-csv')
        with open(event.value.path(), encoding='utf-8-sig', newline='') as handle:
            protected_rows = list(csv.reader(handle))
        assert protected_rows[1][0] == "'=1+1"
        page.fill('#vp-org-name', '<img src=x onerror=alert(1)>')
        page.locator('#vp-org-form button[type="submit"]').click()
        assert page.locator('#vp-org-preview img').count() == 0
        page.fill('#vp-org-name', 'Example community organization')
        page.locator('#vp-org-form button[type="submit"]').click()
        page.click('#vp-org-map')
        assert page.locator('#selected-total').inner_text() == '55,853'
        page.click('#vp-tab-voter')
        page.locator('#vp-voter-form button[type="submit"]').click()
        assert page.locator('#vp-personal-actions').is_hidden()
        page.select_option('#vp-parish', '17')
        page.fill('#vp-address', '123 Example Street, Baton Rouge, Louisiana')
        page.fill('#vp-time', '08:30')
        page.check('#vp-confirm')
        page.locator('#vp-voter-form button[type="submit"]').click()
        assert '8:30 a.m. Central Time' in page.input_value('#vp-personal-preview')
        page.evaluate("window.open = url => { window.__plannerDirection = url; return null; }")
        page.click('#vp-directions')
        assert 'destination=123%20Example' in page.evaluate('window.__plannerDirection')
        page.fill('#vp-address', '456 Changed Example Street, Baton Rouge, Louisiana')
        assert not page.is_checked('#vp-confirm')
        assert page.locator('#vp-personal-actions').is_hidden()
        page.click('#vp-clear')
        assert page.input_value('#vp-address') == ''
        assert page.evaluate('localStorage.length === 0 && sessionStorage.length === 0')
        results['planner'] = {'parishes': 64, 'csv': 'PASS', 'print': 'PASS', 'directions': 'PASS', 'confirmation': 'PASS', 'input_safety': 'PASS', 'browser_storage': 'NONE'}
        assert not errors, errors
        assert not failures, failures
        page.evaluate("document.documentElement.style.scrollBehavior='auto';window.scrollTo(0,0)")
        page.screenshot(path=str(OUT / 'desktop-top.png'))
        results['desktop'] = {'map_paths': 64, 'selection': 'PASS', 'calculator': 'REMOVED', 'keyboard': 'PASS', 'zoom': 'PASS', 'search': 'PASS', 'csv_rows': 64, 'page_errors': errors, 'http_failures': failures, 'section_order': order}
        phone = browser.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        phone.goto(url, wait_until='networkidle')
        phone.wait_for_selector('html[data-map-ready="true"][data-education-ready="true"]')
        assert phone.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
        assert phone.locator('#main > section').first.get_attribute('id') == 'runoffs'
        assert phone.locator('.vp-sticky').is_visible()
        assert phone.locator('#ev-total').inner_text() == '536,185'
        phone.screenshot(path=str(OUT / 'mobile-top.png'))
        check_house(phone)
        phone.locator('#house-races').screenshot(path=str(OUT / 'house-races-mobile.png'))
        phone.select_option('#parish-select', '28')
        assert phone.locator('#selected-total').inner_text() == '27,753'
        assert phone.locator('#poll-confidential-bars .bar-row').count() == 10
        phone.locator('#poll-confidential').screenshot(path=str(OUT / 'polling-mobile.png'))
        phone.click('#vp-tab-org')
        phone.select_option('#vp-org-parish', '17')
        phone.locator('#vp-org-form button[type="submit"]').click()
        assert '55,853 reported early ballots' in phone.locator('#vp-org-preview').inner_text()
        assert phone.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
        phone.locator('#voting-plan').screenshot(path=str(OUT / 'planner-mobile.png'))
        results['mobile'] = {'horizontal_overflow': False, 'selection': 'PASS', 'parish_plan': 'PASS'}
        for width in [320, 768]:
            page.set_viewport_size({'width': width, 'height': 900})
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), width
        plain = browser.new_page(java_script_enabled=False, viewport={'width': 390, 'height': 844})
        plain.goto(url, wait_until='networkidle')
        check_house(plain)
        assert plain.locator('#voting-plan').count() == 1
        assert plain.locator('#senate-research').count() == 1
        assert plain.locator('#calculator').count() == 0
        assert plain.evaluate("Boolean(document.getElementById('registration').compareDocumentPosition(document.getElementById('voting-plan')) & Node.DOCUMENT_POSITION_FOLLOWING)")
        assert plain.evaluate("Boolean(document.getElementById('voting-plan').compareDocumentPosition(document.getElementById('methodology')) & Node.DOCUMENT_POSITION_FOLLOWING)")
        results['house_races'] = {'districts': 5, 'candidates': 29, 'source_links': 'PASS', 'names_and_parties': 'PASS', 'uniform_style': 'PASS', 'without_javascript': 'PASS'}
        browser.close()
finally:
    server.shutdown()
(OUT / 'results.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
