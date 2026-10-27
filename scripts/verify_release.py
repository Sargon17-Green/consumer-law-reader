#!/usr/bin/env python3
"""Check source preservation and the exact assets that the Android loader opens."""
from pathlib import Path
from collections import Counter
from urllib.parse import unquote
from zipfile import ZipFile
import hashlib,json,re
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
VERSION=(ROOT/'VERSION').read_text().strip()
original=BeautifulSoup((ROOT/'original/Consumer_Protection_Law.html').read_bytes(),'lxml')
generated=BeautifulSoup((ROOT/'dist/index.html').read_bytes(),'lxml')
checks=[]
def check(name,condition,details=None):
    checks.append({'check':name,'passed':bool(condition),'details':details})
    if not condition:raise AssertionError(name)

check('Main legal document subtree preserved',str(original.select_one('#frame'))==str(generated.select_one('#frame')))
for selector in ['.sources_box','.bills_box','.protocols_box','.history_box','footer']:
    a=[str(x) for x in original.select(selector)];b=[str(x) for x in generated.select(selector)]
    check('Preserved '+selector,a==b,{'count':len(a)})
check('All original legal links preserved',Counter(x.get('href') for x in original.select('a[href]'))==Counter(x.get('href') for x in generated.select('a[href]')))
original_ids=Counter(x['id'] for x in original.select('[id]'))
generated_ids=Counter(x['id'] for x in generated.select('[id]'))
check('All original IDs preserved',all(generated_ids[k]==v for k,v in original_ids.items()),{'original_id_occurrences':sum(original_ids.values())})
for source in (ROOT/'original').iterdir():
    if source.suffix.lower() in ['.html','.ico','.lnk']:continue
    check('Bundled asset '+source.name,source.read_bytes()==(ROOT/'dist'/source.name).read_bytes())
check('Network-dependent legacy accessibility script is inert',all(x.get('type')=='application/x-law-original' for x in generated.find_all('script') if 'Fingerprint2' in (x.string or '')))
with ZipFile(ROOT/f'release/Consumer_Law_Mobile_{VERSION}.apk') as apk:
    check('APK ZIP integrity',apk.testzip() is None)
    for p in sorted((ROOT/'dist').iterdir()):
        if p.is_file():check('Android asset path and bytes: '+p.name,apk.read('assets/www/'+p.name)==p.read_bytes())
    check('Native classes packaged',len(apk.read('classes.dex'))>0)
    attachments=[x for x in apk.infolist() if x.filename.endswith('.doc')]
    check('Word attachment accessible via AssetFileDescriptor',len(attachments)==1 and attachments[0].compress_type==0)

missing=sorted({unquote(a['href'][1:]) for a in original.select('a[href^="#"]') if a['href'][1:] not in original_ids})
result={'status':'PASS','checks_passed':len(checks),'checks':checks,'original_source_limitations':{'missing_internal_targets':missing,'duplicate_ids':{k:v for k,v in original_ids.items() if v>1}},'apk_sha256':hashlib.sha256((ROOT/f'release/Consumer_Law_Mobile_{VERSION}.apk').read_bytes()).hexdigest(),'runtime_validation_limit':'No physical Android or iPhone installation was performed in this environment.'}
(ROOT/'evidence/release-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'status':'PASS','checks':len(checks),'original_missing_link_targets':len(missing),'original_duplicate_ids':len(result['original_source_limitations']['duplicate_ids'])}))
