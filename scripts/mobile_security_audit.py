#!/usr/bin/env python3
"""Bounded static checks; report findings, never print potential secret material."""
from pathlib import Path
import subprocess,re,json,hashlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
tracked=subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).decode().split('\0')
patterns=[re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),re.compile(rb'gh[pousr]_[A-Za-z0-9]{35,}'),re.compile(rb'github_pat_[A-Za-z0-9_]{50,}'),re.compile(rb'AKIA[A-Z0-9]{16}')]
findings=[]
for name in tracked:
 p=ROOT/name
 if not p.is_file()or p.suffix in ('.apk','.png','.jpg','.gif','.ico','.doc')or name=='scripts/mobile_security_audit.py':continue
 raw=p.read_bytes()
 for index,pattern in enumerate(patterns):
  if pattern.search(raw):findings.append({'file':name,'type':'possible-secret','pattern':index})
ns={'a':'http://schemas.android.com/apk/res/android'}
manifest=ET.parse(ROOT/'android/AndroidManifest.xml').getroot()
permissions={p.attrib.get('{'+ns['a']+'}name')for p in manifest.findall('uses-permission')}
assert permissions=={'android.permission.INTERNET'},permissions
application=manifest.find('application');assert application.attrib['{'+ns['a']+'}usesCleartextTraffic']=='false'
assert application.attrib['{'+ns['a']+'}allowBackup']=='false'
source=(ROOT/'android/src/il/org/lawreader/consumer/MainActivity.java').read_text()
for text in ['setAllowFileAccess(false)','setAllowContentAccess(false)','MIXED_CONTENT_NEVER_ALLOW','setInstanceFollowRedirects(false)','uri.getUserInfo() != null','private boolean trusted()']:
 assert text in source,text
swift=(ROOT/'ios/ConsumerLawReader/ConsumerLawReaderApp.swift').read_text()
for text in ['message.frameInfo.isMainFrame','message.webView === webView','ReaderPolicy.isBundledDocument','guard let reader, reader.isTrustedMessage(message)']:
 assert text in swift,text
# Scan tracked names throughout history without reading or printing any private data.
history_names=set(subprocess.check_output(['git','log','--all','--pretty=format:','--name-only'],cwd=ROOT).decode().splitlines())
suspicious=[n for n in history_names if re.search(r'(?i)(?:\.p12|\.pfx|\.keystore|key-password\.txt|\.env)$',n)]
findings.extend({'file':n,'type':'suspicious-historical-name'}for n in suspicious)
report={'scope':'Tracked current text; secret-like byte patterns and historical filenames. Not a penetration test or proof of absence from every historical blob.','permissions':sorted(permissions),'findings':findings,'result':'PASS'if not findings else'REVIEW'}
(ROOT/'evidence').mkdir(exist_ok=True);(ROOT/'evidence/mobile-security-static.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
if findings:raise SystemExit(1)
