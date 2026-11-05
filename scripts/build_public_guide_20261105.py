"""Simplify the public dashboard without changing any source data or archives."""
from pathlib import Path
from bs4 import BeautifulSoup
import hashlib, html, json, re

ROOT = Path(__file__).resolve().parents[1]
VERSION = '20261105-plain1'
protected = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
             for folder in ['data', 'archive'] for p in (ROOT/folder).rglob('*') if p.is_file()}
soup = BeautifulSoup((ROOT/'index.html').read_text(), 'html.parser')
assert soup.select_one('meta[name="dashboard-release"]')['content'] == '20261104-parish1'
assert soup.select_one('#parish-comparison') is not None
soup.select_one('#parish-comparison').decompose()

def text(selector, value):
    item = soup.select_one(selector)
    assert item is not None, selector
    item.clear(); item.append(value)

def inner(selector, value):
    item = soup.select_one(selector)
    assert item is not None, selector
    item.clear()
    fragment = BeautifulSoup(value, 'html.parser')
    for node in list(fragment.contents): item.append(node)

text('title', 'Louisiana Voter Guide and Parish Participation | Tia Fields')
soup.select_one('meta[name="dashboard-release"]')['content'] = VERSION
soup.select_one('meta[name="description"]')['content'] = 'Understand November election results, explore voting in your parish and make a plan for the December 12 runoffs. A nonpartisan guide by Tia Fields, Provisional Consulting LLC.'
text('.edition', 'LOUISIANA VOTER GUIDE')
inner('.nav-inner', ''.join(f'<a href="#{ident}">{label}</a>' for ident,label in [
    ('runoffs','December runoffs'),('parish-map','Your parish'),('november-results','November results'),
    ('registration','Registration'),('voting-plan','Voting plan'),('methodology','About the data')]))
text('#runoffs .results-note', 'These pairings come from complete SOS returns checked November 4. Those returns were marked unofficial, not certified.')
intro = soup.new_tag('p', attrs={'class':'guide-purpose'})
intro.string = 'Understand the November results. Explore participation in your parish. Make a plan to vote or help others get to the polls, regardless of party.'
soup.select_one('#runoffs .runoff-lead').insert_after(intro)
inner('#runoffs .runoff-actions', '<a class="button" href="#voting-plan" id="start-voter-plan">Make my voting plan</a><a class="button secondary" href="#voting-plan" id="start-org-plan">Help others vote</a><a class="button secondary" href="https://voterportal.sos.la.gov/Home/VoterLogin" target="_blank" rel="noopener noreferrer">Check my ballot</a>')
for p in soup.select('#runoffs p.fine'):
    if 'A parish selection' in p.get_text(): p.string = 'Your address determines your district and ballot. Check GeauxVote to see which congressional or local races you can vote in this December.'
for strong in soup.select('#runoffs .deadline-grid strong'):
    if strong.get_text() == 'Ordinary absentee request': strong.string = 'Request an absentee ballot'
    if strong.get_text() == 'Ordinary absentee receipt': strong.string = 'Return your absentee ballot'
text('#map-title', 'What did voting look like in your parish?')
text('#parish-map .section-intro', 'Choose a parish to see its November participation. Use Turnout to compare voting across parishes. Race, Gender and Voting method show the early and absentee breakdowns available for this release.')
text('#view-overview', 'Turnout')
text('#scope-label', 'Senate race. Early, absentee and Election Day votes.')
text('#view-description', 'The turnout map uses the same statewide race for every parish. It does not show which candidate people supported.')
text('label[for="map-metric"]', 'What should the map show?')
text('#selected-label', 'Senate race turnout')
text('#panel-heading', 'YOUR PARISH AT A GLANCE')
inner('#parish-map .parish-actions', '<button class="button" disabled id="share-parish" type="button">Share this parish</button><button class="button secondary" disabled id="copy-parish" type="button">Copy link</button><button class="button secondary" disabled id="print-parish" type="button">Print or save PDF</button><button class="button secondary" disabled id="download-parish" type="button">Download this view</button><button class="button secondary" disabled id="download-data" type="button">Download all parishes</button>')
inner('#parish-map noscript', '<p class="notice">Turn on JavaScript to use the map. You can still <a href="data/processed/parish_participation_2026-11-03.csv">download the parish spreadsheet</a>, <a href="https://voterportal.sos.la.gov/graphical">read official election results</a>, or <a href="https://voterportal.sos.la.gov/Home/VoterLogin">find your polling place</a>. The demographic spreadsheet covers early and absentee voting only.</p>')
text('#registration-title', 'Who is registered to vote?')
inner('#registration .section-intro', 'Louisiana had <strong>2,984,520 registered voters</strong> in the November 1 report, <strong>6,377 more</strong> than in October. Being registered does not mean someone voted.')
text('#registration details > summary', 'See registration by congressional district')

results = json.loads((ROOT/'data/processed/election_results_2026-11-03.json').read_text())
assert len(results['races']) == 7 and results['certified'] is False
cards = []
for race in results['races']:
    ordered = sorted(race['candidates'], key=lambda c:c['votes'], reverse=True)
    h = html.escape(race['label'])
    if race['district'] in [5,6]:
        names = ' and '.join(html.escape(c['name'].replace('"','')) for c in ordered[:2])
        body = f'<p class="result-status">December 12 runoff</p><h4>{names}</h4><p>No candidate received more than half of the reported votes.</p>'
    else:
        lead = ordered[0]
        assert lead['votes']*2 > race['candidate_total']
        name = html.escape(lead['name'].replace('"',''))
        body = f'<p class="result-status">Majority of reported votes</p><h4>{name}</h4><p><strong>{lead["votes"]:,}</strong> votes. SOS displayed {html.escape(lead["sos_percentage"])}.</p>'
    cards.append(f'<article class="november-card" data-race-id="{race["id"]}"><h3>{h}</h3>{body}</article>')
section = BeautifulSoup('<section id="november-results" class="section" aria-labelledby="november-title"><p class="eyebrow">NOVEMBER 3 ELECTION</p><h2 id="november-title">What happened in November?</h2><p>See the congressional results or open the official results tool for local races in your parish.</p><details class="november-summary"><summary>See the Senate and six House results</summary><p class="fine">Complete reporting, marked unofficial by SOS when retrieved November 4 at 9:11 a.m. Central. These are not certified results. Candidate percentages follow the rounding shown by SOS.</p><div class="november-grid">'+''.join(cards)+'</div><p><a href="archive/november-2026/#election-results">Read the full November candidate results</a></p></details><div class="local-results"><h3>School board, judicial and other local races</h3><p>Open the SOS results tool, choose November 3, 2026, and select your parish. It includes local contests beyond this dashboard\'s congressional summary.</p><a class="button secondary" href="https://voterportal.sos.la.gov/graphical" target="_blank" rel="noopener noreferrer">See official local results</a></div></section>', 'html.parser').section
soup.select_one('#parish-map').insert_after(section)
inner('#methodology', '<p class="eyebrow">ABOUT THE DATA</p><h2 id="methods-title">What these numbers can tell you</h2><div class="source-cards"><article><h3>November turnout</h3><p>The map shows votes cast in the Senate race compared with registered voters listed for that race. We use the same race in every parish so the comparison is consistent. A ballot without a Senate vote is not counted in this measure.</p><p><a href="https://voterportal.sos.la.gov/graphical">Official SOS results</a></p></article><article><h3>Race, gender and voting method</h3><p>These views include early and absentee ballots only. They do not include Election Day demographics. The percentage shown is a share of these ballots, not the percentage of everyone in that group who voted.</p><p><a href="https://electionstatistics.sos.la.gov/default.aspx?Stats=Early_Voting_Statistics&amp;Type=Parish">Official early and absentee reports</a></p></article></div><details><summary>Sources, dates and calculation details</summary><p>Parish returns were checked November 4 at 8:28 p.m. Central. The early and absentee report was printed November 4 at 3:10 a.m. Central. The full election demographic report was not available in that review. Registration uses the November 1 report.</p><p>SOS calls the gender columns sex and reports male and female. Counts that do not fit those two totals are left unclassified. These records do not reveal how any person voted.</p><p><a href="docs/PARISH_FOCUS_20261104.md">Read the calculation and verification notes</a> · <a href="data/processed/parish_participation_2026-11-03.csv">Download the full parish spreadsheet</a> · <a href="data/processed/parish_participation_2026-11-03.json">Download source data JSON</a></p></details><details><summary>Earlier results, candidate lists and polls</summary><p>Previous research is preserved for reference. It is not the December ballot.</p><p><a href="archive/november-2026/">Open the November research archive</a></p></details><p class="fine">Independent, nonpartisan analysis by Tia Fields, Provisional Consulting LLC. This is not an official government website. No individual voter records are collected.</p>')
for node in soup.select('script[src],link[href]'):
    attr = 'src' if node.name=='script' else 'href'
    if 'parish-participation-' in node.get(attr,''): node[attr] = node[attr].split('?')[0]+'?v='+VERSION
for node in soup.find_all(string=True):
    if 'Release 20261104.parish.1' in node: node.replace_with(str(node).replace('Release 20261104.parish.1','Release 20261105.plain.1'))
(ROOT/'index.html').write_text(str(soup)+'\n')

jsfile=ROOT/'assets/parish-participation-20261104.js'
js=jsfile.read_text()
def replace(old,new):
    global js
    assert old in js, old[:100]
    js=js.replace(old,new)
def function(start,end,new):
    global js
    a=js.index('  function '+start);b=js.index('  function '+end,a)
    js=js[:a]+new+'\n'+js[b:]
replace("['all','All reported race categories']", "['all','All early and absentee ballots']")
replace("['other','Other reported race']", "['other','Other race categories']")
replace("['all','All reported sex categories']", "['all','All early and absentee ballots']")
function('label()', 'controls()', r'''  function label() {
    if(view==='overview') return measure==='rate' ? 'Senate race turnout' : 'Votes cast in the Senate race';
    const name=fields[view].find(f=>f[0]===group)?.[1] || 'Early and absentee ballots';
    if(group==='all') return measure==='share' ? 'Share of all early and absentee ballots' : 'Early and absentee ballots';
    return name + (measure==='share' ? ': share of early and absentee ballots' : ': early and absentee ballots');
  }
  function scope() { return view==='overview' ? 'Senate race. Early, absentee and Election Day votes.' : 'Early and absentee voting only. Election Day is not included.'; }
  function display(p) { return measure==='count' ? fmt(value(p)) : pct(value(p)); }''')
replace("view==='gender'?'Reported sex category':view==='race'?'Reported race category':'Voting method'", "view==='gender'?'Choose a group':view==='race'?'Choose a race category':'Choose a voting method'")
replace('Turnout rate</option><option value="count">Contest vote count', 'Turnout percentage</option><option value="count">Number of votes')
replace('Reported ballot count</option>', 'Number of ballots</option>')
replace("{overview:'Parish overview',race:'Participation by race',gender:'Participation by gender',method:'Participation by voting method'}", "{overview:'YOUR PARISH AT A GLANCE',race:'WHO VOTED EARLY OR ABSENTEE?',gender:'WHO VOTED EARLY OR ABSENTEE?',method:'HOW WERE THESE BALLOTS CAST?'}")
function('detail(p)', 'select(code', r'''  function detail(p) {
    const e=p.early,r=p.results;
    const more = body => `<details class="number-notes"><summary>About these numbers</summary>${body}</details>`;
    const plan = `<div class="parish-next"><strong>Get ready for December</strong><p>Confirm your ballot and polling place, choose a voting time, and arrange a ride if needed.</p><a href="#voting-plan" data-parish-plan>Make a voting or outreach plan</a></div>`;
    const local = `<p class="fine"><a href="https://voterportal.sos.la.gov/graphical" target="_blank" rel="noopener noreferrer">See official local election results</a>. Choose November 3, 2026, then ${current==='state'?'your parish':esc(p.name)}.</p>`;
    if(view==='overview') {
      const story=r?.turnout_pct!=null ? `About ${Math.round(r.turnout_pct)} out of every 100 registered voters listed for the Senate race cast a vote${current==='state'?' statewide':' in this parish'}.` : 'A verified turnout figure is not available for this parish.';
      const compare=current==='state'?'Choose a parish to compare its turnout with Louisiana as a whole.':`Turnout here was ${pct(r?.turnout_pct)}, compared with ${pct(data.statewide.results?.turnout_pct)} statewide.`;
      return `<p class="parish-story">${story}</p><p class="parish-comparison-note">${compare}</p><div class="detail-numbers"><div><span>Votes cast in this race</span><strong>${fmt(r?.votes)}</strong></div><div><span>Registered voters listed for this race</span><strong>${fmt(r?.qualified)}</strong></div></div>`+more(`<p>We use the Senate race because it was on ballots statewide. These figures include early, absentee and Election Day votes in that race, but not ballots with no Senate vote.</p><p>Voting places reporting: ${r?fmt(r.precincts_reporting)+' of '+fmt(r.precincts_expected):'Not available'}. Early and absentee results: ${r?.complete_early_absentee?'all reporting':'not confirmed'}. The source marked these returns unofficial when checked.</p><p>The separate early and absentee report contains ${fmt(e.total)} ballots. It cannot be subtracted from Senate votes to count Election Day voters.</p>`)+local+plan;
    }
    const opening=`<p class="parish-story">This breakdown covers ${fmt(e.total)} early and absentee ballots${current==='state'?' statewide':' in '+esc(p.name)}. Election Day ballots are not included.</p>`;
    if(view==='race') return opening+bars([['White',e.race.white],['Black',e.race.black],['Other race categories',e.race.other]],e.total)+more('<p>The labels follow SOS records. Each percentage shows a share of early and absentee ballots, not the turnout rate among all registered voters of that race. These totals do not tell us which candidates anyone supported.</p>')+plan;
    if(view==='gender') return opening+bars([['Male',e.sex.male],['Female',e.sex.female]],e.total)+more(`<p>SOS records this as sex and reports male and female. Those counts add up to ${fmt(e.sex.unallocated)} fewer than the total ballots. We do not assign the difference to a gender.</p><p>Percentages use all ${fmt(e.total)} early and absentee ballots. They do not show the turnout rate among all registered male or female voters.</p>`)+plan;
    return opening+bars([['Early voting in person',e.in_person],['Absentee',e.absentee]],e.total)+more('<p>The full election breakdown by voting method was not available in the source checked November 4. This view therefore shows early and absentee voting only, not Election Day participation.</p>')+plan;
  }''')
replace("'Turnout uses reported Senate votes divided by the qualified voters for that same contest and parish. Counts and rates are separate measures.':'Race, gender and method views cover early and absentee ballots only. Full election demographic participation remains unavailable in the reviewed SOS postelection files.'", "'Compare the share who voted, not just the number of votes. Larger parishes can have more votes without having higher turnout.':'These breakdowns tell us about early and absentee voting. They do not include the race, gender or voting method of Election Day voters.'")
replace("redraw();table();saveURL();", "redraw();saveURL();")
replace("'Results retrieved '+data.results_source.retrieved_label:'Early and absentee report printed '+data.early_source.printed_label", "'Results checked '+data.results_source.retrieved_label:'Report printed '+data.early_source.printed_label")
replace("'Verified dated workbook · not final turnout'", "'Early and absentee ballots only'")
replace("known+' of 64 parishes have a value for this view.'", "known===64?'Data is available for every parish.':known+' parishes have data for this view. Missing information is not zero.'")
replace("'Larger parish populations can produce larger counts. Counts are not turnout rates.':'Each parish uses its own stated denominator.'", "'A larger number does not necessarily mean higher turnout.':view==='overview'?'A darker shade means a larger share voted in the Senate race.':'A darker shade means this group accounts for a larger share of early and absentee ballots.'")
a=js.index('  function rows()');b=js.index('  function download(',a);js=js[:a]+js[b:]
replace("'Denominator','Denominator definition'", "'Comparison total','What the comparison total means'")
replace("'Qualified voters in the same U.S. Senate contest'", "'Registered voters listed for the Senate race'")
replace("'CSV prepared with the selected view, source and denominator.'", "'Spreadsheet ready. It includes the view, dates and an explanation of the numbers.'")
replace("for(const id of ['parish-search','parish-sort'])$(id).addEventListener('input',table);", "// The repetitive parish comparison table has been removed.")
replace("download(rows(),'Louisiana_Parish_'", "download(data.parishes,'Louisiana_Parish_'")
replace("document.body.classList.add('parish-printing');window.print();", "out.querySelectorAll('details').forEach(n=>n.open=true);document.body.classList.add('parish-printing');window.print();")
replace("'#parish-map [disabled],#parish-comparison [disabled]'", "'#parish-map [disabled]'")
replace("source+'?v=20261104-parish1'", "source+'?v=20261105-plain1'")
replace("if(location.hash==='#parish-map')requestAnimationFrame", "if(location.hash==='#parish-comparison'){history.replaceState(null,'',location.pathname+location.search+'#parish-map');}if(location.hash==='#parish-map')requestAnimationFrame")
replace("  function bind() {\n    for(const t of tabs) {", """  function bind() {
    document.addEventListener('click',event=>{
      const link=event.target.closest('#start-org-plan,#start-voter-plan,[data-parish-plan]');
      if(!link)return;
      const org=link.id!=='start-voter-plan';
      $(org?'vp-tab-org':'vp-tab-voter')?.click();
      if(current!=='state'){
        const field=$(org?'vp-org-parish':'vp-parish');
        if(field){field.value=current;field.dispatchEvent(new Event('change',{bubbles:true}));}
        if(org)$('vp-org-form')?.requestSubmit();
      }
    });
    for(const t of tabs) {""")
jsfile.write_text(js)
css=ROOT/'assets/parish-participation-20261104.css'
styles=css.read_text()
styles='\n'.join(line for line in styles.splitlines() if not line.startswith('#parish-comparison '))+'\n'
styles+='''\n/* Reader friendly explanations and an optional November results summary. */
.guide-purpose{max-width:72ch;font-size:1rem;line-height:1.65}.parish-story{font-size:1.05rem;line-height:1.65;font-weight:650}.parish-comparison-note{line-height:1.6;color:var(--muted)}.number-notes{margin:18px 0;border-top:1px solid var(--line);padding-top:12px}.number-notes summary{cursor:pointer;min-height:44px;font-weight:650;line-height:1.5}.number-notes p{font-size:.86rem;line-height:1.65}.parish-next{margin-top:20px;padding:18px;background:#edf3f8;border-radius:10px;border:1px solid var(--line)}.parish-next p{font-size:.9rem;line-height:1.6}.parish-next a{display:inline-block;padding:8px 0;font-weight:650}.november-summary{margin:18px 0;padding:18px;background:#fff;border:1px solid var(--line);border-radius:10px}.november-summary>summary{font-weight:700;cursor:pointer;min-height:44px;font-size:1.05rem}.november-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px;margin-top:20px}.november-card{padding:18px;border:1px solid var(--line);border-radius:8px}.november-card h3{font-size:1rem;margin:0 0 14px}.november-card h4{font-size:1.15rem;margin:8px 0;line-height:1.4}.november-card p{font-size:.88rem;line-height:1.6}.result-status{font-weight:650;color:var(--muted)}.local-results{padding:20px;border:1px solid var(--line);border-radius:10px;background:#fff}.local-results p{max-width:72ch;line-height:1.65}#selected-label{font-size:.95rem}#parish-map .bar-label{font-size:.95rem}#parish-map .detail-numbers span{font-size:.85rem}#parish-map .map-readout{font-size:.85rem}
@media(max-width:840px){.november-grid{grid-template-columns:1fr 1fr}}@media(max-width:480px){.november-grid{grid-template-columns:1fr}.parish-story{font-size:1rem}.november-summary{padding:14px}.parish-actions button{flex:1 1 100%}.local-results .button{width:100%;white-space:normal}.parish-next{padding:14px}}
@media print{#parish-printout .parish-next{display:none}#parish-printout .number-notes{border:0;padding:0;margin:10pt 0}#parish-printout .number-notes summary{min-height:0}#parish-printout .number-notes p{font-size:9pt}}
'''
css.write_text(styles)

# Retain all source, selection, sharing, planner, mobile and error tests; replace only removed table expectations.
testfile=ROOT/'tests/test_parish_focus.py'
if testfile.exists():
    t=testfile.read_text()
    t=t.replace("'parish-map','parish-comparison','registration'", "'parish-map','november-results','registration'")
    t=t.replace("assert page.locator('#parish-table tr').count()==64", "assert page.locator('#parish-comparison,#parish-table').count()==0\n  assert page.locator('#november-results .november-card').count()==7\n  assert page.locator('#november-results details').get_attribute('open') is None")
    t=t.replace("'not full election demographics'", "'Election Day is not included'")
    t=t.replace("assert 'unallocated difference of 79' in page.locator('#detail-body').inner_text()", "assert '79 fewer' in page.locator('#detail-body').text_content()")
    t=t.replace("assert 'not yet supplied' in page.locator('#detail-body').inner_text()", "assert 'not available in the source checked November 4' in page.locator('#detail-body').text_content()")
    a=t.index("  page.fill('#parish-search','Baton Rouge')"); b=t.index("  page.select_option('#parish-select','17');page.click('#view-gender')",a)
    t=t[:a]+'''  with page.expect_download() as e:page.click('#download-data')
  with open(e.value.path(),encoding='utf-8-sig',newline='') as f:rows=list(csv.reader(f))
  assert len(rows)==65
  assert 'Denominator' not in rows[0]
  assert 'out of every 100' in page.locator('#detail-body').inner_text()
  assert 'denominator' not in page.locator('#main').inner_text().lower()
  page.click('#start-org-plan');assert page.locator('#vp-tab-org').get_attribute('aria-selected')=='true'
  page.click('#start-voter-plan');assert page.locator('#vp-tab-voter').get_attribute('aria-selected')=='true'
'''+t[b:]
    t=t.replace("assert plain.locator('#parish-table tr').count()==64", "assert plain.locator('#parish-comparison,#parish-table').count()==0\n  assert plain.locator('noscript a[href=\"data/processed/parish_participation_2026-11-03.csv\"]').count()==1")
    t=t.replace("'no_Javascript_table':'PASS'", "'no_Javascript_fallback':'PASS','comparison_table':'REMOVED','plain_language':'PASS','november_summary':'PASS'")
    testfile.write_text(t)

(ROOT/'docs').mkdir(exist_ok=True)
(ROOT/'docs/PUBLIC_GUIDE_20261105.md').write_text('''# Public voter guide readability update

Removed the 64 parish comparison table and its navigation entry, duplicate Selected value and Count columns, and public denominator wording. The map remains the parish exploration tool. Each selection now explains participation in everyday language, including an approximate out of 100 illustration and a comparison with the statewide Senate race rate. No estimate of people who did not vote is created.

Race, gender and method views still cover early and absentee ballots only. Their limits remain visible above the map; calculation and reporting details are expandable. Sex reporting differences are left unclassified. All source records, snapshots, archive files and boundaries remain unchanged.

Runoffs remain first, followed by the map. A closed summary presents seven congressional outcomes from the preserved November 4 unofficial SOS snapshot without listing every former candidate or restoring polls. Local races are linked to the official SOS tool with clear instructions, not described as embedded results. Voting and organization shortcuts open the corresponding planner, retaining the selected parish when available.

The all parish spreadsheet remains available without restoring the public table. Shared view URLs, selected parish exports, print or save PDF, all 64 parish selection checks, mobile checks, source failure handling and historical archive tests are preserved. Plain language metadata accompanies exports. Official December dates and hours were checked against https://www.sos.la.gov/elections-voting/election-dates on November 5, 2026. This update does not claim a new results retrieval or certification.
''')
assert all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in protected.items()), 'A source or archive was changed'
print(json.dumps({'release':VERSION,'comparison_table':'removed','source_and_archive_files_unchanged':len(protected),'congressional_summaries':len(cards)}))
