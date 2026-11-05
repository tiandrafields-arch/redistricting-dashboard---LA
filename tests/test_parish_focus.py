"""Browser and source checks for the parish focused dashboard."""
from pathlib import Path
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from functools import partial
import csv,json,math,threading
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'test-output';OUT.mkdir(exist_ok=True)
d=json.loads((ROOT/'data/processed/parish_participation_2026-11-03.json').read_text())
assert len(d['parishes'])==64
assert sum(p['results']['votes'] for p in d['parishes'])==1466069
assert sum(p['results']['qualified'] for p in d['parishes'])==2975695
assert sum(p['early']['total'] for p in d['parishes'])==536185
assert sum(p['early']['sex']['unallocated'] for p in d['parishes'])==278
for p in d['parishes']:
 r=p['results'];e=p['early']
 assert r['turnout_pct']==math.floor(r['votes']/r['qualified']*1000+.5)/10
 assert sum(e['sex'].values())==sum(e['race'].values())==e['total']==e['in_person']+e['absentee']
assert d['availability']['full_election_demographics'] is False
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
threading.Thread(target=server.serve_forever,daemon=True).start()
base=f'http://127.0.0.1:{server.server_port}/'
expected=['runoffs','parish-map','parish-comparison','registration','voting-plan','methodology']
report={'data':'PASS','parishes':64,'demographic_scope':'Early and absentee only'}
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch();page=b.new_page(viewport={'width':1440,'height':1000},accept_downloads=True)
  errors=[];failures=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.on('response',lambda r:failures.append(r.url) if r.status>=400 and 'favicon' not in r.url else None)
  page.goto(base,wait_until='networkidle');page.wait_for_selector('html[data-parish-ready="true"][data-map-ready="true"]')
  assert page.locator('#main > section').evaluate_all('(es)=>es.map(e=>e.id)')==expected
  assert page.locator('.nav-inner a').evaluate_all('(es)=>es.map(e=>e.getAttribute("href").slice(1))')==expected
  assert page.locator('#polling-research,#house-races,#senate-research,#election-results,#early-voting,#calculator').count()==0
  assert page.locator('#runoffs .runoff-card').count()==2
  assert page.locator('#runoffs .runoff-person').count()==4
  assert page.locator('#map-shapes path').count()==64
  assert page.locator('#district-cards .district-card').count()==6
  assert page.locator('#selected-total').inner_text()=='49.3%'
  assert page.locator('#parish-table tr').count()==64
  for p in d['parishes']:
   page.select_option('#parish-select',p['parish_code'])
   assert page.locator('#selected-total').inner_text()==f"{p['results']['turnout_pct']:.1f}%"
   assert page.locator('#map-shapes path.selected').get_attribute('data-code')==p['parish_code']
  page.select_option('#parish-select','17');page.click('#view-race');page.select_option('#group-select','black');page.select_option('#map-metric','share')
  p=next(x for x in d['parishes'] if x['parish_code']=='17')
  assert page.locator('#selected-total').inner_text()==f"{100*p['early']['race']['black']/p['early']['total']:.1f}%"
  assert 'not full election demographics' in page.locator('#scope-label').inner_text()
  share_url=page.url
  with page.expect_download() as e:page.click('#download-parish')
  with open(e.value.path(),encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
  assert len(rows)==2 and rows[1][0]=='East Baton Rouge Parish' and rows[1][3]=='race' and rows[1][4]=='black'
  assert rows[1][8]==str(p['early']['total'])
  page.reload(wait_until='networkidle');page.wait_for_selector('html[data-parish-ready="true"]')
  assert page.locator('#parish-select').input_value()=='17'
  assert page.locator('#view-race').get_attribute('aria-selected')=='true'
  assert page.locator('#group-select').input_value()=='black'
  assert page.locator('#map-metric').input_value()=='share'
  page.click('#view-gender');page.select_option('#group-select','female')
  assert page.locator('#selected-total').inner_text()==f"{p['early']['sex']['female']:,}"
  assert 'unallocated difference of 79' in page.locator('#detail-body').inner_text()
  page.click('#view-method');page.select_option('#group-select','absentee')
  assert page.locator('#selected-total').inner_text()==f"{p['early']['absentee']:,}"
  assert 'not yet supplied' in page.locator('#detail-body').inner_text()
  page.click('#view-overview');page.select_option('#map-metric','count')
  assert page.locator('#selected-total').inner_text()==f"{p['results']['votes']:,}"
  page.fill('#parish-find','Orleans Parish');page.locator('#parish-find').dispatch_event('change')
  assert page.locator('#parish-select').input_value()=='36'
  page.locator('#map-shapes path[data-code="17"]').focus();page.keyboard.press('Enter')
  assert page.locator('#parish-select').input_value()=='17'
  box=page.locator('#map-svg').get_attribute('viewBox');page.click('#zoom-in');assert page.locator('#map-svg').get_attribute('viewBox')!=box
  page.click('#map-reset');assert page.locator('#parish-select').input_value()=='state'
  page.fill('#parish-search','Baton Rouge');assert page.locator('#parish-table tr').count()==2
  with page.expect_download() as e:page.click('#download-data')
  with open(e.value.path(),encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
  assert len(rows)==3
  page.fill('#parish-search','');page.select_option('#parish-sort','low')
  text=page.locator('#parish-table tr').first.inner_text();assert min(d['parishes'],key=lambda p:p['results']['votes'])['name'] in text
  page.select_option('#parish-select','17');page.click('#view-gender')
  page.evaluate('window.print=()=>{window.__printed=true}')
  page.click('#print-parish');assert page.evaluate('window.__printed')
  assert 'East Baton Rouge Parish participation' in page.locator('#parish-printout').inner_text()
  page.pdf(path=str(OUT/'Parish_Participation_Summary.pdf'),prefer_css_page_size=True,print_background=True)
  page.evaluate("document.body.classList.remove('parish-printing')")
  assert page.locator('#commission a[href="https://www.tiafields.com/engage"]').count()==1
  assert page.locator('#commission a[href="https://civiclensdata.com/"]').count()==1
  page.click('#vp-tab-org')
  for p in d['parishes']:
   page.select_option('#vp-org-parish',p['parish_code']);page.locator('#vp-org-form button[type=submit]').click()
   assert f"{p['early']['total']:,} reported early ballots" in page.locator('#vp-org-preview').inner_text()
   assert 'Saturday, December 12, 2026' in page.locator('#vp-org-preview').inner_text()
  page.select_option('#vp-org-parish','17');page.locator('#vp-org-form button[type=submit]').click();page.click('#vp-org-map')
  assert page.locator('#parish-select').input_value()=='17'
  with page.expect_download() as e:page.click('#vp-csv')
  assert e.value.suggested_filename.endswith('20261212.csv')
  assert page.evaluate('localStorage.length===0&&sessionStorage.length===0')
  page.click('#view-overview');page.select_option('#parish-select','state')
  page.evaluate('window.scrollTo(0,0)');page.screenshot(path=str(OUT/'parish-desktop-top.png'))
  page.locator('#parish-map').screenshot(path=str(OUT/'parish-desktop-map.png'))
  assert not errors,errors;assert not failures,failures
  for width in [320,390,768]:
   phone=b.new_page(viewport={'width':width,'height':844},is_mobile=True,has_touch=True)
   phone.goto(base,wait_until='networkidle');phone.wait_for_selector('html[data-map-ready="true"]')
   for tab in ['overview','race','gender','method']:
    phone.click('#view-'+tab)
    assert phone.evaluate('document.documentElement.scrollWidth<=innerWidth+1'),(width,tab)
   if width==390:
    phone.click('#view-overview');phone.screenshot(path=str(OUT/'parish-mobile-map.png'),full_page=False)
    phone.evaluate('window.scrollTo(0,0)');phone.screenshot(path=str(OUT/'parish-mobile-top.png'))
   phone.close()
  plain=b.new_page(java_script_enabled=False)
  plain.goto(base,wait_until='networkidle')
  assert plain.locator('#parish-table tr').count()==64
  assert plain.locator('#voting-plan').count()==1
  assert plain.locator('#polling-research,#senate-research,#house-races').count()==0
  broken=b.new_page();broken.route('**/data/processed/parish_participation_2026-11-03.json*',lambda r:r.fulfill(status=503,body='Unavailable'))
  broken.goto(base,wait_until='networkidle');broken.wait_for_selector('html[data-parish-ready="error"]')
  assert broken.locator('#parish-select').is_disabled()
  assert 'could not be loaded' in broken.locator('#scope-label').inner_text()
  assert broken.locator('#runoffs').is_visible()
  report.update({'page_order':expected,'map':'PASS','all_parish_selections':'PASS','views':'PASS','csv':'PASS','PDF':'PASS','share_URL_restore':'PASS','planner_parishes':64,'mobile_widths':[320,390,768],'source_failure':'PASS','no_Javascript_table':'PASS','console_errors':errors})
  b.close()
finally:server.shutdown()
(OUT/'parish-focus-results.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
