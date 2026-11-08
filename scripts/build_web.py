#!/usr/bin/env python3
"""Preserve the supplied source verbatim and add an independent mobile layer."""
from pathlib import Path
import hashlib,json,shutil,re,base64,subprocess,html as html_module
from bs4 import BeautifulSoup
from prepare_typed_sources import prepare
from bundled_assets import is_bundled_asset
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'original'
DIST=ROOT/'dist'
if DIST.is_symlink():
    raise RuntimeError('The generated dist directory must not be a symlink')
if DIST.exists():
    shutil.rmtree(DIST)
DIST.mkdir()
for path in SOURCE.iterdir():
    if is_bundled_asset(path):
        shutil.copy2(path,DIST/path.name)
original=(SOURCE/'Consumer_Protection_Law.html').read_text()
# Keep legacy accessibility code as inert source; replace its network-dependent widget
# with the local mobile accessibility panel. No legal text is changed.
def disable_legacy(m):
    if 'Fingerprint2' in m.group(2) and 'StartAccessibility' in m.group(2):
        return '<script type="application/x-law-original">'+m.group(2)+'</script>'
    return m.group(0)
original=re.sub(r'<script\b([^>]*)>(.*?)</script>',disable_legacy,original,flags=re.S)
head='''<meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src https://raw.githubusercontent.com/Sargon17-Green/pastafari-calendar/main/docs/api/seer-now.json https://api.github.com/repos/Sargon17-Green/pastafari-calendar/contents/docs/api/seer-now.json https://sargon17-green.github.io/pastafari-calendar/api/seer-now.json; frame-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'"><meta name="theme-color" content="#142f41"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="default"><meta name="apple-mobile-web-app-title" content="חוק הגנת הצרכן, התשמ&quot;א–1981"><link rel="manifest" href="./manifest.webmanifest"><link rel="apple-touch-icon" href="./icon-192.png"><link rel="stylesheet" href="./mobile.css">'''
# Safari needs a mobile viewport for correct iPhone sizing.  Never modify
# the authoritative legal-source document; inject only when the source lacks it.
if not re.search(r'<meta[^>]+name\s*=\s*["\']viewport["\']', original, flags=re.I):
    head='<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'+head
# Authorize existing packaged inline scripts and handlers by exact deterministic hashes.
# Unlike unsafe-inline, this also blocks attacker-controlled inline scripts in srcdoc.
parsed=BeautifulSoup(original,'lxml')
inline=[script.string or '' for script in parsed.find_all('script') if not script.get('src') and script.get('type','').lower() in ('','text/javascript','application/javascript','module')]
handlers=[value for tag in parsed.find_all(True) for name,value in tag.attrs.items() if name.lower().startswith('on') and isinstance(value,str)]
hashes=sorted({"'sha256-"+base64.b64encode(hashlib.sha256(value.encode('utf-8')).digest()).decode('ascii')+"'" for value in inline+handlers})
security,head=head.split('<meta name="theme-color"',1)
security=security.replace("script-src 'self' 'unsafe-inline'","script-src 'self' 'unsafe-hashes' "+' '.join(hashes))
head='<meta name="theme-color"'+head
original=original.replace('<head>','<head>'+security,1)
shell=(ROOT/'web/mobile-shell.html').read_text()
editorial=json.loads((ROOT/'metadata/editorial_status.json').read_text(encoding='utf-8'))
assert editorial['law_text_last_verified_on'] and editorial['editor_publisher']=='סרגון 17 גרין'
embedded=json.dumps(editorial,ensure_ascii=False).replace('<','\\u003c').replace('&','\\u0026')
editorial_tag='<script type="application/json" id="law-editorial-status">'+embedded+'</script>'
privacy=json.loads((ROOT/'web/privacy.json').read_text())
privacy_tag='<script type="application/json" id="law-privacy">'+json.dumps(privacy,ensure_ascii=False).replace('<','\\u003c').replace('&','\\u0026')+'</script>'

prepare(ROOT/'typed-sources',DIST,ROOT/'evidence')
html=original.replace('<html>','<html lang="he" dir="rtl">',1).replace('</head>',head+'\n</head>',1).replace('<body onload="start()">','<body onload="start()">\n'+shell,1).replace('</body>',editorial_tag+privacy_tag+'<script defer src="./mobile-core.js"></script><script defer src="./mobile-settings.js"></script><script defer src="./mobile-sources.js"></script><script defer src="./mobile-topics.js"></script><script defer src="./mobile.js"></script>\n</body>',1)
# The Android asset handler uses MimeTypeMap.getFileExtensionFromUrl, which
# can be ambiguous for '+' in a filename. Generate lossless ASCII-safe aliases
# for PEGI age pictograms, without changing the preserved source HTML.
for age in (3, 7, 12, 16, 18):
    original_name=f'PEGI_{age}+.png'
    alias_name=f'PEGI_{age}_plus.png'
    shutil.copy2(SOURCE/original_name, DIST/alias_name)
    old=f'src="./{original_name}"'
    assert html.count(old)==1, (old,html.count(old))
    html=html.replace(old, f'src="./{alias_name}"')
(DIST/'index.html').write_text(html)
privacy_html='<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'"><title>'+html_module.escape(privacy['title'])+'</title><style>body{font:1.15rem/1.8 Arial,sans-serif;max-width:55rem;margin:2rem auto;padding:0 1rem;color:#172f40;background:#fff}a{color:#124e70}</style></head><body><h1>'+html_module.escape(privacy['title'])+'</h1>'+''.join('<p>'+html_module.escape(p)+'</p>' for p in privacy['paragraphs'])+'<p><a href="./">חזרה לממשק הקריאה</a> · <a href="https://github.com/Sargon17-Green/consumer-law-reader/issues">פניות ודיווח תקלות</a></p></body></html>'
(DIST/'privacy.html').write_text(privacy_html)
for name in ['mobile-core.js','mobile-settings.js','mobile.css','mobile.js','mobile-topics.js','mobile-sources.js','icon-192.png','icon-512.png']:
    shutil.copy2(ROOT/'web'/name,DIST/name)
manifest={'id':'./','name':'חוק הגנת הצרכן, התשמ"א–1981','short_name':'חוק הגנת הצרכן, התשמ"א–1981','lang':'he','dir':'rtl','start_url':'./','scope':'./','display':'standalone','background_color':'#f5f6f4','theme_color':'#142f41','description':'חוק הגנת הצרכן, התשמ"א–1981; חקיקת משנה ותוספים מתוך הקובץ המצורף.','icons':[{'src':'./icon-192.png','sizes':'192x192','type':'image/png','purpose':'any'},{'src':'./icon-512.png','sizes':'512x512','type':'image/png','purpose':'any maskable'}]}
(DIST/'manifest.webmanifest').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
files=['./']+['./'+p.name for p in sorted(DIST.iterdir()) if p.is_file() and p.name not in ['sw.js']]
version=hashlib.sha256(b''.join(p.read_bytes() for p in sorted(DIST.iterdir()) if p.is_file() and p.name!='sw.js')).hexdigest()[:16]
worker='''const CACHE='law-reader-VERSION';const FILES=FILES_JSON;
self.addEventListener('install',event=>event.waitUntil((async()=>{const cache=await caches.open(CACHE);for(const path of FILES){const response=await fetch(path,{cache:'reload',credentials:'same-origin'});if(!response.ok)throw Error('offline asset failed');await cache.put(path,response);}await self.skipWaiting();})()));
self.addEventListener('activate',event=>event.waitUntil((async()=>{for(const key of await caches.keys())if(key.startsWith('law-reader-')&&key!==CACHE)await caches.delete(key);await self.clients.claim();for(const client of await self.clients.matchAll())client.postMessage({type:'OFFLINE_READY'});})()));
self.addEventListener('message',event=>{if(event.data?.type==='OFFLINE_STATUS')event.waitUntil((async()=>{const cache=await caches.open(CACHE);const ready=(await cache.keys()).length>=FILES.length;event.source?.postMessage({type:ready?'OFFLINE_READY':'OFFLINE_ERROR'});})());});
self.addEventListener('fetch',event=>{const url=new URL(event.request.url);if(url.origin!==self.location.origin||event.request.method!=='GET')return;event.respondWith((async()=>{const cached=await caches.match(event.request,{ignoreSearch:true});if(cached)return cached;try{return await fetch(event.request);}catch(error){if(event.request.mode==='navigate')return await caches.match('./index.html');throw error;}})());});
'''.replace('VERSION',version).replace('FILES_JSON',json.dumps(files,ensure_ascii=False))
(DIST/'sw.js').write_text(worker)
evidence={'original_html_sha256':hashlib.sha256((SOURCE/'Consumer_Protection_Law.html').read_bytes()).hexdigest(),'original_html_bytes':(SOURCE/'Consumer_Protection_Law.html').stat().st_size,'document_preserved':'Original HTML is embedded without deleting or changing content; mobile markup, metadata, CSS and JS added.','assets':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(DIST.iterdir()) if p.is_file()},'web_version':version}
try:
    evidence['sourceCommit']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,stderr=subprocess.DEVNULL,text=True).strip()
    evidence['sourceTree']=subprocess.check_output(['git','rev-parse','HEAD^{tree}'],cwd=ROOT,stderr=subprocess.DEVNULL,text=True).strip()
    evidence['sourceDirty']=bool(subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],cwd=ROOT,text=True))
except (OSError,subprocess.CalledProcessError):
    evidence['sourceCommit']=None
    evidence['sourceTree']=None
    evidence['sourceDirty']=None
(ROOT/'evidence/content-manifest.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
print(json.dumps({'web_version':version,'assets':len(files),'index_bytes':(DIST/'index.html').stat().st_size}))
