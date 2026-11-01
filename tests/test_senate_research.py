"""Senate research checks on repository files served over a local HTTP server."""
import json
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'test-output'
OUT.mkdir(exist_ok=True)
DATA = json.loads((ROOT / 'data/processed/polling_senate_2026-11-01.json').read_text())
assert len(DATA['polls']) == 3
assert len({p['pollster'] for p in DATA['polls']}) == 2
assert all(p['campaign_sponsored'] for p in DATA['polls'])
assert DATA['polls'][0]['sample_n'] == 502
assert DATA['polls'][2]['moe_percentage_points'] is None
assert DATA['national_context'][1]['sample_n'] == 1289
for poll in DATA['polls']:
    assert sum(poll[k] for k in ['davis', 'letlow', 'uncommitted']) == 100
    assert poll['field_end'] <= DATA['reviewed_date']
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(QuietHandler, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{server.server_port}/'
results = {'dataset': 'PASS', 'surveys': 3, 'firms': 2}
try:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.goto(url, wait_until='networkidle')
        page.wait_for_selector('#senate-research[data-ready="true"]')
        assert page.evaluate("document.querySelector('#senate-research').nextElementSibling.id") == 'polling-research'
        assert page.locator('#senate-poll-select option').count() == 3
        assert '03B' in page.locator('#polling-research .eyebrow').first.inner_text()
        assert page.locator('.nav-inner a[href="#senate-research"]').count() == 1
        for poll in DATA['polls']:
            page.select_option('#senate-poll-select', poll['id'])
            values = page.locator('#senate-poll-chart .sr-bar-label strong').all_text_contents()
            assert values == [str(poll[k]) + '%' for k in ['davis','letlow','uncommitted']]
            assert poll['sponsor'] in page.locator('#senate-poll-meta').inner_text()
            assert poll['evidence'] in page.locator('#senate-poll-meta').inner_text()
            widths = page.locator('#senate-poll-chart .sr-fill').evaluate_all("es=>es.map(e=>e.style.width)")
            assert widths == values
        assert 'Not supplied' in page.locator('#senate-poll-meta').inner_text()
        page.select_option('#senate-poll-select', 'hart_october')
        assert '502' in page.locator('#senate-poll-meta').inner_text()
        page.locator('#sr-panel-louisiana summary').click()
        assert page.locator('#sr-panel-louisiana tbody tr').count() == 3
        page.locator('#sr-panel-louisiana summary').click()
        page.locator('#senate-research').screenshot(path=str(OUT/'senate-desktop.png'))
        page.click('#sr-tab-national')
        assert page.locator('#sr-panel-louisiana').is_hidden()
        assert page.locator('#sr-panel-national .sr-bar-label strong').all_text_contents() == ['52%', '42%', '52%', '44%']
        assert 'not a Louisiana Senate poll' in page.locator('#sr-panel-national').inner_text()
        assert 'Solid Republican' in page.locator('#sr-panel-national').inner_text()
        assert 'Likely Republican' in page.locator('#sr-panel-national').inner_text()
        page.locator('#sr-tab-national').focus()
        page.keyboard.press('ArrowRight')
        assert page.locator('#sr-tab-sources').get_attribute('aria-selected') == 'true'
        with page.expect_download() as event:
            page.click('#senate-download')
        event.value.save_as(OUT/'senate-export.json')
        exported = json.loads((OUT/'senate-export.json').read_text())
        assert exported == DATA
        page.keyboard.press('Home')
        page.click('#sr-tab-louisiana')
        assert not errors, errors
        for width in [320, 390, 768]:
            phone = browser.new_page(viewport={'width': width, 'height': 844}, is_mobile=True, has_touch=True)
            phone.goto(url, wait_until='networkidle')
            phone.wait_for_selector('#senate-research[data-ready="true"]')
            assert phone.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), width
            for kind in ['national', 'sources', 'louisiana']:
                phone.click('#sr-tab-' + kind)
                assert phone.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'), (width, kind)
            if width == 390:
                phone.locator('#senate-research').screenshot(path=str(OUT/'senate-mobile.png'))
            phone.close()
        broken = browser.new_page()
        broken.route('**/data/processed/polling_senate_2026-11-01.json*', lambda route: route.fulfill(status=503, body='Unavailable'))
        broken.goto(url, wait_until='networkidle')
        broken.wait_for_selector('#senate-research[data-ready="error"]')
        assert 'could not be loaded' in broken.locator('#senate-status').inner_text()
        assert broken.locator('#polling-research').is_visible()
        broken.close()
        archived = browser.new_page()
        archived.add_init_script("Date.now=()=>Date.parse('2026-11-04T03:00:00Z')")
        archived.goto(url, wait_until='networkidle')
        archived.wait_for_selector('#senate-research[data-ready="true"]')
        assert archived.locator('#senate-archive').is_visible()
        archived.close()
        browser.close()
        results.update({'placement':'PASS','poll_selector':'PASS','national_context':'PASS','source_download':'PASS','keyboard_tabs':'PASS','mobile_widths':[320,390,768],'failure_fallback':'PASS','archive_notice':'PASS','page_errors':errors})
finally:
    server.shutdown()
(OUT/'senate-results.json').write_text(json.dumps(results,indent=2))
print(json.dumps(results,indent=2))
