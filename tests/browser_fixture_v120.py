"""Browser-level functional smoke suite using in-memory HTML fixture.
Not a full legal document, not a physical device or APK verification.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import json, traceback
ROOT=Path(__file__).resolve().parents[1]
SHELL=(ROOT/'web/mobile-shell.html').read_text()
FIXTURE='''<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"></head><body>
<main id="frame"><h1 id="law_name">חוק הגנת הצרכן</h1><div id="index"><div id="index_title">מפתח</div><div id="index_content"><table><tr><td class="article_link"><a href="#article_2">סעיף 2</a></td></tr></table></div></div>
<table id="article_2" class="article"><tbody><tr><td class="side_title">הטעיה</td><td class="article_number">2.</td><td>האיסור על הטעיה בפרסומת ועל מסירת מידע מטעה לצרכן.</td></tr></tbody></table>
<table id="article_3" class="article"><tbody><tr><td class="side_title">ביטול</td><td class="article_number">3.</td><td>ביטול עסקה מותר בתנאים שנקבעו.</td></tr></tbody></table>
<nav id="navigator"><ul><li><a href="#article_2">הטעיה</a></li><li class="nav_list_title" id="topic_cancel_title">ביטול עסקה</li><ul class="nav_list"><li><a href="#article_3">זכות ביטול</a></li></ul></ul></nav></main><footer>מסמך בדיקה סינתטי בלבד.</footer>
'''+SHELL+'''</body></html>'''
results=[]
def check(name,fn):
 try:
  result=fn(); print('PASS',name,str(result)[:100],flush=True);results.append({'name':name,'status':'PASS','result':str(result)[:180]})
 except Exception as e:
  print('FAIL',name,str(e)[:220],flush=True);results.append({'name':name,'status':'FAIL','error':str(e)[:500]})
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width in [320,375,430]:
  page=browser.new_page(viewport={'width':width,'height':760},locale='he-IL')
  errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  page.set_content(FIXTURE,timeout=15000)
  page.evaluate('''() => {const mem={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>Object.prototype.hasOwnProperty.call(mem,k)?mem[k]:null,setItem:(k,v)=>mem[k]=String(v),removeItem:k=>delete mem[k]}})}''')
  page.add_style_tag(content=(ROOT/'web/mobile.css').read_text())
  page.add_script_tag(content=(ROOT/'web/mobile-sources.js').read_text())
  page.add_script_tag(content=(ROOT/'web/mobile-topics.js').read_text())
  page.add_script_tag(content=(ROOT/'web/mobile.js').read_text())
  check(f'init_{width}',lambda:page.evaluate('window.lawMobile.version'))
  check(f'topics_{width}',lambda:(page.locator('[data-mobile=navigate]').click(timeout=3000),page.locator('.m-topic').count()))
  if width==375:
   check('create_topic',lambda:(page.get_by_role('button',name='+ נושא חדש').click(),page.get_by_role('textbox',name='שם נושא חדש').fill('לימוד מבחן'),page.get_by_role('button',name='יצירת נושא').click(),page.get_by_text('לימוד מבחן').count()))
   check('add_to_topic',lambda:(page.locator('#mobile-sheet-close').click(),page.locator('#article_2 .m-article-actions').click(),page.get_by_role('button',name='הוסף לניווט לפי נושא').click(),page.locator('.m-topic-select').select_option(label='לימוד מבחן'),page.get_by_role('button',name='הוסף קישור').click(),page.evaluate("JSON.parse(localStorage.getItem('law-reader-topics-v1')).links.length")))
   check('search_return',lambda:(page.locator('[data-mobile=search]').click(),page.locator('#mobile-search').fill('הטעיה'),page.wait_for_timeout(280),page.locator('.m-result').first.click(),page.locator('#mobile-return').click(),page.locator('#mobile-search').input_value()))
   check('align_store',lambda:(page.locator('#mobile-sheet-close').click(),page.locator('[data-mobile=more]').click(),page.get_by_role('button',name='יישור לשני הצדדים').click(),page.evaluate("[document.documentElement.classList.contains('m-justify'),localStorage.getItem('law-reader-align')]")))
   check('font_css',lambda:page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--reading-size').trim()"))
  check(f'no_overflow_{width}',lambda:page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
  check(f'errors_{width}',lambda:errors)
  page.close()
 browser.close()
(ROOT/'evidence/browser-fixture-v1.2.0.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print('FAIL_COUNT',sum(r['status']=='FAIL' for r in results))
