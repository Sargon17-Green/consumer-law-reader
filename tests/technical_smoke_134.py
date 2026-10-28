"""Browser integration tests of legal-text-only search and clean UI."""
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import shutil
ROOT=Path(__file__).resolve().parents[1]
doc=BeautifulSoup((ROOT/'dist/index.html').read_text(encoding='utf-8'),'lxml')
notes_script=doc.select_one('script#notes_script')
assert notes_script is not None and 'function note_reveal' in notes_script.get_text()
notes_js=notes_script.get_text()
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
        # Execute the original legal document's note handler, not a test-only mock.
        page.add_script_tag(content=notes_js)
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
        # A navigation highlight lasts until a *completed click* inside the
        # document. Pointerdown, text selection, dragging, and touch scroll
        # are not sufficient to clear it.
        highlight=page.evaluate("""() => {
            const article=document.querySelector('#frame table.article[id]');
            const frame=document.querySelector('#frame');
            const link=document.createElement('a');
            link.textContent='QA internal navigation';
            link.href='#'+article.id;
            frame.append(link);
            const check=(condition,label)=>{if(!condition)throw Error('highlight QA: '+label);};
            const pointer=(kind,el,x,y,id=91)=>el.dispatchEvent(new PointerEvent(kind,{
              bubbles:true,cancelable:true,pointerId:id,pointerType:'touch',
              isPrimary:true,clientX:x,clientY:y
            }));
            const click=(el,detail=1)=>el.dispatchEvent(new MouseEvent('click',{
              bubbles:true,cancelable:true,detail
            }));
            const highlighted=()=>article.classList.contains('m-target');
            window.lawMobile.goTo(article,false,true);
            check(highlighted(),'navigation start');
            // A plain press may precede either a click or a scroll.
            pointer('pointerdown',frame,20,20);
            check(highlighted(),'pointerdown did not clear');
            pointer('pointermove',frame,20,72);
            pointer('pointerup',frame,20,72);
            click(frame);
            check(highlighted(),'dragged pointer left highlight intact');
            // Touch scrolling may cancel the pointer sequence.
            pointer('pointerdown',frame,20,20);
            pointer('pointercancel',frame,20,45);
            click(frame);
            check(highlighted(),'touch cancel left highlight intact');
            // Clicking other controls, outside the document, must not clear it.
            pointer('pointerdown',document.body,20,20);
            click(document.body);
            check(highlighted(),'outside click left highlight intact');
            // A true tap elsewhere in the document clears it.
            pointer('pointerdown',frame,20,20);
            pointer('pointerup',frame,21,21);
            click(frame);
            check(!highlighted(),'real document tap cleared target');
            // Activating a document link creates a fresh target/link highlight.
            pointer('pointerdown',link,20,20);
            pointer('pointerup',link,20,20);
            click(link);
            check(highlighted(),'link navigated to new target');
            check(link.classList.contains('m-link-pressed'),'link received pressed highlight');
            pointer('pointerdown',link,20,20);
            pointer('pointermove',link,50,75);
            pointer('pointerup',link,50,75);
            click(link);
            check(highlighted()&&link.classList.contains('m-link-pressed'),
                  'drag on link did not clear or reactivate');
            // A real click on another place clears both types of highlight.
            pointer('pointerdown',frame,20,20);
            pointer('pointerup',frame,20,20);
            click(frame);
            check(!highlighted()&&!link.classList.contains('m-link-pressed'),
                  'document click cleared target and source link');
            // A fresh click still clears highlights even if previously selected
            // text has not yet been collapsed by the browser.
            window.lawMobile.goTo(article,false,true);
            const selection=window.getSelection(),range=document.createRange();
            range.selectNodeContents(link);selection.removeAllRanges();selection.addRange(range);
            pointer('pointerdown',frame,20,20);
            pointer('pointerup',frame,20,20);
            click(frame);
            check(!highlighted(),'real click clears despite stale text selection');
            selection.removeAllRanges();
            // Keyboard-initiated click is also an intentional activation.
            window.lawMobile.goTo(article,false,true);
            click(frame,0);
            check(!highlighted(),'keyboard click cleared target');
            link.remove();
            return {drag:true,cancel:true,documentClick:true,link:true,keyboard:true};
        }""")
        assert all(highlight.values()),highlight
        # Both newly added editor notes must open and close, including when the
        # reader taps the body of an already open note. The latter previously
        # bubbled to the outer UL and toggled twice, leaving the note open.
        for section_id, note_id in (
            ('article_16c_subsection_c', 'article_16c_subsection_c_checks_unavailable_note'),
            ('A_database_for_limiting_marketing_inquiries_article_3_subsection_a',
             'marketing_registry_reg_3a_checks_unavailable_note'),
        ):
            page.evaluate('(id) => window.lawMobile.goTo(id, false, false)', section_id)
            wrapper=page.locator('#'+note_id)
            inner=wrapper.locator(':scope > .note_div')
            assert wrapper.count()==1 and inner.count()==1, note_id
            assert inner.evaluate('(e) => getComputedStyle(e).display')=='none', note_id
            wrapper.evaluate("(e) => e.dispatchEvent(new MouseEvent('click',{bubbles:true}))")
            assert inner.evaluate('(e) => getComputedStyle(e).display')=='block', note_id
            # Use a real Chromium click to check the bubbling regression.
            inner.click(timeout=15000)
            assert inner.evaluate('(e) => getComputedStyle(e).display')=='none', note_id
            wrapper.evaluate("(e) => e.dispatchEvent(new MouseEvent('click',{bubbles:true}))")
            assert inner.evaluate('(e) => getComputedStyle(e).display')=='block', note_id
            wrapper.evaluate("(e) => e.dispatchEvent(new MouseEvent('click',{bubbles:true}))")
            assert inner.evaluate('(e) => getComputedStyle(e).display')=='none', note_id
        # The exact editor text may be visible in a note, but must never
        # be indexed as legal prose by the statutory search.
        assert all('מיום ז׳ בתשרי התשפ״ה' not in rec.text
                   for rec in page.evaluate('window.lawMobile.buildSearch().map(r => ({text:r.text}))'))
        page.evaluate('window.lawMobile.showSearch()')
        assert page.locator('#mobile-search').count()==1
        assert page.locator('text=חיפוש במקורות מוקלדים').count()==0
        assert page.locator('select[aria-label="תחום חיפוש"] option').count()==3
        # The original index remains in the DOM as data for the fixed bottom TOC,
        # but is no longer a duplicate visible list in the reading surface.
        assert page.locator('#index').count()==1
        assert page.evaluate("""() => getComputedStyle(document.querySelector('#frame #index')).display""")=='none'
        assert page.locator('[data-mobile="toc"]').count()==1
        page.locator('#mobile-sheet-close').click()
        page.locator('[data-mobile="toc"]').click()
        assert page.locator('.m-toc-link').count()>50
        assert not errors,errors
        print('PASS',width,data['count'])
        page.close()
    browser.close()
