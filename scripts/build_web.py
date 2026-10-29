#!/usr/bin/env python3
"""Preserve the supplied source verbatim and add an independent mobile layer."""
from pathlib import Path
import hashlib,json,shutil,re
from prepare_typed_sources import prepare
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'original'
DIST=ROOT/'dist'
DIST.mkdir(exist_ok=True)
for path in SOURCE.iterdir():
    if path.is_file() and path.suffix.lower() not in ['.html','.lnk','.ico']:
        shutil.copy2(path,DIST/path.name)
original=(SOURCE/'Consumer_Protection_Law.html').read_text()
# Keep legacy accessibility code as inert source; replace its network-dependent widget
# with the local mobile accessibility panel. No legal text is changed.
def disable_legacy(m):
    if 'Fingerprint2' in m.group(2) and 'StartAccessibility' in m.group(2):
        return '<script type="application/x-law-original">'+m.group(2)+'</script>'
    return m.group(0)
original=re.sub(r'<script\b([^>]*)>(.*?)</script>',disable_legacy,original,flags=re.S)
head='''<meta name="theme-color" content="#142f41"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-status-bar-style" content="default"><meta name="apple-mobile-web-app-title" content="חוק הגנת הצרכן, התשמ&quot;א–1981"><link rel="manifest" href="./manifest.webmanifest"><link rel="apple-touch-icon" href="./icon-192.png"><link rel="stylesheet" href="./mobile.css">'''
# Safari needs a mobile viewport for correct iPhone sizing.  Never modify
# the authoritative legal-source document; inject only when the source lacks it.
if not re.search(r'<meta\\s+[^>]*name\\s*=\\s*["\\\']viewport["\\\']', original, flags=re.I):
    head='<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">'+head
shell=(ROOT/'web/mobile-shell.html').read_text()
editorial=json.loads((ROOT/'metadata/editorial_status.json').read_text(encoding='utf-8'))
assert editorial['law_text_last_verified_on'] and editorial['editor_publisher']=='סרגון 17 גרין'
embedded=json.dumps(editorial,ensure_ascii=False).replace('<','\\u003c').replace('&','\\u0026')
editorial_tag='<script type="application/json" id="law-editorial-status">'+embedded+'</script>'

prepare(ROOT/'typed-sources',DIST,ROOT/'evidence')
html=original.replace('<html>','<html lang="he" dir="rtl">',1).replace('</head>',head+'\n</head>',1).replace('<body onload="start()">','<body onload="start()">\n'+shell,1).replace('</body>',editorial_tag+'<script defer src="./mobile-sources.js"></script><script defer src="./mobile-topics.js"></script><script defer src="./mobile.js"></script>\n</body>',1)
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
for name in ['mobile.css','mobile.js','mobile-topics.js','mobile-sources.js','icon-192.png','icon-512.png']:
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
(ROOT/'evidence/content-manifest.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
print(json.dumps({'web_version':version,'assets':len(files),'index_bytes':(DIST/'index.html').stat().st_size}))
