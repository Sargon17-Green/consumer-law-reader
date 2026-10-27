#!/usr/bin/env python3
"""Regression on actual full document: heading table CELLS + justified prose at mobile widths.
Uses Chromium, not Android WebView or a physical device.
"""
import json,time
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
root=Path(__file__).resolve().parents[1]
allchecks=[]
def check(label,valid,actual):
 allchecks.append({'test':label,'pass':bool(valid),'value':actual}); print(('PASS' if valid else 'FAIL'),label,str(actual)[:130],flush=True)
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-background-networking'])
 page=browser.new_page(viewport={'width':375,'height':850},device_scale_factor=1)
 page.set_default_timeout(7000)
 errs=[];page.on('pageerror',lambda e:errs.append(str(e)))
 soup=BeautifulSoup((root/'dist/index.html').read_text(),'lxml')
 for el in soup.find_all('script'):el.decompose()
 if soup.body:soup.body.attrs.pop('onload',None)
 for el in soup.find_all('iframe'):el.decompose()
 for el in soup.find_all('link',rel='stylesheet'):el.decompose()
 page.set_content(str(soup),wait_until='domcontentloaded',timeout=35000)
 page.evaluate("""() => {const v={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>v[k]??null,setItem:(k,x)=>v[k]=String(x),removeItem:k=>delete v[k]}})}""")
 page.add_style_tag(content=(root/'web/mobile.css').read_text())
 for fname in ('mobile-sources.js','mobile-topics.js','mobile.js'):page.add_script_tag(content=(root/'web'/fname).read_text())
 page.wait_for_function("window.lawMobile&&window.lawMobile.version==='1.2.3'",timeout=20000)
 for width in (320,375,430,600):
  page.set_viewport_size({'width':width,'height':850})
  d=page.evaluate("""() => {
    const q=s=>document.querySelector(s), val=e=>e?getComputedStyle(e).textAlign:null,
       chapter=q('table.chapter_title td.title'), sub=q('table.subchapter_title td.title'),
       appendix=q('table.appendix_title th'), delegated=q('h1.delegated_legislation_title'),
       prose=q('#article_4a_detail_1 td:last-child')||q('#article_4a tr.detail td:last-child'),
       para=q('.delegated_legislation p.opening'),side=q('#article_4a .side_title');
    return {width:innerWidth,docWidth:document.documentElement.scrollWidth,
      mode:document.documentElement.dataset.lawAlign,chapter:val(chapter),
      sub:val(sub),appendix:val(appendix),delegated:val(delegated),
      prose:val(prose),opening:val(para),side:val(side),
      chapterWidth:chapter?.getBoundingClientRect().width,
      oldCssFallbackPresent:[...document.styleSheets].filter(x=>{try{return [...x.cssRules].some(r=>r.conditionText?.includes('479px')&&r.cssText?.includes('text-align:right'))}catch{return false}}).length}
    }""")
  check(f'center_chapter_cell_{width}',d['chapter']=='center',d['chapter'])
  check(f'center_subchapter_cell_{width}',d['sub']=='center',d['sub'])
  check(f'center_appendix_cell_{width}',d['appendix']=='center',d['appendix'])
  check(f'center_regulation_title_{width}',d['delegated']=='center',d['delegated'])
  check(f'justify_article_prose_{width}',d['prose']=='justify',d['prose'])
  check(f'justify_regulation_opening_{width}',d['opening']=='justify',d['opening'])
  check(f'no_overflow_{width}',d['docWidth']<=width,d['docWidth'])
  check(f'side_title_not_centered_{width}',d['side']=='right',d['side'])
  check(f'justify_default_{width}',d['mode']=='justify',d['mode'])
  if width==375:
   page.locator('#chapter_a_title').scroll_into_view_if_needed(timeout=5000)
   page.screenshot(path='/mnt/data/Consumer_Law_Mobile_1.2.3_Chapter_Proof.png')
  if width==430:
   page.locator('#article_4a').scroll_into_view_if_needed(timeout=5000)
   page.screenshot(path='/mnt/data/Consumer_Law_Mobile_1.2.3_Justification_Proof.png')
 # Manual preference right still functional, then justify
 page.evaluate("document.documentElement.dataset.lawAlign='right';document.documentElement.classList.remove('m-justify')")
 check('right_alignment_is_optional',page.evaluate("getComputedStyle(document.querySelector('#article_4a_detail_1 td:last-child')).textAlign")=='right','right')
 page.evaluate("document.documentElement.dataset.lawAlign='justify';document.documentElement.classList.add('m-justify')")
 check('justify_can_be_restored',page.evaluate("getComputedStyle(document.querySelector('#article_4a_detail_1 td:last-child')).textAlign")=='justify','justify')
 check('runtime_errors_none',len(errs)==0,errs[:4])
 browser.close()
(root/'evidence/browser-regression-v1.2.3.json').write_text(json.dumps({'checks':allchecks,'passed':sum(x['pass'] for x in allchecks),'failed':sum(not x['pass'] for x in allchecks),'physical_device':False},ensure_ascii=False,indent=2))
print('RESULT',sum(x['pass'] for x in allchecks),'/',len(allchecks),flush=True)
raise SystemExit(1 if any(not x['pass'] for x in allchecks) else 0)
