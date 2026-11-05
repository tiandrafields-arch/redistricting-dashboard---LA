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
  const fields = {race:[['all','All reported race categories'],['white','White'],['black','Black'],['other','Other reported race']],gender:[['all','All reported sex categories'],['male','Male'],['female','Female']],method:[['all','All early and absentee ballots'],['in_person','Early voting in person'],['absentee','Absentee']]};
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
    if(view==='overview') return measure==='rate' ? 'SOS unofficial turnout' : 'Reported U.S. Senate contest votes';
    const text=fields[view].find(f=>f[0]===group)?.[1] || 'All early and absentee ballots';
    return text + (measure==='share' ? ' · share of early and absentee ballots' : ' · reported ballots');
  }
  function scope() { return view==='overview' ? 'November 3 U.S. Senate contest · provisional parish comparison' : 'Early and absentee ballots through November 3 · not full election demographics'; }
  function display(p) { return measure==='count' ? fmt(value(p)) : pct(value(p)); }
  function controls() {
    for(const t of tabs) { const b=$('view-'+t);b.setAttribute('aria-selected',String(t===view));b.tabIndex=t===view?0:-1; }
    $('group-control').hidden=view==='overview';
    $('group-select').innerHTML=view==='overview'?'':fields[view].map(([v,l])=>`<option value="${v}">${l}</option>`).join('');
    if(view!=='overview') $('group-select').value=group;
    $('group-label').textContent=view==='gender'?'Reported sex category':view==='race'?'Reported race category':'Voting method';
    $('map-metric').innerHTML=view==='overview'?'<option value="rate">Turnout rate</option><option value="count">Contest vote count</option>':'<option value="count">Reported ballot count</option><option value="share">Share of early and absentee ballots</option>';
    $('map-metric').value=measure;
    $('panel-heading').textContent={overview:'Parish overview',race:'Participation by race',gender:'Participation by gender',method:'Participation by voting method'}[view];
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
    if(view==='overview') return `<div class="detail-numbers"><div><span>Votes recorded in the Senate contest</span><strong>${fmt(r?.votes)}</strong></div><div><span>Qualified voters in the SOS contest record</span><strong>${fmt(r?.qualified)}</strong></div><div><span>Election Day precincts reporting</span><strong>${r?fmt(r.precincts_reporting)+' of '+fmt(r.precincts_expected):'Not available'}</strong></div><div><span>Early and absentee reporting</span><strong>${r?.complete_early_absentee?'Complete':'Not confirmed'}</strong></div></div><p class="fine">The same statewide contest makes parish comparisons consistent. This rate follows the SOS contest calculation. It is not an audited count of unique people who voted in any race. Complete reporting is not certification.</p><p class="fine"><strong>Early and absentee ballots:</strong> ${fmt(e.total)}. This separately reported voter participation record is not subtracted from contest votes to estimate Election Day voters.</p>`;
    if(view==='race') return bars([['White',e.race.white],['Black',e.race.black],['Other reported race',e.race.other]],e.total)+'<p class="fine">SOS aggregate race categories. Percentages describe the composition of early and absentee participation, not turnout among all registered voters in each racial group. Categories are not combined with sex or method.</p>';
    if(view==='gender') return bars([['Male',e.sex.male],['Female',e.sex.female]],e.total)+`<p class="fine"><strong>Source terminology:</strong> SOS reports sex, not gender identity. The two reported columns leave an unallocated difference of <strong>${fmt(e.sex.unallocated)}</strong> ballots. That difference is shown separately and is not assigned a demographic identity. Percentages use all ${fmt(e.total)} early and absentee ballots.</p>`;
    return bars([['Early voting in person',e.in_person],['Absentee',e.absentee]],e.total)+'<p class="fine">These are the two methods in the verified early and absentee report. Election Day voter participation by method is not yet supplied in the audited parish report. No Election Day value is estimated by subtracting unlike datasets.</p>';
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
    $('view-description').textContent=view==='overview'?'Turnout uses reported Senate votes divided by the qualified voters for that same contest and parish. Counts and rates are separate measures.':'Race, gender and method views cover early and absentee ballots only. Full election demographic participation remains unavailable in the reviewed SOS postelection files.';
    $('detail-body').innerHTML=detail(p);
    $('selected-source').innerHTML=`<a href="${esc(view==='overview'?data.results_source.url:data.early_source.url)}" target="_blank" rel="noopener noreferrer">Read the official source</a><br>${esc(view==='overview'?'Results retrieved '+data.results_source.retrieved_label:'Early and absentee report printed '+data.early_source.printed_label)}<br>${view==='overview'?'Unofficial results · not certified':'Verified dated workbook · not final turnout'}`;
    $('selection-status').textContent=p.name+'. '+label()+': '+display(p)+'. '+scope()+'.';
    const known=data.parishes.filter(p=>value(p)!==null).length;
    $('map-coverage').textContent=known+' of 64 parishes have a value for this view.';
    redraw();table();saveURL();
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
    $('metric-description').textContent=label()+'. '+(measure==='count'?'Larger parish populations can produce larger counts. Counts are not turnout rates.':'Each parish uses its own stated denominator.');
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
  function rows() {
    const q=$('parish-search').value.trim().toLowerCase(),sort=$('parish-sort').value;
    const result=data.parishes.filter(p=>p.name.toLowerCase().includes(q));
    result.sort((a,b)=>sort==='name'?a.name.localeCompare(b.name):value(a)===null?1:value(b)===null?-1:sort==='low'?value(a)-value(b):value(b)-value(a));return result;
  }
  function table() {
    $('table-measure').textContent=label();$('parish-table').replaceChildren();
    for(const p of rows()) {
      const tr=document.createElement('tr');const name=document.createElement('th');name.scope='row';const b=document.createElement('button');b.type='button';b.textContent=p.name;b.addEventListener('click',()=>select(p.parish_code,true));name.append(b);tr.append(name);
      const den=view==='overview'?p.results?.qualified:p.early.total;
      for(const text of [display(p),fmt(count(p)),fmt(den),view==='overview'?(p.results?.complete_reporting?'Complete · unofficial':'Not available'):'Early and absentee only']) {const td=document.createElement('td');td.textContent=text;tr.append(td);}
      $('parish-table').append(tr);
    }
    $('table-count').textContent=rows().length+' of 64 parishes';$('table-scope').textContent=scope()+'. Denominator: '+(view==='overview'?'qualified voters in the same Senate contest.':'all reported early and absentee ballots in the parish.');
  }
  function download(items,filename) {
    const head=['Parish','Parish code','Election date','View','Selected category','Map measure','Displayed value','Count','Denominator','Denominator definition','Source status','Coverage','Source URL','Source retrieved or printed'];
    const list=[head,...items.map(p=>[p.name,p.parish_code,'2026-11-03',view,group,measure,display(p),count(p),view==='overview'?p.results?.qualified:p.early.total,view==='overview'?'Qualified voters in the same U.S. Senate contest':'All early and absentee ballots',view==='overview'?'Unofficial contest returns':'Verified early and absentee workbook',scope(),view==='overview'?data.results_source.url:data.early_source.url,view==='overview'?data.results_source.retrieved_label:data.early_source.printed_label])];
    const cell=v=>'"'+String(v??'Not available').replace(/"/g,'""')+'"';
    const content='\uFEFF'+list.map(r=>r.map(cell).join(',')).join('\r\n');
    const u=URL.createObjectURL(new Blob([content],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=u;a.download=filename;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(u),30000);
    $('export-status').textContent='CSV prepared with the selected view, source and denominator.';
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
    document.body.classList.add('parish-printing');window.print();
  }
  function bind() {
    for(const t of tabs) {
      $('view-'+t).addEventListener('click',()=>{view=t;group='all';measure=t==='overview'?'rate':'count';controls();update()});
      $('view-'+t).addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const i=tabs.indexOf(t),next=e.key==='Home'?tabs[0]:e.key==='End'?tabs[3]:tabs[(i+(e.key==='ArrowRight'?1:3))%4];$('view-'+next).click();$('view-'+next).focus()});
    }
    $('parish-select').addEventListener('change',e=>select(e.target.value));
    $('parish-find').addEventListener('change',e=>{const q=e.target.value.trim().toLowerCase();const p=data.parishes.find(p=>p.name.toLowerCase()===q||p.name.toLowerCase().replace(/ parish$/,'')===q);if(p)select(p.parish_code);else $('selection-status').textContent='Choose a parish name from the suggestions.'});
    $('group-select').addEventListener('change',e=>{group=e.target.value;update()});
    $('map-metric').addEventListener('change',e=>{measure=e.target.value;update()});
    for(const id of ['parish-search','parish-sort'])$(id).addEventListener('input',table);
    $('download-data').addEventListener('click',()=>download(rows(),'Louisiana_Parish_'+view+'_'+measure+'_20261103.csv'));
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
      const r=await fetch(source+'?v=20261104-parish1',{cache:'no-store'});if(!r.ok)throw Error('Data unavailable');data=validate(await r.json());
      $('parish-select').innerHTML='<option value="state">Louisiana statewide</option>'+data.parishes.map(p=>`<option value="${p.parish_code}">${esc(p.name)}</option>`).join('');
      $('parish-names').innerHTML=data.parishes.map(p=>`<option value="${esc(p.name)}"></option>`).join('');
      for(const e of document.querySelectorAll('#parish-map [disabled],#parish-comparison [disabled]'))e.disabled=false;
      bind();readURL();update();document.documentElement.dataset.parishReady='true';
      try{const g=await fetch('data/louisiana_parishes_2026.geojson');if(!g.ok)throw Error('Map unavailable');draw(await g.json());}catch(e){$('map-loading').textContent='Map unavailable. The parish menu, comparison table and downloads remain usable.';document.documentElement.dataset.mapReady='error';}
      if(location.hash==='#parish-map')requestAnimationFrame(()=>$('parish-map').scrollIntoView());
    } catch(e) {
      $('scope-label').textContent='Participation data could not be loaded or did not pass validation.';
      $('map-loading').textContent='Data unavailable. Use the official SOS links below.';
      $('selection-status').textContent='No figures have been substituted for missing data.';document.documentElement.dataset.parishReady='error';
    }
  }
  init();
})();
