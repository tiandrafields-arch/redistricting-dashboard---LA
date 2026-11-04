/* Compose the existing independently tested modules without replacing their data. */
'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const planner = $('voting-plan');
  const registration = $('registration');
  if (planner && registration) registration.after(planner);
  const intro = document.querySelector('#early-voting .intro');
  if (intro) intro.textContent = 'Explore recorded early and absentee ballots, parish data and voter registration. These statistics describe participation, not election results.';
  const labels = [
    ['#parish-map > .section-heading .eyebrow', '01 / PARISH PARTICIPATION DATA'],
    ['#polling-research > .section-heading .eyebrow', '03 / DISTRICT 6 SURVEY RESEARCH'],
    ['#house-races > .section-heading .eyebrow', '04 / CONGRESSIONAL RACE SNAPSHOTS'],
    ['#registration > .section-heading .eyebrow', '05 / REGISTRATION CONTEXT'],
    ['#voting-plan .vp-kicker', '06 / YOUR ELECTION DAY PLAN'],
    ['#methodology > .eyebrow', '07 / SOURCES AND ACCOUNTABILITY']
  ];
  for (const [selector, text] of labels) {
    const item = document.querySelector(selector);
    if (item) item.textContent = text;
  }
  // The Senate module renders asynchronously. Align its heading after rendering,
  // then disconnect instead of observing subsequent chart or tab interactions.
  const senate = $('senate-research');
  function alignSenate() {
    if (!senate) return;
    const label = senate.querySelector('.eyebrow');
    const text = '02 / SENATE SURVEY RESEARCH';
    if (label && label.textContent !== text) label.textContent = text;
    for (const paragraph of senate.querySelectorAll('p')) {
      const old = 'early voting counts, race, party registration, parish location or the participation calculator';
      if (paragraph.textContent.includes(old)) {
        paragraph.textContent = paragraph.textContent.replace(old, 'early voting counts, race, party registration or parish location');
      }
    }
  }
  alignSenate();
  if (senate && !['true', 'error'].includes(senate.dataset.ready)) {
    const observer = new MutationObserver(() => {
      alignSenate();
      if (['true', 'error'].includes(senate.dataset.ready)) observer.disconnect();
    });
    observer.observe(senate, {childList: true, subtree: true, attributes: true, attributeFilter: ['data-ready']});
  }
  const nav = document.querySelector('.nav-inner');
  const order = [
    ['runoffs', 'Runoffs'],
    ['election-results', 'Results and turnout'],
    ['early-voting', 'Early ballot statistics'],
    ['parish-map', 'Parish map'],
    ['senate-research', 'Senate'],
    ['polling-research', 'District 6'],
    ['house-races', 'Other House races'],
    ['registration', 'Registration'],
    ['voting-plan', 'Voting plan'],
    ['methodology', 'Sources']
  ];
  if (nav) {
    for (const [id, text] of order) {
      const matches = [...nav.querySelectorAll('a[href="#' + id + '"]')];
      const item = matches.shift() || document.createElement('a');
      for (const duplicate of matches) duplicate.remove();
      item.href = '#' + id;
      item.textContent = text;
      nav.append(item);
    }
  }
  document.documentElement.dataset.educationReady = 'true';
})();
