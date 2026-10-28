'use strict';
(() => {
const $=id=>document.getElementById(id), fmt=n=>Math.round(n).toLocaleString('en-US'), pct=n=>(n*100).toFixed(1)+'%';
const colors={democratic:'#2563eb',republican:'#d92d3a',no_party:'#8054b8',other:'#6b7280'};
const labels={democratic:'Democratic',republican:'Republican',no_party:'No Party',other:'Other parties'};
const V='20261028-parish-v2';
let data=null,selected='state',features=[],paths=new Map(),view=[0,0,800,660],drag=null,moved=false;
function node(tag,text,cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e}
function need(test,message){if(!test)throw new Error(message)}
const isCount=n=>typeof n==='number'&&Number.isSafeInteger(n)&&n>=0;
function validate(d){
 need(d.status==='verified_snapshot','Snapshot has not passed verification');
 need(d.reporting_period_end==='2026-10-27','Unexpected reporting cutoff');
 need(Array.isArray(d.parishes)&&d.parishes.length===64,'64 parishes required');
 need(new Set(d.parishes.map(p=>p.parish_code)).size===64,'Duplicate SOS parish code');
 need(new Set(d.parishes.map(p=>p.geoid)).size===64,'Duplicate Census GEOID');
 for(const p of [...d.parishes,d.statewide]){
  for(const k of ['total','in_person','absentee'])need(isCount(p[k]),'Invalid count');
  need(p.in_person+p.absentee===p.total,'Voting methods do not reconcile');
  for(const group of ['party','race']){const values=Object.values(p.breakdowns[group]);need(values.every(isCount),'Invalid breakdown');need(values.reduce((a,b)=>a+b,0)===p.total,'Breakdown does not reconcile')}
 }
 for(const k of ['total','in_person','absentee'])need(d.parishes.reduce((s,p)=>s+p[k],0)===d.statewide[k],'Parish total mismatch');
 for(const group of ['party','race'])for(const k of Object.keys(d.statewide.breakdowns[group]))need(d.parishes.reduce((s,p)=>s+p.breakdowns[group][k],0)===d.statewide.breakdowns[group][k],'Parish category mismatch');
 return d;
}
async function json(path){const r=await fetch(path+'?v='+V,{cache:'no-store'});if(!r.ok)throw new Error('Unable to load '+path);return r.json()}
const nice=s=>s==='LASALLE'?'LaSalle':s.toLowerCase().replace(/\b[a-z]/g,c=>c.toUpperCase());
function geography(id){return id==='state'?data.statewide:data.parishes.find(p=>p.parish_code===id)}
function geographyName(id){return id==='state'?'Louisiana statewide':nice(geography(id).parish)+' Parish'}
function addOptions(select){select.replaceChildren();const o=node('option','Louisiana statewide');o.value='state';select.append(o);for(const p of data.parishes){const option=node('option',nice(p.parish)+' Parish');option.value=p.parish_code;select.append(option)}select.disabled=false}
function bars(target,rows,total){target.replaceChildren();for(const [label,value,color] of rows){const row=node('div',undefined,'bar-row'),top=node('div',undefined,'bar-label'),right=node('strong',pct(total?value/total:0));right.append(node('small',' · '+fmt(value)));top.append(node('span',label),right);const track=node('div',undefined,'bar-track'),fill=node('span',undefined,'bar-fill');fill.style.background=color;fill.style.width=(total?100*value/total:0)+'%';track.append(fill);row.append(top,track);target.append(row)}}
function selection(){
 const p=geography(selected);$('selection-title').textContent=geographyName(selected);$('selected-total').textContent=fmt(p.total);$('selected-share').textContent=pct(p.total/data.statewide.total)+' of statewide reported ballots';$('selected-inperson').textContent=fmt(p.in_person);$('selected-absentee').textContent=fmt(p.absentee);
 const type=$('composition').value;let rows;
 if(type==='party'){rows=Object.entries(p.breakdowns.party).map(([k,v])=>[labels[k],v,colors[k]]);$('composition-note').textContent='Party registration is not vote choice. No Party is not the same as undecided.'}
 else if(type==='race'){rows=[['White',p.breakdowns.race.white,'#456d8b'],['Black',p.breakdowns.race.black,'#087e8b'],['Other reported race',p.breakdowns.race.other,'#7e8895']];$('composition-note').textContent='SOS reported race categories describe the recorded electorate, not candidate preferences.'}
 else{rows=[['In person',p.in_person,'#173e65'],['Absentee',p.absentee,'#3b8a96']];$('composition-note').textContent='Voting methods cover this reporting cutoff. Later absentee receipts are not included.'}
 bars($('composition-bars'),rows,p.total);
 for(const [code,path] of paths){path.classList.toggle('selected',code===selected);path.setAttribute('aria-pressed',String(code===selected))}
}
function choose(code){selected=code;$('parish-select').value=code;selection();const p=geography(code);$('map-readout').textContent=geographyName(code)+': '+fmt(p.total)+' reported ballots.'}
function metric(p){const key=$('map-metric').value;if(key==='total')return p.total;if(key==='in_person_share')return p.in_person/p.total;if(key==='absentee_share')return p.absentee/p.total;if(key==='black_share')return p.breakdowns.race.black/p.total;return p.breakdowns.party[key]/p.total}
function palette(){const key=$('map-metric').value;return key==='democratic'?['#edf2ff','#cbdcff','#9abaff','#5689f2','#2563eb']:key==='republican'?['#fff0f0','#ffd0d3','#f59ca3','#e66d78','#d92d3a']:key==='no_party'?['#f4effb','#ddd0ee','#bba1d7','#9b79c4','#8054b8']:key==='black_share'?['#e9f5f3','#c2e5df','#8dc8bd','#419f9c','#087e8b']:['#e6edf5','#bfcee0','#839fbc','#4a7195','#173e65']}
function bin(v){const breaks=$('map-metric').value==='total'?[2500,5000,10000,20000]:[.2,.4,.6,.8];return breaks.reduce((b,x)=>b+(v>=x?1:0),0)}
function redraw(){
 const pal=palette(),key=$('map-metric').value;
 for(const p of data.parishes){const path=paths.get(p.parish_code);if(path){path.setAttribute('fill',pal[bin(metric(p))]);path.querySelector('title').textContent=nice(p.parish)+' Parish: '+(key==='total'?fmt(p.total)+' reported ballots':pct(metric(p)))}}
 const ticks=key==='total'?['Under 2,500','2,500 to 4,999','5,000 to 9,999','10,000 to 19,999','20,000 or more']:['Under 20%','20% to under 40%','40% to under 60%','60% to under 80%','80% to 100%'];
 $('map-legend').replaceChildren();ticks.forEach((t,i)=>{const item=node('span'),swatch=node('i');swatch.style.background=pal[i];item.append(swatch,document.createTextNode(t));$('map-legend').append(item)});
 $('metric-description').textContent=key==='total'?'Reported ballots by parish. Larger populations can produce larger counts; this is not a turnout rate.':$('map-metric').selectedOptions[0].textContent+' as a share of each parish’s reported ballots, not a share of registered or eligible voters.';
}
function mapGeometry(g){
 need(g.type==='FeatureCollection'&&g.features.length===64,'Map must contain 64 parishes');
 const byGeoid=new Map(data.parishes.map(p=>[p.geoid,p]));need(new Set(g.features.map(f=>f.properties.GEOID)).size===64,'Duplicate boundary');
 need(g.features.every(f=>byGeoid.has(f.properties.GEOID)),'Unmatched Census parish');features=g.features;
 const project=([lon,lat])=>[lon*Math.PI/180,Math.log(Math.tan(Math.PI/4+lat*Math.PI/360))];
 const rings=f=>f.geometry.type==='Polygon'?f.geometry.coordinates:f.geometry.coordinates.flat();
 const points=features.flatMap(f=>rings(f).flat().map(project));const xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);const minX=Math.min(...xs),maxX=Math.max(...xs),minY=Math.min(...ys),maxY=Math.max(...ys),scale=Math.min(744/(maxX-minX),574/(maxY-minY));const ox=(800-(maxX-minX)*scale)/2,oy=25;
 const xy=coord=>{const [x,y]=project(coord);return[(x-minX)*scale+ox,(maxY-y)*scale+oy]};
 const ns='http://www.w3.org/2000/svg';$('map-shapes').replaceChildren();
 for(const f of features){const p=byGeoid.get(f.properties.GEOID),path=document.createElementNS(ns,'path');path.setAttribute('d',rings(f).map(r=>r.map((c,i)=>(i?'L':'M')+xy(c).map(v=>v.toFixed(2)).join(',')).join(' ')+'Z').join(' '));path.setAttribute('fill-rule','evenodd');path.setAttribute('tabindex','0');path.setAttribute('role','button');path.setAttribute('aria-label',nice(p.parish)+' Parish, '+fmt(p.total)+' reported ballots');path.setAttribute('aria-pressed','false');path.dataset.code=p.parish_code;const title=document.createElementNS(ns,'title');path.append(title);path.addEventListener('click',()=>{if(!moved)choose(p.parish_code)});path.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(p.parish_code)}});path.addEventListener('pointerenter',()=>{$('map-readout').textContent=nice(p.parish)+' Parish: '+fmt(p.total)+' ballots · '+$('map-metric').selectedOptions[0].textContent+': '+($('map-metric').value==='total'?fmt(p.total):pct(metric(p)))});$('map-shapes').append(path);paths.set(p.parish_code,path)}
 $('map-loading').hidden=true;redraw();selection();document.documentElement.dataset.mapReady='true';
}
function applyView(){$('map-svg').setAttribute('viewBox',view.join(' '))}
function zoom(factor){const w=Math.max(160,Math.min(1600,view[2]*factor)),h=w*660/800;view=[view[0]+(view[2]-w)/2,view[1]+(view[3]-h)/2,w,h];applyView()}
$('zoom-in').addEventListener('click',()=>zoom(.8));$('zoom-out').addEventListener('click',()=>zoom(1.25));$('map-reset').addEventListener('click',()=>{view=[0,0,800,660];applyView();if(data)choose('state')});
$('map-svg').addEventListener('pointerdown',e=>{moved=false;if(e.pointerType==='mouse'&&e.button===0)drag={x:e.clientX,y:e.clientY,view:[...view]}});
window.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.x,dy=e.clientY-drag.y;if(Math.abs(dx)+Math.abs(dy)>6)moved=true;if(moved){const rect=$('map-svg').getBoundingClientRect();view=[drag.view[0]-dx*drag.view[2]/rect.width,drag.view[1]-dy*drag.view[3]/rect.height,drag.view[2],drag.view[3]];applyView()}});
window.addEventListener('pointerup',()=>{drag=null});
function table(){const q=$('parish-search').value.trim().toLowerCase(),sort=$('parish-sort').value,rows=data.parishes.filter(p=>p.parish.toLowerCase().includes(q));rows.sort((a,b)=>sort==='name'?a.parish.localeCompare(b.parish):sort==='absentee'?b.absentee/b.total-a.absentee/a.total:b.total-a.total);$('parish-table').replaceChildren();for(const p of rows){const tr=node('tr'),td=node('td'),button=node('button',nice(p.parish));button.addEventListener('click',()=>{choose(p.parish_code);$('parish-map').scrollIntoView({behavior:'auto'})});td.append(button);tr.append(td);for(const value of [fmt(p.total),fmt(p.in_person),fmt(p.absentee),pct(p.breakdowns.party.democratic/p.total),pct(p.breakdowns.party.republican/p.total),pct(p.breakdowns.party.no_party/p.total)])tr.append(node('td',value));$('parish-table').append(tr)}$('table-count').textContent=rows.length+' of 64 parishes'}
function scenario(){if(!data)return;const id=$('calculator-geography').value,p=geography(id),r=Number($('additional-rate').value),extra=Math.round(p.total*r/100);$('additional-label').textContent=r+'%';$('scenario-geography').textContent=geographyName(id).toUpperCase();$('scenario-observed').textContent=fmt(p.total);$('scenario-additional').textContent=fmt(extra);$('scenario-total').textContent=fmt(p.total+extra)}
function benchmark(){const r=Number($('ev-scenario').value),n=Math.round(2978143*r/100);$('ev-scenario-rate').textContent=r+'%';$('ev-scenario-total').textContent=fmt(n);if(data)$('benchmark-additional').textContent=fmt(n-data.statewide.total)+' more than the recorded October 27 snapshot.'}
function download(){const head=['SOS parish code','Census GEOID','Parish','Reported ballots','In person','Absentee','Democratic','Republican','No Party','Other party','White','Black','Other race'],rows=data.parishes.map(p=>[p.parish_code,p.geoid,p.parish,p.total,p.in_person,p.absentee,...Object.values(p.breakdowns.party),...Object.values(p.breakdowns.race)]);const text=[head,...rows].map(r=>r.map(x=>'"'+String(x).replaceAll('"','""')+'"').join(',')).join('\r\n');const url=URL.createObjectURL(new Blob(['\uFEFF'+text],{type:'text/csv;charset=utf-8'}));const a=node('a');a.href=url;a.download='Louisiana_early_voting_20261027.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
function polls(){const rows=[['Edmonds (R)',13.8,colors.republican],['Banks (D)',13.2,colors.democratic],['Miguez (R)',9.7,colors.republican],['Garcia (D)',7.7,colors.democratic],['Forbes (D)',7.6,colors.democratic],['Undecided',35.7,colors.other]];$('poll-bars').replaceChildren();for(const [name,value,color] of rows){const row=node('div',undefined,'bar-row'),label=node('div',undefined,'bar-label');label.append(node('span',name),node('strong',value+'%'));const track=node('div',undefined,'bar-track'),fill=node('span',undefined,'bar-fill');fill.style.width=value+'%';fill.style.background=color;track.append(fill);row.append(label,track);$('poll-bars').append(row)}}
function registration(d){need(d.districts.length===6,'Registration districts missing');need(d.districts.reduce((s,x)=>s+x.total_registered,0)===2978143,'Registration control mismatch');$('district-cards').replaceChildren();for(const p of d.districts){const card=node('article',undefined,'district-card');card.append(node('h3','Congressional District '+p.district),node('strong',fmt(p.total_registered)),node('p','Registered voters · '+p.black_share_pct.toFixed(2)+'% Black registration'));const key=node('div',undefined,'party-key');for(const [label,share,cls] of [['Dem',p.democratic_share_pct,'dem'],['Rep',p.republican_share_pct,'rep'],['No Party',p.no_party_share_pct,'nop']])key.append(node('span',label+' '+share.toFixed(2)+'%','key '+cls));card.append(key);$('district-cards').append(card)}}
async function init(){
 try{
  data=validate(await json('data/processed/early_voting_2026.json'));
  $('ev-total').textContent=fmt(data.statewide.total);$('ev-inperson').textContent=fmt(data.statewide.in_person);$('ev-absentee').textContent=fmt(data.statewide.absentee);$('inperson-share').textContent=pct(data.statewide.in_person/data.statewide.total)+' of reported ballots';$('absentee-share').textContent=pct(data.statewide.absentee/data.statewide.total)+' of reported ballots';
  addOptions($('parish-select'));addOptions($('calculator-geography'));selection();table();scenario();benchmark();$('download-data').disabled=false;$('use-in-calculator').disabled=false;
  $('parish-select').addEventListener('change',e=>choose(e.target.value));$('composition').addEventListener('change',selection);$('map-metric').addEventListener('change',redraw);$('parish-search').addEventListener('input',table);$('parish-sort').addEventListener('change',table);$('additional-rate').addEventListener('input',scenario);$('calculator-geography').addEventListener('change',scenario);$('reset-scenario').addEventListener('click',()=>{$('additional-rate').value='100';scenario()});$('use-in-calculator').addEventListener('click',()=>{$('calculator-geography').value=selected;scenario();$('calculator').scrollIntoView({behavior:'auto'})});$('download-data').addEventListener('click',download);document.documentElement.dataset.dataReady='true';
  try{mapGeometry(await json('data/louisiana_parishes_2026.geojson'))}catch(e){$('map-loading').textContent='Map unavailable. The parish menu and comparison table remain available.';console.error(e)}
 }catch(e){$('data-status').textContent='Interactive data could not be loaded or did not pass validation. The headline figures show the verified October 27 snapshot saved with this page. Review the source files before reuse.';$('data-status').classList.add('error');$('map-loading').textContent='Interactive data unavailable.';console.error(e)}
}
$('ev-scenario').addEventListener('input',benchmark);benchmark();polls();init();
json('data/processed/registration_snapshot_2026-10-01.json').then(registration).catch(()=>{$('district-cards').textContent='Registration detail could not be loaded. Use the source record below.'});
})();
