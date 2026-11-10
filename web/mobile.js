/* Mobile interaction layer. The supplied legal document remains the content source. */
(()=>{'use strict';
const $=(q,r=document)=>r.querySelector(q), $$=(q,r=document)=>Array.from(r.querySelectorAll(q));
const sheet=$('#mobile-sheet'), body=$('#mobile-sheet-body'), title=$('#mobile-sheet-title');
let returnFocus=null,toastTimer,searchTimer,searchRecords=null,activeArticle=null,currentTarget=null,deferredInstall=null,searchState=null;
let openedRegulation=null,lastActivatedLink=null,readingOrigin=null,pointRestore=0;
const SESSION='law-reader-session-v1';
const safeGet=k=>{try{return localStorage.getItem(k);}catch{return null;}};
const safeSet=(k,v)=>{try{localStorage.setItem(k,String(v));return true;}catch{toast('שמירת ההעדפות נכשלה');return false;}};
const safeRemove=k=>{try{localStorage.removeItem(k);}catch{toast('שמירת ההעדפות נכשלה');}};
const native=()=>window.NativeLaw;
let offlineState='saving';
const offlineMessage=()=>offlineState==='ready'?'העותק המקומי מוכן לקריאה, לניווט ולחיפוש ללא רשת.':offlineState==='saving'?'העותק המקומי נשמר כעת. יש להמתין לאישור המוכנות לפני שימוש ללא רשת.':'לא ניתן לאמת עותק מקומי מלא. אפשר להמשיך לקרוא כעת; לפני שימוש ללא רשת יש לפתוח שוב עם חיבור ולבדוק מוכנות.';
function setOfflineState(state){offlineState=state;document.documentElement.dataset.lawOfflineReady=state==='ready'?'true':state==='saving'?'pending':'false';const status=$('#mobile-offline-status');if(status)status.textContent=offlineMessage();}
const editorial=(()=>{try{return JSON.parse($('#law-editorial-status')?.textContent||'{}');}catch{return {};}})();
const editorialDate=()=>{const t=editorial.law_text_last_verified_on||'';const m=/^(\d{4})-(\d{2})-(\d{2})$/.exec(t);return m?m[3]+'.'+m[2]+'.'+m[1]:'לא צוין';};
const cleanText=s=>String(s||'').replace(/\s+/g,' ').trim();
const escape=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fold=s=>window.LawCore.normalized(s).text;
function toast(message){const e=$('#mobile-toast');clearTimeout(toastTimer);e.textContent=message;e.hidden=false;toastTimer=setTimeout(()=>e.hidden=true,3200);}
function closeSheet(){if(!sheet.open)return false;clearTimeout(searchTimer);sheet.close();body.replaceChildren();if(returnFocus?.isConnected)returnFocus.focus({preventScroll:true});return true;}
function openSheet(label){clearTimeout(searchTimer);if(!sheet.open)returnFocus=document.activeElement;title.textContent=label;body.replaceChildren();if(!sheet.open)sheet.showModal();sheet.scrollTop=0;body.scrollTop=0;return body;}
function action(label,fn,detail=''){const b=document.createElement('button');b.type='button';b.className='m-action';b.textContent=label;if(detail){const s=document.createElement('small');s.textContent=detail;b.append(s);}b.addEventListener('click',fn);return b;}
function stripIds(root){if(root.removeAttribute)root.removeAttribute('id');$$('[id]',root).forEach(e=>e.removeAttribute('id'));return root;}
function readableText(el){const c=el.cloneNode(true);$$('.the_definition,.note_button,.note_div,.done_accordingly,.validity,.m-article-actions,.m-source-tools,.sources_box,.bills_box,.protocols_box,.history_box,script,style,noscript',c).forEach(e=>e.remove());return cleanText(c.textContent);}
function articleLabel(el){if(!el)return '';if(/^appendix_\d+$/.test(el.id)){const h=$(':scope>.appendix_title',el)?.cloneNode(true);if(h)$$('.m-article-actions,.m-source-tools',h).forEach(e=>e.remove());return cleanText(h?.textContent||'תוספת');}const n=$(':scope>tbody>tr>td.article_number',el)||$('.article_number',el),s=$(':scope>tbody>tr>td.side_title',el)||$('.side_title',el);const c=s?.cloneNode(true);if(c)$$('.m-article-actions,.m-source-tools,.the_definition',c).forEach(e=>e.remove());return cleanText((el.closest('.delegated_legislation')?'תקנה / סעיף ':'סעיף ')+(n?.textContent||'').replace(/\.$/,'')+(c?' · '+c.textContent:''));}
function expandAncestors(el){let p=el,regulationOpened=false;while(p&&p!==document.body){if(p.classList.contains('delegated_legislation')){if(!regulationOpened){openRegulation(p);regulationOpened=true;}const li=document.getElementById('li_'+p.id);if(li){li.style.listStyle='disclosure-open';const name=$(':scope>.name',li);if(name)name.style.fontWeight='bold';}}if(p.classList.contains('note_div')){p.style.display='block';const n=p.closest('.note_button');if(n)n.style.listStyleType='disclosure-open';}if(p.id.endsWith('_contnet')&&getComputedStyle(p).display==='none')p.style.display='block';p=p.parentElement;}}
function clearTargetHighlight(keepLink=false){
  if(currentTarget){currentTarget.classList.remove('m-target');currentTarget=null;}
  $$('.m-link-pressed').forEach(link=>link.classList.remove('m-link-pressed'));
  $$('#frame a.m-link-return').forEach(link=>link.classList.remove('m-link-return'));
  if(keepLink&&lastActivatedLink?.isConnected)lastActivatedLink.classList.add('m-link-return');
}
function pressLink(link){
  $$('.m-link-pressed').forEach(old=>old.classList.remove('m-link-pressed'));
  if(link?.isConnected)link.classList.add('m-link-pressed');
}
function readingLayout(){return {width:innerWidth,size:getComputedStyle(document.documentElement).getPropertyValue('--reading-size').trim()};}
function navigationPoint(){return {scroll:scrollY,regulation:openedRegulation?.id||null,regScroll:openedRegulation?.scrollTop||0,layout:readingLayout()};}
function restorePoint(point){
 if(!point)return;if(point.regulation){const reg=document.getElementById(point.regulation);if(reg?.classList.contains('delegated_legislation'))openRegulation(reg);}else closeRegulation();
 const token=++pointRestore;
 const apply=()=>{if(token!==pointRestore)return;const layout=readingLayout();if(point.layout&&(point.layout.width!==layout.width||point.layout.size!==layout.size))return;scrollTo(0,Number(point.scroll)||0);if(openedRegulation)openedRegulation.scrollTop=Number(point.regScroll)||0;};
 // WKWebView can restore its native scroll snapshot after popstate's first
 // frame, even with manual restoration. Settle after traversal; a new action
 // or a real user gesture cancels the correction, so it cannot fight scrolling.
 setTimeout(()=>requestAnimationFrame(()=>requestAnimationFrame(apply)),0);
 setTimeout(apply,150);
}
for(const event of ['pointerdown','touchstart','wheel','keydown'])window.addEventListener(event,()=>{pointRestore++;},{passive:true});
function goTo(target,push=true,highlight=true){
 const el=typeof target==='string'?document.getElementById(target.replace(/^#/,'')):target;
 if(!el){toast('היעד אינו קיים בקובץ המצורף');return false;}
 pointRestore++;
 if(push)history.replaceState({...history.state,lawPoint:navigationPoint()},'');
 closeSheet();if(openedRegulation&&!el.closest('.delegated_legislation'))closeRegulation();expandAncestors(el);clearTargetHighlight(false);
 if(highlight){currentTarget=el;el.classList.add('m-target');}
 el.scrollIntoView({block:'start',behavior:'instant'});
 if(push&&el.id&&location.hash!=='#'+encodeURIComponent(el.id))history.pushState({lawTarget:el.id},'','#'+encodeURIComponent(el.id));
 if(!el.hasAttribute('tabindex'))el.setAttribute('tabindex','-1');el.focus({preventScroll:true});
 // Focus may adjust a nested scroller even with preventScroll. Align only
 // afterwards, below the actual fixed return control at the current font size.
 if(openedRegulation&&el!==openedRegulation&&openedRegulation.contains(el)){
  const back=$('#mobile-regulation-back'),top=openedRegulation.getBoundingClientRect().top;
  const visibleTop=Math.max(top,back&&!back.hidden?back.getBoundingClientRect().bottom:top)+12;
  openedRegulation.scrollBy({top:el.getBoundingClientRect().top-visibleTop,behavior:'instant'});
 }
 saveSession(el.id);return true;
}
function saveSession(target){try{const previous=JSON.parse(safeGet(SESSION)||'{}');safeSet(SESSION,JSON.stringify({schema:1,target:target||currentArticle()?.id||previous.target||'',point:navigationPoint(),search:searchState}));}catch{}}
function shareLink(id){const el=document.getElementById(id);if(!el){toast('היעד אינו קיים');return;}const url='https://sargon17-green.github.io/consumer-law-reader/reader/#'+encodeURIComponent(id);if(native()?.share)native().share(url);else if(navigator.share)navigator.share({title:articleLabel(el),url}).catch(e=>{if(e.name!=='AbortError')copy(url);});else copy(url);}

function copyResult(ok){toast(ok?'הטקסט הועתק':'ההעתקה לא הושלמה. אפשר לנסות שוב או לבחור קטע קטן יותר.');}
function copyFallback(text,message){const d=openSheet('טקסט להעתקה'),hint=document.createElement('p'),t=document.createElement('textarea');hint.className='m-hint';hint.textContent=message;t.value=text;t.setAttribute('aria-label','הטקסט המלא לבחירת קטע להעתקה');t.style.cssText='width:100%;min-height:240px;font:17px/1.7 Arial';d.append(hint,t);t.focus();if(text.length<=100000)t.select();}
async function copy(text){
 if(!text){toast('אין טקסט להעתקה');return;}
 try{
  const bridge=native();
  if(bridge){
   const limit=typeof bridge.copyLimit==='function'?Number(bridge.copyLimit()):1000000;
   if(!Number.isSafeInteger(limit)||limit<1)throw Error('Invalid clipboard capability');
   if(text.length>limit){copyFallback(text,'הקטע גדול ממגבלת ההעתקה הישירה של המכשיר. הטקסט המלא נשמר כאן; אפשר לבחור ולהעתיק חלקים ממנו.');return;}
   bridge.copy(text);return; // Native acknowledges actual completion via copyResult.
  }
  await navigator.clipboard.writeText(text);copyResult(true);
 }catch{copyFallback(text,'מערכת ההפעלה לא אישרה העתקה ישירה. אפשר לבחור ולהעתיק את הטקסט מכאן.');}
}

function closeRegulation(restore=true){if(!openedRegulation)return false;openedRegulation.classList.remove('m-regulation-open');openedRegulation.style.display='none';openedRegulation=null;document.documentElement.classList.remove('m-regulation-mode');const back=$('#mobile-regulation-back');if(back)back.hidden=true;if(restore&&readingOrigin){scrollTo(0,readingOrigin.scroll);readingOrigin=null;}return true;}
function openRegulation(reg){if(!reg)return false;if(openedRegulation===reg)return true;if(openedRegulation)closeRegulation(false);else readingOrigin={scroll:scrollY};openedRegulation=reg;reg.style.display='block';reg.classList.add('m-regulation-open');document.documentElement.classList.add('m-regulation-mode');const back=$('#mobile-regulation-back');if(back)back.hidden=false;return true;}
function currentArticle(){
  const reg=openedRegulation,top=$('#mobile-header')?.getBoundingClientRect().bottom||75;
  const hit=(x,y)=>{const el=document.elementFromPoint(x,y);const target=el?.closest('table.article[id],table.article_deleted[id],table.appendix[id]');return target&&(reg?reg.contains(target):true)?target:null;};
  for(const y of [top+95,Math.max(top+100,innerHeight*.46),Math.max(top+125,innerHeight*.68)]){
    for(const x of [innerWidth*.5,innerWidth*.72,innerWidth*.28]){
      const found=hit(x,Math.min(y,innerHeight-120));if(found)return found;
    }
  }
  if(activeArticle?.isConnected){const r=activeArticle.getBoundingClientRect();if(r.bottom>top&&r.top<innerHeight-65)return activeArticle;}
  return null;
}
function showGlobalActions(){
  const item=currentArticle();if(item){showActions(item);const heading=document.createElement('p');heading.className='m-global-context';heading.textContent='הפעולות מתייחסות ל'+articleLabel(item);body.prepend(heading);targetGlobalExtras(body);return;}
  const target=openSheet('פעולות');target.append(action('כל המקורות וההיסטוריה',()=>window.LawSources.showHub()),action('הגדרות תצוגה ונגישות',showMore));
  if(openedRegulation)target.append(action('חזרה לחוק',closeRegulation));
}
function targetGlobalExtras(target){target.append(action('כל המקורות וההיסטוריה',()=>window.LawSources.showHub()),action('הגדרות תצוגה ונגישות',showMore));if(openedRegulation)target.append(action('חזרה לחוק',()=>{closeSheet();closeRegulation();}));}
function textForCopy(el){const clone=el.cloneNode(true);$$('.m-article-actions,.m-source-tools',clone).forEach(e=>e.remove());try{return HTML_to_string(clone).trim();}catch{return readableText(el);}}
function showSource(kind,article){window.LawSources.showPanel(kind,article.id);}
function showActions(article,subsection=null){activeArticle=article;const target=openSheet(articleLabel(article));target.append(action(/^appendix_\d+$/.test(article.id)?'העתקת התוספת':'העתקת הסעיף',()=>copy(textForCopy(article))));target.append(action('שיתוף קישור לסעיף',()=>shareLink(article.id)));target.append(action('הוסף לניווט לפי נושא',()=>window.LawTopics.pickLink(article)));const subs=$$('.subsection[id]',article).filter(x=>x.closest('.article')===article);if(subs.length)target.append(action('העתקת סעיף משנה…',()=>{const d=openSheet('בחירת סעיף משנה');subs.forEach(x=>{const n=$(':scope>td.numbering',x)?.textContent||x.id;d.append(action('סעיף משנה '+cleanText(n),()=>copy(textForCopy(x))));});}));if(subsection)target.append(action('העתקת סעיף המשנה',()=>copy(textForCopy(subsection))));const sel=window.getSelection()?.toString();if(sel)target.append(action('העתקת הטקסט הנבחר',()=>copy(sel)));for(const [kind,label] of [['history','היסטוריית נוסחים'],['sources','מקורות'],['bills','הצעות חוק'],['protocols','פרוטוקולים']]){if(window.LawSources.availableKinds(article.id).includes(kind))target.append(action(label,()=>showSource(kind,article)));}const dl=article.closest('.delegated_legislation');if(dl)target.append(action('לתחילת התקנות או הצו',()=>goTo(document.getElementById('li_'+dl.id)||dl)));target.append(action('למפתח העניינים',showToc));}
function definition(el){const source=$(':scope>.the_definition',el);if(!source)return;const label=el.cloneNode(true);$$('.the_definition',label).forEach(x=>x.remove());const target=openSheet('הגדרה · '+cleanText(label.textContent).slice(0,90));const c=stripIds(source.cloneNode(true));c.className='m-definition';c.removeAttribute('style');target.append(c);}
function showToc(){const target=openSheet('תוכן עניינים');const toggle=action('הצגת פרקים בלבד',()=>{list.classList.toggle('m-toc-chapters');toggle.textContent=list.classList.contains('m-toc-chapters')?'הצגת כל הסעיפים':'הצגת פרקים בלבד';});target.append(toggle);const list=document.createElement('div');target.append(list);$$('#index_content td[class]').forEach(td=>{const a=$('a[href^="#"]',td);if(!a)return;const link=document.createElement('a');link.className='m-toc-link';link.href=a.getAttribute('href');link.dataset.kind=td.classList.contains('chapter_link')?'chapter':td.classList.contains('article_link')?'article':'subchapter';link.textContent=cleanText(a.textContent);list.append(link);});}
function showNavigate(){window.LawTopics.show();}
function buildSearch(){if(searchRecords)return searchRecords;searchRecords=[];$$('#frame .article[id],#frame .appendix[id]').forEach(el=>{const dl=el.closest('.delegated_legislation');const text=readableText(el);if(!text)return;const dlTitle=dl?cleanText($('.delegated_legislation_title',dl)?.textContent):'';const label=el.classList.contains('article')?articleLabel(el):'תוספת · '+(dlTitle||'חוק הגנת הצרכן');searchRecords.push({el,title:label,kind:dl?'delegated':'law',subtitle:dlTitle||'חוק הגנת הצרכן',text,folded:fold(text)});});return searchRecords;}
function appendSnippet(node,text,query,exact=false){const part=window.LawCore.snippet(text,query,exact);node.append(document.createTextNode(part.before));if(part.mark){const mark=document.createElement('mark');mark.textContent=part.mark;node.append(mark);}node.append(document.createTextNode(part.after));}
function showSearch(){
 const target=openSheet('חיפוש בחוק ובחקיקת המשנה'),restoring=!!searchState,restoreScroll=searchState?.scroll||0;
 const input=document.createElement('input');input.type='search';input.maxLength=512;input.className='m-search-input';input.id='mobile-search';input.placeholder='מילה, צירוף או מספר סעיף';input.setAttribute('aria-label','חיפוש בטקסט');input.value=searchState?.query||'';
 const meta=document.createElement('div');meta.className='m-search-meta';
 const count=document.createElement('span');count.setAttribute('role','status');count.setAttribute('aria-live','polite');
 const scope=document.createElement('select');scope.setAttribute('aria-label','תחום חיפוש');for(const[value,label]of [['all','הכול'],['law','החוק'],['delegated','חקיקת משנה']]){const o=document.createElement('option');o.value=value;o.textContent=label;scope.append(o);}scope.value=searchState?.scope||'all';
 const mode=document.createElement('select');mode.setAttribute('aria-label','אופן התאמה');for(const[value,label]of [['normalized','התאמה מנורמלת'],['exact','התאמה מדויקת']]){const o=document.createElement('option');o.value=value;o.textContent=label;mode.append(o);}mode.value=searchState?.mode||'normalized';
 meta.append(count,scope,mode);const results=document.createElement('div');results.id='mobile-search-results';target.append(input,meta,results);
 const remember=()=>{searchState={query:input.value,scope:scope.value,mode:mode.value,scroll:target.scrollTop,rendered:results.querySelectorAll('.m-result').length};};
 const run=()=>{
  if(!input.isConnected)return;results.replaceChildren();const raw=input.value,q=mode.value==='exact'?raw:fold(raw);
  if(!q||q.length>512){count.textContent='';const hint=document.createElement('p');hint.className='m-hint';hint.textContent=q.length>512?'החיפוש מוגבל ל־512 תווים.':'הקלד מילה או ביטוי לחיפוש.';results.append(hint);remember();return;}
  const records=buildSearch(),number=/^(?:סעיף\s*)?[0-9]+[א-ת]*$/.test(q)?q.replace(/^סעיף\s*/,''):null;
  const matches=records.filter(r=>(scope.value==='all'||r.kind===scope.value)&&((mode.value==='exact'?r.text:r.folded).includes(q)||(number&&(r.title.startsWith('סעיף '+number+' ·')||r.title.startsWith('תקנה / סעיף '+number+' ·')))));
  count.textContent=matches.length+' תוצאות';
  if(!matches.length){const p=document.createElement('p');p.className='m-empty';p.textContent='לא נמצאו תוצאות בקובץ המצורף.';results.append(p);remember();return;}
  const render=from=>{const fragment=document.createDocumentFragment(),batch=from===0?Math.max(60,Math.min(searchState?.rendered||60,matches.length)):60;
   for(const r of matches.slice(from,from+batch)){
    const b=document.createElement('button');b.type='button';b.className='m-result';const heading=document.createElement('strong'),sub=document.createElement('small'),snippet=document.createElement('span');heading.textContent=r.title;sub.textContent=r.subtitle+' · '+(r.text.includes(raw)?'התאמה מדויקת':'התאמה מנורמלת');appendSnippet(snippet,r.text,raw,mode.value==='exact');b.append(heading,sub,snippet);
    b.addEventListener('click',()=>{remember();goTo(r.el);$('#mobile-return').hidden=false;saveSession(r.el.id);});fragment.append(b);
   }results.append(fragment);if(from+batch<matches.length){const more=action('תוצאות נוספות',()=>{more.remove();render(from+batch);});results.append(more);}
  };render(0);remember();
 };
 input.addEventListener('input',()=>{remember();clearTimeout(searchTimer);searchTimer=setTimeout(run,160);});scope.addEventListener('change',run);mode.addEventListener('change',run);run();
 if(restoring)requestAnimationFrame(()=>{target.scrollTop=restoreScroll;});else input.focus();
}

function returnToSearch(){if(!searchState)return false;$('#mobile-return').hidden=true;showSearch();return true;}
function print(){if(native()){native().printDocument();return;}window.print();}
function showMore(){const target=openSheet('תצוגה ופעולות');const sizes=document.createElement('div');sizes.className='m-size';const label=document.createElement('span');label.textContent='גודל הטקסט';const less=document.createElement('button'),more=document.createElement('button');less.textContent='א−';more.textContent='א+';less.setAttribute('aria-label','הקטנת הטקסט');more.setAttribute('aria-label','הגדלת הטקסט');const set=delta=>{const size=Math.max(16,Math.min(28,parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--reading-size'))+delta));document.documentElement.style.setProperty('--reading-size',size+'px');safeSet('law-reader-font',size);};less.onclick=()=>set(-1);more.onclick=()=>set(1);sizes.append(label,less,more);const align=document.createElement('div');align.className='m-alignment';align.setAttribute('role','group');align.setAttribute('aria-label','יישור טקסט הקריאה');const setAlign=value=>{document.documentElement.dataset.lawAlign=value;document.documentElement.classList.toggle('m-justify',value==='justify');safeSet('law-reader-align',value);showMore();};const right=action('יישור לימין',()=>setAlign('right'));const both=action('יישור לשני הצדדים',()=>setAlign('justify'));right.setAttribute('aria-pressed',String(document.documentElement.dataset.lawAlign==='right'));both.setAttribute('aria-pressed',String(document.documentElement.dataset.lawAlign==='justify'));align.append(right,both);const preview=document.createElement('p');preview.className='m-reading-preview';preview.textContent='זו דוגמה לטקסט קריאה משפטי. אפשר לבחור יישור המתאים למסך, לניקוד ולהעדפת הקריאה.';target.append(sizes,align,preview,action('חזרה לתחילת החוק',()=>goTo('law_name')),action('הדפסה או שמירה כ־PDF',print),action('תפריט נגישות',showAccessibility),action('גיבוי ההגדרות לקובץ',()=>window.lawSettings.exportFile()),action('שחזור הגדרות מקובץ',()=>window.lawSettings.importFile()));if(!native())target.append(action('התקנת האפליקציה',installInstructions));target.append(action('משוב על גרסת הבטא',()=>{const panel=openSheet('דיווח תקלה או הצעה');const p=document.createElement('p');p.className='m-hint';p.textContent='הדיווח יועתק ללוח בלבד ולא יישלח אוטומטית. יש להסיר מידע אישי מצילומי המסך.';panel.append(p,action('העתקת תבנית משוב',()=>{const item=currentArticle();const lines=['חוק הגנת הצרכן, התשמ"א–1981 · בטא 1.3.9-dev (נייד / מחשב)','מכשיר וגרסת מערכת:','מיקום בחוק: '+(item?articleLabel(item):'לא צוין'),'מה ניסיתי לעשות:','מה קרה בפועל:','מה ציפיתי שיקרה:','האם ניתן לשחזר:'];copy(lines.join('\n'));}));}));target.append(action('מדיניות פרטיות ותקשורת',showPrivacy));target.append(action('על הקובץ',()=>{const t=openSheet('על הקובץ');t.append(stripIds($('footer').cloneNode(true)));const p=document.createElement('p');p.className='m-hint';p.textContent='בטא 1.3.9-dev · בעלים, עורך ומפרסם: '+(editorial.editor_publisher||'סרגון 17 גרין')+' (אדם פרטי). הוא אחראי לנכונות נוסח חוק הגנת הצרכן ליום הבדיקה האחרון: '+editorialDate()+'. תאריך הבדיקה אינו מתקדם אוטומטית עם עדכון האפליקציה; ייתכן שתיקונים שפורסמו אחריו טרם שולבו. האפליקציה אינה פרסום ממשלתי או מטעם הרשות להגנת הצרכן ולסחר הוגן.';t.append(p);const q=document.createElement('p');q.className='m-hint';q.textContent='אין התחייבות לנכונות או לשלמות של מטא־דאטה ומידע נלווה, לרבות הערות, תאריכים, היסטוריה, קישורים ושיוך חקיקת משנה. טרם הושלמה בדיקה עובדתית של ביטול אכרזות פיקוח ושל ביטול או תיקון צווים היסטוריים. זהו פער באימות המקורות, לא ספק נטען במסגרת המשפטית. היעדר צו מן הרשימה אינו ראיה לביטולו.';t.append(q);const lic=document.createElement('p');lic.className='m-hint';lic.textContent='קוד האפליקציה: MIT. נוסחי חקיקה, סימנים מסחריים וקבצים של צדדים שלישיים אינם מוקנים ברישיון MIT מכוח הכללתם בחבילה.';t.append(lic);}));}

function showPrivacy(){const panel=openSheet('מדיניות פרטיות ותקשורת');let policy;try{policy=JSON.parse($('#law-privacy').textContent);}catch{toast('מידע הפרטיות אינו זמין');return;}for(const text of policy.paragraphs){const p=document.createElement('p');p.textContent=text;panel.append(p);}const link=document.createElement('a');link.className='m-action';link.textContent='פתיחת מדיניות הפרטיות בדפדפן';link.href=policy.publicURL;link.target='_blank';link.rel='noopener noreferrer';panel.append(link);}
function setSystemFontScale(scale){if(safeGet('law-reader-font')===null&&Number.isFinite(scale)&&scale>0){const size=Math.max(16,Math.min(48,19*scale))+'px';if(readingLayout().size===size)return;const anchor=currentArticle()||document.getElementById('law_name');pointRestore++;document.documentElement.style.setProperty('--reading-size',size);anchor?.scrollIntoView({block:'start',behavior:'instant'});}}
function showAccessibility(){const target=openSheet('נגישות');const apply=(name,on)=>{document.documentElement.classList.toggle(name,on);safeSet('law-a11y-'+name,on?'1':'0');};for(const [name,label] of [['m-contrast-dark','ניגודיות: צהוב על שחור'],['m-contrast-blue','ניגודיות: שחור על כחול בהיר'],['m-underline','קו תחתון לקישורים'],['m-no-motion','עצירת הנפשות'],['m-gray','תמונות בגווני אפור'],['m-serif','גופן עם תגיות']]){const b=action(label,()=>{const on=!document.documentElement.classList.contains(name);if(name==='m-contrast-dark')apply('m-contrast-blue',false);if(name==='m-contrast-blue')apply('m-contrast-dark',false);apply(name,on);showAccessibility();});b.setAttribute('aria-pressed',document.documentElement.classList.contains(name)?'true':'false');target.append(b);}target.append(action('שחזור הגדרות תצוגה',()=>{['m-contrast-dark','m-contrast-blue','m-underline','m-no-motion','m-gray','m-serif'].forEach(n=>apply(n,false));document.documentElement.style.removeProperty('--reading-size');safeRemove('law-reader-font');document.documentElement.classList.add('m-justify');document.documentElement.dataset.lawAlign='justify';safeRemove('law-reader-align');showAccessibility();}));}

function installInstructions(){
  const target=openSheet('התקנת האפליקציה');
  const status=document.createElement('p');status.id='mobile-offline-status';status.className='m-hint';status.setAttribute('role','status');status.textContent=offlineMessage();target.append(status);
  const installed=matchMedia('(display-mode: standalone)').matches||navigator.standalone===true;
  const p=document.createElement('p');
  if(installed){p.textContent='האפליקציה כבר נפתחה מהתקנה במסך הבית. אפשר לחזור אליה מהסמל הקבוע, בלי לחפש שוב את הקישור.';target.append(p);return;}
  p.textContent='התקנה תיצור סמל קבוע במסך הבית, שממנו אפשר לפתוח את האפליקציה ישירות. האישור הסופי נעשה בחלון של מערכת ההפעלה או הדפדפן.';
  target.append(p);
  if(deferredInstall)target.append(action('התקנה במסך הבית',async()=>{
    const prompt=deferredInstall;deferredInstall=null;
    try{await prompt.prompt();const choice=await prompt.userChoice;
      toast(choice?.outcome==='accepted'?'בקשת ההתקנה אושרה':'ההתקנה בוטלה; אפשר לנסות שוב מתפריט הדפדפן');
    }catch{toast('לא ניתן לפתוח התקנה כעת. אפשר להוסיף למסך הבית מתפריט הדפדפן');}
  }));
  const instructions=document.createElement('p');
  const apple=/iPhone|iPad|iPod/.test(navigator.userAgent)||(navigator.platform==='MacIntel'&&navigator.maxTouchPoints>1);
  instructions.textContent=apple?'ב־Safari: פתח את תפריט השיתוף, בחר ״הוספה למסך הבית״ ואשר.':'ב־Chrome: פתח את תפריט הדפדפן ובחר ״התקנת האפליקציה״ או ״הוספה למסך הבית״.';
  target.append(instructions);
  if(/Android/.test(navigator.userAgent)){
    const link=document.createElement('a');link.className='m-original-link';
    link.href='https://raw.githubusercontent.com/Sargon17-Green/consumer-law-reader/main/downloads/latest.apk';
    link.textContent='הורדת אפליקציית Android המקורית — בטא ציבורית 1.3.5';
    target.append(link);
    const note=document.createElement('p');note.className='m-hint';
    note.textContent='זהו קובץ APK מההפצה החתומה הקיימת, עם סמל ברשימת היישומים. פתח את הקובץ ואשר התקנה ב־Android. אל תסיר גרסה קיימת במקרה של אי־התאמת חתימה, כדי לשמור על הנתונים.';
    target.append(note);
  }
}
// Numbered legal prose can reflow. Genuine forms and data keep their two-dimensional cells.
function prepareReadingTables(){
  const tables=$$('#frame table').filter(t=>!t.closest('.sources_box,.bills_box,.protocols_box,.history_box'));
  for(const table of tables){
    if(table.matches('.article,.article_deleted,.appendix'))continue;
    const rows=$$(':scope>tbody>tr',table);
    if(rows.length&&rows.some(row=>row.children.length>=2&&row.firstElementChild.classList.contains('numbering'))&&rows.every(row=>
      ((row.children.length===2||row.children.length===3)&&row.firstElementChild.classList.contains('numbering'))||
      (row.children.length===2&&!row.firstElementChild.textContent.trim()&&row.lastElementChild.classList.contains('done_accordingly'))||
      (row.children.length===1&&row.firstElementChild.matches('.done_accordingly,[colspan]')))){
      table.classList.add('m-prose-table');table.setAttribute('role','presentation');
    }
  }
  for(const table of tables){
    if(table.matches('.article,.article_deleted,.m-prose-table,.chapter_title,.subchapter_title,.appendix_title,.subappendix_title,#law_name,#index')||table.closest('.m-table-scroll'))continue;
    const rows=$$(':scope>tbody>tr,:scope>thead>tr,:scope>tfoot>tr',table);
    const columns=Math.max(0,...rows.map(row=>[...row.children].reduce((n,cell)=>n+(cell.colSpan||1),0)));
    if(columns<=1&&rows.every(row=>row.children.length===1)){table.classList.add('m-flow-table');table.setAttribute('role','presentation');continue;}
    // Original forms and mathematical rows can have neither IDs nor TH cells.
    // Preserve their cells; a one-cell document heading is not a data table.
    if(columns<=1)continue;
    const wrap=document.createElement('div');wrap.className='m-table-scroll';wrap.tabIndex=0;
    wrap.setAttribute('role','region');wrap.setAttribute('aria-label','טבלה לגלילה אופקית');
    table.classList.add('m-data-table');table.before(wrap);wrap.append(table);
  }
}
function init(){try{window.LawCore.recover(localStorage);}catch{toast('לא ניתן לשחזר את ההגדרות הקודמות');return;}const editorLabel=$('.m-subtitle');if(editorLabel)editorLabel.textContent='נוסח נבדק: '+editorialDate();const storedAlign=safeGet('law-reader-align');const preferredAlign=storedAlign==='right'?'right':'justify';document.documentElement.dataset.lawAlign=preferredAlign;document.documentElement.classList.toggle('m-justify',preferredAlign==='justify');['m-contrast-dark','m-contrast-blue','m-underline','m-no-motion','m-gray','m-serif'].forEach(n=>document.documentElement.classList.toggle(n,safeGet('law-a11y-'+n)==='1'));$$('#frame .defined').forEach(e=>{e.setAttribute('role','button');e.tabIndex=0;const term=e.cloneNode(true);$$('.the_definition',term).forEach(node=>node.remove());e.setAttribute('aria-label','הצגת הגדרה: '+cleanText(term.textContent).slice(0,120));e.addEventListener('keydown',v=>{if(v.key==='Enter'||v.key===' '){v.preventDefault();pressLink(e);definition(e);}});});$$('#frame .name[onclick]').forEach(e=>{if(e.querySelector('a[href],button,input,select,[role=button]'))return;e.setAttribute('role','button');e.tabIndex=0;e.addEventListener('keydown',v=>{if(v.key==='Enter'||v.key===' '){v.preventDefault();e.click();}});});$$('a[tabindex="-1"]').forEach(e=>e.removeAttribute('tabindex'));$$('#frame a[href^="#"][onclick]').forEach(a=>{if((a.getAttribute('onclick')||'').includes('mark_and_verify_open('))a.removeAttribute('onclick');});document.onclick=null;document.oncontextmenu=null;$$('[oncontextmenu]').forEach(e=>e.removeAttribute('oncontextmenu'));const font=Number(safeGet('law-reader-font'));if(font>=16&&font<=28)document.documentElement.style.setProperty('--reading-size',font+'px');$('#index_content').style.display='none';$('#index_title').style.listStyle='disclosure-closed';prepareReadingTables();window.copy_article=()=>activeArticle&&copy(textForCopy(activeArticle));window.copy_selected=()=>copy(window.getSelection()?.toString()||'');$('#mobile-sheet-close').onclick=closeSheet;sheet.addEventListener('cancel',e=>{e.preventDefault();closeSheet();});$('#mobile-return').onclick=returnToSearch;$('#mobile-regulation-back').onclick=closeRegulation;sheet.addEventListener('click',e=>{if(e.target===sheet){const r=sheet.getBoundingClientRect();if(e.clientY<r.top||e.clientX<r.left||e.clientX>r.right)closeSheet();}});// The nested legacy note body already toggles itself via inline onclick.
// Stop its click from reaching the outer note_button, which would toggle twice.
$$('#frame .note_button_text').forEach(label=>{const parent=label.closest('.note_button');if(!parent||label.querySelector('a,button'))return;label.setAttribute('role','button');label.tabIndex=0;const update=()=>label.setAttribute('aria-expanded',String(getComputedStyle(parent.querySelector('.note_div')).display!=='none'));update();parent.addEventListener('click',update);label.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();label.click();}});});
$$('#frame .note_button > .note_div[onclick]').forEach(div=>div.addEventListener('click',e=>e.stopPropagation()));
// Highlight lifetime follows a completed click in the document, not pointerdown.
// A touch scroll, mouse drag or text selection must leave navigation highlights intact.
let highlightPointer=null;
document.addEventListener('pointerdown',e=>{
  highlightPointer={id:e.pointerId,x:e.clientX,y:e.clientY,moved:false,inside:!!e.target.closest?.('#frame')};
},{capture:true,passive:true});
document.addEventListener('pointermove',e=>{
  if(highlightPointer?.id===e.pointerId&&Math.hypot(e.clientX-highlightPointer.x,e.clientY-highlightPointer.y)>10)highlightPointer.moved=true;
},{capture:true,passive:true});
document.addEventListener('pointercancel',e=>{
  if(highlightPointer?.id===e.pointerId)highlightPointer.moved=true;
},{capture:true,passive:true});
document.addEventListener('click',e=>{
  const withinDocument=!!e.target.closest?.('#frame');
  const dragged=e.detail!==0&&!!highlightPointer?.moved;
  const startedHere=!highlightPointer||highlightPointer.inside;
  highlightPointer=null;
  // Do not clear highlights, activate links, or interpret a drag as a tap.
  if(withinDocument&&dragged){e.preventDefault();e.stopImmediatePropagation();return;}
  if(withinDocument&&startedHere){
    clearTargetHighlight(false);
    lastActivatedLink=null;
  }
const b=e.target.closest('[data-mobile]');if(b){({search:showSearch,toc:showToc,navigate:showNavigate,actions:showGlobalActions,sources:()=>window.LawSources.showHub(),more:showMore})[b.dataset.mobile]();return;}const tapped=e.target.closest('#frame table.article[id],#frame table.article_deleted[id],#frame table.appendix[id]');if(tapped)activeArticle=tapped;const defined=e.target.closest('.defined');if(defined){e.preventDefault();e.stopPropagation();pressLink(defined);definition(defined);return;}const a=e.target.closest('a[href]');if(!a)return;const href=a.getAttribute('href');if(href.startsWith('#')){e.preventDefault();lastActivatedLink=a;try{goTo(decodeURIComponent(href.slice(1)));pressLink(a);}catch{toast('כתובת הקישור אינה תקינה');}}else if(href.startsWith('./')&&native()){e.preventDefault();try{native().openAttachment(decodeURIComponent(href.slice(2)));}catch{toast('כתובת הקובץ אינה תקינה');}}else if(/^https?:/.test(href)){a.target='_blank';a.rel='noopener noreferrer';}if(!href.startsWith('#'))pressLink(a);},true);history.scrollRestoration='manual';window.addEventListener('popstate',event=>{clearTargetHighlight(true);if(sheet.open)closeSheet();if(location.hash){try{goTo(decodeURIComponent(location.hash.slice(1)),false,false);}catch{}}else scrollTo(0,0);if(event.state?.lawPoint)restorePoint(event.state.lawPoint);if(lastActivatedLink?.isConnected)lastActivatedLink.classList.add('m-link-return');});window.lawMobileBack=()=>{clearTargetHighlight(true);return closeSheet()||(!$('#mobile-return').hidden&&returnToSearch())||closeRegulation();};window.LawTopics.init({openSheet,action,goTo,toast,articleLabel});window.LawSources.init({openSheet,action,articleLabel,stripIds,goTo,copy,fold});window.reveal=(id)=>{const el=document.getElementById(id);if(!el)return;if(openedRegulation===el){closeRegulation();return;}if(el.classList.contains('delegated_legislation')){openRegulation(el);el.scrollTop=0;return;}el.style.display=el.style.display==='block'?'none':'block';};window.lawMobile={version:window.LawCore.VERSION,goTo,showActions,showGlobalActions,currentArticle,showToc,showNavigate,showSearch,showMore,buildSearch,definition,openRegulation,closeRegulation,shareLink,saveSession,setSystemFontScale,copyResult};window.addEventListener('pagehide',()=>saveSession());document.addEventListener('visibilitychange',()=>{if(document.hidden)saveSession();});let restored=false,session;try{session=JSON.parse(safeGet(SESSION)||'null');}catch{}if(session?.schema===1){searchState=session.search&&typeof session.search.query==='string'&&session.search.query.length<=512?session.search:null;if(searchState)$('#mobile-return').hidden=false;if(typeof session.target==='string'&&document.getElementById(session.target)&&(!location.hash||location.hash==='#'+encodeURIComponent(session.target))){goTo(session.target,false,false);restorePoint(session.point);restored=true;}}document.documentElement.dataset.lawReady='true';window.dispatchEvent(new Event('law-ready'));let scrollSave;window.addEventListener('scroll',()=>{clearTimeout(scrollSave);scrollSave=setTimeout(()=>{if(!sheet.open)saveSession();},350);},{passive:true});if(!native())initOffline();if(location.hash&&!restored)setTimeout(()=>{try{goTo(decodeURIComponent(location.hash.slice(1)),false);}catch{}},100);window.addEventListener('load',()=>{document.onclick=null;document.oncontextmenu=null;});}
async function initOffline(){
 setOfflineState('saving');
 if(!('serviceWorker' in navigator)){setOfflineState('unavailable');return;}
 const worker=navigator.serviceWorker;
 const deadline=setTimeout(()=>setOfflineState('unavailable'),60000);
 const requestStatus=()=>{if(worker.controller)worker.controller.postMessage({type:'OFFLINE_STATUS'});};
 worker.addEventListener('message',event=>{
  if(event.source!==worker.controller||!['OFFLINE_READY','OFFLINE_ERROR'].includes(event.data?.type))return;
  clearTimeout(deadline);setOfflineState(event.data.type==='OFFLINE_READY'?'ready':'unavailable');
 });
 worker.addEventListener('controllerchange',requestStatus);
 try{const registration=await worker.register('./sw.js');registration.addEventListener('updatefound',()=>{const installing=registration.installing;installing?.addEventListener('statechange',()=>{if(installing.state==='redundant'&&!worker.controller){clearTimeout(deadline);setOfflineState('unavailable');}});});await worker.ready;requestStatus();}
 catch{clearTimeout(deadline);setOfflineState('unavailable');}
}

window.addEventListener('beforeinstallprompt',e=>{e.preventDefault();deferredInstall=e;});
window.addEventListener('appinstalled',()=>{deferredInstall=null;toast('האפליקציה הותקנה; אפשר לפתוח אותה מהסמל הקבוע');});
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
