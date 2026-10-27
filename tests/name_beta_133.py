#!/usr/bin/env python3
"""Focused 1.3.3 brand/viewport regression checks on unmodified legal source."""
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import hashlib,json,subprocess,zipfile,sys
sys.path.insert(0,'/mnt/data')
from inspect_axml import parse_axml
root=Path(__file__).resolve().parents[1]
output=Path('/mnt/data')
NAME='חוק הגנת הצרכן, התשמ"א–1981'
checks=[]
def ck(n,b,d=''):
  checks.append({'name':n,'pass':bool(b),'detail':str(d)[:220]})
  print(('PASS ' if b else 'FAIL ')+n,flush=True)
  if not b: raise AssertionError(n+' : '+str(d))
ck('source_html_exact_unchanged_sha256',hashlib.sha256((root/'original/Consumer_Protection_Law.html').read_bytes()).hexdigest()=='e046bc015b1e1a7c0fe471f821cdbc53ca0b120f343929418ac393d004a424d4')
compiled=(root/'dist/index.html').read_text(encoding='utf-8')
soup=BeautifulSoup(compiled,'lxml')
ck('browser_window_document_title_exact',soup.title.text==NAME,soup.title.text)
ck('header_name_exact',next(x for x in soup.select_one('.m-brand').contents if isinstance(x,str)).strip()==NAME)
ck('header_subtitle_has_no_duplicate_year','1981' not in soup.select_one('.m-subtitle').text)
manifest=json.loads((root/'dist/manifest.webmanifest').read_text(encoding='utf-8'))
ck('pwa_name_exact',manifest['name']==NAME)
ck('pwa_short_name_exact',manifest['short_name']==NAME)
ck('apple_web_app_name_exact',soup.select_one('meta[name="apple-mobile-web-app-title"]')['content']==NAME)
ck('javascript_syntax',subprocess.run(['node','--check',str(root/'dist/mobile.js')],capture_output=True).returncode==0)
ck('editorial_date_unchanged',json.loads((root/'metadata/editorial_status.json').read_text())['law_text_last_verified_on']=='2026-10-27')
with zipfile.ZipFile(output/'Consumer_Law_Reader_1.3.3_Beta_Android.apk') as apk:
  axml=apk.read('AndroidManifest.xml')
  strings,_,attrs=parse_axml(axml)
  for tag,attr,expected in [('application','label',NAME),('manifest','versionName','1.3.3')]:
    found=next(x for x in attrs if x['tag']==tag and x['name']==attr)
    ck('android_'+attr,strings[found['dataValue']][0]==expected)
  code=next(x for x in attrs if x['tag']=='manifest' and x['name']=='versionCode')
  ck('android_versioncode',code['dataValue']==11)
  ck('apk_web_match',apk.read('assets/www/index.html')==(root/'dist/index.html').read_bytes())
# Layout check on full legal source: scripts removed to prevent outside request.
for x in soup.find_all('script'): x.decompose()
for x in soup.find_all('iframe'): x.decompose()
for x in soup.find_all('link',rel='stylesheet'): x.decompose()
if soup.body:soup.body.attrs.pop('onload',None)
with sync_playwright() as p:
  browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-background-networking'])
  for width in (320,375,430,1280):
    page=browser.new_page(viewport={'width':width,'height':860},device_scale_factor=1)
    page.set_content(str(soup),wait_until='domcontentloaded',timeout=80000)
    page.add_style_tag(content=(root/'web/mobile.css').read_text(encoding='utf-8'))
    r=page.evaluate('''() => {const head=document.querySelector('.m-top').getBoundingClientRect(),frame=document.querySelector('#frame').getBoundingClientRect(),title=document.querySelector('.m-brand').getBoundingClientRect(); return {headBottom:head.bottom,frameTop:frame.top,titleWidth:title.width,docWidth:document.documentElement.scrollWidth,screenWidth:innerWidth,titleText:document.querySelector('.m-brand').childNodes[0].textContent.trim()}}''')
    ck(f'header_does_not_overlap_law_{width}',r['headBottom']<=r['frameTop']+2,r)
    ck(f'full_name_not_cut_off_{width}',r['titleWidth']>=110 and r['titleText']==NAME,r)
    ck(f'header_fits_viewport_{width}',r['titleWidth']<=r['screenWidth']-35,r)
    if width==375:page.screenshot(path=str(output/'Consumer_Law_Reader_1.3.3_Beta_Title_375.png'))
    page.close()
  browser.close()
report={'version':'1.3.3-beta.1','name':NAME,'count':len(checks),'passes':sum(x['pass'] for x in checks),'physical_device_test':'NOT_RUN','checks':checks}
(output/'Consumer_Law_Reader_1.3.3_Beta_Name_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'passed':report['passes'],'count':report['count']},ensure_ascii=False))
