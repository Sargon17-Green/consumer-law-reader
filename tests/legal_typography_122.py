"""Focused Browser QA 1.2.2. Synthetic interaction plus real excerpt of §4a.
Not physical device or full legal corpus certification."""
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import json
ROOT=Path(__file__).resolve().parents[1]
source=BeautifulSoup((ROOT/'original/Consumer_Protection_Law.html').read_text(),'lxml')
a=source.find('table',{'id':'article_4a'})
assert a
for n in a.select('.delegated_legislation'):n.decompose()
for n in a.select('.done_accordingly'):n.decompose()
chapter='''<div class="chapter_title" id="chapter_example">פרק שני: ההוראות הכלליות</div>
<div class="subchapter_title" id="subchapter_example">סימן א: גילוי לצרכן</div>'''
head='''<!DOCTYPE html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body>'''+(ROOT/'web/mobile-shell.html').read_text()+'''<main id="frame"><h1 id="law_name">חוק הגנת הצרכן</h1><div id="index"><div id="index_title">מפתח</div><div id="index_content"><table><tr><td class="article_link"><a href="#article_4a">סעיף 4א</a></td></tr></table></div></div>'''
foot='''<a id="go-to-link" href="#article_4a_detail_2">לעבור לסעיף</a></main><nav id="navigator"><ul><li><a href="#article_4a">ניווט</a></li></ul></nav><footer>בדיקת קריאה</footer></body></html>'''
html=head+chapter+str(a)+foot
checks=[]
def test(name,passed,detail=''):
 checks.append({'check':name,'pass':bool(passed),'detail':str(detail)[:140]});print(('PASS' if passed else 'FAIL'),name,detail,flush=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 for w in [320,375,430,600]:
  page=browser.new_page(viewport={'width':w,'height':780})
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(html,wait_until='domcontentloaded')
  page.evaluate('''() => {const s={}; Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>s[k]||null,setItem:(k,v)=>s[k]=v,removeItem:k=>delete s[k]}})}''')
  page.add_style_tag(content=(ROOT/'web/mobile.css').read_text())
  for file in ['mobile-sources.js','mobile-topics.js','mobile.js']:
   page.add_script_tag(content=(ROOT/'web'/file).read_text())
  data=page.evaluate('''() => {const title=document.querySelector('#article_4a .side_title');const first=title.querySelector('.defined');const opening=document.createElement('p');opening.className='opening';opening.textContent='בתוקף סמכותי לפי חוק הגנת הצרכן אני מתקין תקנות אלה';const reg=document.createElement('div');reg.className='delegated_legislation';reg.append(opening);document.querySelector('#frame').append(reg);const ch=document.querySelector('.chapter_title'),sub=document.querySelector('.subchapter_title');return {width:innerWidth,docWidth:document.documentElement.scrollWidth,titleDisplay:getComputedStyle(title).display,headingColor:getComputedStyle(title).color,linkColor:getComputedStyle(first).color,titleText:title.innerText, chapterAlign:getComputedStyle(ch).textAlign,subAlign:getComputedStyle(sub).textAlign,openingSize:getComputedStyle(opening).fontSize,bodySize:getComputedStyle(document.body).fontSize,proseAlign:getComputedStyle(document.querySelector('#article_4a_detail_1 td:last-child')).textAlign,onclickRemoved:document.querySelector('#article_4a_detail_1 a').getAttribute('onclick')===null}}''')
  test(f'law_title_integrated_{w}',data['titleDisplay']=='block' and data['headingColor']==data['linkColor'], data['titleDisplay'])
  test(f'unit_titles_centered_{w}',data['chapterAlign']=='center' and data['subAlign']=='center')
  test(f'opening_full_size_{w}',data['openingSize']==data['bodySize'],(data['openingSize'],data['bodySize']))
  test(f'no_horizontal_overflow_{w}',data['docWidth']<=data['width'],(data['docWidth'],data['width']))
  test(f'legacy_link_highlight_handler_removed_{w}',data['onclickRemoved'])
  test(f'responsive_alignment_{w}',data['proseAlign']==('right' if w<480 else 'justify'),data['proseAlign'])
  page.locator('#go-to-link').click()
  test(f'target_highlight_after_link_{w}',page.locator('#article_4a_detail_2').evaluate("e=>e.classList.contains('m-target')"))
  page.locator('.chapter_title').click()
  test(f'clear_highlight_tap_anywhere_{w}',not page.locator('#article_4a_detail_2').evaluate("e=>e.classList.contains('m-target')"))
  page.locator('#go-to-link').click()
  page.go_back(wait_until='domcontentloaded') if False else page.evaluate('history.back()')
  page.wait_for_timeout(120)
  test(f'back_clear_background_{w}',not page.locator('#article_4a_detail_2').evaluate("e=>e.classList.contains('m-target')"))
  test(f'back_emphasize_link_only_{w}',page.locator('#go-to-link').evaluate("e=>e.classList.contains('m-link-return')"))
  page.evaluate("document.querySelector('#go-to-link').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}))")
  test(f'next_tap_removes_link_emphasis_{w}',not page.locator('#go-to-link').evaluate("e=>e.classList.contains('m-link-return')"))
  test(f'no_runtime_errors_{w}',not errors,errors[:1])
  if w==375:
   page.locator('#article_4a').scroll_into_view_if_needed()
   page.screenshot(path='/mnt/data/Consumer_Law_Mobile_1.2.2_Section4a_Proof.png',full_page=False)
  page.close()
 browser.close()
path=ROOT/'evidence/legal-typography-v1.2.2.json'
path.write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print('TOTAL',len(checks),'FAILED',sum(not c['pass'] for c in checks),flush=True)
raise SystemExit(1 if any(not c['pass'] for c in checks) else 0)
