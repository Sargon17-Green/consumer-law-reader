"""Browser integration tests of legal-text-only search and clean UI."""
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import shutil
ROOT=Path(__file__).resolve().parents[1]
doc=BeautifulSoup((ROOT/'dist/index.html').read_text(encoding='utf-8'),'lxml')
for script in doc.find_all('script'):
    if script.get('id')!='law-editorial-status':script.decompose()
for link in doc.find_all('link',rel='stylesheet'):link.decompose()
if doc.body:doc.body.attrs.pop('onload',None)
with sync_playwright() as pw:
    kwargs={'args':['--no-sandbox','--disable-dev-shm-usage']}
    if shutil.which('chromium'): kwargs['executable_path']=shutil.which('chromium')
    browser=pw.chromium.launch(**kwargs)
    for width in (320,375,430,1280):
        page=browser.new_page(viewport={'width':width,'height':850})
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content(str(doc),timeout=120000)
        page.evaluate("""() => {
          let memory={};
          Object.defineProperty(window,'localStorage',{configurable:true,value:{
            getItem:k=>memory[k]??null,setItem:(k,v)=>memory[k]=String(v),removeItem:k=>delete memory[k]}})
        }""")
        page.add_style_tag(content=(ROOT/'web/mobile.css').read_text())
        for name in ('mobile-sources.js','mobile-topics.js','mobile.js'):
            page.add_script_tag(content=(ROOT/'web'/name).read_text())
        page.wait_for_function('window.lawMobile',timeout=80000)
        data=page.evaluate("""() => {
            let article=document.querySelector('#frame table.article[id]');
            let note=document.createElement('span');note.className='note_div';note.textContent='EDITOR_SENTINEL';article.append(note);
            let popup=document.createElement('span');popup.className='the_definition';popup.textContent='POPUP_SENTINEL';article.append(popup);
            let link=document.createElement('a');link.href='#article_2';link.textContent='LEGAL_LINK_SENTINEL';article.append(link);
            let entry=window.lawMobile.buildSearch().find(r=>r.el===article);
            return {text:entry.text,count:window.lawMobile.buildSearch().length,date:document.querySelector('.m-subtitle').textContent,status:!!document.querySelector('#mobile-status')};
        }""")
        assert 'EDITOR_SENTINEL' not in data['text']
        assert 'POPUP_SENTINEL' not in data['text']
        assert 'LEGAL_LINK_SENTINEL' in data['text']
        assert data['date']=='נוסח נבדק: 28.10.2026'
        assert not data['status']
        assert data['count']>500
        page.evaluate('window.lawMobile.showSearch()')
        assert page.locator('#mobile-search').count()==1
        assert page.locator('text=חיפוש במקורות מוקלדים').count()==0
        assert page.locator('select[aria-label="תחום חיפוש"] option').count()==3
        assert not errors,errors
        print('PASS',width,data['count'])
        page.close()
    browser.close()
