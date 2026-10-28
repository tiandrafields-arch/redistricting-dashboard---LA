"""Browser regression tests against real repository files, with no mocked responses."""
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
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
        errors = []
        failures = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('response', lambda r: failures.append(f'{r.status} {r.url}') if r.status >= 400 and 'favicon' not in r.url else None)
        page.goto(url, wait_until='networkidle')
        page.wait_for_selector('html[data-map-ready="true"]')
        assert page.locator('#map-shapes path').count() == 64
        assert page.locator('#district-cards .district-card').count() == 6
        assert page.locator('#ev-total').inner_text() == '520,942'
        page.select_option('#parish-select', '17')
        assert page.locator('#selected-total').inner_text() == '53,645'
        page.click('#use-in-calculator')
        assert page.locator('#scenario-total').inner_text() == '107,290'
        page.locator('#additional-rate').evaluate("e => {e.value='50';e.dispatchEvent(new Event('input',{bubbles:true}));}")
        assert page.locator('#scenario-total').inner_text() == '80,468'
        page.select_option('#map-metric', 'republican')
        assert 'Republican registration share' in page.locator('#metric-description').inner_text()
        before = page.locator('#map-svg').get_attribute('viewBox')
        page.click('#zoom-in')
        assert page.locator('#map-svg').get_attribute('viewBox') != before
        page.click('#map-reset')
        page.locator('#map-shapes path[data-code="36"]').focus()
        page.keyboard.press('Enter')
        assert page.locator('#selected-total').inner_text() == '47,645'
        page.locator('.table-details > summary').click()
        page.fill('#parish-search', 'Baton Rouge')
        assert page.locator('#parish-table tr').count() == 2
        with page.expect_download() as event:
            page.click('#download-data')
        download = event.value
        download.save_as(OUT / 'export.csv')
        assert len((OUT / 'export.csv').read_text(encoding='utf-8-sig').splitlines()) == 65
        assert page.locator('#commission a[href="https://www.tiafields.com/engage"]').count() == 1
        assert page.locator('#commission a[href="https://civiclensdata.com/"]').count() == 1
        # Confidential poll regression
        assert page.locator('#poll-confidential-bars .bar-row').count() == 10
        assert page.locator('#poll-bars .bar-row').count() == 6
        assert 'Pull date: October 28, 2026' in page.locator('#poll-confidential').inner_text()
        assert 'Source verified by Tia Fields' in page.locator('#poll-confidential-source').inner_text()
        assert 'Central Time' in page.locator('.snapshot-line').inner_text()
        page.locator('#polling-research').screenshot(path=str(OUT / 'polling-desktop.png'))
        assert not errors, errors
        assert not failures, failures
        page.evaluate("document.documentElement.style.scrollBehavior='auto';window.scrollTo(0,0)")
        page.screenshot(path=str(OUT / 'desktop.png'), full_page=True)
        results['desktop'] = {'map_paths': 64, 'selection': 'PASS', 'calculator': 'PASS', 'keyboard': 'PASS', 'zoom': 'PASS', 'search': 'PASS', 'csv_rows': 64, 'page_errors': errors, 'http_failures': failures}
        phone = browser.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        phone.goto(url, wait_until='networkidle')
        phone.wait_for_selector('html[data-map-ready="true"]')
        assert phone.evaluate('document.documentElement.scrollWidth <= innerWidth + 1')
        y = phone.locator('#ev-total').bounding_box()['y']
        assert y < 500, y
        phone.select_option('#parish-select', '28')
        assert phone.locator('#selected-total').inner_text() == '26,858'
        assert phone.locator('#poll-confidential-bars .bar-row').count() == 10
        phone.locator('#poll-confidential').screenshot(path=str(OUT / 'polling-mobile.png'))
        phone.evaluate("document.documentElement.style.scrollBehavior='auto';window.scrollTo(0,0)")
        phone.screenshot(path=str(OUT / 'mobile.png'), full_page=True)
        results['mobile'] = {'horizontal_overflow': False, 'early_vote_total_y': y, 'selection': 'PASS'}
        browser.close()
finally:
    server.shutdown()
(OUT / 'results.json').write_text(json.dumps(results, indent=2))
print(json.dumps(results, indent=2))
