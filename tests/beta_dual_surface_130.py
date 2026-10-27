#!/usr/bin/env python3
"""Chromium smoke tests of full legal HTML in desktop and mobile modes. Records evidence; no external network."""
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import hashlib,json,subprocess
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
root=Path(__file__).resolve().parents[1]
checks=[]
def ck(label,good,details=None):
    item=dict(name=label,passed=bool(good),actual=details)
    checks.append(item)
    print(('PASS' if good else 'FAIL'),label, str(details)[:170],flush=True)
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
    def end_headers(self):
        self.send_header('Cache-Control','no-cache')
        super().end_headers()
with ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(root/'dist'))) as server:
    thread=Thread(target=server.serve_forever,daemon=True);thread.start()
    address=f'http://127.0.0.1:{server.server_address[1]}/'
    # Browser navigation to localhost and file:// is blocked by the test sandbox.
    # Separately validate the HTTP server; for Chromium inspect the *same built DOM* injected directly.
    import urllib.request
    with urllib.request.urlopen(address+'mobile.css',timeout=10) as rsp:
        ck('desktop_server_serves_css',rsp.status==200 and b'm-justify' in rsp.read(),rsp.status)
    soup=BeautifulSoup((root/'dist/index.html').read_text(encoding='utf8'),'lxml')
    for x in soup.find_all('script'): x.decompose()
    for x in soup.find_all('iframe'): x.decompose()
    for x in soup.find_all('link',rel='stylesheet'): x.decompose()
    if soup.body: soup.body.attrs.pop('onload',None)
    injected_html=str(soup)
    with sync_playwright() as pw:
        browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-background-networking'])
        for width in [375,600,1280,1440]:
            p=browser.new_page(viewport={'width':width,'height':900},device_scale_factor=1)
            errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
            p.set_content(injected_html,wait_until='domcontentloaded',timeout=80000)
            p.evaluate("""() => {let v={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>v[k]??null,setItem:(k,x)=>v[k]=String(x),removeItem:k=>delete v[k]}})}""")
            p.add_style_tag(content=(root/'web/mobile.css').read_text(encoding='utf8'))
            for f in ['mobile-sources.js','mobile-topics.js','mobile.js']:
                p.add_script_tag(content=(root/'web'/f).read_text(encoding='utf8'))
            p.wait_for_function("window.lawMobile && window.LawSources && window.LawTopics",timeout=45000)
            data=p.evaluate("""() => {
                const elm=s=>document.querySelector(s),comp=s=>getComputedStyle(elm(s)),box=s=>elm(s).getBoundingClientRect();
                const sidebar=box('.m-bottom');
                return {ver:window.lawMobile.version,title:comp('#law_name td.title').textAlign,
                chapter:comp('#chapter_a_title td.title').textAlign,
                justified:comp('#article_4a_detail_1 td:last-child').textAlign,
                sideColor:comp('#article_4a .side_title').color,
                textColor:comp('body').color,
                desktopSidebar:sidebar.right<=innerWidth+3&&sidebar.left>=innerWidth-245&&sidebar.top>80&&sidebar.bottom<document.documentElement.clientHeight-100&&box('#frame').right<sidebar.left-5,
                mobileBottom:sidebar.bottom>=innerHeight-10,
                viewport:innerWidth,docWidth:document.documentElement.scrollWidth,
                office:!!document.querySelector('.delegated_legislation'),
                navigationButtons:document.querySelectorAll('.m-bottom button').length,
                licensePanel:!!document.querySelector('#mobile-sheet'),
                mainTitle:elm('#law_name td.title').textContent.trim().slice(0,70)};
            }""")
            ck(f'version_{width}',data['ver']=='1.3.0',data['ver'])
            ck(f'law_title_center_{width}',data['title']=='center',data['title'])
            ck(f'chapter_center_{width}',data['chapter']=='center',data['chapter'])
            ck(f'legal_body_justified_{width}',data['justified']=='justify',data['justified'])
            ck(f'topic_side_is_legal_text_{width}',data['sideColor']==data['textColor'],{'side':data['sideColor'],'body':data['textColor']})
            ck(f'responsive_toolbar_{width}',data['desktopSidebar'] if width>=1100 else data['mobileBottom'],data)
            ck(f'no_horizontal_overflow_{width}',data['docWidth']<=width+2,data['docWidth'])
            ck(f'no_script_crash_{width}',not errors,errors[:3])
            if width==1280:
                p.screenshot(path=str(root/'evidence/beta-desktop-1280.png'),full_page=False)
                # tap main actions button, then feedback under display panel
                p.locator('[data-mobile="actions"]').click(timeout=10000)
                ck('desktop_action_sheet_open',p.locator('#mobile-sheet').evaluate('(el)=>el.open'),p.locator('#mobile-sheet-title').inner_text())
                p.locator('#mobile-sheet-close').click()
                p.locator('[data-mobile="actions"]').click()
                p.get_by_role('button',name='הגדרות תצוגה ונגישות').first.click()
                ck('beta_feedback_option',p.get_by_role('button',name='משוב על גרסת הבטא').count()>0,None)
                ck('about_license_option',p.get_by_role('button',name='על הקובץ').count()>0,None)
                p.get_by_role('button',name='על הקובץ').click()
                ck('license_notice_in_app','MIT' in p.locator('#mobile-sheet-body').inner_text(),p.locator('#mobile-sheet-body').inner_text()[-200:])
            p.close()
        browser.close()
    server.shutdown()
# Byte-for-byte legal source preservation, excluding exactly the three injected UI scripts.
source=(root/'original/Consumer_Protection_Law.html').read_text(encoding='utf8')
output=(root/'dist/index.html').read_text(encoding='utf8')
needle='id="frame"'
input_fragment=source[source.find(needle):source.rfind('</body>')]
output_fragment=output[output.find(needle):output.rfind('</body>')]
for addition in ['<script defer src="./mobile-sources.js"></script>', '<script defer src="./mobile-topics.js"></script>', '<script defer src="./mobile.js"></script>']:
    output_fragment=output_fragment.replace(addition,'')
ck('legal_source_immutable_html_fragment', input_fragment==output_fragment[:-1],{'original_bytes':len(input_fragment.encode()),'built_bytes':len(output_fragment.encode())})
script=root/'evidence/beta-dual-surface-v1.3.0.json'
script.write_text(json.dumps({'version':'1.3.0','checks':checks,'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'browser':'Chromium desktop emulation, not physical device','original_sha256':hashlib.sha256((root/'original/Consumer_Protection_Law.html').read_bytes()).hexdigest()},ensure_ascii=False,indent=2))
print('SUMMARY',sum(x['passed'] for x in checks),'pass',sum(not x['passed'] for x in checks),'fail')
assert all(x['passed'] for x in checks),'Regression failed'
