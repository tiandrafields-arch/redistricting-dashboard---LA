"""Read public SOS aggregate election pages. No voter lookup, login or publishing."""
import datetime
import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright

OUT = Path('official-source-review')
OUT.mkdir(exist_ok=True)
HOSTS = {'voterportal.sos.la.gov', 'electionstatistics.sos.la.gov'}
PAGES = [
    ('graphical', 'https://voterportal.sos.la.gov/graphical'),
    ('post_statewide', 'https://electionstatistics.sos.la.gov/default.aspx?Stats=Post_Election_Statistics&Type=Statewide'),
    ('post_parish', 'https://electionstatistics.sos.la.gov/default.aspx?Stats=Post_Election_Statistics&Type=Parish'),
    ('registration_statewide', 'https://electionstatistics.sos.la.gov/default.aspx?Stats=Registration_Statistics&Type=Statewide'),
    ('registration_parish', 'https://electionstatistics.sos.la.gov/default.aspx?Stats=Registration_Statistics&Type=Parish'),
]
manifest = {'retrieved_at_local': datetime.datetime.now(ZoneInfo('America/Chicago')).isoformat(), 'pages': [], 'responses': [], 'downloads': []}
with sync_playwright() as p:
    browser = p.chromium.launch()
    context = browser.new_context(accept_downloads=True, viewport={'width':1440,'height':1000})
    page = context.new_page()
    def capture(response):
        if (urlparse(response.url).hostname or '') not in HOSTS:
            return
        try:
            content_type = response.headers.get('content-type', '')
            if 'json' not in content_type:
                return
            if 'GetClientIpAddress' in response.url:
                return
            body = response.body()
            if len(body) > 12000000:
                return
            filename = 'response_' + str(len(manifest['responses'])).zfill(3) + '.json'
            (OUT / filename).write_bytes(body)
            manifest['responses'].append({'url':response.url,'status':response.status,'content_type':content_type,'file':filename,'sha256':hashlib.sha256(body).hexdigest(),'retrieved_at_local':datetime.datetime.now(ZoneInfo('America/Chicago')).isoformat()})
        except Exception as exc:
            manifest['responses'].append({'url':response.url,'error':str(exc)[:200]})
    page.on('response', capture)
    for key,url in PAGES:
        record = {'key':key,'url':url}
        try:
            response = page.goto(url, wait_until='domcontentloaded', timeout=35000)
            page.wait_for_timeout(10000 if key == 'graphical' else 1500)
            record['status'] = response.status if response else None
            record['final_url'] = page.url
            record['text'] = page.locator('body').inner_text(timeout=10000)
            record['selects'] = page.locator('select').evaluate_all('(es)=>es.map(e=>({id:e.id,name:e.name,options:Array.from(e.options).map(o=>({value:o.value,text:o.text,selected:o.selected}))}))')
            record['links'] = page.locator('a[href]').evaluate_all('(es)=>es.map(e=>({text:e.innerText,url:e.href}))')
            record['retrieved_at_local'] = datetime.datetime.now(ZoneInfo('America/Chicago')).isoformat()
            (OUT / (key+'.html')).write_text(page.content())
            (OUT / (key+'.txt')).write_text(record['text'])
            page.screenshot(path=str(OUT / (key+'.png')), full_page=True)
            print('\nSOURCE', key, record['status'], record['final_url'])
            print(record['text'][:45000])
            print('SELECTS', json.dumps(record['selects']))
            if key != 'graphical':
                seen=set()
                for a in record['links']:
                    target = a['url']
                    if target in seen or urlparse(target).hostname not in HOSTS:
                        continue
                    seen.add(target)
                    if not any(x in target for x in ['2026_1103','20261103','2026_1101','20261101','2026_11_01']):
                        continue
                    if not any(target.lower().split('?')[0].endswith(x) for x in ['.xlsx','.xls','.csv','.pdf','.zip','.txt']):
                        continue
                    try:
                        r=context.request.get(target,timeout=30000)
                        body=r.body()
                        filename=key+'_'+Path(urlparse(target).path).name
                        if r.ok and len(body) < 40000000:
                            (OUT/filename).write_bytes(body)
                        manifest['downloads'].append({'url':target,'status':r.status,'file':filename,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()})
                    except Exception as exc:
                        manifest['downloads'].append({'url':target,'error':str(exc)[:200]})
        except Exception as exc:
            record['error']=str(exc)[:500]
            print('SOURCE ERROR',key,record['error'])
        manifest['pages'].append(record)
        (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    browser.close()
(OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
print('RESPONSE INDEX',json.dumps(manifest['responses'],indent=2))
print('DOWNLOAD INDEX',json.dumps(manifest['downloads'],indent=2))
