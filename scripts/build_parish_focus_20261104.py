"""Build the parish focused release from preserved aggregate SOS evidence.

Requires the parish-source-review artifact extracted under source-input/parish.
Does not contact any network service, publish, change branches or infer vote choice.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import copy, csv, hashlib, html, json, math, shutil
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/'source-input/parish/parish-source-review'
PROCESSED=ROOT/'data/processed'
DEST=ROOT/'data/sources/20261104_parish'
DEST.mkdir(parents=True,exist_ok=True)
RELEASE='20261104-parish1'
PORTAL='https://voterportal.sos.la.gov/graphical'
ARCHIVE=ROOT/'archive/november-2026'

def load(p): return json.loads(p.read_text())
def dump(p,d): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def title(s): return 'LaSalle' if s=='LASALLE' else s.title()
def fmt(n): return f'{n:,}'
def fragment(s): return BeautifulSoup(s,'html.parser')

# Freeze the prior published page and its dependencies before removing anything.
if not ARCHIVE.exists():
    ARCHIVE.mkdir(parents=True)
    old=BeautifulSoup((ROOT/'index.html').read_text(),'html.parser')
    for e in old.select('script[src],link[rel=stylesheet]'):
        name=(e.get('src') or e.get('href')).split('?')[0]
        if not name.startswith(('http:','https:','/')):
            target=ARCHIVE/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    shutil.copytree(PROCESSED,ARCHIVE/'data/processed')
    shutil.copytree(ROOT/'docs',ARCHIVE/'docs')
    for name in ['louisiana_parishes_2026.geojson','boundary_source.json']:
        shutil.copyfile(ROOT/'data'/name,ARCHIVE/'data'/name)
    old.title.string='Archived November election research | Tia Fields'
    old.body.insert(0,fragment('<aside style="padding:16px;background:#fff4df;color:#152d48"><strong>Historical November election research.</strong> This page preserves the prior release, including polls and candidates who are not in the runoff. <a href="../../">Return to the current parish dashboard</a>.</aside>'))
    (ARCHIVE/'index.html').write_text(str(old))

manifest=load(INPUT/'manifest.json')
records={r['key']:r for r in manifest['sources']}
required=['senate_parishes','senate_early','stats_parish','stats_statewide','senate_stats','election_dates','all_results']
assert all(records[k]['status']==200 for k in required)
for name in [k+'.json' for k in required]+['post_parish.txt','post_statewide.txt','manifest.json']:
    shutil.copyfile(INPUT/name,DEST/name)
meta=load(INPUT/'election_dates.json')['Dates']['Date']
election=next(r for r in meta if r['ElectionDate']=='11/03/2026')
assert election['ResultsOfficial']=='0', 'Source status changed; review certification before building'
assert election['PostElectionStatsAvailable']=='0', 'Audited participation is now available; review instead of using the early only fallback'
assert not records['post_parish']['november_listed'] and not records['post_statewide']['november_listed']
assert all(int(v)==0 for k,v in load(INPUT/'stats_statewide.json')['Stats'].items() if k.endswith('_Voted'))
raw=load(INPUT/'senate_parishes.json')['Parishes']['Parish']
state=next(r for r in load(INPUT/'all_results.json')['Races']['Race'] if r['ID']=='67997')
assert len(raw)==64 and len({r['ParishValue'] for r in raw})==64
assert sum(int(r['VoterCountQualified']) for r in raw)==int(state['VoterCountQualified'])
assert sum(sum(int(c['VoteTotal']) for c in r['Choice']) for r in raw)==sum(int(c['VoteTotal']) for c in state['Choice'])
assert sum(int(r['PrecinctsExpected']) for r in raw)==int(state['PrecinctsExpected'])

# This matrix was extracted and reconciled using ArtifactTool from the preserved
# statewide workbook. Store the unallocated numerical difference, not an invented sex.
sex_matrix=[[1,2294,2700,1],[2,895,1125,1],[3,7733,10062,4],[4,879,1245,1],[5,1696,2158,2],[6,1596,1840,1],[7,720,1138,1],[8,6308,8025,2],[9,9917,15674,7],[10,8399,10998,1],[11,592,697,0],[12,314,350,0],[13,493,607,0],[14,1019,1465,0],[15,855,1214,0],[16,1924,2767,2],[17,22252,33522,79],[18,426,622,0],[19,1342,1711,2],[20,1437,1723,0],[21,969,1231,0],[22,793,901,0],[23,2662,3509,0],[24,1696,2380,1],[25,987,1377,0],[26,18143,27201,29],[27,2020,2666,0],[28,12049,15687,17],[29,4118,5068,2],[30,713,877,0],[31,2202,3215,1],[32,6730,8534,1],[33,490,787,0],[34,1557,2321,0],[35,1790,2522,0],[36,18893,30277,80],[37,7087,10754,1],[38,1893,2259,2],[39,1246,1705,0],[40,5379,7185,2],[41,432,719,1],[42,946,1277,0],[43,1250,1514,2],[44,1752,2426,2],[45,2586,3429,2],[46,684,926,0],[47,1521,2184,0],[48,2443,3789,2],[49,3196,4668,2],[50,3272,3941,0],[51,2085,2927,0],[52,18614,23475,12],[53,5674,7779,5],[54,390,526,0],[55,3939,4895,1],[56,1162,1365,1],[57,2136,2559,1],[58,1883,2051,3],[59,2040,2869,2],[60,2032,2917,2],[61,1708,2385,0],[62,497,599,0],[63,829,1183,0],[64,792,1034,0]]
assert sha(ROOT/'data/sources/20261104/early_statewide_2026_1103_StatewideStats.xlsx')=='21c9a2cebba310305e61e582a1be5d7f170c02d9ecd48ced69caf5b53444c495'
sex={f'{r[0]:02}':dict(zip(['male','female','unallocated'],r[1:])) for r in sex_matrix}
early=load(PROCESSED/'early_voting_2026-11-03.json')
assert early['statewide']['total']==536185 and early['verification']['workbooks_reconciled']

def result(r):
    total=sum(int(c['VoteTotal']) for c in r['Choice']);qualified=int(r['VoterCountQualified'])
    full=r['PrecinctsReporting']==r['PrecinctsExpected'] and r['NumAbsenteeReporting']==r['NumAbsenteeExpected']
    return {'votes':total,'qualified':qualified,'turnout_pct':math.floor(total/qualified*1000+.5)/10 if full and qualified>0 else None,'precincts_reporting':int(r['PrecinctsReporting']),'precincts_expected':int(r['PrecinctsExpected']),'complete_early_absentee':r['NumAbsenteeReporting']==r['NumAbsenteeExpected'],'complete_reporting':full}

def e_record(e,s):
    assert e['total']==e['in_person']+e['absentee']==sum(e['breakdowns']['race'].values())==sum(s.values())
    return {'total':e['total'],'in_person':e['in_person'],'absentee':e['absentee'],'race':e['breakdowns']['race'],'sex':s}

bycode={r['ParishValue']:r for r in raw}
parishes=[{'name':title(p['parish'])+' Parish','parish_code':p['parish_code'],'geoid':p['geoid'],'results':result(bycode[p['parish_code']]),'early':e_record(p,sex[p['parish_code']])} for p in early['parishes']]
sex_state={k:sum(r[k] for r in sex.values()) for k in ['male','female','unallocated']}
assert sex_state=={'male':224371,'female':311536,'unallocated':278}
data={'schema_version':1,'release':RELEASE,'election_date':'2026-11-03','results_source':{'url':PORTAL,'payload_url':records['senate_parishes']['url'],'retrieved_at_local':records['senate_parishes']['retrieved_at_local'],'retrieved_label':'November 4, 2026 at 8:28 p.m. Central','status':'Unofficial','source_update_timestamp':None,'method':'Identical to the SOS one seat unofficial turnout calculation: reported contest votes divided by qualified voters, rounded to one decimal place. Not audited all voter participation.'},'early_source':{'url':early['source_url'],'printed_at_local':early['report_printed_at'],'printed_label':'November 4, 2026 at 3:10:08 a.m. Central','status':'Verified workbook snapshot','coverage':'Early and absentee only'},'availability':{'full_election_demographics':False,'audited_participation_available':False,'explanation':'SOS PostElectionStatsAvailable is 0. All_Voted and demographic voted fields are unpopulated zero placeholders, not evidence of zero participation. November 3 audited parish and statewide files are not listed.'},'statewide':{'name':'Louisiana statewide','parish_code':'state','geoid':None,'results':result(state),'early':e_record(early['statewide'],sex_state)},'parishes':parishes}
dump(PROCESSED/'parish_participation_2026-11-03.json',data)
with (PROCESSED/'parish_participation_2026-11-03.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Parish','SOS parish code','Senate contest votes','SOS contest qualified voters','Unofficial contest turnout percent','Precincts reporting','Precincts expected','Early and absentee ballots','Early in person','Absentee','White early ballots','Black early ballots','Other race early ballots','Male early ballots','Female early ballots','Unallocated sex difference','Results source','Early source'])
    for p in parishes:
        r=p['results'];e=p['early'];w.writerow([p['name'],p['parish_code'],r['votes'],r['qualified'],r['turnout_pct'],r['precincts_reporting'],r['precincts_expected'],e['total'],e['in_person'],e['absentee'],*e['race'].values(),*e['sex'].values(),PORTAL,early['source_url']])
manifest['preserved_files']=[{'file':str(f.relative_to(ROOT)),'sha256':sha(f)} for f in DEST.glob('*') if f.name!='manifest.json']
manifest['checks']={'parish_count':64,'votes_reconciled':1466069,'qualified_voters_reconciled':2975695,'early_ballots_reconciled':536185,'sex_unallocated':278,'full_election_demographics_available':False,'historical_records_preserved':True}
dump(DEST/'manifest.json',manifest)

s=BeautifulSoup((ROOT/'index.html').read_text(),'html.parser')
for e in s.select('script[src]'): e.decompose()
for name in ['assets/parish-participation-20261104.js','assets/voting-plan-20261101.js']:
    tag=s.new_tag('script',src=name+'?v='+RELEASE);tag['defer']='';s.head.append(tag)
link=s.new_tag('link',rel='stylesheet',href='assets/parish-participation-20261104.css?v='+RELEASE);s.head.append(link)
s.select_one('meta[name=dashboard-release]')['content']=RELEASE
s.select_one('meta[name=description]')['content']='December 12 Louisiana congressional runoffs, parish participation maps, demographic views and voting plans by Tia Fields, Provisional Consulting LLC.'
s.title.string='Louisiana Runoffs and Parish Participation | Tia Fields'
for id in ['election-results','early-voting','parish-map','polling-research','house-races']:
    e=s.find(id=id)
    if e:e.decompose()
for n in list(s.select('main > noscript')):
    if n.find(id='senate-research'):n.decompose()
for e in s.select('#runoffs .runoff-person p,#runoffs a[href^="#results-"]'):e.decompose()
s.find(id='runoff-title').string='December 12 congressional runoffs'
for e in s.select('#runoffs .results-note'):
    e.string='Districts 5 and 6 advance to a runoff based on complete unofficial SOS returns. Certification remains pending.'
nav=s.select_one('.nav-inner');nav.clear()
order=[('runoffs','Runoffs'),('parish-map','Parish map'),('parish-comparison','Compare parishes'),('registration','Registration'),('voting-plan','Voting plan'),('methodology','Sources')]
for id,label in order:
    a=s.new_tag('a',href='#'+id);a.string=label;nav.append(a)

explorer='''<section id="parish-map" class="section" aria-labelledby="map-title">
<div class="section-heading"><div><p class="eyebrow">NOVEMBER 3 PARTICIPATION</p><h2 id="map-title">Explore your parish</h2></div><span class="badge neutral">All 64 parishes</span></div>
<p class="section-intro">Start with turnout, then explore race, gender or voting method. Each view names exactly which ballots it covers. Select a parish on the map, search its name or use the menu.</p>
<div class="parish-picker"><div><label for="parish-find">Search a parish</label><input id="parish-find" type="search" list="parish-names" placeholder="Start typing a parish name" autocomplete="off" disabled><datalist id="parish-names"></datalist></div><div><label for="parish-select">Select a parish</label><select id="parish-select" disabled><option value="state">Louisiana statewide</option></select></div></div>
<div class="parish-tabs" role="tablist" aria-label="Participation views"><button type="button" id="view-overview" role="tab" aria-selected="true" aria-controls="view-panel" tabindex="0" disabled>Overview</button><button type="button" id="view-race" role="tab" aria-selected="false" aria-controls="view-panel" tabindex="-1" disabled>Race</button><button type="button" id="view-gender" role="tab" aria-selected="false" aria-controls="view-panel" tabindex="-1" disabled>Gender</button><button type="button" id="view-method" role="tab" aria-selected="false" aria-controls="view-panel" tabindex="-1" disabled>Voting method</button></div>
<p class="coverage-banner" id="scope-label">November 3 U.S. Senate contest · provisional parish comparison</p>
<p class="fine" id="view-description">Turnout is provisional. Demographic views cover early and absentee ballots only while full election participation statistics remain unavailable.</p>
<div id="view-panel" role="tabpanel" aria-labelledby="view-overview"><div class="explorer"><div class="map-card"><div class="map-toolbar"><div><label for="map-metric">Map measure</label><select id="map-metric" disabled><option value="rate">Turnout rate</option><option value="count">Contest vote count</option></select></div><div id="group-control" hidden><label id="group-label" for="group-select">Category</label><select id="group-select" disabled></select></div><div class="zoom-controls" aria-label="Map controls"><button type="button" id="zoom-in" aria-label="Zoom in" disabled>+</button><button type="button" id="zoom-out" aria-label="Zoom out" disabled>−</button><button type="button" id="map-reset" disabled>Reset</button></div></div>
<div class="map-frame"><svg id="map-svg" viewBox="0 0 800 660" role="group" aria-labelledby="map-svg-title map-svg-desc"><title id="map-svg-title">Louisiana parish participation map</title><desc id="map-svg-desc">Use the parish menu or focus a parish and press Enter. Colors represent the selected participation measure, not party preference.</desc><defs><pattern id="missing-pattern" width="8" height="8" patternUnits="userSpaceOnUse"><rect width="8" height="8" fill="#f4f4f4"/><path d="M0 8L8 0" stroke="#b0b0b0" stroke-width="2"/></pattern></defs><g id="map-shapes"></g></svg><p id="map-loading" role="status">Loading parish data.</p><p class="map-readout" id="map-readout">Louisiana statewide</p></div>
<div id="map-legend" class="legend" aria-label="Map legend"></div><p class="fine" id="metric-description"></p><p class="fine" id="map-coverage"></p><p class="attribution">Parish boundaries: U.S. Census Bureau, January 2026. Generalized for display. <a href="data/boundary_source.json">Boundary source</a>.</p></div>
<aside class="selection-card"><p class="eyebrow" id="panel-heading">Parish overview</p><h3 id="selection-title">Louisiana statewide</h3><div class="selection-total" id="selected-total">49.3%</div><p class="fine" id="selected-label">SOS unofficial turnout</p><div id="detail-body"></div><p class="fine selected-source" id="selected-source"></p></aside></div></div>
<p class="sr-only" id="selection-status" role="status" aria-live="polite"></p><div class="parish-actions"><button type="button" class="button" id="share-parish" disabled>Share this view</button><button type="button" class="button secondary" id="copy-parish" disabled>Copy parish link</button><button type="button" class="button secondary" id="print-parish" disabled>Print or save PDF</button><button type="button" class="button secondary" id="download-parish" disabled>Download this view CSV</button></div><label class="sr-only" for="share-link">Shareable parish link</label><input id="share-link" readonly hidden><p class="fine" id="export-status" role="status" aria-live="polite"></p>
<noscript><p class="notice">The interactive views need JavaScript. The parish table below and the <a href="data/processed/parish_participation_2026-11-03.csv">full parish CSV</a> remain available. The full demographic counts cover early and absentee ballots, not audited full election participation.</p></noscript>
</section>'''
comparison='''<section id="parish-comparison" class="section" aria-labelledby="compare-title"><div class="section-heading"><div><p class="eyebrow">PARISH COMPARISON</p><h2 id="compare-title">Compare all 64 parishes</h2></div><button type="button" class="button secondary" id="download-data" disabled>Download filtered table CSV</button></div><p class="fine" id="table-scope">November 3 U.S. Senate contest. Denominator: qualified voters in the same contest and parish. All returns remain unofficial.</p><div class="table-tools"><div><label for="parish-search">Filter parish names</label><input id="parish-search" type="search" placeholder="Enter a parish name" disabled></div><div><label for="parish-sort">Sort table</label><select id="parish-sort" disabled><option value="name">Parish name</option><option value="high">Highest selected value</option><option value="low">Lowest selected value</option></select></div><p id="table-count" role="status">64 of 64 parishes</p></div><div class="table-scroll" role="region" tabindex="0" aria-label="Parish comparison table"><table><caption id="table-measure">SOS unofficial turnout</caption><thead><tr><th scope="col">Parish</th><th scope="col">Selected value</th><th scope="col">Count</th><th scope="col">Denominator</th><th scope="col">Coverage</th></tr></thead><tbody id="parish-table">ROWS</tbody></table></div><p class="fine">Use the views above to compare the same measure across parishes. Counts alone do not identify low turnout. Missing values are never treated as zero.</p></section>'''
rows=''.join(f'<tr><th scope="row">{html.escape(p["name"])}</th><td>{p["results"]["turnout_pct"]:.1f}%</td><td>{fmt(p["results"]["votes"])}</td><td>{fmt(p["results"]["qualified"])}</td><td>Complete · unofficial</td></tr>' for p in parishes)
s.find(id='runoffs').insert_after(fragment(explorer+comparison.replace('ROWS',rows)))

# Render registration statically. The obsolete polling/map module is no longer loaded.
reg=load(PROCESSED/'registration_snapshot_2026-11-01.json')
cards=s.find(id='district-cards')
if cards:
    cards.clear()
    for d in reg['districts']:
        cards.append(fragment(f'<article class="district-card"><h3>Congressional District {d["district"]}</h3><strong>{fmt(d["total_registered"])}</strong><p>Registered voters · {d["black_share_pct"]:.2f}% Black registration</p></article>'))
if s.select_one('#registration .eyebrow'):s.select_one('#registration .eyebrow').string='REGISTRATION CONTEXT'
method=s.find(id='methodology');method.clear()
method.append(fragment('''<p class="eyebrow">SOURCES AND ACCOUNTABILITY</p><h2>Know what each view measures</h2><div class="source-cards"><article><h3>Overview</h3><p>Parish comparisons use the same statewide Senate contest. Unofficial turnout equals votes recorded in that contest divided by its qualified voter count, rounded to one decimal place using the SOS method. It is not an audited count of everyone who voted in any race.</p><p><a href="https://voterportal.sos.la.gov/graphical">Official SOS results</a> · <a href="data/sources/20261104_parish/senate_parishes.json">Preserved parish returns</a></p></article><article><h3>Race, gender and method</h3><p>These views cover early and absentee participation through November 3. SOS has not supplied the audited full election demographic participation for this release. Zero placeholders in unavailable participation fields are not displayed as zero turnout. SOS calls its gender columns sex. Any unallocated difference remains unclassified.</p><p><a href="https://electionstatistics.sos.la.gov/default.aspx?Stats=Early_Voting_Statistics&amp;Type=Parish">Official early and absentee reports</a></p></article></div><p><a href="data/processed/parish_participation_2026-11-03.csv">Full parish spreadsheet CSV</a> · <a href="data/processed/parish_participation_2026-11-03.json">Parish data JSON</a> · <a href="docs/PARISH_FOCUS_20261104.md">Methodology and verification</a></p><details><summary>Historical election results, candidate lists and survey research</summary><p>The previous November page is preserved separately. It includes the full candidate returns, District 6 and Senate polls, and original candidate lists. Those records are historical, not the current runoff ballot.</p><p><a href="archive/november-2026/">Open the November research archive</a></p></details><p class="fine">Results source retrieved November 4, 2026 at 8:28 p.m. Central. Early and absentee report printed November 4 at 3:10:08 a.m. Central. Registration remains the verified November 1 snapshot. No demographic category is used to infer candidate choice. No individual voter records are collected.</p>'''))
printout=s.new_tag('div',id='parish-printout');s.body.append(printout)
(ROOT/'index.html').write_text(str(s))
planner=ROOT/'assets/voting-plan-20261101.js';text=planner.read_text()
assert 'main.prepend(section);' in text
text=text.replace('main.prepend(section);',"const registration = document.getElementById('registration');\n  if (registration) registration.after(section); else main.append(section);")
planner.write_text(text)

# Keep the full prior browser suites and run them against the frozen archive.
for name in ['test_dashboard.py','test_senate_research.py']:
    p=ROOT/'tests'/name;t=p.read_text();t=t.replace("url = f'http://127.0.0.1:{server.server_port}/'","url = f'http://127.0.0.1:{server.server_port}/archive/november-2026/'")
    t=t.replace("url=f'http://127.0.0.1:{server.server_port}/'","url=f'http://127.0.0.1:{server.server_port}/archive/november-2026/'")
    p.write_text(t)
workflow=ROOT/'.github/workflows/dashboard-checks.yml'
w=workflow.read_text();w=w.replace('python tests/test_dashboard.py','python tests/test_dashboard.py\n          python tests/test_parish_focus.py');workflow.write_text(w)
notes='''# Parish participation release

The public reading order is runoff announcement, parish map, parish comparison, registration context, voting planner and sources. Senate and District 6 polls, the old candidate lists and detailed November results are removed from the main page and preserved in a self contained November archive. The calculator remains removed.

## Official source coverage

All 64 parishes are joined by SOS parish code and Census GEOID. Parish Senate votes sum to 1,466,069. Their qualified voter denominators sum to 2,975,695 and expected precincts sum to 3,722. Every parish reports complete precinct and early absentee reporting. The map uses the exact SOS one seat contest turnout calculation, rounded to one decimal place. This is provisional contest turnout, not audited unique voter participation in any race. Candidate support is not mapped.

The source was retrieved November 4, 2026 at 8:28 p.m. Central. The source result timestamp is a 1900 placeholder, not a publication time. ResultsOfficial and PostElectionStatsAvailable are both 0. The statewide and parish audited report indexes contain no November 3 report. Demographic voted fields are zero placeholders, not actual zero turnout. These fields are not published as participation.

Race, gender and method views use the independently reconciled early and absentee report through November 3, printed November 4 at 3:10:08 a.m. Central. They total 536,185 ballots. Male 224,371 and female 311,536 leave an unallocated numerical difference of 278. That residual is not assigned a demographic identity. Sex source matrix was extracted using ArtifactTool and checked against the unchanged workbook SHA256.

Demographic percentages are shares of early and absentee ballots, not rates among registered members of each group. Race, sex and voting method are marginal views, not a cross tabulation. Election Day participation is not inferred by subtracting the early participation report from Senate vote totals. Individual voter details are not collected.

## Features and preservation

Neutral map scale, explicit missing data style, keyboard parish selection, searchable parish menu, four synchronized views, count and rate/share controls, sortable parish table, source scoped CSV, print or save PDF, and shareable parish view URLs. The selected parish, view, category and measure are stored only in the URL, not browser storage. Race and sex labels follow the source without inferring sensitive traits about individuals.

The December 12 planner remains after registration and before sources. Polls are 7 a.m. to 8 p.m. Central, verified against the SOS calendar. November source data, registration records, polls and backup branch are unchanged. Archive scripts, datasets and styles are frozen copies of the previous release.

Primary sources: https://voterportal.sos.la.gov/graphical and https://www.sos.la.gov/elections-voting/election-dates . Machine readable source manifest: data/sources/20261104_parish/manifest.json .
'''
(ROOT/'docs/PARISH_FOCUS_20261104.md').write_text(notes)
print(json.dumps(manifest['checks'],indent=2))
