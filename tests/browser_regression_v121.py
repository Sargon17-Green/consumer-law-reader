"""Bounded synthetic browser regressions for the 1.2.1 mobile fixes.
Not a physical Android test, and not full-document QA.
"""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
SHELL=(ROOT/'web/mobile-shell.html').read_text()
HTML='''<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head><body>
<main id="frame"><h1 id="law_name">חוק הגנת הצרכן</h1><div id="index"><div id="index_title">מפתח</div><div id="index_content"><table><tr><td class="article_link"><a href="#article_2">סעיף 2</a></td></tr></table></div></div>
<table id="article_2" class="article"><tbody><tr><td class="side_title">הטעיה</td><td class="article_number">2.</td><td><table class="content"><tr class="subsection" id="article_2_a"><td class="numbering">(א)</td><td>בטקסט המשפטי יש <span class="defined">הגדרה בעלת מילים רבות<span class="the_definition">הסבר משפטי</span></span> וגם <a href="#article_3">הפניה ארוכה לסעיף אחר</a>. אין להצמיד את הטקסט לשורה אחת.
<div class="done_accordingly">לעניין פסקה זו נקבעו תקנות:<ul><li id="li_test_reg"><span class="name" onclick="reveal('test_reg')">תקנות הגנת הצרכן (בדיקה)</span>
<div id="test_reg" class="delegated_legislation" style="display:none"><h1 class="delegated_legislation_title">תקנות בדיקה</h1>
<table id="test_reg_article_1" class="article"><tbody><tr><td class="side_title">חובת גילוי</td><td class="article_number">1.</td><td>
<table class="content"><tr class="subsection" id="test_reg_article_1_a"><td class="numbering">(א)</td><td>עוסק יקיים את חובות הגילוי כאמור <a href="#article_2_a">בסעיף משנה (א)</a>, לפי העניין באמצעים המפורטים להלן לפחות:
<table><tr class="detail" id="test_reg_article_1_a_1"><td class="numbering">(1)</td><td>הצבת שלט בבית העסק לפי הוראות אלה: המילים נדרשות להופיע ברצף רגיל ומסודר.</td></tr></table>
</td></tr></table></td></tr></tbody></table></div></li></ul></div></td></tr></table></td></tr></tbody></table>
<table id="article_3" class="article"><tbody><tr><td class="side_title">ביטול</td><td class="article_number">3.</td><td>ביטול עסקה מותר בתנאים שנקבעו.</td></tr></tbody></table>
<nav id="navigator"><ul><li><a href="#article_2">הטעיה</a></li><li class="nav_list_title" id="topic_cancel_title">ביטול עסקה</li><ul class="nav_list"><li><a href="#article_3">זכות ביטול</a></li></ul></ul></nav></main>
<footer>מסמך בדיקה סינתטי בלבד</footer>
<div class="history_box" id="history_box_article_2">נוסח קודם מסמך בדיקה</div>
'''+SHELL+'''</body></html>'''
checks=[]
def check(key,ok,details=''):
 checks.append({'name':key,'passed':bool(ok),'details':str(details)[:160]});print(('PASS' if ok else 'FAIL'),key,details,flush=True)
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 for w in [320,375,430]:
  pg=b.new_page(viewport={'width':w,'height':780},device_scale_factor=1)
  errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
  pg.set_content(HTML,timeout=20000)
  pg.evaluate('''() => {const store={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>Object.hasOwn(store,k)?store[k]:null,setItem:(k,v)=>store[k]=String(v),removeItem:k=>delete store[k]}})}''')
  pg.add_style_tag(content=(ROOT/'web/mobile.css').read_text())
  for name in ('mobile-sources.js','mobile-topics.js','mobile.js'):pg.add_script_tag(content=(ROOT/'web'/name).read_text())
  initial=pg.evaluate('''() => ({v:window.lawMobile?.version,buttons:document.querySelectorAll('.m-bottom [data-mobile]').length,local:document.querySelectorAll('.m-article-actions,.m-source-tools').length,justify:document.documentElement.classList.contains('m-justify'),width:document.documentElement.scrollWidth,screen:innerWidth,link:getComputedStyle(document.querySelector('#article_2 .defined')).display,whiteSpace:getComputedStyle(document.querySelector('#article_2 .defined')).whiteSpace})''')
  check(f'load_{w}',initial['v']=='1.2.1' and initial['buttons']==4,initial)
  check(f'no_local_actions_{w}',initial['local']==0)
  check(f'justify_default_{w}',initial['justify'])
  check(f'inline_wrap_{w}',initial['link']=='inline' and initial['whiteSpace']=='normal')
  check(f'no_horizontal_scroll_{w}',initial['width']<=initial['screen'],(initial['width'],initial['screen']))
  pg.locator('#article_2').scroll_into_view_if_needed()
  pg.locator('[data-mobile=actions]').click()
  check(f'global_local_history_{w}',pg.get_by_role('button',name='היסטוריית נוסחים').count()==1,pg.locator('#mobile-sheet-title').inner_text())
  pg.locator('#mobile-sheet-close').click()
  pg.locator('#li_test_reg > .name').click()
  overlay=pg.locator('#test_reg')
  if w==375:pg.screenshot(path='/mnt/data/regulation_reader_121_fixture.png')
  data=overlay.evaluate('''e=>{const r=e.getBoundingClientRect();const td=e.querySelector('#test_reg_article_1_a_1 > td:last-child').getBoundingClientRect();return {open:e.classList.contains('m-regulation-open'),width:r.width,left:r.left,cell:td.width,back:!document.querySelector('#mobile-regulation-back').hidden}}''')
  check(f'regulation_full_width_{w}',data['open'] and data['back'] and data['width']>=w-2 and data['cell']>=w*.40,data)
  pg.locator('#mobile-regulation-back').click()
  check(f'regulation_close_{w}',not overlay.evaluate('e=>e.classList.contains("m-regulation-open")'))
  check(f'no_js_errors_{w}',not errors,errors[:2])
  pg.close()
 b.close()
out=ROOT/'evidence/browser-regression-v1.2.1.json'
out.write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print('TOTAL',len(checks),'PASSED',sum(x['passed'] for x in checks),'FAILED',sum(not x['passed'] for x in checks))
raise SystemExit(1 if any(not x['passed'] for x in checks) else 0)
