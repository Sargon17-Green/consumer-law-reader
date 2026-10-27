from pathlib import Path
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json
ROOT=Path(__file__).resolve().parents[1]
s=BeautifulSoup((ROOT/'dist/index.html').read_text(), 'lxml')
for t in s.find_all('script'):t.decompose()
for t in s.find_all('iframe'):t.decompose()
for t in s.find_all('link',rel='stylesheet'):t.decompose()
html=str(s)
print('DOM_SOURCE_CHARS',len(html),flush=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 pg=b.new_page(viewport={'width':375,'height':760})
 pg.set_content(html,wait_until='domcontentloaded',timeout=20000)
 pg.add_style_tag(content=(ROOT/'web/mobile.css').read_text())
 report=pg.evaluate('''() => ({width:innerWidth,scrollWidth:document.documentElement.scrollWidth,frameWidth:document.querySelector('#frame').getBoundingClientRect().width,articles:document.querySelectorAll('.article').length,navTopics:document.querySelectorAll('#navigator li.nav_list_title').length, bottomButtons:document.querySelectorAll('.m-bottom button').length})''')
 print(json.dumps(report,ensure_ascii=False),flush=True)
 (ROOT/'evidence/full-dom-v1.2.0.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 b.close()
