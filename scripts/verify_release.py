#!/usr/bin/env python3
"""Verify exact source and bundled assets; compare a new APK only when supplied.

No check here certifies legal accuracy or the editor's declared verification date.
"""
from pathlib import Path
from collections import Counter
from zipfile import ZipFile
import argparse, hashlib, json
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'original/Consumer_Protection_Law.html'
DIST=ROOT/'dist'
EXPECTED_SHA256='e046bc015b1e1a7c0fe471f821cdbc53ca0b120f343929418ac393d004a424d4'

def verify(apk=None):
    checks=[]
    def check(name,okay):
        checks.append({'check':name,'passed':bool(okay)})
        if not okay: raise AssertionError(name)
    raw=SOURCE.read_bytes()
    check('Exact original HTML SHA256',hashlib.sha256(raw).hexdigest()==EXPECTED_SHA256)
    original=BeautifulSoup(raw,'lxml')
    generated=BeautifulSoup((DIST/'index.html').read_bytes(),'lxml')
    aliases={f'./PEGI_{x}_plus.png':f'./PEGI_{x}+.png' for x in (3,7,12,16,18)}
    for img in generated.select('img[src]'):
        if img['src'] in aliases:img['src']=aliases[img['src']]
    check('Legal document DOM unchanged except documented PEGI alias',
          str(original.select_one('#frame'))==str(generated.select_one('#frame')))
    for selector in ('.sources_box','.bills_box','.protocols_box','.history_box','footer'):
        check('Preserved '+selector,[str(x) for x in original.select(selector)]==[str(x) for x in generated.select(selector)])
    a=Counter(x['id'] for x in original.select('[id]'))
    b=Counter(x['id'] for x in generated.select('[id]'))
    check('Original ID occurrences',all(b[k]==v for k,v in a.items()))
    check('Original link targets',Counter(x.get('href') for x in original.select('a[href]'))==Counter(x.get('href') for x in generated.select('a[href]')))
    for src in (ROOT/'original').iterdir():
        if src.suffix.lower() in ('.html','.ico','.lnk'):continue
        check('Bundled unchanged: '+src.name,src.read_bytes()==(DIST/src.name).read_bytes())
    for age in (3,7,12,16,18):
        check('PEGI alias '+str(age),(DIST/f'PEGI_{age}_plus.png').read_bytes()==(ROOT/'original'/f'PEGI_{age}+.png').read_bytes())
    check('Old external accessibility widget inactive',all(x.get('type')=='application/x-law-original' for x in generated.find_all('script') if 'Fingerprint2' in (x.string or '')))
    report={'checks':checks,'source_sha256':EXPECTED_SHA256,'editorial_verification_date':json.loads((ROOT/'metadata/editorial_status.json').read_text())['law_text_last_verified_on'],'limitation':'No independent legal-text review; no device installation'}
    if apk is not None:
        apk=Path(apk).resolve()
        with ZipFile(apk) as z:
            check('APK archive integrity',z.testzip() is None)
            for p in sorted(DIST.iterdir()):
                if p.is_file():
                    check('APK web asset exact bytes: '+p.name,z.read('assets/www/'+p.name)==p.read_bytes())
            check('Native classes present',bool(z.read('classes.dex')))
        report['apk_sha256']=hashlib.sha256(apk.read_bytes()).hexdigest()
    report.update({'status':'PASS','checks_passed':len(checks)})
    (ROOT/'evidence').mkdir(exist_ok=True)
    (ROOT/'evidence/release-verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    return report

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--apk',help='Path to a newly built APK matching this source tree')
    args=ap.parse_args()
    r=verify(args.apk)
    print(json.dumps({k:v for k,v in r.items() if k!='checks'},ensure_ascii=False))
