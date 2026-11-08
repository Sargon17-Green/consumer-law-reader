"""Fetch a reproducible Linux Android toolchain, verified before extraction."""
from pathlib import Path
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
import hashlib,json,zipfile,os
ROOT=Path(__file__).resolve().parents[1]
TOOLS=Path(os.environ.get('LAW_ANDROID_TOOLS',str(ROOT/'.toolchain'))).resolve();TOOLS.mkdir(exist_ok=True)
LOCK=json.loads((ROOT/'scripts/android_toolchain.lock.json').read_text())
def fetch(item):
    path=TOOLS/item['file']
    if not path.is_file():
        temporary=path.with_suffix(path.suffix+'.partial')
        try:
            with urlopen(item['url'],timeout=90)as response,temporary.open('wb')as output:
                while block:=response.read(1024*1024):output.write(block)
            if hashlib.sha256(temporary.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Toolchain digest mismatch: '+item['file'])
            temporary.replace(path)
        finally:temporary.unlink(missing_ok=True)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Cached toolchain digest mismatch: '+item['file'])
    if item.get('directory'):
        directory=TOOLS/item['directory'];directory.mkdir(exist_ok=True)
        with zipfile.ZipFile(path)as archive:
            if any(not (directory/name).resolve().is_relative_to(directory.resolve())for name in archive.namelist()):raise ValueError('Toolchain path traversal')
            archive.extractall(directory)
        for file in directory.rglob('*'):
            if file.is_file()and(file.suffix=='.so'or'.'not in file.name):file.chmod(0o755)
    print('READY',item['file'],item['sha256'],flush=True)
with ThreadPoolExecutor(max_workers=3)as executor:list(executor.map(fetch,LOCK['packages']))
