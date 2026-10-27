from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import json
ROOT=Path(__file__).resolve().parents[1]
s=BeautifulSoup((ROOT/'dist/index.html').read_text(),'lxml')
for t in s.find_all(['script','iframe']):t.decompose()
for t in s.find_all('link',rel='stylesheet'):t.decompose()
html=str(s).replace('onload="start()"','')
checks=[]
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 for w in (320,375,430):
  pg=b.new_page(viewport={'width':w,'height':780})
  errors=[];pg.on('pageerror',lambda e: errors.append(str(e)))
  pg.set_content(html,wait_until='domcontentloaded',timeout=22000)
  pg.evaluate('''() => {const map={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>Object.hasOwn(map,k)?map[k]:null,setItem:(k,v)=>map[k]=String(v),removeItem:k=>delete map[k]}})}''')
  pg.add_style_tag(content=(ROOT/'web/mobile.css').read_text())
  for name in ('mobile-sources.js','mobile-topics.js','mobile.js'):pg.add_script_tag(content=(ROOT/'web'/name).read_text())
  p1=pg.evaluate('''() => ({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,version:window.lawMobile?.version,topics:window.LawTopics.inspect(),articles:document.querySelectorAll('.article').length})''')
  try:
   pg.locator('[data-mobile=navigate]').click(timeout=3500)
   p1['topicCards']=pg.locator('.m-topic').count()
   pg.locator('#mobile-sheet-close').click(timeout=3500)
   pg.locator('[data-mobile=search]').click(timeout=3500)
   pg.locator('#mobile-search').fill('הטעיה',timeout=3500)
   pg.wait_for_timeout(450)
   p1['searchResults']=pg.locator('.m-result').count()
  except Exception as e:p1['error']=str(e)[:400]
  p1['pageErrors']=errors[:3]
  print(json.dumps(p1,ensure_ascii=False),flush=True);checks.append(p1)
  pg.close()
 b.close()
(ROOT/'evidence/full-dom-interactive-v1.2.0.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
