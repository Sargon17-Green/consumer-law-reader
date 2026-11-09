"""Exercise a real ServiceWorker and cached installed-app entry, without a phone claim."""
from pathlib import Path
from urllib.parse import urlparse,unquote
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from playwright.sync_api import sync_playwright
import json,mimetypes,os,re,shutil,subprocess,threading
ROOT=Path(__file__).resolve().parents[1];PREFIX='/consumer-law-reader/reader/'
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path=unquote(urlparse(self.path).path)
        if not path.startswith(PREFIX):self.send_error(404);return
        target=(ROOT/'dist'/(path[len(PREFIX):] or 'index.html')).resolve()
        if not target.is_relative_to((ROOT/'dist').resolve()) or not target.is_file():self.send_error(404);return
        body=target.read_bytes();self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(target.name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
    def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
    with sync_playwright() as pw:
        options={'args':['--no-sandbox','--disable-dev-shm-usage']}
        executable=os.environ.get('LAW_QA_CHROMIUM') or shutil.which('chromium')
        if executable:options['executable_path']=executable
        browser=pw.chromium.launch(**options)
        context=browser.new_context(viewport={'width':375,'height':812})
        context.route('https://**/*',lambda route:route.abort('internetdisconnected'))
        page=context.new_page();url='http://127.0.0.1:'+str(server.server_port)+PREFIX
        page.goto(url+'#article_14',wait_until='load');page.wait_for_function("()=>document.documentElement.dataset.lawReady==='true'")
        page.wait_for_function("()=>navigator.serviceWorker.controller!==null",timeout=60000)
        status=page.evaluate('''async()=>{
          await navigator.serviceWorker.ready;
          return await new Promise((resolve,reject)=>{
            const timer=setTimeout(()=>reject(Error('Offline cache status timeout')),60000);
            const receive=e=>{if(e.data?.type==='OFFLINE_READY'||e.data?.type==='OFFLINE_ERROR'){clearTimeout(timer);navigator.serviceWorker.removeEventListener('message',receive);resolve(e.data.type)}};
            navigator.serviceWorker.addEventListener('message',receive);navigator.serviceWorker.controller.postMessage({type:'OFFLINE_STATUS'});
          });
        }''')
        assert status=='OFFLINE_READY',status
        manifest_data=context.new_cdp_session(page).send('Page.getAppManifest')
        assert not manifest_data['errors'],manifest_data['errors']
        manifest=json.loads(manifest_data['data'])
        assert manifest['id']=='./' and manifest['start_url']=='./' and manifest['scope']=='./' and manifest['display']=='standalone'
        cache=page.evaluate('''async()=>{const names=(await caches.keys()).filter(n=>n.startsWith('law-reader-'));return {names,files:(await (await caches.open(names[0])).keys()).length,script:navigator.serviceWorker.controller.scriptURL}}''')
        assert len(cache['names'])==1 and cache['files']>=38,cache
        assert cache['script']==url+'sw.js'
        page.evaluate("localStorage.setItem('law-reader-font','24');lawMobile.goTo('article_14');lawMobile.saveSession()")
        context.set_offline(True)
        page.reload(wait_until='load');page.wait_for_function("()=>document.documentElement.dataset.lawReady==='true'")
        assert page.evaluate('lawMobile.buildSearch().length')>500
        page.locator('[data-mobile=search]').click();page.locator('#mobile-search').fill('14');page.wait_for_function("()=>document.querySelectorAll('.m-result').length>0")
        page.get_by_role('button',name=re.compile(r'^סעיף 14(?:\s|$)')).first.click();assert page.evaluate('location.hash')=='#article_14'
        page.close();page=context.new_page();page.goto(url+'?entry=home#article_14',wait_until='load');page.wait_for_function("()=>document.documentElement.dataset.lawReady==='true'")
        assert page.evaluate("localStorage.getItem('law-reader-font')")=='24'
        assert page.evaluate('location.hash')=='#article_14'
        assert page.evaluate('lawMobile.buildSearch().length')>500
        report={'schema':1,'sourceCommit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'result':'PASS','environment':'Actual Chromium ServiceWorker at trusted loopback origin, canonical /consumer-law-reader/reader/ subpath, Playwright network fully offline after cache activation','coverage':['real complete cache activation and OFFLINE_STATUS reply','stable manifest identity/start_url/scope/standalone','offline reload, Hebrew search and exact section navigation','new page at home-screen start URL with query/hash and preserved preferences'],'cache':cache,'limitations':'Not a physical Android/iOS installation or OS home-screen icon test; native launcher tests are separate'}
        (ROOT/'evidence').mkdir(exist_ok=True);(ROOT/'evidence/pwa-offline.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
        context.close();browser.close()
finally:
    server.shutdown();server.server_close();thread.join(timeout=3)
