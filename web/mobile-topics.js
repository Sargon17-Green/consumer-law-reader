/* Local-only personal topic overlay. Never edits the legal document or source index. */
(()=>{'use strict';
const KEY='law-reader-topics-v1', SCHEMA=1;
let app=null, baseTopics=[], baseLinks=[], state=null;
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>Array.from(r.querySelectorAll(s));
const clean=s=>String(s??'').replace(/\s+/g,' ').trim();
const id=()=>('u:'+((globalThis.crypto&&typeof crypto.randomUUID==='function')?crypto.randomUUID():String(Date.now())+'-'+Math.random().toString(36).slice(2)));
const empty=()=>({schema:SCHEMA,userTopics:[],links:[],titles:{},hidden:{},ranks:{}});
const validTitle=s=>clean(s).length>=1&&clean(s).length<=90;
function load(){try{const raw=localStorage.getItem(KEY);if(!raw)return empty();const data=JSON.parse(raw);if(data?.schema!==SCHEMA||!Array.isArray(data.userTopics)||!Array.isArray(data.links)||!data.titles||!data.hidden||!data.ranks)throw Error('schema');return data;}catch{app.toast('לא ניתן לטעון את הנושאים האישיים');return empty();}}
function commit(change){const next=JSON.parse(JSON.stringify(state));try{change(next);const serial=JSON.stringify(next);if(serial.length>450000)throw Error('size');localStorage.setItem(KEY,serial);state=next;app.toast('נשמר');return true;}catch{app.toast('השמירה נכשלה. השינוי לא בוצע');return false;}}
function discover(){
 baseTopics=[];baseLinks=[];
 const nav=$('#navigator'),root=nav?.querySelector(':scope > ul');
 if(!root)return;
 // A virtual parent is retained only to read older saved personal links.
 // It must never appear as an artificial topic in the visible navigation.
 baseTopics.push({id:'base:general',parent:null,title:'',origin:'virtual',index:-1});
 let sequence=0;
 const walk=(ul,parent)=>{
  for(const node of ul.children){
   if(node.matches('li.nav_list_title[id]')){
    const topicId='base:'+node.id;
    baseTopics.push({id:topicId,parent,title:clean(node.firstChild?.textContent||node.textContent),origin:'base',index:sequence++});
    const nested=node.nextElementSibling;
    if(nested?.matches('ul.nav_list'))walk(nested,topicId);
   }else if(node.matches('li')){
    for(const a of node.querySelectorAll(':scope > a[href^="#"]')){
     let target;
     try{target=decodeURIComponent(a.getAttribute('href').slice(1));}catch{continue;}
     if(!target||!document.getElementById(target))continue;
     baseLinks.push({id:'base-link:'+sequence,topic:parent,target,title:clean(a.textContent),origin:'base',index:sequence++});
    }
   }
  }
 };
 walk(root,'base:general');
}
function topics(){
 const list=baseTopics.concat(state.userTopics.map(t=>({...t,origin:'user'})));
 return list.map(t=>({...t,title:state.titles[t.id]||t.title,hidden:!!state.hidden[t.id],rank:Number.isFinite(state.ranks[t.id])?state.ranks[t.id]:(t.index??1000)}));
}
function ordered(list){return list.sort((a,b)=>a.rank-b.rank||(a.index??10000)-(b.index??10000)||(a.title||'').localeCompare(b.title||'','he'));}
function entriesFor(parent,all){
 const selected=all.filter(t=>t.id!=='base:general'&&!t.hidden&&(t.parent===parent||(parent==='base:general'&&t.parent===null)));
 const links=baseLinks.filter(l=>l.topic===parent).concat(state.links.filter(l=>l.topic===parent)).filter(l=>typeof l.target==='string'&&document.getElementById(l.target));
 const entries=selected.map(t=>({...t,kind:'topic'})).concat(links.map((l,i)=>({...l,kind:'link',index:l.index??(10000+i),rank:l.index??(10000+i)})));
 return ordered(entries);
}
function controls(row,topic,edit){if(!edit)return;const group=document.createElement('div');group.className='m-topic-controls';group.setAttribute('role','group');group.setAttribute('aria-label','פעולות נושא '+topic.title);
 const add=(name,fn)=>group.append(app.action(name,fn));
 add('שנה שם',()=>nameForm(topic));add('העבר למעלה',()=>move(topic,-1));add('העבר למטה',()=>move(topic,1));
 if(topic.origin==='base')add(topic.hidden?'הצג מחדש':'הסתר ברשימה שלי',()=>{if(commit(s=>{s.hidden[topic.id]=!topic.hidden;}))show(true);});
 else add('מחק נושא אישי',()=>{const hasChildren=topics().some(t=>t.parent===topic.id);if(hasChildren){app.toast('יש להעביר או למחוק תחילה את תתי־הנושאים');return;}if(!confirm('למחוק את הנושא האישי וקישוריו? נוסח החוק לא יימחק.'))return;if(commit(s=>{s.userTopics=s.userTopics.filter(t=>t.id!==topic.id);s.links=s.links.filter(l=>l.topic!==topic.id);}))show(true);});
 row.append(group);
}
function move(topic,delta){
 const siblings=ordered(topics().filter(t=>t.parent===topic.parent&&!t.hidden));
 const index=siblings.findIndex(t=>t.id===topic.id),next=index+delta;
 if(next<0||next>=siblings.length){app.toast('הנושא כבר בקצה הרשימה');return;}
 const other=siblings[next];
 if(commit(s=>{s.ranks[topic.id]=other.rank;s.ranks[other.id]=topic.rank;}))show(true);
}
function nameForm(topic){
 const b=app.openSheet('שינוי שם נושא');
 const input=document.createElement('input');input.className='m-search-input';
 input.setAttribute('aria-label','שם הנושא');input.maxLength=90;input.value=topic.title;
 const save=app.action('שמור שם',()=>{
  if(!validTitle(input.value)){app.toast('נדרש שם באורך 1–90 תווים');return;}
  if(commit(s=>{if(topic.origin==='base')s.titles[topic.id]=clean(input.value);else s.userTopics.find(t=>t.id===topic.id).title=clean(input.value);}))show(true);
 });
 b.append(input,save);input.focus();
}
function createForm(){const b=app.openSheet('נושא אישי חדש');const input=document.createElement('input');input.className='m-search-input';input.placeholder='שם נושא';input.maxLength=90;input.setAttribute('aria-label','שם נושא חדש');const select=document.createElement('select');select.className='m-topic-select';select.setAttribute('aria-label','נושא אב');const root=document.createElement('option');root.value='';root.textContent='ברמה הראשית';select.append(root);ordered(topics().filter(t=>!t.hidden&&t.id!=='base:general')).forEach(t=>{const o=document.createElement('option');o.value=t.id;o.textContent=t.title;select.append(o);});const save=app.action('יצירת נושא',()=>{if(!validTitle(input.value)){app.toast('נדרש שם באורך 1–90 תווים');return;}const parent=select.value||null;if(commit(s=>s.userTopics.push({id:id(),title:clean(input.value),parent,index:1000+s.userTopics.length})))show(true);});b.append(input,select,save);input.focus();}
function linkRow(link,query,edit){
 if(!document.getElementById(link.target))return null;
 if(query&&!clean(link.title).includes(query))return null;
 const row=document.createElement('div');row.className='m-topic-link';
 row.append(app.action(link.title,()=>app.goTo(link.target)));
 if(edit&&link.origin==='user')row.append(app.action('הסר קישור',()=>{
  if(commit(s=>s.links=s.links.filter(l=>l.id!==link.id)))show(true);
 }));
 return row;
}
function topicRow(topic,all,level,query,edit,seen){
 if(seen.has(topic.id)||level>16)return null;
 const ancestry=new Set(seen);ancestry.add(topic.id);
 const selfMatches=!query||clean(topic.title).includes(query);
 const childQuery=selfMatches?'':query;
 const children=entriesFor(topic.id,all).map(entry=>entry.kind==='link'?
  linkRow(entry,childQuery,edit):topicRow(entry,all,level+1,childQuery,edit,ancestry)).filter(Boolean);
 if(!selfMatches&&!children.length)return null;
 // Do not show empty, unopenable headings copied from the source.
 if(topic.origin==='base'&&!children.length)return null;
 const details=document.createElement('details');details.className='m-topic';
 if(level===0||query)details.open=true;
 const summary=document.createElement('summary');summary.textContent=topic.title;details.append(summary);
 controls(details,topic,edit);
 children.forEach(child=>details.append(child));
 return details;
}
function show(edit=false,query=''){
 const b=app.openSheet('ניווט לפי נושא');
 const search=document.createElement('input');search.type='search';search.className='m-search-input';
 search.placeholder='חיפוש נושא או קישור';search.setAttribute('aria-label','חיפוש בניווט הנושאי');search.value=query;
 const bar=document.createElement('div');bar.className='m-topic-toolbar';
 bar.append(app.action('+ נושא חדש',createForm),app.action(edit?'סיום עריכה':'עריכת נושאים',()=>show(!edit,search.value)));
 const list=document.createElement('div');list.className='m-topic-tree';
 const render=()=>{
  list.replaceChildren();const all=topics(),q=clean(search.value);
  entriesFor('base:general',all).forEach(entry=>{
   const node=entry.kind==='link'?linkRow(entry,q,edit):topicRow(entry,all,0,q,edit,new Set());
   if(node)list.append(node);
  });
  if(!list.children.length){const e=document.createElement('p');e.className='m-empty';e.textContent='לא נמצאו נושאים מתאימים';list.append(e);}
 };
 search.oninput=render;b.append(search,bar,list);
 if(edit&&Object.values(state.hidden).some(Boolean)){
  b.append(app.action('שחזור נושאים שהוסתרו',()=>{if(commit(s=>s.hidden={}))show(true);}));
 }
 render();
}
function pickLink(el){if(!el?.id){app.toast('אין לסעיף מזהה שמאפשר קישור יציב');return;}const b=app.openSheet('הוספת סעיף לנושא');const label=document.createElement('p');label.className='m-hint';label.textContent=app.articleLabel(el);const select=document.createElement('select');select.className='m-topic-select';select.setAttribute('aria-label','בחירת נושא');const list=ordered(topics().filter(t=>!t.hidden&&t.id!=='base:general'));for(const t of list){const o=document.createElement('option');o.value=t.id;o.textContent=t.title;select.append(o);}const add=app.action('הוסף קישור',()=>{const topic=select.value;if(!topic){app.toast('יש ליצור נושא תחילה');return;}if(state.links.some(l=>l.topic===topic&&l.target===el.id)){app.toast('הסעיף כבר משויך לנושא');return;}if(commit(s=>s.links.push({id:id(),topic,target:el.id,title:app.articleLabel(el),origin:'user',document:'consumer-protection-law',source_type:el.closest('.delegated_legislation')?'delegated':'law'})))app.goTo(el);});b.append(label,select,add,app.action('צור נושא חדש',createForm));}
function init(adapter){app=adapter;discover();state=load();}
window.LawTopics={init,show,pickLink,inspect:()=>({baseTopics:baseTopics.length,baseLinks:baseLinks.length,userTopics:state?.userTopics.length||0})};
})();
