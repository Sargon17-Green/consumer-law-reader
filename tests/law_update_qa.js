'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const SOURCE = fs.readFileSync(path.join(__dirname, '../web/law-update.js'), 'utf8');
const LAW = 'israel-consumer-protection-law-1981';
const base = {
  schema_version: 1, law_id: LAW, current_revision_sequence: 1,
  law_text_last_amended_on: '2026-09-30',
  law_text_last_verified_on: '2026-10-28',
  next_scheduled_change_on: '2027-03-22',
  published_revision_sequence: 1, revision_status: 'editor_approved'
};

function browser(remote, local = 1, storage = new Map()) {
  const elements = {
    'law-editorial-status': { textContent: JSON.stringify({law_id: LAW, law_revision_sequence: local}) },
    'law-update-banner': { hidden: true },
    'law-update-detail': { textContent: '' },
    'law-update-releases': { href: '', textContent: '' }
  };
  let requests = [], docEvents = {}, winEvents = {};
  const document = {
    visibilityState: 'hidden',
    getElementById: id => elements[id] || null,
    addEventListener: (event, handler) => {docEvents[event] = handler;}
  };
  const window = {
    document,
    localStorage: {
      getItem: name => storage.has(name) ? storage.get(name) : null,
      setItem: (name, value) => storage.set(name, String(value))
    },
    fetch: async (url, options) => {
      requests.push({url, options});
      if (remote instanceof Error) throw remote;
      return { ok: true, text: async () => JSON.stringify(remote) };
    },
    setTimeout, clearTimeout,
    addEventListener: (name, handler) => {winEvents[name] = handler;}
  };
  vm.runInNewContext(SOURCE, {window, AbortController, console});
  return {window, elements, storage, requests,
          visibility: () => {document.visibilityState = 'visible'; docEvents.visibilitychange();},
          pageshow: () => winEvents.pageshow({persisted:true})};
}
async function main() {
  let t=browser(base);
  assert.equal(t.window.LawUpdate.validManifest(base),true);
  assert.equal(await t.window.LawUpdate.check(),false);
  assert.equal(t.elements['law-update-banner'].hidden,true,'same revision must not show update');
  assert.equal(t.requests.length,1);
  assert.match(t.requests[0].url,/^https:\/\/raw\.githubusercontent\.com\/Sargon17-Green\/consumer-law-reader\/main\/metadata\/law_update_manifest\.json\?_t=\d+$/);
  assert.equal(t.requests[0].options.cache,'no-store');
  assert.equal(t.requests[0].options.credentials,'omit');
  assert.equal(t.requests[0].options.referrerPolicy,'no-referrer');

  t=browser({...base, law_text_last_verified_on:'2026-11-30', next_scheduled_change_on:'2027-03-22'});
  await t.window.LawUpdate.check();
  assert.equal(t.elements['law-update-banner'].hidden,true,'verification or future date alone cannot trigger');
  t=browser({...base, next_scheduled_change_on:'2026-11-01'});
  await t.window.LawUpdate.check();
  assert.equal(t.elements['law-update-banner'].hidden,true,'scheduled date in the past is not an approved new text');

  const newer={...base,current_revision_sequence:2,law_text_last_amended_on:'2026-11-14',published_revision_sequence:1};
  t=browser(newer);
  assert.equal(await t.window.LawUpdate.check(),true);
  assert.equal(t.elements['law-update-banner'].hidden,false);
  assert.match(t.elements['law-update-detail'].textContent,/טרם פורסמה/);
  assert.equal(t.elements['law-update-releases'].href,'https://github.com/Sargon17-Green/consumer-law-reader/releases');
  const cached=t.storage;
  const offline=browser(new Error('offline'),1,cached);
  await offline.window.LawUpdate.check();
  assert.equal(offline.elements['law-update-banner'].hidden,false,'a confirmed stale copy stays flagged offline');

  t=browser({...newer,published_revision_sequence:2,malicious_download:'javascript:alert(1)'});
  await t.window.LawUpdate.check();
  assert.match(t.elements['law-update-detail'].textContent,/יש להתקין מהדורה חדשה/);
  assert.equal(t.elements['law-update-releases'].href,'https://github.com/Sargon17-Green/consumer-law-reader/releases');

  for (const bad of [
    {...base,schema_version:2},
    {...base,law_id:'other-law'},
    {...base,revision_status:'draft'},
    {...base,current_revision_sequence:1.5},
    {...base,published_revision_sequence:2},
    {...base,law_text_last_amended_on:'2026-02-30'},
    {...base,next_scheduled_change_on:'2027-02-29'}
  ]) {
    t=browser(bad);
    assert.equal(t.window.LawUpdate.validManifest(bad),false);
    await t.window.LawUpdate.check();
    assert.equal(t.elements['law-update-banner'].hidden,true,'invalid manifest cannot trigger update');
  }

  t=browser({...newer,published_revision_sequence:2},2);
  await t.window.LawUpdate.check();
  assert.equal(t.elements['law-update-banner'].hidden,true,'installed current revision requires no update');
  t=browser(newer);
  t.window.LawUpdate.install();
  await t.window.LawUpdate.check();
  const first=t.requests.length;
  t.visibility();
  await t.window.LawUpdate.check();
  assert.equal(t.requests.length,first+1,'foreground transition issues a new GitHub GET');
  t.pageshow();
  await t.window.LawUpdate.check();
  assert.equal(t.requests.length,first+2,'restored page issues a new GitHub GET');
  console.log('law update contract QA PASS: baseline, future dates, stale, offline, hostile JSON, resume');
}
main().catch(error => {console.error(error);process.exitCode=1;});
