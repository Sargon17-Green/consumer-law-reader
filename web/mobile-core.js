/* Pure shared search and settings primitives; no legal content is stored here. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.LawCore = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';
  const VERSION = '1.3.9-dev';
  const MAX_BACKUP = 1000000;
  const A11Y = ['m-contrast-dark','m-contrast-blue','m-underline','m-no-motion','m-gray','m-serif'];
  const KEYS = ['law-reader-font','law-reader-align','law-reader-topics-v1', ...A11Y.map(k=>'law-a11y-'+k)];
  const JOURNAL = 'law-settings-transaction-v1';
  const bytes = s => new TextEncoder().encode(s).length;
  const object = x => x !== null && typeof x === 'object' && !Array.isArray(x);
  const fields = (x, allowed) => object(x) && Object.keys(x).every(k=>allowed.includes(k));
  function normalized(raw, offsets=false) {
    // Index-only normalization avoids per-character objects and rope strings.
    // Offset maps are built only for the displayed matching snippets.
    if(!offsets)return {text:String(raw ?? '').normalize('NFD').replace(/\p{M}/gu,'')
      .replace(/[״“”„]/g,'"').replace(/[׳‘’‚]/g,"'").replace(/[־‐‑‒–—−]/g,'-')
      .replace(/\s+/gu,' ').trim().toLocaleLowerCase('he').replace(/ς/g,'σ'),starts:[],ends:[]};
    let text='', position=0, space=null;
    const starts=[], ends=[];
    for (const ch of String(raw ?? '')) {
      const begin=position; position+=ch.length;
      const part=ch.normalize('NFD').replace(/\p{M}/gu,'')
        .replace(/[״“”„]/g,'"').replace(/[׳‘’‚]/g,"'")
        .replace(/[־‐‑‒–—−]/g,'-').toLocaleLowerCase('he').replace(/ς/g,'σ');
      if (!part) {
        if (offsets && ends.length && !space) ends[ends.length-1]=position;
        continue;
      }
      if (/^\s+$/u.test(part)) {
        if (text) space={start:space?.start ?? begin,end:position};
        continue;
      }
      if (space) {
        text+=' ';
        if (offsets) {starts.push(space.start); ends.push(space.end);}
        space=null;
      }
      text+=part;
      if (offsets) for(let i=0;i<part.length;i++){starts.push(begin);ends.push(position);}
    }
    return {text,starts,ends};
  }
  function match(raw, query, exact=false) {
    raw=String(raw); query=String(query);
    const needle=exact?query:normalized(query).text;
    if (!needle || needle.length>512) return null;
    const mapped=exact?null:normalized(raw,true);
    const index=(mapped?mapped.text:raw).indexOf(needle);
    if(index<0)return null;
    return {start:mapped?mapped.starts[index]:index,
      end:mapped?mapped.ends[index+needle.length-1]:index+needle.length,
      exact:raw.includes(query)};
  }
  function snippet(raw, query, exact=false, context=65, length=260) {
    raw=String(raw);
    const hit=match(raw,query,exact);
    let start=hit?Math.max(0,hit.start-context):0;
    let end=Math.min(raw.length,Math.max(start+length,hit?.end||0));
    if(start>0 && /[\uDC00-\uDFFF]/.test(raw[start]))start--;
    if(end<raw.length && /[\uDC00-\uDFFF]/.test(raw[end]))end++;
    return {before:(start?'…':'')+raw.slice(start,hit?hit.start:end),
      mark:hit?raw.slice(hit.start,hit.end):'',
      after:hit?raw.slice(hit.end,end)+(end<raw.length?'…':''):'',hit};
  }
  const fail = text => {throw Error(text);};
  function validateTopics(value, hasTarget=()=>true, baseTopics=null) {
    if(!fields(value,['schema','userTopics','links','titles','hidden','ranks']) || value.schema!==1 ||
      !Array.isArray(value.userTopics) || !Array.isArray(value.links) ||
      !object(value.titles)||!object(value.hidden)||!object(value.ranks) ||
      value.userTopics.length>500||value.links.length>2000) fail('מבנה הנושאים אינו תקין');
    const title=t=>typeof t==='string'&&t.trim().length>0&&t.length<=90;
    const id=t=>typeof t==='string'&&/^u:[A-Za-z0-9-]{1,100}$/.test(t);
    const ids=new Set();
    for(const t of value.userTopics){
      if(!fields(t,['id','title','parent','index'])||!id(t.id)||ids.has(t.id)||!title(t.title)||
        (t.index!==undefined&&(!Number.isFinite(t.index)||Math.abs(t.index)>1e7)))fail('נושא אישי אינו תקין');
      ids.add(t.id);
    }
    const known=k=>ids.has(k)||(typeof k==='string'&&k.startsWith('base:')&&k.length<=200&&(!baseTopics||baseTopics.has(k)));
    const parents=new Map(value.userTopics.map(t=>[t.id,t.parent]));
    for(const t of value.userTopics){
      if(t.parent!==null&&!known(t.parent))fail('נושא האב אינו קיים');
      const seen=new Set([t.id]);let parent=t.parent;
      while(parents.has(parent)){if(seen.has(parent))fail('קיים מעגל בין נושאים');seen.add(parent);parent=parents.get(parent);}
    }
    const linkIDs=new Set();
    for(const l of value.links){
      if(!fields(l,['id','topic','target','title','origin','document','source_type']) || !id(l.id)||linkIDs.has(l.id)||
        !known(l.topic)||!title(l.title)||typeof l.target!=='string'||l.target.length>500||
        /[\u0000-\u0020#]/.test(l.target)||!hasTarget(l.target)||
        (l.origin!==undefined&&l.origin!=='user')||
        (l.document!==undefined&&l.document!=='consumer-protection-law')||
        (l.source_type!==undefined&&!['law','delegated'].includes(l.source_type)))fail('קישור אישי או יעדו אינם תקינים');
      linkIDs.add(l.id);
    }
    const preferenceID=k=>known(k)||id(k); // Older versions retained metadata after deleting a personal topic.
    for(const [k,v] of Object.entries(value.titles))if(!preferenceID(k)||!title(v))fail('שם נושא אינו תקין');
    for(const [k,v] of Object.entries(value.hidden))if(!preferenceID(k)||typeof v!=='boolean')fail('העדפת הסתרה אינה תקינה');
    for(const [k,v] of Object.entries(value.ranks))if(!preferenceID(k)||!Number.isFinite(v)||Math.abs(v)>1e7)fail('סדר נושאים אינו תקין');
    return value;
  }
  function validateBackup(raw, options={}) {
    if(typeof raw!=='string'||bytes(raw)>MAX_BACKUP)fail('קובץ הגיבוי גדול מדי');
    let data;try{data=JSON.parse(raw);}catch{fail('קובץ הגיבוי אינו JSON תקין');}
    const legacy=data?.format==='consumer-law-reader-settings-v1';
    if(!fields(data,legacy?['format','settings']:['format','schema','appVersion','settings']) ||
      (legacy?false:(data.format!=='consumer-law-reader-settings'||data.schema!==2)) ||
      !object(data.settings)||Object.keys(data.settings).length>KEYS.length||
      (!legacy&&(typeof data.appVersion!=='string'||data.appVersion.length>40)))fail('פורמט הגיבוי אינו נתמך');
    const settings=Object.create(null);
    for(const [key,value] of Object.entries(data.settings)){
      if(!KEYS.includes(key))fail('הגיבוי מכיל שדה לא מוכר: '+key);
      if(typeof value!=='string'||bytes(value)>(key==='law-reader-topics-v1'?900000:500000))fail('ערך הגדרה אינו תקין');
      if(key==='law-reader-font'&&(!/^(1[6-9]|2[0-8])$/.test(value)))fail('גודל גופן אינו תקין');
      if(key==='law-reader-align'&&!['right','justify'].includes(value))fail('יישור אינו תקין');
      if(key.startsWith('law-a11y-')&&!['0','1'].includes(value))fail('העדפת נגישות אינה תקינה');
      if(key==='law-reader-topics-v1'){
        let topics;try{topics=JSON.parse(value);}catch{fail('נתוני הנושאים אינם JSON תקין');}
        validateTopics(topics,options.hasTarget,options.baseTopics);
      }
      settings[key]=value;
    }
    if(settings['law-a11y-m-contrast-dark']==='1'&&settings['law-a11y-m-contrast-blue']==='1')fail('הגדרות ניגודיות סותרות');
    return settings;
  }
  function snapshot(storage){const out={};for(const k of KEYS){const v=storage.getItem(k);if(v!==null)out[k]=v;}return out;}
  function exportBackup(storage,options){
    const raw=JSON.stringify({format:'consumer-law-reader-settings',schema:2,appVersion:VERSION,settings:snapshot(storage)});
    validateBackup(raw,options);return raw;
  }
  function restoreValues(storage,values){for(const k of KEYS)if(Object.prototype.hasOwnProperty.call(values,k))storage.setItem(k,values[k]);else storage.removeItem(k);}
  function recover(storage){
    const journal=storage.getItem(JOURNAL);if(journal===null)return false;
    const before=JSON.parse(journal);
    if(!object(before)||Object.entries(before).some(([k,v])=>!KEYS.includes(k)||typeof v!=='string'))fail('יומן שחזור אינו תקין');
    restoreValues(storage,before);storage.removeItem(JOURNAL);return true;
  }
  function applyBackup(storage,raw,options){
    const next=validateBackup(raw,options);recover(storage);
    const before=snapshot(storage);
    // Write-ahead journal: a terminated process rolls back before the UI reads preferences.
    // If reserving journal space fails, none of the current values is changed.
    storage.setItem(JOURNAL,JSON.stringify(before));
    try{restoreValues(storage,next);storage.removeItem(JOURNAL);}
    catch(error){try{restoreValues(storage,before);storage.removeItem(JOURNAL);}catch{fail('השחזור נכשל; ההגדרות הקודמות שמורות ביומן ויישוחזרו בפתיחה הבאה');}throw error;}
    return next;
  }
  function preview(settings){
    const topics=JSON.parse(settings['law-reader-topics-v1']||'{"userTopics":[],"links":[]}');
    return Object.keys(settings).length+' הגדרות, '+topics.userTopics.length+' נושאים אישיים, '+topics.links.length+' קישורים אישיים. ההגדרות הנוכחיות יוחלפו, לרבות הגדרות שאינן בקובץ.';
  }
  return {VERSION,MAX_BACKUP,KEYS,JOURNAL,A11Y,normalized,match,snippet,validateTopics,validateBackup,exportBackup,applyBackup,recover,preview};
});
