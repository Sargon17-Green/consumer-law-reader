#!/usr/bin/env python3
"""Full legal source Chromium regression, without replacing or rewriting law text."""
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import json
root=Path(__file__).resolve().parents[1]
checks=[]

def ck(k,v,actual):
 checks.append(dict(name=k,passed=bool(v),actual=actual));print(('PASS' if v else 'FAIL'),k,str(actual)[:135],flush=True)

with sync_playwright() as p:
 browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-background-networking'])
 page=browser.new_page(viewport={'width':375,'height':850},device_scale_factor=1)
 errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 soup=BeautifulSoup((root/'dist/index.html').read_text(encoding='utf8'),'lxml')
 for e in soup.find_all('script'):e.decompose()
 if soup.body: soup.body.attrs.pop('onload',None)
 for e in soup.find_all('iframe'):e.decompose()
 for e in soup.find_all('link',rel='stylesheet'):e.decompose()
 page.set_content(str(soup),wait_until='domcontentloaded',timeout=60000)
 page.evaluate("""() => {let v={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>v[k]??null,setItem:(k,x)=>v[k]=String(x),removeItem:k=>delete v[k]}})}""")
 page.add_style_tag(content=(root/'web/mobile.css').read_text(encoding='utf-8'))
 for f in ['mobile-sources.js','mobile-topics.js','mobile.js']:page.add_script_tag(content=(root/'web'/f).read_text(encoding='utf-8'))
 page.wait_for_function("window.lawMobile?.version==='1.2.4'",timeout=25000)
 for w in [320,375,430,600]:
  page.set_viewport_size({'width':w,'height':850})
  r=page.evaluate("""() => {
   const q=s=>document.querySelector(s),v=s=>getComputedStyle(q(s)).textAlign;
   const t=q('#law_name td.title').getBoundingClientRect();
   const f=q('#frame').getBoundingClientRect();
   return {head:v('#law_name td.title'),chapter:v('#chapter_a_title td.title'),
     prose:v('#article_4a_detail_1 td:last-child'),side:v('#article_4a .side_title'),
     align:document.documentElement.dataset.lawAlign,overflow:document.documentElement.scrollWidth-innerWidth,
     headCenter:t.left+t.width/2,frameCenter:f.left+f.width/2,headWidth:t.width,
     headingText:q('#law_name td.title').textContent.trim()};
  }""")
  ck('title_center_css_'+str(w),r['head']=='center',r['head'])
  ck('title_physical_center_'+str(w),abs(r['headCenter']-r['frameCenter'])<3,r)
  ck('chapter_still_center_'+str(w),r['chapter']=='center',r['chapter'])
  ck('article_still_justified_'+str(w),r['prose']=='justify',r['prose'])
  ck('side_title_still_right_'+str(w),r['side']=='right',r['side'])
  ck('user_default_justify_'+str(w),r['align']=='justify',r['align'])
  ck('no_overflow_'+str(w),r['overflow']<=0,r['overflow'])
  if w==375:
   page.locator('#law_name').scroll_into_view_if_needed(timeout=10000)
   page.screenshot(path='/mnt/data/Consumer_Law_Mobile_1.2.4_Law_Title_Proof.png')
 page.set_viewport_size({'width':375,'height':850})
 selector='#article_1_definition_2-article_22a'
 ck('source_link_exists',page.locator(selector).count()==1,selector)
 page.locator(selector).click(timeout=12000)
 data=page.evaluate("""(s)=>{const a=document.querySelector(s),c=getComputedStyle(a);return {active:a.classList.contains('m-link-pressed'),background:c.backgroundColor,white:c.whiteSpace,display:c.display,scroll:scrollY,hash:location.hash}}""",selector)
 ck('clicked_link_is_visibly_colored',data['active'] and data['background'] not in ['transparent','rgba(0, 0, 0, 0)'],data)
 ck('link_remains_inline',data['display']=='inline' and data['white']=='normal',data)
 ck('navigation_updates_hash',data['hash'].startswith('#article_22a'),data['hash'])
 # Click empty document area: pointerdown is the touch-start path used by Android WebView.
 page.evaluate("""() => document.querySelector('#law_name').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerType:'touch'}))""")
 ck('tap_elsewhere_removes_link_background',not page.locator(selector).evaluate("e=>e.classList.contains('m-link-pressed')"),'link class after tapping title')
 # Repeat navigation: Browser Back should clear background but leave a text-only marker.
 page.locator(selector).click(timeout=12000)
 ck('reclick_restores_background',page.locator(selector).evaluate("e=>e.classList.contains('m-link-pressed')"),True)
 page.go_back(wait_until='domcontentloaded',timeout=16000)
 page.wait_for_timeout(150)
 d=page.evaluate("""(s)=>{let a=document.querySelector(s);return {pressed:a.classList.contains('m-link-pressed'),returnMarker:a.classList.contains('m-link-return'),bg:getComputedStyle(a).backgroundColor,targetCount:document.querySelectorAll('#frame .m-target').length}}""",selector)
 ck('back_clears_link_background',not d['pressed'] and d['bg'] in ['rgba(0, 0, 0, 0)','transparent'],d)
 ck('back_keeps_text_only_emphasis',d['returnMarker'],d)
 # Next generic touch clears return marker too.
 page.evaluate("""() => document.querySelector('#law_name').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerType:'touch'}))""")
 ck('next_tap_clears_return_emphasis',not page.locator(selector).evaluate("e=>e.classList.contains('m-link-return')"),True)
 # Inline definition behaves like a link on actual document, modal can be closed by tap.
 definition='#frame .defined:has(> .the_definition)'
 if page.locator(definition).count():
  e=page.locator(definition).first
  e.click(timeout=12000)
  ck('definition_activates_highlight',e.evaluate("e=>e.classList.contains('m-link-pressed')"),True)
  page.evaluate("""() => document.querySelector('#law_name').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}))""")
  ck('definition_highlight_clears',not e.evaluate("e=>e.classList.contains('m-link-pressed')"),True)
  page.evaluate("document.querySelector('#mobile-sheet').close()")
 ck('no_js_page_errors',not errors,errors[:3])
 browser.close()
(root/'evidence/browser-regression-v1.2.4.json').write_text(json.dumps({'checks':checks,'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'on_physical_android':False},ensure_ascii=False,indent=2))
print('RESULT',sum(x['passed'] for x in checks),'/',len(checks),flush=True)
raise SystemExit(1 if any(not x['passed'] for x in checks) else 0)
