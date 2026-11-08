"""Run the complete packaged DOM and its real scripts, not a stripped fixture."""
from pathlib import Path
from urllib.parse import urlparse,unquote
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
import hashlib,json,mimetypes,shutil,time,os
ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'evidence';EVIDENCE.mkdir(exist_ok=True)
SOURCE=ROOT/'original/Consumer_Protection_Law.html'
EXPECTED='de5240a877dd3830ec9ac80f8bc60bf001882b6e36e8615b991d7defcd8e2ed9'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==EXPECTED

def serve(route):
    url=urlparse(route.request.url)
    if url.hostname!='law.local':
        route.abort('internetdisconnected');return
    path=ROOT/'dist'/unquote(url.path.lstrip('/') or 'index.html')
    assert path.resolve().is_relative_to((ROOT/'dist').resolve())
    if path.is_file():route.fulfill(status=200,body=path.read_bytes(),content_type=mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
    else:route.fulfill(status=404,body='missing')

dimensions=[(320,740),(430,932),(768,1024),(1180,820)]
if os.environ.get('LAW_QA_WIDTH'):
    requested=os.environ['LAW_QA_WIDTH']
    if requested not in {str(width) for width,_ in dimensions}:
        raise ValueError('Unknown QA viewport: '+requested)
    dimensions=[size for size in dimensions if str(size[0])==requested]

report=[]
axe_source=(ROOT/'tests/qa/node_modules/axe-core/axe.min.js').read_text()
accessibility=[]
with sync_playwright() as pw:
    options={'args':['--no-sandbox','--disable-dev-shm-usage']}
    if shutil.which('chromium'):options['executable_path']=shutil.which('chromium')
    browser=pw.chromium.launch(**options)
    for width,height in dimensions:
        context=browser.new_context(viewport={'width':width,'height':height},has_touch=width<800,reduced_motion='reduce',service_workers='block')
        context.route('**/*',serve)
        page=context.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        started=time.monotonic();page.goto('https://law.local/index.html',wait_until='load',timeout=90000)
        page.wait_for_function("()=>document.documentElement.dataset.lawReady==='true'",timeout=60000)
        opening=(time.monotonic()-started)*1000
        metrics=page.evaluate("""()=>{
          const start=performance.now(),records=lawMobile.buildSearch(),index=performance.now()-start;
          const timings=[];for(let i=0;i<50;i++){const at=performance.now();records.filter(r=>r.folded.includes(LawCore.normalized(i%2?'עסקה':'14').text));timings.push(performance.now()-at);}
          return {indexMs:index,records:records.length,searchMedianMs:timings.sort((a,b)=>a-b)[25],heap:performance.memory?.usedJSHeapSize};
        }""")
        assert metrics['records']>500
        definition_names=page.locator('#frame .defined').evaluate_all('(els)=>els.map(e=>e.getAttribute("aria-label"))')
        assert len(set(definition_names))>3, 'Screen readers must distinguish definition buttons by their terms'
        assert page.locator('#frame table.m-prose-table').count()>0
        assert page.locator('#frame table.m-prose-table:not([role=presentation])').count()==0, 'Layout tables must expose prose semantics after classification'
        assert page.locator('.m-table-scroll>table[role=presentation]').count()==0, 'Real data tables retain table semantics'
        assert page.evaluate("""()=>lawMobile.buildSearch().every(r=>{const c=r.el.cloneNode(true);for(const e of c.querySelectorAll('.the_definition,.note_button,.note_div,.done_accordingly,.validity,.m-article-actions,.m-source-tools,.sources_box,.bills_box,.protocols_box,.history_box,script,style,noscript'))e.remove();return c.textContent.replace(/\\s+/g,' ').trim()===r.text;})"""), 'Index text must preserve every statutory unit while excluding the documented editorial elements'
        assert page.evaluate("()=>LawCore.snippet('אָב שָׁלוֹם סוף','שלום').mark")=='שָׁלוֹם'
        page.locator('[data-mobile=search]').click();page.locator('#mobile-search').fill('עסקה')
        page.wait_for_function("()=>document.querySelectorAll('.m-result').length>0")
        expected=page.locator('#mobile-search').input_value()
        page.locator('.m-result').first.click()
        assert page.evaluate('location.hash').startswith('#')
        page.locator('#mobile-return').click();assert page.locator('#mobile-search').input_value()==expected
        page.locator('#mobile-sheet-close').click()
        # HTML metacharacters in an input remain text; the search path creates no HTML.
        page.locator('[data-mobile=search]').click();page.locator('#mobile-search').fill('<img src=x onerror=alert(1)>')
        page.wait_for_timeout(250);assert page.locator('#mobile-search-results img').count()==0
        page.locator('#mobile-sheet-close').click()
        # Preview -> restore: stale settings disappear, unrelated keys survive, invalid files fail unchanged.
        backup=page.evaluate("""()=>{
          localStorage.setItem('law-reader-font','24');localStorage.setItem('unrelated','keep');
          const raw=lawSettings.exportJSON();localStorage.setItem('law-reader-align','right');
          if(!lawSettings.prepareImport(raw).ok||!lawSettings.applyImport(raw).ok)throw Error('restore failed');
          if(localStorage.getItem('law-reader-align')!==null||localStorage.getItem('unrelated')!=='keep')throw Error('restore isolation');
          const before=lawSettings.exportJSON();if(lawSettings.prepareImport('{"format":"evil"}').ok)throw Error('unsafe file accepted');
          if(before!==lawSettings.exportJSON())throw Error('validation mutated settings');return raw;
        }""")
        if width==320:
            # Invalid UTF-8 inside an otherwise JSON-like file must be rejected,
            # rather than silently replacing bytes and previewing corrupted data.
            with page.expect_file_chooser() as chooser:
                page.evaluate('lawSettings.importFile()')
            chooser.value.set_files({'name':'corrupt.json','mimeType':'application/json','buffer':b'{"format":"consumer-law-reader-settings","schema":2,"appVersion":"\xff","settings":{}}'})
            page.wait_for_function("()=>document.getElementById('mobile-toast').textContent.includes('UTF-8')")
            assert page.locator('#mobile-confirm-restore').count()==0
            assert page.evaluate('lawSettings.exportJSON()')==backup
            page.locator('#mobile-sheet-close').click()
        before_back=page.evaluate("()=>{lawMobile.goTo('article_2');scrollBy(0,100);const point=scrollY;lawMobile.goTo('article_3');return point}")
        page.go_back()
        page.wait_for_function("point=>location.hash==='#article_2'&&Math.abs(scrollY-point)<3",arg=before_back)
        page.evaluate('lawMobile.goTo("article_14");lawMobile.saveSession()')
        # Malformed fragment fails safely without throwing, and the state survives a real reload.
        page.evaluate("()=>{const a=document.createElement('a');a.href='#%ZZ';document.getElementById('frame').append(a);a.click();a.remove();}")
        page.reload(wait_until='load');page.wait_for_function('()=>window.lawMobile')
        assert page.evaluate("localStorage.getItem('law-reader-font')")=='24'
        assert page.evaluate('location.hash')=='#article_14'
        page.wait_for_timeout(400)
        assert page.evaluate('lawMobile.currentArticle()?.id')=='article_14', 'A font change restores the logical anchor, not pixels from the old layout'
        assert page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--reading-size').trim()")=='24px'
        # Keyboard dialog focus returns to the invoker even after replacing a nested sheet.
        page.locator('[data-mobile=toc]').click();assert page.locator('dialog[open]').count()==1
        page.keyboard.press('Escape');assert page.locator('dialog[open]').count()==0
        assert page.locator('[data-mobile=toc]').evaluate('(e)=>e===document.activeElement')
        # No unsolicited external content or bridging frames can execute.
        frame=page.evaluate("""async()=>{
          window.__frameRan=false;const f=document.createElement('iframe');f.srcdoc='<script>parent.__frameRan=true<'+ '/script>';document.body.append(f);await new Promise(r=>setTimeout(r,100));f.remove();return window.__frameRan;
        }""")
        assert frame is False
        # Long sequence across legislation and back, and stable cached index identity.
        assert page.evaluate("""()=>{const first=lawMobile.buildSearch();for(let i=0;i<120;i++){lawMobile.goTo(first[i%first.length].el,false);if(lawMobile.buildSearch()!==first)return false;}return true;}""")
        page.evaluate('lawMobile.goTo("law_name",false,false)')
        dimensions=page.evaluate("({viewport:innerWidth,width:document.documentElement.scrollWidth})")
        assert dimensions['width']<=dimensions['viewport']+2,dimensions
        # Primary controls have accessible names and platform-sized hit areas.
        for button in page.locator('.m-bottom button').all():
            box=button.bounding_box();assert box and box['height']>=44 and box['width']>=44
            assert button.inner_text().strip()
        assert page.locator('#mobile-sheet').get_attribute('aria-labelledby')=='mobile-sheet-title'
        page.evaluate(axe_source)
        for scenario in ('reading','search','contents','settings','privacy','contrast-dark','contrast-blue','large-text'):
            page.evaluate("document.documentElement.classList.remove('m-contrast-dark','m-contrast-blue')")
            if scenario.startswith('contrast-'):page.evaluate('(name)=>document.documentElement.classList.add(name)','m-'+scenario)
            if scenario=='large-text':
                page.evaluate("document.documentElement.style.setProperty('--reading-size','28px')")
                assert page.evaluate('document.documentElement.scrollWidth<=innerWidth+2'), 'Large reading text must not overflow the viewport'
            if scenario=='search':page.evaluate('lawMobile.showSearch()')
            if scenario=='contents':page.evaluate('lawMobile.showToc()')
            if scenario=='settings':page.evaluate('lawMobile.showMore()')
            if scenario=='privacy':
                page.evaluate('lawMobile.showMore()')
                page.get_by_role('button',name='מדיניות פרטיות ותקשורת',exact=True).click()
                assert page.locator('#mobile-sheet-body').inner_text().count('JSON')>=2
            scan=page.evaluate("async()=>await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21aa','wcag22aa']}})")
            accessibility.append({'viewport':[width,height],'scenario':scenario,'violations':scan['violations'],'incomplete':scan['incomplete'],'passes':len(scan['passes'])})
            (EVIDENCE/'accessibility-axe-report.json').write_text(json.dumps(accessibility,ensure_ascii=False,indent=2))
            print('Accessibility',width,scenario,'violations',len(scan['violations']),flush=True)
            assert not scan['violations'],[(v['id'],[n['target']for n in v['nodes'][:4]])for v in scan['violations']]
            if page.locator('#mobile-sheet[open]').count():page.locator('#mobile-sheet-close').click()
        if width==430:page.screenshot(path=str(EVIDENCE/'reader-430.png'))
        assert not errors,errors
        report.append({'browser':browser.version,'environment':'Linux headless Chromium; full bundled DOM; remote resources aborted','viewport':[width,height],'openingMs':opening,**metrics,'result':'PASS'})
        context.close()
    browser.close()
(EVIDENCE/'accessibility-axe-report.json').write_text(json.dumps(accessibility,ensure_ascii=False,indent=2))
(EVIDENCE/'mobile-browser-report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
