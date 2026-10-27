from playwright.sync_api import sync_playwright
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
import threading,json,os,traceback,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]/'dist'
server=ThreadingHTTPServer(('127.0.0.1',0),partial(SimpleHTTPRequestHandler,directory=str(root)))
threading.Thread(target=server.serve_forever,daemon=True).start()
url=f'http://127.0.0.1:{server.server_port}/index.html'
report=[]
def check(name, f):
 try:r=f();report.append({'test':name,'status':'PASS','detail':r});print('PASS',name,str(r)[:100])
 except Exception as e:report.append({'test':name,'status':'FAIL','error':str(e)});print('FAIL',name,str(e)[:180]);traceback.print_exc(limit=2)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
 for width in [320,375,430]:
  context=browser.new_context(viewport={'width':width,'height':780},locale='he-IL',service_workers='block')
  page=context.new_page();errors=[];page.on('pageerror',lambda e: errors.append(str(e)))
  check(f'load_{width}',lambda: (page.goto(url,wait_until='domcontentloaded',timeout=45000),page.wait_for_function('window.lawMobile && window.LawTopics',timeout=25000),page.locator('#mobile-header').is_visible()))
  check(f'no_horizontal_overflow_{width}',lambda:page.evaluate('({overflow:document.documentElement.scrollWidth>innerWidth,scroll:document.documentElement.scrollWidth,width:innerWidth})'))
  check(f'topics_open_{width}',lambda:(page.get_by_role('button',name='ניווט לפי נושא').click(),page.locator('.m-topic').count()))
  if width==375:
   check('topics_rename_and_create',lambda:(page.get_by_role('button',name='+ נושא חדש').click(),page.get_by_role('textbox',name='שם נושא חדש').fill('לימוד מבחן'),page.get_by_role('button',name='יצירת נושא').click(),page.get_by_text('לימוד מבחן').count()))
   check('topics_persist_reload',lambda:(page.reload(wait_until='domcontentloaded',timeout=45000),page.wait_for_function('window.lawMobile && window.LawTopics',timeout=25000),page.locator('[data-mobile=navigate]').click(),page.get_by_text('לימוד מבחן').count()))
   check('add_article_to_topic',lambda:(page.locator('#mobile-sheet-close').click(),page.locator('#article_2 .m-article-actions').first.click(),page.get_by_role('button',name='הוסף לניווט לפי נושא').click(),page.locator('.m-topic-select').select_option(label='לימוד מבחן'),page.get_by_role('button',name='הוסף קישור').click(),page.evaluate("JSON.parse(localStorage.getItem('law-reader-topics-v1')).links.length")))
   check('search_return',lambda:(page.locator('[data-mobile=search]').click(),page.locator('#mobile-search').fill('הטעיה'),page.wait_for_timeout(600),page.locator('.m-result').first.click(),page.locator('#mobile-return').click(),page.locator('#mobile-search').input_value()))
   check('alignment_saved',lambda:(page.locator('#mobile-sheet-close').click(),page.locator('[data-mobile=more]').click(),page.get_by_role('button',name='יישור לשני הצדדים').click(),page.evaluate("[document.documentElement.classList.contains('m-justify'),localStorage.getItem('law-reader-align')]")))
   check('font_default',lambda:page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--reading-size').trim()"))
  check(f'pageerrors_{width}',lambda:errors)
  context.close()
 browser.close()
server.shutdown()
Path('/mnt/data/consumer_mobile_work/evidence/browser-v1.2.0.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print('FAILURES',sum(x['status']=='FAIL' for x in report))
