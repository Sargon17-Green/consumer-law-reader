// Verify the original calendar widget against controlled Seer responses.
// No independent calendar algorithm, live network dependency, or legal text edits.
'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'original/Consumer_Protection_Law.html'), 'utf8');
const match = source.match(/<script id="pastafari_current_date_script">([\s\S]*?)<\/script>/);
assert(match, 'Original Pastafarian widget missing');
const script = match[1];
const java = fs.readFileSync(path.join(root, 'android/src/il/org/lawreader/consumer/MainActivity.java'), 'utf8');

// The Android network exception must match only the widget's three read-only
// canonical endpoints. No wildcard host or general-purpose internet exception.
const networkPolicy = java.match(/private static boolean isApprovedDateSource\(Uri uri\)([\s\S]*?)@Override public void onCreate/);
assert(networkPolicy, 'Date-specific native allowlist missing');
const allowlist = networkPolicy[1];
for (const host of ['raw.githubusercontent.com', 'api.github.com', 'sargon17-green.github.io']) {
  assert(allowlist.includes('"' + host + '".equals(host)'), 'Missing exact host: ' + host);
  assert(fs.readFileSync(path.join(root,'scripts/build_web.py'),'utf8').includes('https://' + host), 'CSP does not permit: ' + host);
}
for (const endpoint of [
  '/Sargon17-Green/pastafari-calendar/main/docs/api/seer-now.json',
  '/repos/Sargon17-Green/pastafari-calendar/contents/docs/api/seer-now.json',
  '/pastafari-calendar/api/seer-now.json'
]) assert(allowlist.includes('"' + endpoint + '".equals(path)'), 'Missing exact path: ' + endpoint);
assert.equal((allowlist.match(/\.equals\(path\)/g) || []).length, 3);
assert(allowlist.includes('uri.getPort() != -1'), 'Unexpected port must be blocked');
assert(allowlist.includes('"https".equals(uri.getScheme())'), 'Only HTTPS permitted');
assert(java.includes('if ("GET".equals(request.getMethod()) && isApprovedDateSource(uri)) return dateResponse(uri);'));
assert(java.includes('return missing();'), 'Other remote resources must remain blocked');
assert(!java.includes("connect-src 'none'"), 'Network CSP still forbids date fetches');
assert(java.includes('setInstanceFollowRedirects(false)'), 'Redirects must be blocked');
assert(!/connect-src[^;]*\*/.test(java), 'Broad CSP network wildcard forbidden');
assert(java.includes('frame-src \'none\''), 'Frame protection unexpectedly weakened');

const now = Date.now();
const jdn = String(2440588 + Math.floor(now / 86400000));
const snapshot = {
  calculationAt: new Date(now).toISOString(),
  calculationDay: {jdn},
  targetDay: {jdn},
  pastafarianDate: {
    year: '5000',
    cutlet: {canonicalIndex: 5, day: 389},
    month: {canonicalIndex: 11, day: 53}
  },
  cacheMeta: {mode: 'automated-seer-snapshot', fetchedAt: new Date(now).toISOString()}
};
async function exercise(responseAt, payload, expectedCalls, options={}) {
  const date = {textContent: 'לוח השנה הפסטפרי'};
  const link = {title: ''};
  const urls = [];
  const context = {
    document: {
      readyState: 'complete',
      getElementById(id) {
        if (id === 'pastafari_current_date_text') return date;
        if (id === 'pastafari_current_date_link') return link;
        return null;
      }
    },
    fetch: async (url, request) => {
      assert.equal(request.method, 'GET');
      assert.equal(request.mode, 'cors');
      urls.push(url);
      const index = urls.length - 1;
      if(options.failure==='dns')throw new TypeError('Controlled DNS/offline failure');
      if(options.failure==='timeout')return await new Promise((resolve,reject)=>request.signal.addEventListener('abort',()=>reject(new Error('Controlled timeout')),{once:true}));
      if (index !== responseAt) throw new Error('Simulated endpoint failure');
      return {ok: options.failure!=='http', status:503, text: async () => {
        if(options.failure==='body')throw new TypeError('Controlled disconnection during body');
        if(options.failure==='json')return '{';
        if(options.failure==='html')return '<html>error</html>';
        if (index === 1) {
          return JSON.stringify({
            type: 'file',
            content: Buffer.from(JSON.stringify(payload), 'utf8').toString('base64')
          });
        }
        return JSON.stringify(payload);
      }};
    },
    AbortController, setTimeout: (fn,ms)=>setTimeout(fn,options.failure==='timeout'&&ms===15000?1:ms), clearTimeout,
    setInterval: () => 1,
    atob: value => Buffer.from(value, 'base64').toString('binary'),
    TextDecoder, Uint8Array,
    console: {log(){}, info(){}, warn(){}, error(){}}
  };
  vm.runInNewContext(script, context, {timeout: 3000});
  for (let i=0; i<300 && date.textContent==='לוח השנה הפסטפרי'; i++) await new Promise(resolve => setTimeout(resolve,1));
  assert.equal(urls.length, expectedCalls, 'Unexpected source fallback count');
  return {date: date.textContent, title: link.title, urls};
}
(async () => {
  for (const index of [0,1,2]) {
    const result = await exercise(index, snapshot, index+1);
    assert(result.date.includes('53 בחודש ערפל'), 'Wrong month label');
    assert(result.date.includes('389 לקציצה מחשבה'), 'Wrong cutlet label');
    assert(result.date.includes('שנת 5,000'), 'Wrong year formatting');
    assert(result.title.includes('להסבר'), 'Widget link is broken');
  }
  const stale = JSON.parse(JSON.stringify(snapshot));
  stale.calculationAt = '2000-01-01T00:00:00Z';
  const fail = await exercise(2, stale, 3);
  assert.equal(fail.date, 'התאריך הפסטפרי אינו זמין כרגע');
  assert(fail.title.includes('לא התקבל תאריך פסטפרי עדכני'));
  for(const failure of ['dns','timeout','http','body','json','html']){
    const result=await exercise(2,snapshot,3,{failure});
    assert.equal(result.date,'התאריך הפסטפרי אינו זמין כרגע',failure);
  }
  for(const payload of [{},{...snapshot,cacheMeta:{mode:'unknown'}},{...snapshot,targetDay:{jdn:String(BigInt(jdn)+3n)}},{...snapshot,pastafarianDate:{...snapshot.pastafarianDate,month:{canonicalIndex:999,day:1}}}]){
    assert.equal((await exercise(2,payload,3)).date,'התאריך הפסטפרי אינו זמין כרגע');
  }
  console.log('PASS: Seer raw/REST/Pages fallback; stale/malformed/invalid data; DNS/offline, HTTP, aborted timeout and partial-body failure; exact Android allowlist');
})().catch(error => {console.error(error);process.exitCode=1;});
