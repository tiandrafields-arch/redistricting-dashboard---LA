"""Build the reviewed November 4 release from preserved official SOS evidence.

Run with two already downloaded GitHub evidence artifacts in source-input/early
and source-input/latest. Never fetch third party results or overwrite historical
snapshots. This script does not commit, push, or change account settings.
"""
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from datetime import datetime
from zoneinfo import ZoneInfo
import copy, csv, hashlib, html, json, re
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
EARLY = ROOT / 'source-input/early'
LATEST = ROOT / 'source-input/latest'
DEST = ROOT / 'data/sources/20261104'
DEST.mkdir(parents=True, exist_ok=True)
P = ROOT / 'data/processed'
N = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
RELEASE = '20261104-results1'
NOW = datetime.now(ZoneInfo('America/Chicago')).isoformat()
PORTAL = 'https://voterportal.sos.la.gov/graphical'
DATES = 'https://www.sos.la.gov/elections-voting/election-dates'
RULES = 'https://www.sos.la.gov/elections-voting/how-candidates-are-elected'
EARLY_FILE = 'early_voting_2026-11-03.json'
REG_FILE = 'registration_snapshot_2026-11-01.json'
RESULTS_FILE = 'election_results_2026-11-03.json'
manifest = {'release': RELEASE, 'built_at_local': NOW, 'source_files': [], 'checks': {}}

def dump(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')

def preserve(folder, filename, expected, target=None, url=None):
    path=folder/filename
    body=path.read_bytes()
    assert hashlib.sha256(body).hexdigest()==expected, 'Evidence hash changed: '+filename
    name=target or filename
    (DEST/name).write_bytes(body)
    manifest['source_files'].append({'file':str((DEST/name).relative_to(ROOT)), 'sha256':expected, 'url':url})
    return path

def sheets(path):
    with ZipFile(path) as z:
        ss=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            ss=[''.join(t.text or '' for t in si.iter('{'+N['s']+'}t')) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',N)]
        out={}
        for name in sorted(n for n in z.namelist() if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',n)):
            rows=[]
            for row in ET.fromstring(z.read(name)).findall('s:sheetData/s:row',N):
                d={}
                for cell in row.findall('s:c',N):
                    elem=cell.find('s:v',N); val=elem.text if elem is not None else None
                    if cell.get('t')=='s': val=ss[int(val)] if val is not None else None
                    elif cell.get('t')=='inlineStr': val=''.join(t.text or '' for t in cell.iter('{'+N['s']+'}t'))
                    elif val is not None:
                        try:
                            val=float(val); val=int(val) if val.is_integer() else val
                        except ValueError: pass
                    if val is not None: d[re.sub(r'\d','',cell.get('r'))]=val
                if d: rows.append(d)
            out[name]=rows
        return out

def replace_required(text, old, new):
    assert old in text, 'Expected text not found: '+old[:100]
    return text.replace(old,new)

# Preserve exact public evidence, not unrelated browsing responses or identifiers.
em=json.loads((EARLY/'manifest.json').read_text())
lm=json.loads((LATEST/'manifest.json').read_text())
for m in (em,lm):
    assert all(p.get('status')==200 for p in m['pages']), 'Incomplete source review'
source_time=next(p['retrieved_at_local'] for p in lm['pages'] if p['key']=='graphical')
for label,filename,sha in [('candidates','response_003.json','71d09488b6e02028305f386d9fc81ce9850c784ead840322430fff58f625f08a'),('votes','response_004.json','6d1d3bee6647da11f687aa7695d4d8e802a118943ff88b3f0aac03baa937cc6b')]:
    record=next(r for r in lm['responses'] if r.get('file')==filename)
    preserve(LATEST,filename,sha,'sos_'+label+'.json',record['url'])
for filename in ['graphical.txt','graphical.png','post_statewide.txt','post_parish.txt','registration_statewide.txt','registration_parish.txt']:
    body=(LATEST/filename).read_bytes(); (DEST/filename).write_bytes(body)
    manifest['source_files'].append({'file':str((DEST/filename).relative_to(ROOT)),'sha256':hashlib.sha256(body).hexdigest()})
for m,folder,names in [(em,EARLY,['early_statewide_2026_1103_StatewideStats.xlsx','early_parish_2026_1103_ParishStats.xlsx']),(lm,LATEST,['registration_statewide_2026_1101_sta_comb.xlsx'])]:
    for name in names:
        record=next(r for r in m['downloads'] if r.get('file')==name)
        preserve(folder,name,record['sha256'],url=record['url'])

# Candidate totals join on official race and choice IDs. Percentages come from
# the rendered SOS display and are checked against its raw count payload.
raw_meta=json.loads((DEST/'sos_candidates.json').read_text())
raw_votes=json.loads((DEST/'sos_votes.json').read_text())
metas=raw_meta['Races']['Race']; votes={r['ID']:r for r in raw_votes['Races']['Race']}
text=(LATEST/'graphical.txt').read_text()
selected=[r for r in metas if r.get('OfficeLevel') in ['140','145'] and ('Senator' in r['SpecificTitle'] or 'Congressional District' in r['SpecificTitle'])]
# Some SOS exports encode the Senate office level differently. The exact known
# public contest title and six House titles remain the definitive selection.
selected=[r for r in metas if r['SpecificTitle']=='U. S. Senator' or 'Congressional District' in r['SpecificTitle']]
assert len(selected)==7
races=[]
for i,m in enumerate(selected):
    v=votes[m['ID']]
    title=m['SpecificTitle']; district=None if title=='U. S. Senator' else int(re.search(r'(\d+)(?:st|nd|rd|th) Congressional',title).group(1))
    block=text.split(title,1)[1].split('U. S. Representative',1)[0]
    if district is None: block=block.split('U. S. Representative',1)[0]
    total=sum(int(c['VoteTotal']) for c in v['Choice'])
    displayed_total=int(re.search(r'Total:\s*([\d,]+)',block).group(1).replace(',',''))
    assert total==displayed_total
    turnout=re.search(r'Unofficial Turnout:\s*([\d.]+%)',block).group(1)
    counts={c['ID']:int(c['VoteTotal']) for c in v['Choice']}
    candidates=[]
    for c in m['Choice']:
        desc=c['Desc']; match=re.search(re.escape(desc)+r'\s*(\d+%)',block)
        assert match, 'Candidate not found in rendered evidence: '+desc
        part=re.search(r'\(([^)]+)\)$',desc).group(1)
        name=re.sub(r'\s*\([^)]+\)$','',desc)
        candidates.append({'id':c['ID'],'name':name,'party':part,'votes':counts[c['ID']],'sos_percentage':match.group(1)})
    complete=int(v['PrecinctsReporting'])==int(v['PrecinctsExpected']) and int(v['NumAbsenteeReporting'])==int(v['NumAbsenteeExpected'])
    ordered=sorted(candidates,key=lambda c:c['votes'],reverse=True)
    runoff=bool(district is not None and complete and ordered[0]['votes']*2<=total)
    if runoff: assert ordered[1]['votes']>ordered[2]['votes'], 'Tie requires separate legal review'
    races.append({'id':m['ID'],'district':district,'label':'U.S. Senate' if district is None else 'House District '+str(district),'candidate_total':total,'sos_unofficial_turnout':turnout,'precincts_reporting':int(v['PrecinctsReporting']),'precincts_expected':int(v['PrecinctsExpected']),'early_absentee_parishes_reporting':int(v['NumAbsenteeReporting']),'early_absentee_parishes_expected':int(v['NumAbsenteeExpected']),'sos_qualified_voters':int(v['VoterCountQualified']),'complete_reporting':complete,'status':'unofficial','runoff_based_on_complete_unofficial_returns':runoff,'runoff_candidates':[c['id'] for c in ordered[:2]] if runoff else [],'candidates':candidates})
assert [r['district'] for r in races]==[None,1,2,3,4,5,6]
assert [r['district'] for r in races if r['runoff_based_on_complete_unofficial_returns']]==[5,6]
results={'schema_version':1,'election_date':'2026-11-03','retrieved_at_local':source_time,'timezone':'America/Chicago','source_url':PORTAL,'source_status':'Unofficial Results','certified':False,'source_update_timestamp':None,'source_timestamp_note':'The source returns a 1900 placeholder timestamp. Actual retrieval time is shown; no source update time is invented.','turnout_note':'Rates are copied from the SOS Unofficial Turnout display. Contest votes are not a unique statewide voter count and are not summed across races. The monthly registration snapshot is not substituted for the SOS contest denominator.','percent_note':'SOS displays whole candidate percentages. Rounding may prevent their sum from equaling 100.','races':races,'runoff_election':{'date':'2026-12-12','polls_open':'07:00','polls_close':'20:00','timezone':'America/Chicago','early_start':'2026-11-28','early_end':'2026-12-05','early_excluded':['2026-11-29'],'early_hours':'8:30 a.m. to 6 p.m.','registration_mail_inperson':'2026-11-12','registration_online':'2026-11-21','ordinary_absentee_request':'2026-12-08T16:30:00-06:00','ordinary_absentee_receipt':'2026-12-11T16:30:00-06:00','calendar_source':DATES,'rules_source':RULES,'reviewed':'2026-11-04'},'audited_postelection_statistics':{'available_at_review':False,'scope':'The official statewide and parish 2026 indexes did not list November 3 at the recorded retrieval time.'}}
dump(P/RESULTS_FILE,results)
manifest['checks']['candidate_sums_and_displayed_totals']='All seven match; 41 candidates'

# Reconcile the full early/absentee workbooks, including every detailed row.
sw=sheets(DEST/'early_statewide_2026_1103_StatewideStats.xlsx')['xl/worksheets/sheet1.xml']
parish_rows={r['A'].rsplit('-',1)[1]:r for r in sw if isinstance(r.get('D'),int) and r['A']!='STATE TOTAL'}
state=next(r for r in sw if r.get('A')=='STATE TOTAL')
assert len(parish_rows)==64
for col in 'DEFGHIJKLMNOPQRS': assert sum(r[col] for r in parish_rows.values())==state[col]
detail_count=0; checked=set()
for name,rows in sheets(DEST/'early_parish_2026_1103_ParishStats.xlsx').items():
    labels=[r['A'] for r in rows if isinstance(r.get('A'),str) and '-' in r['A'] and r['A'].rsplit('-',1)[-1] in parish_rows]
    if not labels:
        grand=next(r for r in rows if r.get('A')=='Total')
        for a,b in zip('DEFGHIJKLMNOPQRS','JKLMNOPQRSTUVWXY'): assert state[a]==grand[b]
        continue
    assert len(labels)==1
    code=labels[0].rsplit('-',1)[1]; checked.add(code)
    details=[r for r in rows if isinstance(r.get('J'),int) and r.get('A')!='SUM']
    subtotal=next(r for r in rows if r.get('A')=='SUM')
    for a,b in zip('DEFGHIJKLMNOPQRS','JKLMNOPQRSTUVWXY'):
        assert sum(r[b] for r in details)==subtotal[b]==parish_rows[code][a], (name,a)
    for r in details:
        assert r['J']==r['V']+r['W']==sum(r[c] for c in 'KLM')==sum(r[c] for c in 'PQRS')
    detail_count+=len(details)
assert len(checked)==64
old=json.loads((P/'early_voting_2026.json').read_text())
def early_record(r):
    assert r['D']==r['P']+r['Q']==sum(r[c] for c in 'EFG')==sum(r[c] for c in 'JKLM')
    return {'total':r['D'],'in_person':r['P'],'absentee':r['Q'],'breakdowns':{'party':dict(zip(['democratic','republican','no_party','other'],[r[c] for c in 'JKLM'])),'race':dict(zip(['white','black','other'],[r[c] for c in 'EFG']))}}
early={'schema_version':2,'status':'verified_snapshot','election_date':'2026-11-03','reporting_period_end':'2026-11-03','report_printed_at':'2026-11-04T03:10:08-06:00','report_printed_at_local':'2026-11-04 03:10:08','report_printed_timezone':'America/Chicago','display_timezone_label':'Central Time','verified_at_local':NOW,'source_url':'https://electionstatistics.sos.la.gov/default.aspx?Stats=Early_Voting_Statistics&Type=Parish','source_files':[x for x in manifest['source_files'] if 'Early' in x.get('url','')],'verification':{'parishes':64,'detail_rows_checked':detail_count,'workbooks_reconciled':True,'geography_matches':64,'reported_sex_gap':state['D']-state['H']-state['I']},'scope_note':'November 3 election early and absentee participation through November 3. Not total Election Day participation or audited final turnout.','statewide':early_record(state),'parishes':[]}
for p in old['parishes']:
    r=parish_rows[p['parish_code']]
    assert r['A'].rsplit('-',1)[0]==p['parish']
    early['parishes'].append({k:p[k] for k in ['parish_code','geoid','parish']}|early_record(r))
assert early['statewide']['total']==536185 and detail_count==6314
dump(P/EARLY_FILE,early)
with (P/'early_voting_parishes_2026-11-03.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f); w.writerow(['parish_code','geoid','parish','total','in_person','absentee','democratic','republican','no_party','other_party','white','black','other_race'])
    for r in early['parishes']: w.writerow([r[k] for k in ['parish_code','geoid','parish','total','in_person','absentee']]+list(r['breakdowns']['party'].values())+list(r['breakdowns']['race'].values()))
manifest['checks']['early_workbooks']={'parishes':64,'detail_rows':detail_count,'total':536185,'sex_residual':278}

# November registration: use the explicit Congress summaries and reconcile their
# parish components. The previous October files remain unchanged.
reg_sheets=sheets(DEST/'registration_statewide_2026_1101_sta_comb.xlsx')
reg_rows=reg_sheets['xl/worksheets/sheet3.xml']
assert any('Status Both AND Office Congress' in str(r.get('A')) for r in reg_rows)
ds=[r for r in reg_rows if str(r.get('B','')).isdigit() and isinstance(r.get('C'),int)]
rt=next(r for r in reg_rows if r.get('B')=='Overall Total')
assert len(ds)==6 and rt['C']==2984520
for col in 'CDEFGHIJKLMNOPQRSTUV': assert sum(r[col] for r in ds)==rt[col]
details=[r for r in reg_sheets['xl/worksheets/sheet4.xml'] if isinstance(r.get('C'),int) and str(r.get('A','')).strip().isdigit()]
for r in ds+[rt]:
    assert r['C']==sum(r[c] for c in 'DEF')==sum(r[c] for c in 'GKOS')
    for total,parts in [('G','HIJ'),('K','LMN'),('O','PQR'),('S','TUV')]: assert r[total]==sum(r[c] for c in parts)
for d in ds:
    group=[r for r in details if str(r['A']).strip()==d['B']]
    for col in 'CDEFGHIJKLMNOPQRSTUV': assert sum(r[col] for r in group)==d[col]
def registration_record(r):
    keys=['total_registered','white_registered','black_registered','other_race_registered','democratic','republican','no_party','other_parties']
    out=dict(zip(keys,[r[c] for c in 'CDEFGKOS']))
    for key,col in [('black','E'),('democratic','G'),('republican','K'),('no_party','O')]: out[key+'_share_pct']=round(100*r[col]/r['C'],2)
    return out
registration={'metadata':{'source':'Louisiana Secretary of State Registered Voters by Party and Race','report_date':'2026-11-01','status':'Both','source_url':next(x['url'] for x in manifest['source_files'] if 'Registration' in x.get('url','')),'retrieved_at_local':lm['retrieved_at_local'],'qa':'Six congressional summaries and their parish components reconcile to statewide party and race controls.','registration_note':'Monthly registration, not Census voting age population, candidate support, or the election results portal turnout denominator.'},'statewide':registration_record(rt),'districts':[{'district':int(r['B'])}|registration_record(r) for r in ds],'derived':{'black_registered_outside_district_2':rt['E']-ds[1]['E'],'pct_black_registered_outside_district_2':round(100*(rt['E']-ds[1]['E'])/rt['E'],2)}}
dump(P/REG_FILE,registration)
for key,filename,rows in [('districts','registration_districts_2026-11-01.csv',registration['districts']),('statewide','registration_statewide_2026-11-01.csv',[registration['statewide']])]:
    with (P/filename).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
manifest['checks']['registration']={'statewide':2984520,'districts':6,'black_registered':936512,'outside_district_2':635050,'outside_district_2_pct':67.81}

# Static results are available without JavaScript and do not depend on live SOS
# cross origin requests. Existing interactive exploration remains intact.
E=lambda s:html.escape(str(s),quote=True)
F=lambda n:f'{n:,}'
parties={'DEM':'Democrat','REP':'Republican','NOPTY':'No Party','LBT':'Libertarian'}
runoff_cards=[]
for r in [r for r in races if r['district'] in [5,6]]:
    cs=sorted([c for c in r['candidates'] if c['id'] in r['runoff_candidates']],key=lambda c:c['votes'],reverse=True)
    runoff_cards.append('<article class="runoff-card"><p class="eyebrow">U.S. HOUSE</p><h2>District '+str(r['district'])+'</h2>'+''.join('<div class="runoff-person"><strong>'+E(c['name'])+'</strong><span>'+parties[c['party']]+'</span><p>'+F(c['votes'])+' November votes <span class="fine">· SOS '+c['sos_percentage']+'</span></p></div>' for c in cs)+'<a href="#results-district-'+str(r['district'])+'">Review the full November result</a></article>')
runoff_html='''<section id="runoffs" class="runoff-overview" aria-labelledby="runoff-title"><p class="eyebrow">LOUISIANA CONGRESSIONAL VOTER &amp; PARTICIPATION DASHBOARD</p><h1 id="runoff-title">Next: December 12 runoffs</h1><p class="runoff-lead">Saturday, December 12, 2026 · Polls open 7 a.m. to 8 p.m. Central Time.</p><div class="runoff-grid">'''+''.join(runoff_cards)+'''</div><p class="results-note">Pairings are based on complete unofficial SOS returns and the House majority rule. These results are not certified. Whole percentages are rounded by SOS; exact vote totals determine rank.</p><div class="runoff-actions"><a class="button" href="#voting-plan">Make my December voting plan</a><a class="button secondary" href="https://voterportal.sos.la.gov/Home/VoterLogin" target="_blank" rel="noopener noreferrer">Check my district and ballot</a></div><details class="runoff-dates"><summary>Registration, early voting and absentee deadlines</summary><div class="deadline-grid"><p><strong>Register in person or by mail</strong>November 12</p><p><strong>Register online</strong>November 21</p><p><strong>Early voting</strong>November 28 through December 5<br>Except November 29 · 8:30 a.m. to 6 p.m.</p><p><strong>Ordinary absentee request</strong>December 8 by 4:30 p.m.</p><p><strong>Ordinary absentee receipt</strong>December 11 by 4:30 p.m.</p><p><strong>Election Day</strong>December 12 · 7 a.m. to 8 p.m.</p></div><p class="fine">All times Central. Military and overseas exceptions apply. Check the official calendar for the rules that apply to you.</p></details><p class="fine">House runoffs are in Districts 5 and 6. Other local contests may appear on your ballot. A parish selection does not establish your congressional district or whether you have a December contest.</p><div class="resource-row"><a href="'''+DATES+'''">Official election calendar</a><a href="'''+RULES+'''">Official House election rules</a><a href="'''+PORTAL+'''">SOS results</a></div></section>'''
turnout_cards=[]; full_cards=[]
for r in races:
    suffix='senate' if r['district'] is None else 'district-'+str(r['district'])
    turnout_cards.append('<a class="turnout-card" href="#results-'+suffix+'"><span>'+r['label']+'</span><strong>'+r['sos_unofficial_turnout']+'</strong><span>SOS unofficial turnout</span><div class="turnout-track" aria-hidden="true"><i style="width:'+r['sos_unofficial_turnout']+'"></i></div><small>'+F(r['candidate_total'])+' contest votes</small></a>')
    rows=''.join('<tr><th scope="row">'+E(c['name'])+'</th><td>'+parties[c['party']]+'</td><td>'+F(c['votes'])+'</td><td>'+c['sos_percentage']+'</td></tr>' for c in sorted(r['candidates'],key=lambda c:c['votes'],reverse=True))
    status='Runoff pairings shown above' if r['runoff_based_on_complete_unofficial_returns'] else 'Complete reporting · Unofficial'
    full_cards.append('<details class="race-result" id="results-'+suffix+'"><summary>'+r['label']+' <span>'+F(r['candidate_total'])+' votes · '+r['sos_unofficial_turnout']+' turnout</span></summary><p>'+status+'</p><p class="fine">Election Day: '+F(r['precincts_reporting'])+' of '+F(r['precincts_expected'])+' precincts. Early and absentee: '+str(r['early_absentee_parishes_reporting'])+' of '+str(r['early_absentee_parishes_expected'])+' parishes.</p><div class="result-table-wrap" tabindex="0" role="region" aria-label="'+r['label']+' candidate results"><table><caption>'+r['label']+' · November 3, 2026 · Unofficial SOS returns</caption><thead><tr><th scope="col">Candidate</th><th scope="col">Party</th><th scope="col">Votes</th><th scope="col">SOS share</th></tr></thead><tbody>'+rows+'</tbody></table></div></details>')
retrieved=datetime.fromisoformat(source_time).strftime('%B %-d, %Y at %-I:%M %p')+' Central'
results_html='<section id="election-results" class="section" aria-labelledby="results-title"><div class="section-heading"><div><p class="eyebrow">CURRENT SOS RETURNS</p><h2 id="results-title">November 3 results and turnout</h2></div><span class="badge">Unofficial · Not certified</span></div><p>Retrieved '+retrieved+'. All seven congressional contests report all expected precincts and early and absentee parishes.</p><div class="turnout-grid">'+''.join(turnout_cards)+'</div><p class="results-note">These are the turnout rates displayed by SOS for each contest. Candidate vote totals are not a count of unique voters across races. Do not add Senate and House totals together. Monthly registration figures below are a separate dataset.</p><h3>Explore every congressional result</h3>'+''.join(full_cards)+'<p class="fine">SOS reports candidate shares as whole percentages, so rounded shares may not total 100. A source update timestamp was not available; the retrieval time above is recorded instead. Complete reporting does not mean certification.</p><p class="fine">Audited November 3 statewide and parish participation reports were not listed in the official postelection indexes at this review. The map below shows early and absentee ballots, not full election turnout.</p><div class="resource-row"><a href="'+PORTAL+'">Official results portal</a><a href="data/processed/'+RESULTS_FILE+'">Download results JSON</a><a href="data/processed/election_results_2026-11-03.csv">Download candidate results CSV</a><a href="docs/RESULTS_RELEASE_20261104.md">Source records and limitations</a></div></section>'
with (P/'election_results_2026-11-03.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['contest','candidate','party','votes','sos_share','sos_unofficial_turnout','precincts_reporting','precincts_expected','status','retrieved_at','source'])
    for r in races:
        for c in r['candidates']:w.writerow([r['label'],c['name'],c['party'],c['votes'],c['sos_percentage'],r['sos_unofficial_turnout'],r['precincts_reporting'],r['precincts_expected'],'unofficial',source_time,PORTAL])

index=ROOT/'index.html'; original=index.read_text(); soup=BeautifulSoup(original,'html.parser')
assert not soup.select_one('#runoffs'), 'Release already applied'
main=soup.select_one('#main'); main.insert(0,BeautifulSoup(runoff_html+results_html,'html.parser'))
soup.title.string='Louisiana Election Results and Runoffs | Tia Fields'
soup.select_one('meta[name="description"]')['content']='Louisiana congressional results, SOS unofficial turnout, December 12 runoff information, parish participation and voting plans by Tia Fields, Provisional Consulting LLC.'
soup.select_one('meta[name="dashboard-release"]')['content']=RELEASE
soup.head.append(BeautifulSoup('<link rel="stylesheet" href="assets/results-20261104.css?v='+RELEASE+'">','html.parser'))
for item in soup.select('script[src]'): item['src']=item['src'].split('?')[0]+'?v='+RELEASE
soup.select_one('#page-title').name='h2';soup.select_one('#page-title').string='Early and absentee voting statistics'
soup.select_one('#early-voting .updated').clear();soup.select_one('#early-voting .updated').append(BeautifulSoup('Data updated November 4, 2026 · Central Time<br><span>November election participation through November 3</span>','html.parser'))
soup.select_one('#ev-total').string=F(state['D']);soup.select_one('#ev-inperson').string=F(state['P']);soup.select_one('#ev-absentee').string=F(state['Q'])
soup.select_one('#inperson-share').string=f"{100*state['P']/state['D']:.1f}% of reported ballots";soup.select_one('#absentee-share').string=f"{100*state['Q']/state['D']:.1f}% of reported ballots"
soup.select_one('#data-status').string='Verified November 4 workbook snapshot. All 64 parishes reconcile across both workbooks. These early and absentee ballots are not total Election Day turnout or certified results.'
soup.select_one('.snapshot-line span').string='SOS report printed November 4 at 3:10:08 a.m. Central Time.'
soup.select_one('#map-title').string='Early and absentee ballots by parish'
soup.select_one('#selected-total').string=F(state['D']);soup.select_one('#selected-inperson').string=F(state['P']);soup.select_one('#selected-absentee').string=F(state['Q'])
soup.select_one('#parish-map table caption').string='Parish early and absentee participation through November 3, 2026'
soup.select_one('.mini-heading h4').string='Who voted early or absentee'
soup.select_one('#polling-research .section-intro').insert(0,'Historical research before the November 3 election. Actual returns appear above. ')
soup.select_one('#house-races .section-intro').insert(0,'Historical November 1 ballot snapshot. Actual November results appear above. ')
soup.select_one('#registration .badge').string='November 1, 2026'
soup.select_one('#registration .section-intro').clear();soup.select_one('#registration .section-intro').append(BeautifulSoup('The verified SOS monthly snapshot contains <strong>2,984,520 registered voters</strong> across six congressional districts. It uses the same Status Both definition as October, a net increase of 6,377. Registration is not votes cast or the denominator substituted for SOS turnout.','html.parser'))
soup.select_one('#registration details .fine').string='The November congressional subtotals put 635,050 of 936,512 Black registrants outside District 2, or 67.81%. The October finding was 67.79%. This is a registration finding, not candidate support or a turnout rate.'
# Preserve source history while changing the current display to dated records.
for a in soup.select('a[href]'):
    if a['href']=='data/processed/early_voting_2026.json':a['href']='data/processed/'+EARLY_FILE
    if a['href']=='docs/REGISTRATION_UPDATE_2026-10-01.md':a['href']='docs/RESULTS_RELEASE_20261104.md'
source_articles=soup.select('#methodology .methods-grid article')
source_articles[0].select_one('p').string='Louisiana Secretary of State early voting workbooks downloaded November 4 cover the November election through November 3. Both workbooks and their checksums are preserved. Their print footer is November 4, 2026, 3:10:08 a.m. Central Time.'
source_articles[1].select_one('p').string='All 64 parish totals and 6,314 detailed rows reconcile across both workbooks. Voting method, race and party totals match. Reported male and female counts leave a residual of 278, which is not assigned a gender.'
source_articles[1].select_one('a')['href']='docs/RESULTS_RELEASE_20261104.md'
for p in soup.select('#methodology > p.fine'):
    if 'Only one reporting cutoff' in p.get_text():p.string='October 27 and November 3 participation snapshots are preserved separately. Snapshot differences are administrative revisions, not a daily voting series. The parish map shows early and absentee counts or shares, not full election turnout.'
extra='<p class="fine">Current result, registration and early voting records have distinct source dates. No district boundaries or legal status findings were changed by this release.</p><div class="resource-row"><a href="data/sources/20261104/source_manifest.json">Source checksums and verification</a><a href="data/processed/registration_snapshot_2026-11-01.json">November registration JSON</a><a href="data/processed/early_voting_2026.json">October 27 historical participation</a><a href="data/processed/registration_snapshot_2026-10-01.json">October registration archive</a></div>'
soup.select_one('#methodology').append(BeautifulSoup(extra,'html.parser'))
for span in soup.select('.footer-base span'):
    if 'Release ' in span.get_text():span.string='Release 20261104.results.1'
for ns in soup.select('noscript'):
    if ns.select_one('#voting-plan'):
        ns.string=None if False else ns.string
        # Replace only this planner fallback, not historical Senate dates.
        raw=str(ns).replace('Tuesday, November 3, 2026','Saturday, December 12, 2026').replace('6 a.m. to 8 p.m.','7 a.m. to 8 p.m.')
        ns.replace_with(BeautifulSoup(raw,'html.parser'))
nav=soup.select_one('.nav-inner');nav.insert(0,BeautifulSoup('<a href="#runoffs">Runoffs</a><a href="#election-results">Results and turnout</a>','html.parser'))
index.write_text(str(soup),encoding='utf-8')

# Adapt existing modules rather than adding competing fetches or hiding errors.
core=ROOT/'assets/dashboard-v20261028.js';js=core.read_text()
js=replace_required(js,"2026-10-27","2026-11-03").replace('October 27','November 3').replace('early_voting_2026.json',EARLY_FILE).replace('20261027.csv','20261103.csv').replace('registration_snapshot_2026-10-01.json',REG_FILE)
js=replace_required(js,"===2978143,'Registration control mismatch'","===d.statewide.total_registered,'Registration control mismatch'")
js=js.replace('Who has voted so far','Who voted early or absentee').replace("const V='20261101-education-v1'","const V='20261104-results-v1'")
core.write_text(js)
planner=ROOT/'assets/voting-plan-20261101.js';js=planner.read_text()
js=replace_required(js,"const reviewed = 'November 1, 2026'","const reviewed = 'November 4, 2026'")
js=replace_required(js,"const election = 'Tuesday, November 3, 2026'","const election = 'Saturday, December 12, 2026'")
js=replace_required(js,"const hours = '6 a.m. to 8 p.m. Central Time'","const hours = '7 a.m. to 8 p.m. Central Time'")
js=js.replace('2026-11-04T02:00:00Z','2026-12-13T02:00:00Z').replace('archive for November 3, 2026','archive for December 12, 2026').replace('the November 3, 2026 election has passed','the December 12, 2026 election has passed').replace('_Voting_Plan_20261103.csv','_Voting_Plan_20261212.csv')
js=js.replace('early_voting_2026.json',EARLY_FILE)
js=replace_required(js,"$('vp-rta').hidden = code !== '36';","$('vp-rta').hidden = true;")
js=re.sub(r'<p id="vp-rta" hidden>.*?</p>', '<p id="vp-rta" hidden></p>',js)
js=replace_required(js,'The linked ride page contains older notices alongside current information. Use the SOS hours above for November 3. Provider information reviewed ${reviewed}; RTA announcement dated October 23, 2026. This dashboard does not book rides or promise availability.','No December transportation service or no fare offer has been verified for this planner. Prior November offers are not evidence of December availability. Contact providers directly. This dashboard does not book rides or promise availability.')
js=re.sub(r"\$\{code === '36' \? '<p>New Orleans RTA announced.*?</p>' : '<p>No dedicated parish transportation provider.*?</p>'\}",'<p>No December transportation service has been verified in this packet. Confirm local availability directly before offering a ride.</p>',js)
js=re.sub(r"\$\{code === '36' \? '<br>RTA source: ' \+ link\(URLS.rta, URLS.rta\) : ''\}",'',js)
js=re.sub(r"^\s*if \(p.code === '36'\) rows.push\(.*?;\n",'\n',js,flags=re.M)
js=replace_required(js,'${Number(row.total).toLocaleString(\'en-US\')} reported early ballots through ${date}.','Historical November election: ${Number(row.total).toLocaleString(\'en-US\')} reported early ballots through ${date}.')
js=replace_required(js,'A parish selection does not establish anyone\'s precinct.','House runoffs are in Districts 5 and 6. Other local contests may appear on a voter\'s ballot. Confirm that each person has a December 12 contest and verify their assignment. A parish selection does not establish anyone\'s precinct.')
js=replace_required(js,'Use your assigned Election Day polling place, not simply the nearest location. Official lookup opens on the Louisiana Secretary of State website.','Confirm your December 12 ballot and assigned polling place, not simply the nearest location. House runoffs are in Districts 5 and 6; other local contests may appear on your ballot. Official lookup opens on the Louisiana Secretary of State website.')
js=replace_required(js,'I confirmed this is my assigned Election Day polling place using GeauxVote or my registrar.','I confirmed my December 12 ballot and assigned polling place using GeauxVote or my registrar.')
js=re.sub(r'<details class="vp-rule"><summary>How this congressional election works</summary>.*?</details>', '<details class="vp-rule"><summary>December election information</summary><p>Saturday, December 12, 2026. Polls are open 7 a.m. to 8 p.m. Central Time. House runoffs are in Districts 5 and 6. Check your December sample ballot for congressional and any local contests.</p><p>Register in person or by mail by November 12, or online by November 21. Early voting runs November 28 through December 5, excluding November 29, from 8:30 a.m. to 6 p.m. Ordinary absentee request deadline: December 8 at 4:30 p.m. Ordinary receipt deadline: December 11 at 4:30 p.m. Military and overseas exceptions apply.</p><div class="vp-source-links">${link(URLS.dates, \'Official election calendar\')}${link(URLS.rules, \'Official election rules\')}</div></details>',js,flags=re.S)
# Prevent the planner from changing the historical map heading back.
js=js.replace("composition.textContent = 'Who has voted so far'","composition.textContent = 'Who voted early or absentee'")
assert 'RTA announced no fares' not in js and 'No fares on RTA' not in js
planner.write_text(js)
education=ROOT/'assets/voter-education-20261101.js';js=education.read_text()
js=replace_required(js,"const order = [","const order = [\n    ['runoffs', 'Runoffs'],\n    ['election-results', 'Results and turnout'],")
js=js.replace("['early-voting', 'Voting statistics']","['early-voting', 'Early ballot statistics']")
education.write_text(js)

# Update existing regression expectations to the newly dated sources, retaining
# the original map, export, keyboard, injection and privacy checks.
test=ROOT/'tests/test_dashboard.py';t=test.read_text()
t=t.replace("order = ['early-voting'","order = ['runoffs', 'election-results', 'early-voting'")
t=t.replace("== 'Louisiana voting statistics'","== 'Early and absentee voting statistics'").replace("== 'Voting statistics'","== 'Early ballot statistics'")
t=t.replace("== 'Who has voted so far'","== 'Who voted early or absentee'")
t=t.replace('early_voting_2026.json',EARLY_FILE)
for old_count,code in [('53,645','17'),('47,645','36'),('26,858','28')]:
    new_count=next(r['total'] for r in early['parishes'] if r['parish_code']==code);t=t.replace(old_count,F(new_count))
t=t.replace('520,942','536,185')
t=t.replace("assert page.locator('#vp-rta').is_visible()","assert page.locator('#vp-rta').is_hidden()")
t=t.replace("assert 'RTA announced no fares' in page.locator('#vp-org-preview').inner_text()","assert 'No December transportation service has been verified' in page.locator('#vp-org-preview').inner_text()")
t=t.replace("first.get_attribute('id') == 'early-voting'","first.get_attribute('id') == 'runoffs'")
test.write_text(t)

# Clear source notes, historical preservation and a machine readable audit trail.
notes='''# November 4 results and runoff release

This release publishes the December 12 House runoffs first, followed by the November 3 congressional returns and SOS unofficial turnout. Results remain unofficial even with all expected precincts reporting. Candidate vote shares are the whole percentages shown by SOS. Totals are not summed across overlapping Senate and House contests.

## Evidence and retrieval

Results were retrieved at SOURCE_TIME from https://voterportal.sos.la.gov/graphical and checked against the official candidate and vote payloads preserved under data/sources/20261104. The source result timestamp is a 1900 placeholder, so no publication timestamp is inferred. The two leading candidates in Districts 5 and 6 advance under the open primary majority rule based on complete unofficial returns. This is not a certification claim.

Official rules: https://www.sos.la.gov/elections-voting/how-candidates-are-elected
Official calendar: https://www.sos.la.gov/elections-voting/election-dates

December 12 polls: 7 a.m. to 8 p.m. Central. Registration: November 12 in person or by mail, November 21 online. Early voting: November 28 through December 5, except November 29, 8:30 a.m. to 6 p.m. Ordinary absentee request: December 8 at 4:30 p.m.; receipt: December 11 at 4:30 p.m. Military and overseas exceptions apply.

## Early and absentee participation

The November 4 workbooks cover participation through November 3. The 64 parish totals, 6,314 detailed rows, statewide controls and every method, race and party column reconcile. Total 536,185; in person 448,587; absentee 87,598. The reported sex columns leave a residual of 278. This is not total Election Day turnout. The prior October 27 snapshot remains unchanged in data/processed/early_voting_2026.json. New data are stored in early_voting_2026-11-03.json and early_voting_parishes_2026-11-03.csv.

## Registration

The November 1 source explicitly uses Status Both and Office Congress, matching the October scope. Six congressional district summaries and their parish components reconcile with all statewide race and party controls. Statewide registrations: 2,984,520, a net increase of 6,377 from October 1. Black registrations: 936,512; outside District 2: 635,050, or 67.81%. This supersedes the dated October 67.79% finding without changing that historical record. The monthly registration total is not substituted for the SOS result portal's contest qualified voter denominator.

Source workbook: https://electionstatistics.sos.la.gov/Data/Registration_Statistics/statewide/2026_1101_sta_comb.xlsx

## Audited participation and preservation

The successfully retrieved official postelection statewide and parish indexes did not list a November 3 audited report. The display therefore uses the portal's explicitly unofficial turnout and does not invent audited parish turnout. The parish map remains an early and absentee ballot map. All October source datasets, polling records, original candidate lists and the backup branch remain untouched. District boundaries and legal status findings are not changed.

The planner now uses December 12 dates and correct Saturday hours. Prior November transportation offers are removed from current service claims. Every voter must check their actual December ballot and polling place. No voter identities, pickup addresses, party based targeting or candidate preferences are collected.

## Reproducibility

source_manifest.json records source checksums, retrieval details and validation. Data are built from the preserved official evidence, not media reports. GitHub source evidence runs: 41850427492 and 41854993575. Release build script: scripts/build_results_release_20261104.py.
'''.replace('SOURCE_TIME',source_time)
(ROOT/'docs/RESULTS_RELEASE_20261104.md').write_text(notes)
manifest['retrieved_at_local']=source_time
manifest['historical_files_preserved']=['data/processed/early_voting_2026.json','data/processed/registration_snapshot_2026-10-01.json','data/processed/house_races_2026-11-01.json','data/processed/polling_senate_2026-11-01.json','data/processed/polling_la6_2026-10-28.json']
dump(DEST/'source_manifest.json',manifest)
print(json.dumps(manifest['checks'],indent=2))
