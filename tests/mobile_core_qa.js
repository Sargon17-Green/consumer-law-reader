'use strict';
const assert=require('node:assert/strict');
const core=require('../web/mobile-core.js');
const cases=[['אב שָׁלוֹם סיום','שלום','שָׁלוֹם'],['אָב שָׁלוֹם','שָׁלוֹם','שָׁלוֹם'],['😀 אָב סוף','אב','אָב'],['תשפ״ו','תשפ“ו','תשפ״ו'],['סעיף 14־ג','14-ג','14־ג'],['א  \n ב','א ב','א  \n ב'],['אָב   סוף','אב','אָב'],['A\u0301BC','abc','A\u0301BC'],['x 😀 שָׁלוֹם','😀 שלום','😀 שָׁלוֹם']];
for(const [raw,q,expected]of cases){const m=core.match(raw,q);assert(m,[raw,q]);assert.equal(raw.slice(m.start,m.end),expected);assert.equal(core.snippet(raw,q).mark,expected);}
assert.equal(core.match('אב','\u05B7'),null);assert.equal(core.match('אב',''),null);assert.equal(core.match('x','x'.repeat(513)),null);
for(const raw of [' א\n\n ב ','ΟΣ ος','שָׁל֑וֹם','A\u0301BC','😀 אב','א\u0301  ב'])assert.equal(core.normalized(raw).text,core.normalized(raw,true).text);
for(let i=0;i<500;i++){
 const prefix='😀 אָב '.repeat(i%17),raw=prefix+'שָׁל֑וֹם  סיום',hit=core.match(raw,'שלום');
 assert.equal(raw.slice(hit.start,hit.end),'שָׁל֑וֹם');
}
class Storage{constructor(){this.data=new Map();this.fail=null;}getItem(k){return this.data.get(k)??null;}setItem(k,v){if(this.fail===k){this.fail=null;throw Error('quota');}this.data.set(k,String(v));}removeItem(k){this.data.delete(k);}}
const s=new Storage();s.setItem('unrelated','keep');s.setItem('law-reader-font','24');
const backup=core.exportBackup(s);core.validateBackup(backup);
assert.deepEqual(core.validateBackup('\uFEFF'+backup),core.validateBackup(backup),'Optional UTF-8 BOM has the same meaning on native and browser decoders');
s.setItem('law-reader-align','right');core.applyBackup(s,backup);assert.equal(s.getItem('law-reader-align'),null);assert.equal(s.getItem('unrelated'),'keep');assert.equal(s.getItem('law-reader-font'),'24');
const next=JSON.stringify({format:'consumer-law-reader-settings-v1',settings:{'law-reader-align':'right','law-reader-font':'20'}});
s.fail='law-reader-align';assert.throws(()=>core.applyBackup(s,next));assert.equal(s.getItem('law-reader-font'),'24');assert.equal(s.getItem('law-reader-align'),null);assert.equal(s.getItem(core.JOURNAL),null);
s.setItem(core.JOURNAL,JSON.stringify({'law-reader-font':'22'}));s.setItem('law-reader-font','17');assert(core.recover(s));assert.equal(s.getItem('law-reader-font'),'22');
s.fail=core.JOURNAL;assert.throws(()=>core.applyBackup(s,next));assert.equal(s.getItem('law-reader-font'),'22');
for(const patch of [{schema:3},{unknown:true},{settings:{'law-secret':'x'}},{settings:{'law-reader-font':'999'}},{settings:{'law-a11y-m-gray':'yes'}},{settings:{'law-reader-topics-v1':'{"schema":1}'}}])assert.throws(()=>core.validateBackup(JSON.stringify({...JSON.parse(backup),...patch})));
assert.throws(()=>core.validateBackup('x'.repeat(1000001)));
const topics={schema:1,userTopics:[{id:'u:one',title:'אישי',parent:null}],links:[{id:'u:link',topic:'u:one',target:'article_2',title:'סעיף 2'}],titles:{},hidden:{},ranks:{}};
topics.titles['u:deleted']='כותרת קודמת';topics.ranks['u:deleted']=20;core.validateTopics(topics,k=>k==='article_2');
assert.throws(()=>core.validateTopics(topics,()=>false));
topics.userTopics[0].parent='u:one';assert.throws(()=>core.validateTopics(topics));
console.log('PASS: normalized UTF-16 spans (500 generated cases), schema/limits, legacy round-trip, rollback, crash recovery, unrelated data preservation');
