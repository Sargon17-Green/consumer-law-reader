"""QA for source-exact topic navigation, broken targets and personal overlays."""
from pathlib import Path
import json, shutil
from urllib.parse import unquote
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'original/Consumer_Protection_Law.html'
doc=BeautifulSoup(SOURCE.read_bytes(),'lxml')
nav=doc.select_one('#navigator')
assert nav is not None
root=nav.find('ul',recursive=False)
assert root is not None
all_ids={x.get('id') for x in doc.select('[id]')}
valid_anchors=[a for a in nav.select('a[href^="#"]') if unquote(a['href'][1:]) in all_ids]
broken=[a for a in nav.select('a[href^="#"]') if unquote(a['href'][1:]) not in all_ids]
expected_targets=[unquote(a['href'][1:]) for a in valid_anchors]
assert len(broken)==1, [(a.get_text(' ',strip=True),a['href']) for a in broken]
assert len(expected_targets)==79, len(expected_targets)
expected_root=[]
for element in root.find_all(recursive=False):
    if element.name!='li':continue
    if 'nav_list_title' in element.get('class',[]):
        expected_root.append(['topic',element.get_text(' ',strip=True)])
    else:
        link=element.find('a',recursive=False)
        if link and link.get('href','').startswith('#') and unquote(link['href'][1:]) in all_ids:
            expected_root.append(['link',link.get_text(' ',strip=True)])
target_nodes=''.join('<div id="'+x+'"></div>' for x in sorted(set(expected_targets)))
html='<html lang="he" dir="rtl"><body>'+str(nav)+target_nodes+'<div id="test-sheet"></div></body></html>'
js=(ROOT/'web/mobile-topics.js').read_text(encoding='utf-8')
with sync_playwright() as pw:
    options={'headless':True,'args':['--no-sandbox','--disable-dev-shm-usage']}
    executable=shutil.which('chromium')
    if executable: options['executable_path']=executable
    browser=pw.chromium.launch(**options)
    for width in (320,375,430,1280):
        page=browser.new_page(viewport={'width':width,'height':800})
        errors=[]
        page.on('pageerror',lambda err:errors.append(str(err)))
        page.set_content(html)
        page.evaluate("""() => {
          const values={};
          Object.defineProperty(window,'localStorage',{configurable:true,value:{
            getItem:k=>values[k]??null,
            setItem:(k,v)=>{values[k]=String(v);},
            removeItem:k=>{delete values[k];}
          }});
          window.__visited=[];
          window.__alerts=[];
          window.__app={
            openSheet:(name)=>{let root=document.getElementById('test-sheet');root.replaceChildren();return root;},
            action:(label,fn)=>{let b=document.createElement('button');b.type='button';b.textContent=label;b.addEventListener('click',fn);return b;},
            goTo:(target)=>window.__visited.push(target),
            toast:(text)=>window.__alerts.push(text),
            articleLabel:(el)=>'סעיף לדוגמה'
          };
        }""")
        page.add_script_tag(content=js)
        page.evaluate("() => {LawTopics.init(window.__app);LawTopics.show();}")
        inspect=page.evaluate("LawTopics.inspect()")
        assert inspect['baseTopics']==13,inspect
        assert inspect['baseLinks']==79,inspect
        rendered_root=page.evaluate("""() => Array.from(document.querySelector('.m-topic-tree').children).map(e=>
          e.matches('details')?['topic',e.querySelector(':scope > summary').textContent]:
          e.matches('.m-topic-link')?['link',e.querySelector('button').textContent]:['unexpected',e.tagName])""")
        assert rendered_root==expected_root,(width,rendered_root,expected_root)
        assert not page.get_by_text('נושאי הבסיס נגזרים').count()
        assert not page.locator('.m-topic-tree').get_by_text('בהחלפת חלקים במוצר').count()
        assert not page.get_by_text('יעד לא נמצא').count()
        # All rendered base links, including links nested after a subtopic,
        # are ordered as they appear in the original source.
        page.evaluate("""() => document.querySelectorAll('.m-topic-link > button:first-child').forEach(b=>b.click())""")
        visited=page.evaluate("window.__visited")
        assert visited==expected_targets,(width,len(visited),len(expected_targets))
        # Filtering keeps ancestor paths while hiding unrelated entries.
        page.locator('input[aria-label="חיפוש בניווט הנושאי"]').fill('החזרת התמורה')
        assert page.get_by_role('button',name='החזרת התמורה').count()==1
        assert page.locator('.m-topic-tree > details > summary').filter(has_text='ביטול עסקה').count()==1
        # A broken saved personal link must be omitted without erasing valid personal data.
        page.evaluate("""() => {
          localStorage.setItem('law-reader-topics-v1',JSON.stringify({
            schema:1,userTopics:[{id:'u:test',title:'נושא אישי',parent:null,index:1000}],
            links:[
              {id:'u:bad',topic:'u:test',target:'MISSING_TARGET',title:'קישור שבור',origin:'user'},
              {id:'u:ok',topic:'u:test',target:'article_2',title:'קישור שמור',origin:'user'}
            ],titles:{},hidden:{},ranks:{}
          }));
          LawTopics.init(window.__app);LawTopics.show();
        }""")
        assert page.get_by_text('נושא אישי',exact=True).count()==1
        assert page.get_by_role('button',name='קישור שמור').count()==1
        assert page.get_by_text('קישור שבור').count()==0
        page.get_by_role('button',name='קישור שמור').evaluate('(b)=>b.click()')
        assert page.evaluate('window.__visited.at(-1)')=='article_2'
        assert not errors,errors
        page.close()
        print('PASS topics source order, all 79 links, search and personal overlay, width',width)
    browser.close()
