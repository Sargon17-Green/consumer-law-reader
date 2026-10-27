from pathlib import Path
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
import xml.etree.ElementTree as ET
import zipfile,hashlib,os
root=Path(__file__).resolve().parents[1]/'.toolchain';root.mkdir(exist_ok=True)
base='https://dl.google.com/android/repository/'
data=urlopen(base+'repository2-3.xml',timeout=60).read()
xml=ET.fromstring(data)
packages=['build-tools;36.0.0','platforms;android-36']
jobs=[]
for package in packages:
 for p in xml.iter('remotePackage'):
  if p.get('path')!=package:continue
  for a in p.findall('./archives/archive'):
   if a.findtext('host-os') not in [None,'linux']:continue
   c=a.find('complete')
   jobs.append((package,base+c.findtext('url'),c.findtext('checksum')))
def fetch(item):
 name,url,checksum=item
 dest=root/(url.rsplit('/',1)[-1])
 if not dest.exists():
  with urlopen(url,timeout=90) as r, dest.open('wb') as w:
   while b:=r.read(1024*1024):w.write(b)
 if checksum and hashlib.sha1(dest.read_bytes()).hexdigest()!=checksum:raise RuntimeError('checksum '+name)
 out=root/name.replace(';','-')
 out.mkdir(exist_ok=True)
 with zipfile.ZipFile(dest) as z:z.extractall(out)
 for p in out.rglob('*'):
  if p.is_file() and ((p.suffix=='.so' or '.' not in p.name)):p.chmod(0o755)
 print('READY',name,str(out),flush=True)
 return out
with ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(fetch,jobs))
u='https://repo.maven.apache.org/maven2/org/eclipse/jdt/ecj/3.40.0/ecj-3.40.0.jar'
p=root/'ecj.jar'
if not p.exists():p.write_bytes(urlopen(u,timeout=60).read())
print('READY ecj',p,flush=True)
