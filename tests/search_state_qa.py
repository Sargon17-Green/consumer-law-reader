"""Real full-DOM search -> reading -> layout change -> same result restoration."""
from pathlib import Path
from urllib.parse import urlparse,unquote
from playwright.sync_api import sync_playwright
import json,mimetypes,os,re,shutil,subprocess
ROOT=Path(__file__).resolve().parents[1]
def serve(route):
    url=urlparse(route.request.url)
    if url.hostname!='law.local':route.abort('internetdisconnected');return
    path=(ROOT/'dist'/unquote(url.path.lstrip('/') or 'index.html')).resolve()
    if not path.is_relative_to((ROOT/'dist').resolve()) or not path.is_file():route.fulfill(status=404,body='missing');return
    route.fulfill(status=200,body=path.read_bytes(),content_type=mimetypes.guess_type(path.name)[0] or 'application/octet-stream')
INSPECT='''button=>{const r=button.getBoundingClientRect(),body=document.getElementById('mobile-sheet-body'),box=body.getBoundingClientRect();return {target:button.querySelector('strong').textContent,top:r.top,bottom:r.bottom,bodyTop:box.top,bodyBottom:box.bottom,scroll:body.scrollTop,offset:r.top-box.top,fullyVisible:r.top>=box.top-1&&r.bottom<=box.bottom+1}}'''
report=[]
with sync_playwright() as pw:
    options={'args':['--no-sandbox','--disable-dev-shm-usage']}
    executable=os.environ.get('LAW_QA_CHROMIUM') or shutil.which('chromium')
    if executable:options['executable_path']=executable
    browser=pw.chromium.launch(**options)
    cases=[((1032,1255),(375,697),'all','normalized'),((375,697),(1032,1255),'law','exact'),((430,932),(320,740),'law','normalized'),((375,697),(375,697),'all','normalized'),((1032,1255),(1032,650),'all','normalized')]
    for original,changed,scope,mode in cases:
        context=browser.new_context(viewport={'width':original[0],'height':original[1]},service_workers='block',reduced_motion='reduce');context.route('**/*',serve);page=context.new_page()
        page.goto('https://law.local/');page.wait_for_function("()=>document.documentElement.dataset.lawReady==='true'")
        page.locator('[data-mobile=search]').click();page.get_by_label('תחום חיפוש').select_option(scope);page.get_by_label('אופן התאמה').select_option(mode);page.locator('#mobile-search').fill('14')
        chosen=page.get_by_role('button',name=re.compile(r'^סעיף 14(?:\s|$)')).first;chosen.wait_for();chosen.scroll_into_view_if_needed();before=chosen.evaluate(INSPECT);chosen.click()
        page.set_viewport_size({'width':changed[0],'height':changed[1]});page.locator('#mobile-return').click();page.wait_for_timeout(300);after=chosen.evaluate(INSPECT)
        assert page.locator('#mobile-search').input_value()=='14'
        assert page.get_by_label('תחום חיפוש').input_value()==scope and page.get_by_label('אופן התאמה').input_value()==mode
        assert after['fullyVisible'],{'original':original,'changed':changed,'before':before,'after':after}
        if original==changed:assert abs(before['offset']-after['offset'])<=2,{'before':before,'after':after}
        # Repeated result -> reading -> results stays stable after the correction.
        chosen.click();page.locator('#mobile-return').click();page.wait_for_timeout(200);again=chosen.evaluate(INSPECT);assert again['fullyVisible'],again
        assert abs(again['offset']-after['offset'])<=2,{'firstReturn':after,'secondReturn':again}
        report.append({'original':original,'changed':changed,'scope':scope,'mode':mode,'before':before,'after':after,'repeat':again,'result':'PASS'})
        context.close()
    browser.close()
output={'schema':1,'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'sourceDirty':bool(subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,text=True)),'result':'PASS','environment':'Actual bundled Chromium DOM, network aborted, Playwright; not a physical phone','cases':report}
(ROOT/'evidence').mkdir(exist_ok=True);(ROOT/'evidence/search-state-layout.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n');print(json.dumps(output,ensure_ascii=False))
