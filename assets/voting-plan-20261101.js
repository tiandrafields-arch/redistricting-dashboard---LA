/* Louisiana voting planner. Sources reviewed November 1, 2026. No dependencies. */
'use strict';
(() => {
  if (document.getElementById('voting-plan')) return;
  const $ = id => document.getElementById(id);
  const URLS = Object.freeze({
    voter: 'https://voterportal.sos.la.gov/Home/VoterLogin',
    address: 'https://voterportal.sos.la.gov/Home/AddressLogin',
    parish: 'https://voterportal.sos.la.gov/Home/ParishLogin',
    registrar: 'https://voterportal.sos.la.gov/Registrar',
    dates: 'https://www.sos.la.gov/elections-voting/election-dates',
    faq: 'https://www.sos.la.gov/elections-voting/voting-on-election-day-faqs',
    changes: 'https://www.sos.la.gov/elections-voting/polling-locations',
    rules: 'https://www.sos.la.gov/elections-voting/how-candidates-are-elected',
    college: 'https://www.archives.gov/electoral-college/about',
    rides: 'https://powercoalition.org/powerrides/',
    rta: 'https://www.norta.com/news-list/rta-providing-fare-free-transportation-for-early-voting-and-election-day'
  });
  const names = 'Acadia|Allen|Ascension|Assumption|Avoyelles|Beauregard|Bienville|Bossier|Caddo|Calcasieu|Caldwell|Cameron|Catahoula|Claiborne|Concordia|De Soto|East Baton Rouge|East Carroll|East Feliciana|Evangeline|Franklin|Grant|Iberia|Iberville|Jackson|Jefferson|Jefferson Davis|Lafayette|Lafourche|LaSalle|Lincoln|Livingston|Madison|Morehouse|Natchitoches|Orleans|Ouachita|Plaquemines|Pointe Coupee|Rapides|Red River|Richland|Sabine|St. Bernard|St. Charles|St. Helena|St. James|St. John the Baptist|St. Landry|St. Martin|St. Mary|St. Tammany|Tangipahoa|Tensas|Terrebonne|Union|Vermilion|Vernon|Washington|Webster|West Baton Rouge|West Carroll|West Feliciana|Winn'.split('|');
  const reviewed = 'November 4, 2026';
  const election = 'Saturday, December 12, 2026';
  const hours = '7 a.m. to 8 p.m. Central Time';
  let snapshot = null;
  let packet = null;
  const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const link = (url, text) => `<a href="${url}" target="_blank" rel="noopener noreferrer">${text}</a>`;
  const options = '<option value="">Choose your parish</option>' + names.map((name, i) => `<option value="${String(i + 1).padStart(2, '0')}">${name}</option>`).join('');
  const parishName = code => names[Number(code) - 1];
  const tasks = [
    ['Confirm each voter\'s assigned precinct and Election Day polling address in GeauxVote.', URLS.voter],
    ['Check for polling location changes again before departure.', URLS.changes],
    ['Review identification and voter identification affidavit guidance.', URLS.faq],
    ['Confirm transportation coverage, hours, accessibility and a return trip directly with the provider.', URLS.rides],
    ['Review official transportation rules before offering driver payment or reimbursement.', URLS.faq],
    ['Assign a coordinator, backup contact and volunteer shifts. Keep private contact records in your own secure system.', ''],
    ['Set departure times with travel and waiting time before the 8 p.m. closing time.', URLS.dates],
    ['Share the SOS elections hotline: 1 800 883 2805. Voters in line at 8 p.m. may vote.', URLS.faq],
    ['Confirm completed rides and return arrangements without recording vote choices.', ''],
    ['Keep names, birth information, phone numbers and pickup addresses out of public files.', '']
  ];
  const style = document.createElement('style');
  style.textContent = `
#voting-plan{margin:24px 0 40px;scroll-margin-top:90px;border:1px solid #bdcddd;border-radius:18px;overflow:hidden;background:#fff;color:#172c47;font-family:inherit}#voting-plan *{box-sizing:border-box}#voting-plan [hidden]{display:none!important}.vp-hero{padding:28px;background:#133856;color:#fff}.vp-kicker{font-size:12px;letter-spacing:.12em;font-weight:700;margin:0 0 8px}.vp-hero h2{font-size:clamp(28px,4vw,42px);line-height:1.1;margin:10px 0}.vp-hero p{max-width:70ch;line-height:1.5}.vp-hero a{color:#fff}.vp-actions{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0}.vp-button{display:inline-flex;align-items:center;justify-content:center;min-height:46px;padding:11px 16px;border:1px solid #133856;border-radius:8px;background:#133856;color:#fff!important;text-decoration:none!important;font-family:inherit;font-size:15px;font-weight:600;line-height:1.35;cursor:pointer}.vp-button.vp-light{background:#fff;color:#133856!important;border-color:#fff}.vp-button.vp-outline{background:#fff;color:#133856!important;border-color:#b6c7d9}.vp-button:disabled{opacity:.5;cursor:not-allowed}.vp-body{padding:24px}.vp-tabs{display:flex;gap:8px;border-bottom:1px solid #d5dfea;margin-bottom:22px;padding-bottom:12px}.vp-tabs button{flex:1}.vp-tabs [aria-selected=true]{background:#133856;color:#fff!important}.vp-grid{display:grid;grid-template-columns:1fr 1fr;gap:22px}.vp-card{background:#f5f8fb;border:1px solid #d6e0eb;border-radius:12px;padding:20px;min-width:0}.vp-card h3{margin:0 0 12px;font-size:22px}.vp-card h4{margin:20px 0 8px}.vp-card p,.vp-body li{line-height:1.55}.vp-field{display:block;margin:14px 0 6px;font-weight:650}.vp-input{width:100%;min-height:46px;border:1px solid #9cb1c6;border-radius:7px;padding:10px;background:#fff;font:inherit;color:#172c47}.vp-small{font-size:14px;line-height:1.55;color:#435b72}.vp-check{display:flex;gap:10px;align-items:flex-start;margin:18px 0;line-height:1.5;font-size:15px}.vp-check input{width:22px;height:22px;flex:none;margin-top:1px}.vp-note{border-left:4px solid #287d82;padding:12px 16px;background:#edf7f6;margin:18px 0;line-height:1.5}.vp-warning{border-color:#aa6400;background:#fff4e2}.vp-source-links{display:flex;flex-wrap:wrap;gap:12px;font-size:14px}.vp-preview{white-space:pre-wrap;overflow-wrap:anywhere;width:100%;font-family:inherit;font-size:14px;line-height:1.65;min-height:200px;resize:vertical}.vp-print-preview{padding:20px;background:#fff;border:1px solid #bcccdc;border-radius:10px;margin-top:20px}.vp-print-preview table{border-collapse:collapse;width:100%;font-size:14px}.vp-print-preview th,.vp-print-preview td{border:1px solid #ccd6e1;text-align:left;vertical-align:top;padding:8px}.vp-print-preview td:first-child{width:65%}.vp-print-preview h3{margin-top:0}.vp-print-preview a{overflow-wrap:anywhere}.vp-status{min-height:24px;font-size:14px;line-height:1.5}.vp-sticky{display:none}.vp-rides p{margin:10px 0}.vp-rule{margin-top:20px;border-top:1px solid #d4dfe9;padding-top:18px}.vp-rule summary{cursor:pointer;font-weight:700}.vp-footer{font-size:13px;color:#435b72;margin-top:22px}.vp-hidden-print{display:none}#voting-plan :focus-visible,.vp-sticky :focus-visible{outline:3px solid #b75f00;outline-offset:3px}#vp-share-fallback{height:180px}#vp-printout{display:none}
@media(max-width:680px){.vp-grid{grid-template-columns:1fr}.vp-body,.vp-hero{padding:20px}.vp-card{padding:16px}.vp-tabs{gap:6px}.vp-tabs button{font-size:14px;padding:10px}.vp-actions .vp-button{flex:1 1 auto}.vp-sticky{display:flex;position:fixed;bottom:0;left:0;right:0;z-index:100;background:#fff;border-top:1px solid #b6c7d9;padding:8px 12px calc(8px + env(safe-area-inset-bottom));gap:8px}.vp-sticky a{flex:1;font-size:13px;padding:10px 6px}body{padding-bottom:94px}.vp-print-preview{padding:14px}.vp-print-preview th,.vp-print-preview td{padding:5px;font-size:12px}}
@media print{body.vp-printing{padding:0!important;margin:0!important;background:#fff!important}body.vp-printing>*:not(#vp-printout){display:none!important}body.vp-printing #vp-printout{display:block!important;color:#000;font:11pt/1.45 Arial,sans-serif}#vp-printout h1{font-size:23pt;margin:0 0 10pt}#vp-printout h2{font-size:15pt;margin:18pt 0 8pt}#vp-printout p{margin:7pt 0}#vp-printout table{border-collapse:collapse;width:100%;font-size:10pt}#vp-printout th,#vp-printout td{border:1px solid #999;padding:7pt;text-align:left;vertical-align:top}#vp-printout tr{break-inside:avoid}#vp-printout th:first-child,#vp-printout td:first-child{width:64%}#vp-printout th:not(:first-child),#vp-printout td:not(:first-child){width:18%}#vp-printout thead{display:table-header-group}#vp-printout a{color:#000;overflow-wrap:anywhere}#vp-printout .vp-page{break-before:page}#vp-printout .vp-print-brand{font-size:10pt;letter-spacing:.03em;border-bottom:2pt solid #173e65;padding-bottom:9pt;margin-bottom:16pt}#vp-printout .vp-small{font-size:9pt;color:#222}#vp-printout pre{white-space:pre-wrap;overflow-wrap:anywhere;font:11pt/1.5 Arial,sans-serif}@page{size:letter;margin:.6in}}
`;
  document.head.append(style);
  const section = document.createElement('section');
  section.id = 'voting-plan';
  section.setAttribute('aria-labelledby', 'vp-title');
  section.innerHTML = `
<div class="vp-hero"><p class="vp-kicker">YOUR ELECTION DAY PLAN</p><h2 id="vp-title">Know where. Plan how. Be ready.</h2><p><strong>${election}</strong><br>Polls open ${hours}. If you are in line at 8 p.m., you may vote.</p><div class="vp-actions"><a class="vp-button vp-light" href="${URLS.voter}" target="_blank" rel="noopener noreferrer">Find my precinct and polling place</a><a class="vp-button vp-light" href="#vp-tools">Build a voting plan</a></div><p class="vp-small" style="color:#e2edf5">Confirm your December 12 ballot and assigned polling place, not simply the nearest location. House runoffs are in Districts 5 and 6; other local contests may appear on your ballot. Official lookup opens on the Louisiana Secretary of State website.</p></div>
<div class="vp-body" id="vp-tools"><div id="vp-expired" class="vp-note vp-warning" hidden>This planner is an archive for December 12, 2026. That election has passed. Check the official election calendar before making a plan for another election.</div>
<div class="vp-tabs" role="tablist" aria-label="Choose a planning tool"><button type="button" id="vp-tab-voter" class="vp-button vp-outline" role="tab" aria-selected="true" aria-controls="vp-voter" tabindex="0">For voters</button><button type="button" id="vp-tab-org" class="vp-button vp-outline" role="tab" aria-selected="false" aria-controls="vp-org" tabindex="-1">For organizations</button></div>
<div id="vp-voter" role="tabpanel" aria-labelledby="vp-tab-voter"><div class="vp-grid"><div class="vp-card"><h3>Make my voting plan</h3><p class="vp-small">First confirm your assignment in the ${link(URLS.voter, 'official voter lookup')} or ${link(URLS.address, 'search by address')}. Then copy your polling information here. This dashboard cannot verify it.</p><form id="vp-voter-form" autocomplete="off"><label class="vp-field" for="vp-parish">Parish</label><select class="vp-input" id="vp-parish" required>${options}</select><label class="vp-field" for="vp-precinct">Precinct, if known</label><input class="vp-input" id="vp-precinct" maxlength="40" placeholder="Copy from GeauxVote"><label class="vp-field" for="vp-address">Confirmed polling place address</label><input class="vp-input" id="vp-address" required maxlength="220" placeholder="Street address, city, Louisiana" aria-describedby="vp-address-help"><p id="vp-address-help" class="vp-small">Enter the polling address, not your home or pickup address.</p><label class="vp-field" for="vp-time">Planned departure time in Central Time</label><input class="vp-input" id="vp-time" type="time" required max="19:59"><p class="vp-small">Leave enough time for the trip and a line before polls close.</p><label class="vp-field" for="vp-mode">How will you travel?</label><select class="vp-input" id="vp-mode"><option value="driving">Car or arranged ride</option><option value="transit">Public transit</option><option value="walking">Walking</option></select><label class="vp-check"><input type="checkbox" id="vp-confirm" required><span>I confirmed my December 12 ballot and assigned polling place using GeauxVote or my registrar.</span></label><div class="vp-actions"><button class="vp-button" type="submit">Build my plan</button><button class="vp-button vp-outline" type="button" id="vp-clear">Clear entries</button></div></form></div>
<div class="vp-card"><h3>My plan</h3><p id="vp-empty" class="vp-small">Complete the fields to make a plan you can share with someone helping you reach the polls. Creating a plan does not request or confirm a ride.</p><textarea id="vp-personal-preview" class="vp-input vp-preview" aria-label="Your voting plan" readonly hidden></textarea><div id="vp-personal-actions" hidden><div class="vp-actions"><button class="vp-button" type="button" id="vp-directions">Get directions</button><button class="vp-button vp-outline" type="button" id="vp-share">Share plan</button><button class="vp-button vp-outline" type="button" id="vp-copy">Copy plan</button><button class="vp-button vp-outline" type="button" id="vp-print-personal">Print or save PDF</button></div></div><p id="vp-personal-status" class="vp-status" role="status" aria-live="polite"></p><div class="vp-note"><strong>Before you leave</strong><p class="vp-small">Review your sample ballot and check for polling location changes. Bring accepted identification. Without it, ask about a voter identification affidavit. ${link(URLS.faq, 'Read official voting guidance')}.</p></div></div></div></div>
<div id="vp-org" role="tabpanel" aria-labelledby="vp-tab-org" hidden><div class="vp-grid"><div class="vp-card"><h3>Build a parish planning packet</h3><p class="vp-small">Choose a parish to create an organization checklist with election information, official links and transportation planning steps. This is not a voter list, route schedule or confirmed ride roster.</p><form id="vp-org-form" autocomplete="off"><label class="vp-field" for="vp-org-name">Organization name, optional</label><input class="vp-input" id="vp-org-name" maxlength="90" placeholder="Your organization"><label class="vp-field" for="vp-org-parish">Parish</label><select class="vp-input" id="vp-org-parish" required>${options}</select><div class="vp-actions"><button class="vp-button" type="submit">Generate parish plan</button></div></form><p class="vp-small">Print the packet or use your browser to save it as a PDF. Download the checklist as a CSV file that opens in Excel or Google Sheets.</p></div><div class="vp-card"><h3>Built for volunteers</h3><p>Confirm polling assignments, coordinate departure and return arrangements, and assign tasks to your team.</p><p class="vp-small">House runoffs are in Districts 5 and 6. Other local contests may appear on a voter's ballot. Confirm that each person has a December 12 contest and verify their assignment. A parish selection does not establish anyone's precinct. Verify every voter individually through the official portal. Keep private contact and pickup details in your organization's secure system.</p><div class="vp-actions"><a class="vp-button vp-outline" href="${URLS.parish}" target="_blank" rel="noopener noreferrer">Official parish information</a><a class="vp-button vp-outline" href="${URLS.registrar}" target="_blank" rel="noopener noreferrer">Find a parish registrar</a></div></div></div><div id="vp-org-results" hidden><div class="vp-actions"><button type="button" class="vp-button" id="vp-print-org">Print or save PDF</button><button type="button" class="vp-button vp-outline" id="vp-csv">Download checklist CSV</button><button type="button" class="vp-button vp-outline" id="vp-org-map">View parish data</button></div><p class="vp-small">For PDF, choose your browser's print destination or Save to Files option. The CSV is an editable checklist, not an Excel workbook.</p><div id="vp-org-preview" class="vp-print-preview"></div></div><p id="vp-org-status" class="vp-status" role="status" aria-live="polite"></p></div>
<div class="vp-card vp-rides" style="margin-top:24px"><h3>Need transportation?</h3><p>${link(URLS.rides, 'Power Coalition ride request resource')} offers an external request form. Confirm parish coverage, service hours, accessible vehicles and your return trip directly with the provider. A request is not a confirmed ride.</p><p id="vp-rta" hidden></p><p class="vp-small">No December transportation service or no fare offer has been verified for this planner. Prior November offers are not evidence of December availability. Contact providers directly. This dashboard does not book rides or promise availability.</p></div>
<details class="vp-rule"><summary>December election information</summary><p>Saturday, December 12, 2026. Polls are open 7 a.m. to 8 p.m. Central Time. House runoffs are in Districts 5 and 6. Check your December sample ballot for congressional and any local contests.</p><p>Register in person or by mail by November 12, or online by November 21. Early voting runs November 28 through December 5, excluding November 29, from 8:30 a.m. to 6 p.m. Ordinary absentee request deadline: December 8 at 4:30 p.m. Ordinary receipt deadline: December 11 at 4:30 p.m. Military and overseas exceptions apply.</p><div class="vp-source-links">${link(URLS.dates, 'Official election calendar')}${link(URLS.rules, 'Official election rules')}</div></details>
<div class="vp-note"><strong>Privacy first.</strong> This planner does not send form entries to a database or save them in browser storage. Entries remain on this page until you clear or leave it. Printing, downloading, sharing or opening directions sends the information to the destination you choose. External services have their own privacy policies.</div>
<div class="vp-source-links">${link(URLS.dates, 'Election dates')}${link(URLS.faq, 'Voter rights and identification')}${link(URLS.changes, 'Polling location changes')}<a href="tel:+18008832805">SOS elections hotline: 1 800 883 2805</a></div><p class="vp-footer">Planning guidance checked ${reviewed}. This does not change the date of the dashboard's participation data. Independent civic information by Tiandra Fields, Provisional Consulting LLC. Not an official government tool.</p></div>`;
  const main = $('main') || document.querySelector('main');
  if (!main) return;
  main.prepend(section);
  const nav = document.querySelector('.nav-inner');
  if (nav && !nav.querySelector('a[href="#voting-plan"]')) {
    const item = document.createElement('a'); item.href = '#voting-plan'; item.textContent = 'Voting plan'; nav.prepend(item);
  }
  const intro = document.querySelector('#early-voting .intro');
  if (intro) intro.textContent = 'A clear view of reported participation across Louisiana. Explore where ballots were recorded, who has voted so far, and what different participation assumptions would mean.';
  const composition = document.querySelector('.mini-heading h4');
  if (composition && composition.textContent.trim() === 'Electorate composition') composition.textContent = 'Who voted early or absentee';
  const sticky = document.createElement('div'); sticky.className = 'vp-sticky'; sticky.setAttribute('aria-label', 'Voting shortcuts');
  sticky.innerHTML = `<a class="vp-button" href="${URLS.voter}" target="_blank" rel="noopener noreferrer">Find my polling place</a><a class="vp-button vp-outline" href="#voting-plan">Make a plan</a>`;
  document.body.append(sticky);
  const printout = document.createElement('div'); printout.id = 'vp-printout'; document.body.append(printout);
  const expired = () => Date.now() > Date.parse('2026-12-13T02:00:00Z');
  const archiveNote = () => expired() ? '<p><strong>Archived plan: the December 12, 2026 election has passed. Check the official calendar for future elections.</strong></p>' : '';
  const refreshArchive = () => { $('vp-expired').hidden = !expired(); };
  refreshArchive();
  window.addEventListener('pageshow', refreshArchive);
  function selectTab(kind) {
    for (const k of ['voter', 'org']) {
      const active = k === kind;
      $('vp-tab-' + k).setAttribute('aria-selected', String(active));
      $('vp-tab-' + k).tabIndex = active ? 0 : -1;
      $('vp-' + k).hidden = !active;
    }
    updateRides();
  }
  for (const kind of ['voter', 'org']) {
    $('vp-tab-' + kind).addEventListener('click', () => selectTab(kind));
    $('vp-tab-' + kind).addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === 'Home' ? 'voter' : event.key === 'End' ? 'org' : kind === 'voter' ? 'org' : 'voter';
      selectTab(next); $('vp-tab-' + next).focus();
    });
  }
  function updateRides() {
    const code = $('vp-org').hidden ? $('vp-parish').value : $('vp-org-parish').value;
    $('vp-rta').hidden = true;
  }
  function personal() {
    const form = $('vp-voter-form');
    const address = $('vp-address').value.trim();
    $('vp-address').setCustomValidity(address.length < 8 ? 'Enter the full polling address confirmed by the official lookup.' : '');
    if (!form.reportValidity()) return null;
    const code = $('vp-parish').value;
    if (!parishName(code)) return null;
    const [h, m] = $('vp-time').value.split(':').map(Number);
    const time = `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'a.m.' : 'p.m.'}`;
    const text = `${expired() ? 'ARCHIVED ELECTION PLAN\n' : ''}MY LOUISIANA VOTING PLAN\n${election}\nPolls: ${hours}\n\nParish: ${parishName(code)}\nPrecinct: ${$('vp-precinct').value.trim() || 'See official voter lookup'}\nPolling place: ${address}\nPlanned departure: ${time} Central Time\nTravel: ${$('vp-mode').selectedOptions[0].textContent}\n\nI confirmed this assignment using GeauxVote or my registrar. This dashboard has not independently verified it.\n\nLeave enough time to arrive before 8 p.m. Voters in line at 8 p.m. may vote. Bring accepted identification or ask about a voter identification affidavit. Check for location changes before leaving.\n\nConfirm your ride and return trip directly. This plan does not book a ride.\nOfficial lookup: ${URLS.voter}\nVoting guidance: ${URLS.faq}\nSOS hotline: 1 800 883 2805\nInformation checked ${reviewed}.\nTiandra Fields | Provisional Consulting LLC`;
    $('vp-personal-preview').value = text; $('vp-personal-preview').hidden = false;
    $('vp-personal-actions').hidden = false; $('vp-empty').hidden = true;
    return {text, address, mode: $('vp-mode').value};
  }
  $('vp-voter-form').addEventListener('submit', event => { event.preventDefault(); if (personal()) $('vp-personal-status').textContent = 'Your plan is ready. Review it before sharing.'; });
  function invalidatePersonal() { $('vp-personal-actions').hidden = true; $('vp-personal-preview').hidden = true; $('vp-empty').hidden = false; $('vp-personal-status').textContent = ''; }
  for (const id of ['vp-parish', 'vp-precinct', 'vp-address']) $(id).addEventListener('input', () => { $('vp-confirm').checked = false; invalidatePersonal(); updateRides(); });
  $('vp-address').addEventListener('input', () => $('vp-address').setCustomValidity(''));
  for (const id of ['vp-time', 'vp-mode', 'vp-confirm']) $(id).addEventListener('input', invalidatePersonal);
  $('vp-clear').addEventListener('click', () => { $('vp-voter-form').reset(); $('vp-address').setCustomValidity(''); $('vp-personal-preview').value = ''; printout.replaceChildren(); invalidatePersonal(); updateRides(); });
  $('vp-directions').addEventListener('click', () => {
    const plan = personal(); if (!plan) return;
    const url = 'https://www.google.com/maps/dir/?api=1&destination=' + encodeURIComponent(plan.address) + '&travelmode=' + plan.mode;
    window.open(url, '_blank', 'noopener,noreferrer');
    $('vp-personal-status').textContent = 'Directions open in Google Maps using the polling address you entered. This does not verify the address or reserve transportation.';
  });
  async function copyPlan() {
    const plan = personal(); if (!plan) return;
    try { if (!navigator.clipboard) throw new Error('Clipboard unavailable'); await navigator.clipboard.writeText(plan.text); $('vp-personal-status').textContent = 'Plan copied. Share it privately with the person helping you.'; }
    catch (_) { $('vp-personal-preview').focus(); $('vp-personal-preview').select(); $('vp-personal-status').textContent = 'Select and copy the plan shown above. Automatic copying is unavailable in this browser.'; }
  }
  $('vp-copy').addEventListener('click', copyPlan);
  $('vp-share').addEventListener('click', async () => {
    const plan = personal(); if (!plan) return;
    if (!navigator.share) { await copyPlan(); return; }
    try { await navigator.share({title: 'My Louisiana voting plan', text: plan.text}); $('vp-personal-status').textContent = 'Sharing completed.'; }
    catch (error) { $('vp-personal-status').textContent = error.name === 'AbortError' ? 'Sharing canceled. Your plan is still here.' : 'Sharing is unavailable. Use Copy plan instead.'; }
  });
  const brand = '<div class="vp-print-brand">TIANDRA FIELDS | PROVISIONAL CONSULTING LLC</div>';
  function printPacket(html) { printout.innerHTML = brand + html; document.body.classList.add('vp-printing'); window.print(); }
  window.addEventListener('afterprint', () => document.body.classList.remove('vp-printing'));
  $('vp-print-personal').addEventListener('click', () => { const plan = personal(); if (plan) printPacket('<pre>' + esc(plan.text) + '</pre>'); });
  function ballotContext(code) {
    if (!snapshot) return 'Participation data are unavailable in this packet. Use the dashboard for its dated source snapshot.';
    const row = snapshot.parishes.find(p => p.parish_code === code);
    if (!row) return 'No verified parish participation record is loaded.';
    const date = new Date(snapshot.reporting_period_end + 'T12:00:00Z').toLocaleDateString('en-US', {month:'long', day:'numeric', year:'numeric', timeZone:'UTC'});
    return `Historical November election: ${Number(row.total).toLocaleString('en-US')} reported early ballots through ${date}. This is a ballot count, not a turnout rate, unvoted voter count or certified election result.`;
  }
  function organizationPacket() {
    if (!$('vp-org-form').reportValidity()) return null;
    const code = $('vp-org-parish').value, name = parishName(code);
    if (!name) return null;
    const org = $('vp-org-name').value.trim() || 'Community organization';
    const context = ballotContext(code);
    const html = `${archiveNote()}<h1>${esc(name)} Parish voting plan</h1><p><strong>${esc(org)}</strong></p><p>${election}<br>Polls: ${hours}</p><p class="vp-small">Information reviewed ${reviewed}. Independent planning aid, not an official precinct assignment or ride confirmation.</p><h2>Parish context</h2><p>${esc(context)}</p><p class="vp-small">Source: the dashboard's verified SOS workbook snapshot. Small counts do not establish low turnout rates. This packet does not rank communities by party, race or candidate preference.</p><h2>Confirm before departure</h2><p>Each voter must confirm their assigned Election Day polling place. Parish selection alone cannot identify a precinct. Recheck the official portal before leaving. A registrar's office is not automatically the voter's Election Day polling place.</p><p>Bring accepted identification or ask about a voter identification affidavit. Voters in line at 8 p.m. may vote. SOS elections hotline: 1 800 883 2805.</p><p>Use the official registrar directory and choose ${esc(name)} Parish. Confirm local contacts and polling information directly. The Secretary of State maintains the official contact directory.</p><h2>Transportation</h2><p>Check the Power Coalition ride request resource. Confirm service area, availability, accessibility, pickup and return arrangements directly with the provider. A request is not a confirmed ride.</p><p>No December transportation service has been verified in this packet. Confirm local availability directly before offering a ride.</p><h2>Official links and provider sources</h2><p class="vp-small">Voter lookup: ${link(URLS.voter, URLS.voter)}<br>Registrar directory: ${link(URLS.registrar, URLS.registrar)}<br>Election dates: ${link(URLS.dates, URLS.dates)}<br>Voting and transportation rules: ${link(URLS.faq, URLS.faq)}<br>Polling changes: ${link(URLS.changes, URLS.changes)}<br>Ride request resource: ${link(URLS.rides, URLS.rides)}</p><h2 class="vp-page">Volunteer coordination checklist</h2><p>${esc(org)} | ${esc(name)} Parish | ${election}</p><table><thead><tr><th>Task</th><th>Owner</th><th>Status</th></tr></thead><tbody>${tasks.map(([task]) => `<tr><td>${esc(task)}</td><td>&nbsp;</td><td>&nbsp;</td></tr>`).join('')}</tbody></table><p class="vp-small">Keep voter names, birth information, phone numbers, pickup addresses and vote choices out of public files. Complete private coordination in your own secure system.</p><p class="vp-small">Prepared with the Louisiana Congressional Voter &amp; Participation Dashboard. Tiandra Fields | Provisional Consulting LLC.</p>`;
    packet = {code, name, org, context, html};
    $('vp-org-preview').innerHTML = html; $('vp-org-results').hidden = false;
    $('vp-org-status').textContent = 'Your parish packet is ready. Confirm local arrangements before distributing it.';
    return packet;
  }
  $('vp-org-form').addEventListener('submit', event => { event.preventDefault(); organizationPacket(); });
  for (const id of ['vp-org-parish', 'vp-org-name']) $(id).addEventListener('input', () => { packet = null; $('vp-org-results').hidden = true; $('vp-org-status').textContent = ''; updateRides(); });
  $('vp-print-org').addEventListener('click', () => { const p = organizationPacket(); if (p) printPacket(p.html); });
  function csvCell(value) {
    let text = String(value == null ? '' : value);
    if (/^[\s]*[=+@-]/.test(text) || /^[\t\r\n]/.test(text)) text = "'" + text;
    return '"' + text.replace(/"/g, '""') + '"';
  }
  $('vp-csv').addEventListener('click', () => {
    const p = organizationPacket(); if (!p) return;
    const rows = [['Organization','Parish','Election date','Task','Owner','Status','Notes','Source','Information reviewed']];
    tasks.forEach(([task, source]) => rows.push([p.org,p.name,election,task,'','Not started','',source,reviewed]));
    rows.push([p.org,p.name,election,'Reference: polling hours','','',hours,URLS.dates,reviewed]);
    rows.push([p.org,p.name,election,'Reference: official registrar directory','','','Select ' + p.name + ' Parish in the official directory.',URLS.registrar,reviewed]);
    rows.push([p.org,p.name,election,'Reference: dated participation snapshot','','',p.context,new URL('data/processed/early_voting_2026-11-03.json', document.baseURI).href,reviewed]);

    const csv = '\uFEFF' + rows.map(row => row.map(csvCell).join(',')).join('\r\n');
    const url = URL.createObjectURL(new Blob([csv], {type:'text/csv;charset=utf-8'}));
    const a = document.createElement('a'); a.href = url; a.download = 'Louisiana_' + p.name.replace(/[^a-z0-9]+/gi, '_') + '_Voting_Plan_20261212.csv';
    document.body.append(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 30000);
    $('vp-org-status').textContent = 'Checklist CSV prepared. Open it in Excel or Google Sheets. Private voter information is not included.';
  });
  $('vp-org-map').addEventListener('click', () => {
    const p = organizationPacket(); if (!p) return;
    const select = $('parish-select');
    if (select && !select.disabled && Array.from(select.options).some(o => o.value === p.code)) { select.value = p.code; select.dispatchEvent(new Event('change', {bubbles:true})); }
    if ($('parish-map')) $('parish-map').scrollIntoView({behavior:'auto'});
  });
  fetch('data/processed/early_voting_2026-11-03.json', {cache:'no-store'}).then(r => { if (!r.ok) throw new Error('No snapshot'); return r.json(); }).then(d => {
    if (d.status !== 'verified_snapshot' || !Array.isArray(d.parishes) || d.parishes.length !== 64 || !/^\d{4}-\d{2}-\d{2}$/.test(d.reporting_period_end)) return;
    if (!d.parishes.every(p => Number.isSafeInteger(p.total) && p.total >= 0) || new Set(d.parishes.map(p => p.parish_code)).size !== 64) return;
    if (d.parishes.reduce((sum, p) => sum + p.total, 0) !== d.statewide.total) return;
    snapshot = d;
  }).catch(() => { /* Official links and checklist remain usable without participation data. */ });
  if (location.hash === '#voting-plan' || location.hash === '#vp-tools') requestAnimationFrame(() => section.scrollIntoView());
})();
