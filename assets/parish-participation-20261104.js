/* Aggregate civic participation explorer. No voter records or tracking. */
'use strict';
(() => {
  const $ = id => document.getElementById(id);
  if (!$('parish-map')) return;
  const source = 'data/processed/parish_participation_2026-11-03.json';
  const fmt = n => n == null ? 'Not available' : Number(n).toLocaleString('en-US');
  const pct = n => n == null ? 'Not available' : Number(n).toFixed(1) + '%';
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const colors = ['#e6edf5','#bfcee0','#839fbc','#4a7195','#173e65'];
  const tabs = ['overview','race','gender','method'];
  const fields = {race:[['all','All early and absentee ballots'],['white','White'],['black','Black'],['other','Other race categories']],gender:[['all','All early and absentee ballots'],['male','Male'],['female','Female']],method:[['all','All early and absentee ballots'],['in_person','Early voting in person'],['absentee','Absentee']]};
  let data, current='state', view='overview', group='all', measure='rate', paths=new Map(), box=[0,0,800,660], drag=null, moved=false;
  const point = () => current === 'state' ? data.statewide : data.parishes.find(p=>p.parish_code===current);
  const validNumber = n => Number.isSafeInteger(n) && n >= 0;
  function validate(d) {
    const need=(ok,msg)=>{if(!ok)throw Error(msg);};
    need(d.schema_version===1 && d.election_date==='2026-11-03','Unexpected data version');
    need(d.parishes?.length===64 && new Set(d.parishes.map(p=>p.parish_code)).size===64,'Incomplete parish coverage');
    need(new Set(d.parishes.map(p=>p.geoid)).size===64,'Duplicate geography');
    for(const p of [d.statewide,...d.parishes]) {
      const e=p.early;
      need([e.total,e.in_person,e.absentee].every(validNumber),'Invalid participation count');
      need(e.total===e.in_person+e.absentee,'Voting methods do not reconcile');
      need(Object.values(e.race).every(validNumber) && Object.values(e.race).reduce((a,b)=>a+b,0)===e.total,'Race totals do not reconcile');
      need([e.sex.male,e.sex.female,e.sex.unallocated].every(validNumber) && e.sex.male+e.sex.female+e.sex.unallocated===e.total,'Reported sex totals do not reconcile');
      if(p.results) need(validNumber(p.results.votes) && validNumber(p.results.qualified) && p.results.votes<=p.results.qualified && (p.results.turnout_pct===null || (Number.isFinite(p.results.turnout_pct)&&p.results.turnout_pct>=0&&p.results.turnout_pct<=100)),'Invalid result control');
    }
    for(const k of ['total','in_person','absentee']) need(d.parishes.reduce((s,p)=>s+p.early[k],0)===d.statewide.early[k],'Statewide participation mismatch');
    if(d.parishes.every(p=>p.results)) need(d.parishes.reduce((s,p)=>s+p.results.votes,0)===d.statewide.results.votes,'Statewide contest mismatch');
    return d;
  }
  function count(p) {
    if(view==='overview') return p.results?.votes ?? null;
    if(group==='all') return p.early.total;
    if(view==='race') return p.early.race[group];
    if(view==='gender') return p.early.sex[group];
    return p.early[group];
  }
  function value(p) {
    if(measure==='count') return count(p);
    if(view==='overview') return p.results?.turnout_pct ?? null;
    const n=count(p); return p.early.total>0 ? 100*n/p.early.total : null;
  }
  function label() {
    if(view==='overview') return measure==='rate' ? 'Senate race turnout' : 'Votes cast in the Senate race';
    const name=fields[view].find(f=>f[0]===group)?.[1] || 'Early and absentee ballots';
    if(group==='all') return measure==='share' ? 'Share of all early and absentee ballots' : 'Early and absentee ballots';
    return name + (measure==='share' ? ': share of early and absentee ballots' : ': early and absentee ballots');
  }
  function scope() { return view==='overview' ? 'Senate race. Early, absentee and Election Day votes.' : 'Early and absentee voting only. Election Day is not included.'; }
  function display(p) { return measure==='count' ? fmt(value(p)) : pct(value(p)); }
  function controls() {
    for(const t of tabs) { const b=$('view-'+t);b.setAttribute('aria-selected',String(t===view));b.tabIndex=t===view?0:-1; }
    $('group-control').hidden=view==='overview';
    $('group-select').innerHTML=view==='overview'?'':fields[view].map(([v,l])=>`<option value="${v}">${l}</option>`).join('');
    if(view!=='overview') $('group-select').value=group;
    $('group-label').textContent=view==='gender'?'Choose a group':view==='race'?'Choose a race category':'Choose a voting method';
    $('map-metric').innerHTML=view==='overview'?'<option value="rate">Turnout percentage</option><option value="count">Number of votes</option>':'<option value="count">Number of ballots</option><option value="share">Share of early and absentee ballots</option>';
    $('map-metric').value=measure;
    $('panel-heading').textContent={overview:'YOUR PARISH AT A GLANCE',race:'WHO VOTED EARLY OR ABSENTEE?',gender:'WHO VOTED EARLY OR ABSENTEE?',method:'HOW WERE THESE BALLOTS CAST?'}[view];
    $('view-panel').setAttribute('aria-labelledby','view-'+view);
  }
  function saveURL() {
    const u=new URL(location.href);u.searchParams.delete('v');
    if(current==='state')u.searchParams.delete('parish');else u.searchParams.set('parish',current);
    u.searchParams.set('view',view);u.searchParams.set('group',group);u.searchParams.set('measure',measure);
    history.replaceState(null,'',u.pathname+u.search+u.hash);
  }
  function readURL() {
    const q=new URLSearchParams(location.search);
    current=data.parishes.some(p=>p.parish_code===q.get('parish'))?q.get('parish'):'state';
    view=tabs.includes(q.get('view'))?q.get('view'):'overview';
    group=view!=='overview'&&fields[view].some(f=>f[0]===q.get('group'))?q.get('group'):'all';
    measure=view==='overview'?(q.get('measure')==='count'?'count':'rate'):(q.get('measure')==='share'?'share':'count');
    controls();$('parish-select').value=current;
  }
  function bars(rows,total) {
    return rows.map(([name,n])=>`<div class="bar-row"><div class="bar-label"><span>${esc(name)}</span><strong>${fmt(n)} <small>${pct(total?100*n/total:null)}</small></strong></div><div class="bar-track" aria-hidden="true"><span class="bar-fill" style="width:${total?100*n/total:0}%;background:#173e65"></span></div></div>`).join('');
  }
  function detail(p) {
    const e=p.early,r=p.results;
    const more = body => `<details class="number-notes"><summary>About these numbers</summary>${body}</details>`;
    const plan = `<div class="parish-next"><strong>Get ready for December</strong><p>Confirm your ballot and polling place, choose a voting time, and arrange a ride if needed.</p><a href="#voting-plan" data-parish-plan>Make a voting or outreach plan</a></div>`;
    const local = `<p class="fine"><a href="https://voterportal.sos.la.gov/graphical" target="_blank" rel="noopener noreferrer">See official local election results</a>. Choose November 3, 2026, then ${current==='state'?'your parish':esc(p.name)}.</p>`;
    if(view==='overview') {
      const story=r?.turnout_pct!=null ? `About ${Math.round(r.turnout_pct)} out of every 100 registered voters listed for the Senate race cast a vote${current==='state'?' statewide':' in this parish'}.` : 'A verified turnout figure is not available for this parish.';
      const compare=current==='state'?'Choose a parish to compare its turnout with Louisiana as a whole.':`Turnout here was ${pct(r?.turnout_pct)}, compared with ${pct(data.statewide.results?.turnout_pct)} statewide.`;
      return `<p class="parish-story">${story}</p><p class="parish-comparison-note">${compare}</p><div class="detail-numbers"><div><span>Votes cast in this race</span><strong>${fmt(r?.votes)}</strong></div><div><span>Registered voters listed for this race</span><strong>${fmt(r?.qualified)}</strong></div></div>`+more(`<p>We use the Senate race because it was on ballots statewide. These figures include early, absentee and Election Day votes in that race, but not ballots with no Senate vote.</p><p>Precincts reporting: ${r?fmt(r.precincts_reporting)+' of '+fmt(r.precincts_expected):'Not available'}. Early and absentee results: ${r?.complete_early_absentee?'all reporting':'not confirmed'}. The source marked these returns unofficial when checked.</p><p>The separate early and absentee report contains ${fmt(e.total)} ballots. It cannot be subtracted from Senate votes to count Election Day voters.</p>`)+local+plan;
    }
    const opening=`<p class="parish-story">This breakdown covers ${fmt(e.total)} early and absentee ballots${current==='state'?' statewide':' in '+esc(p.name)}. Election Day ballots are not included.</p>`;
    if(view==='race') return opening+bars([['White',e.race.white],['Black',e.race.black],['Other race categories',e.race.other]],e.total)+more('<p>The labels follow SOS records. Each percentage shows a share of early and absentee ballots, not the turnout rate among all registered voters of that race. These totals do not tell us which candidates anyone supported.</p>')+plan;
    if(view==='gender') return opening+bars([['Male',e.sex.male],['Female',e.sex.female]],e.total)+more(`<p>SOS records this as sex and reports male and female. Those counts add up to ${fmt(e.sex.unallocated)} fewer than the total ballots. We do not assign the difference to a gender.</p><p>Percentages use all ${fmt(e.total)} early and absentee ballots. They do not show the turnout rate among all registered male or female voters.</p>`)+plan;
    return opening+bars([['Early voting in person',e.in_person],['Absentee',e.absentee]],e.total)+more('<p>The full election breakdown by voting method was not available in the source checked November 4. This view therefore shows early and absentee voting only, not Election Day participation.</p>')+plan;
  }
  function select(code,scroll=false) {
    current=code;$('parish-select').value=code;$('parish-find').value='';update();
    if(scroll)$('parish-map').scrollIntoView({behavior:'auto'});
  }
  function update() {
    const p=point();
    $('selection-title').textContent=p.name;
    $('selected-total').textContent=display(p);
    $('selected-label').textContent=label();
    $('scope-label').textContent=scope();
    $('view-description').textContent=view==='overview'?'Compare the share who voted, not just the number of votes. Larger parishes can have more votes without having higher turnout.':'These breakdowns tell us about early and absentee voting. They do not include the race, gender or voting method of Election Day voters.';
    $('detail-body').innerHTML=detail(p);
    $('selected-source').innerHTML=`<a href="${esc(view==='overview'?data.results_source.url:data.early_source.url)}" target="_blank" rel="noopener noreferrer">Read the official source</a><br>${esc(view==='overview'?'Results checked '+data.results_source.retrieved_label:'Report printed '+data.early_source.printed_label)}<br>${view==='overview'?'Unofficial results · not certified':'Early and absentee ballots only'}`;
    $('selection-status').textContent=p.name+'. '+label()+': '+display(p)+'. '+scope()+'.';
    const known=data.parishes.filter(p=>value(p)!==null).length;
    $('map-coverage').textContent=known===64?'Data is available for every parish.':known+' parishes have data for this view. Missing information is not zero.';
    redraw();saveURL();
  }
  function thresholds() {
    if(measure==='count') {
      const max=Math.max(...data.parishes.map(p=>value(p)??0));
      return [max*.1,max*.25,max*.5,max*.75];
    }
    return view==='overview'?[30,40,50,60]:[20,40,60,80];
  }
  function redraw() {
    const cuts=thresholds();
    for(const p of data.parishes) {
      const path=paths.get(p.parish_code);if(!path)continue;
      const v=value(p),i=v===null?-1:cuts.reduce((n,c)=>n+(v>=c?1:0),0);
      path.setAttribute('fill',i<0?'url(#missing-pattern)':colors[i]);
      path.classList.toggle('selected',current===p.parish_code);path.setAttribute('aria-pressed',String(current===p.parish_code));
      const text=p.name+': '+label()+', '+display(p);path.setAttribute('aria-label',text);path.querySelector('title').textContent=text;
    }
    const f=n=>measure==='count'?fmt(Math.ceil(n)):n+'%';
    const labels=['Under '+f(cuts[0]),f(cuts[0])+' to under '+f(cuts[1]),f(cuts[1])+' to under '+f(cuts[2]),f(cuts[2])+' to under '+f(cuts[3]),f(cuts[3])+' or more'];
    $('map-legend').innerHTML=labels.map((l,i)=>`<span><i style="background:${colors[i]}"></i>${l}</span>`).join('')+'<span><i class="missing-swatch"></i>Not available</span>';
    $('metric-description').textContent=label()+'. '+(measure==='count'?'A larger number does not necessarily mean higher turnout.':view==='overview'?'A darker shade means a larger share voted in the Senate race.':'A darker shade means this group accounts for a larger share of early and absentee ballots.');
    $('map-readout').textContent=point().name+': '+display(point());
  }
  function draw(g) {
    if(g.type!=='FeatureCollection'||g.features.length!==64)throw Error('Invalid parish boundaries');
    const byId=new Map(data.parishes.map(p=>[p.geoid,p]));
    if(g.features.some(f=>!byId.has(f.properties.GEOID)))throw Error('Boundary join mismatch');
    const rings=f=>f.geometry.type==='Polygon'?f.geometry.coordinates:f.geometry.coordinates.flat();
    const proj=([lon,lat])=>[lon*Math.PI/180,Math.log(Math.tan(Math.PI/4+lat*Math.PI/360))];
    const pts=g.features.flatMap(f=>rings(f).flat().map(proj));const xs=pts.map(p=>p[0]),ys=pts.map(p=>p[1]);
    const a=Math.min(...xs),b=Math.max(...xs),c=Math.min(...ys),d=Math.max(...ys),scale=Math.min(744/(b-a),574/(d-c));
    const xoff=(800-(b-a)*scale)/2;
    const xy=p=>{const [x,y]=proj(p);return[(x-a)*scale+xoff,(d-y)*scale+25]};
    const ns='http://www.w3.org/2000/svg';$('map-shapes').replaceChildren();
    for(const f of g.features) {
      const p=byId.get(f.properties.GEOID),path=document.createElementNS(ns,'path');
      path.setAttribute('d',rings(f).map(r=>r.map((c,i)=>(i?'L':'M')+xy(c).map(n=>n.toFixed(2)).join(',')).join(' ')+'Z').join(' '));
      path.setAttribute('fill-rule','evenodd');path.setAttribute('tabindex','0');path.setAttribute('role','button');path.dataset.code=p.parish_code;
      path.append(document.createElementNS(ns,'title'));
      path.addEventListener('click',()=>{if(!moved)select(p.parish_code)});
      path.addEventListener('keydown',e=>{if(['Enter',' '].includes(e.key)){e.preventDefault();select(p.parish_code)}});
      path.addEventListener('pointerenter',()=>{$('map-readout').textContent=p.name+': '+display(p)});
      path.addEventListener('pointerleave',()=>{$('map-readout').textContent=point().name+': '+display(point())});
      $('map-shapes').append(path);paths.set(p.parish_code,path);
    }
    $('map-loading').hidden=true;redraw();document.documentElement.dataset.mapReady='true';
  }
  function download(items,filename) {
    const head=['Parish','Parish code','Election date','View','Selected category','Map measure','Displayed value','Count','Comparison total','What the comparison total means','Source status','Coverage','Source URL','Source retrieved or printed'];
    const list=[head,...items.map(p=>[p.name,p.parish_code,'2026-11-03',view,group,measure,display(p),count(p),view==='overview'?p.results?.qualified:p.early.total,view==='overview'?'Registered voters listed for the Senate race':'All early and absentee ballots',view==='overview'?'Unofficial contest returns':'Verified early and absentee workbook',scope(),view==='overview'?data.results_source.url:data.early_source.url,view==='overview'?data.results_source.retrieved_label:data.early_source.printed_label])];
    const cell=v=>'"'+String(v??'Not available').replace(/"/g,'""')+'"';
    const content='\uFEFF'+list.map(r=>r.map(cell).join(',')).join('\r\n');
    const u=URL.createObjectURL(new Blob([content],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=u;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),30000);
    $('export-status').textContent='Spreadsheet ready. It includes the view, dates and an explanation of the numbers.';
  }
  function permalink() { const u=new URL(location.href);u.hash='parish-map';return u.href; }
  async function share(copyOnly=false) {
    const u=permalink();
    try {
      if(navigator.share&&!copyOnly)await navigator.share({title:point().name+' participation',text:scope(),url:u});
      else if(navigator.clipboard)await navigator.clipboard.writeText(u);
      else throw Error('No clipboard');
      $('export-status').textContent=copyOnly||!navigator.share?'Parish link copied.':'Share completed.';
    } catch(e) {
      if(e.name==='AbortError')return;
      $('share-link').hidden=false;$('share-link').value=u;$('share-link').focus();$('share-link').select();$('export-status').textContent='Copy the selected link to share this exact view.';
    }
  }
  function printSummary() {
    const p=point();const out=$('parish-printout');
    out.innerHTML=`<div class="print-brand">TIA FIELDS | PROVISIONAL CONSULTING LLC</div><h1>${esc(p.name)} participation</h1><p>November 3, 2026 election</p><h2>${esc(label())}: ${esc(display(p))}</h2><p><strong>${esc(scope())}</strong></p>${detail(p)}<h2>Source and limitations</h2><p>${esc(view==='overview'?data.results_source.retrieved_label:data.early_source.printed_label)}</p><p>${esc(view==='overview'?data.results_source.url:data.early_source.url)}</p><p>${esc(permalink())}</p><p>December 12 congressional runoffs: District 5, Patricia Pat Moore and Gabe Firment; District 6, Chauna Banks and Blake Miguez. Polls open 7 a.m. to 8 p.m. Central. Confirm your own district and ballot in GeauxVote.</p><p>https://www.sos.la.gov/elections-voting/election-dates</p><p>Aggregate public information. No individual voting choices are inferred.</p>`;
    out.querySelectorAll('details').forEach(n=>n.open=true);document.body.classList.add('parish-printing');window.print();
  }
  function bind() {
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
    for(const t of tabs) {
      $('view-'+t).addEventListener('click',()=>{view=t;group='all';measure=t==='overview'?'rate':'count';controls();update()});
      $('view-'+t).addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const i=tabs.indexOf(t),next=e.key==='Home'?tabs[0]:e.key==='End'?tabs[3]:tabs[(i+(e.key==='ArrowRight'?1:3))%4];$('view-'+next).click();$('view-'+next).focus()});
    }
    $('parish-select').addEventListener('change',e=>select(e.target.value));
    $('parish-find').addEventListener('change',e=>{const q=e.target.value.trim().toLowerCase();const p=data.parishes.find(p=>p.name.toLowerCase()===q||p.name.toLowerCase().replace(/ parish$/,'')===q);if(p)select(p.parish_code);else $('selection-status').textContent='Choose a parish name from the suggestions.'});
    $('group-select').addEventListener('change',e=>{group=e.target.value;update()});
    $('map-metric').addEventListener('change',e=>{measure=e.target.value;update()});
    // The repetitive parish comparison table has been removed.
    $('download-data').addEventListener('click',()=>download(data.parishes,'Louisiana_Parish_'+view+'_'+measure+'_20261103.csv'));
    $('download-parish').addEventListener('click',()=>download([point()],point().name.replace(/[^a-z0-9]/gi,'_')+'_'+view+'_20261103.csv'));
    $('share-parish').addEventListener('click',()=>share());$('copy-parish').addEventListener('click',()=>share(true));$('print-parish').addEventListener('click',printSummary);
    window.addEventListener('afterprint',()=>document.body.classList.remove('parish-printing'));
    window.addEventListener('popstate',()=>{readURL();update()});
    function apply(){$('map-svg').setAttribute('viewBox',box.join(' '))}
    function zoom(f){const w=Math.max(160,Math.min(1600,box[2]*f)),h=w*660/800;box=[box[0]+(box[2]-w)/2,box[1]+(box[3]-h)/2,w,h];apply()}
    $('zoom-in').addEventListener('click',()=>zoom(.8));$('zoom-out').addEventListener('click',()=>zoom(1.25));$('map-reset').addEventListener('click',()=>{box=[0,0,800,660];apply();select('state')});
    $('map-svg').addEventListener('pointerdown',e=>{moved=false;if(e.pointerType==='mouse'&&e.button===0)drag={x:e.clientX,y:e.clientY,box:[...box]}});
    window.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.abs(dx)+Math.abs(dy)>6)moved=true;if(moved){const r=$('map-svg').getBoundingClientRect();box=[drag.box[0]-dx*drag.box[2]/r.width,drag.box[1]-dy*drag.box[3]/r.height,drag.box[2],drag.box[3]];apply()}});window.addEventListener('pointerup',()=>{drag=null});
  }
  async function init() {
    try {
      const r=await fetch(source+'?v=20261105-plain1',{cache:'no-store'});if(!r.ok)throw Error('Data unavailable');data=validate(await r.json());
      $('parish-select').innerHTML='<option value="state">Louisiana statewide</option>'+data.parishes.map(p=>`<option value="${p.parish_code}">${esc(p.name)}</option>`).join('');
      $('parish-names').innerHTML=data.parishes.map(p=>`<option value="${esc(p.name)}"></option>`).join('');
      for(const e of document.querySelectorAll('#parish-map [disabled]'))e.disabled=false;
      bind();readURL();update();document.documentElement.dataset.parishReady='true';
      try{const g=await fetch('data/louisiana_parishes_2026.geojson');if(!g.ok)throw Error('Map unavailable');draw(await g.json());}catch(e){$('map-loading').textContent='Map unavailable. The parish menu, comparison table and downloads remain usable.';document.documentElement.dataset.mapReady='error';}
      if(location.hash==='#parish-comparison'){history.replaceState(null,'',location.pathname+location.search+'#parish-map');}if(location.hash==='#parish-map')requestAnimationFrame(()=>$('parish-map').scrollIntoView());
    } catch(e) {
      $('scope-label').textContent='Participation data could not be loaded or did not pass validation.';
      $('map-loading').textContent='Data unavailable. Use the official SOS links below.';
      $('selection-status').textContent='No figures have been substituted for missing data.';document.documentElement.dataset.parishReady='error';
    }
  }
  init();
})();
