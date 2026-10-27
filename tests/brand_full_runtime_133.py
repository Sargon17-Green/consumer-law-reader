from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import json
r=Path('/mnt/data/consumer_mobile_work')
soup=BeautifulSoup((r/'dist/index.html').read_text(encoding='utf-8'),'lxml')
for x in soup.find_all('script'):x.decompose()
for x in soup.find_all('iframe'):x.decompose()
for x in soup.find_all('link',rel='stylesheet'):x.decompose()
if soup.body:soup.body.attrs.pop('onload',None)
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-background-networking'])
 out=[]
 for width in (320,375,430,1280):
  p=browser.new_page(viewport={'width':width,'height':850})
  errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
  p.set_content(str(soup),wait_until='domcontentloaded',timeout=80000)
  p.evaluate("""() => {let v={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>v[k]??null,setItem:(k,x)=>v[k]=String(x),removeItem:k=>delete v[k]}})}""")
  p.add_style_tag(content=(r/'web/mobile.css').read_text())
  for f in ('mobile-sources.js','mobile-topics.js','mobile.js'):
   p.add_script_tag(content=(r/'web'/f).read_text())
  p.wait_for_function('window.lawMobile',timeout=45000)
  d=p.evaluate('''() => { const a=document.querySelector('.m-top').getBoundingClientRect(), b=document.querySelector('#frame').getBoundingClientRect(), brand=document.querySelector('.m-brand'), brandrect=brand.getBoundingClientRect(), status=document.querySelector('.m-status').getBoundingClientRect(); return {app: brand.childNodes[0].textContent, version:window.lawMobile.version, headBottom:a.bottom, frameTop:b.top, brandRight:brandrect.right, headerRight:a.right, headerLeft:a.left, statusLeft:status.left, docWidth:document.documentElement.scrollWidth, width:innerWidth};}''')
  good=d['app']=='חוק הגנת הצרכן, התשמ"א–1981' and d['version']=='1.3.3' and d['headBottom']<=d['frameTop']+1 and d['headerRight']<=width+1 and d['headerLeft']>=-1 and not errors
  print(width,'PASS' if good else 'FAIL',d,'errors',errors[:3],flush=True)
  assert good
  out.append({'width':width,'metrics':d,'passed':good,'errors':errors})
  if width==375:p.screenshot(path='/mnt/data/Consumer_Law_Reader_1.3.3_Beta_Real_Viewport.png',full_page=False)
  p.close()
 browser.close()
Path('/mnt/data/Consumer_Law_Reader_1.3.3_Beta_Runtime_QA.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
