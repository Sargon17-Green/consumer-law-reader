#!/usr/bin/env python3
"""Run a pinned, digest-verified Gitleaks CLI against all fetched Git history."""
from pathlib import Path
from urllib.request import urlopen
import hashlib,json,subprocess,tarfile
ROOT=Path(__file__).resolve().parents[1]
DIRECTORY=ROOT/'build/security-tools';DIRECTORY.mkdir(parents=True,exist_ok=True)
URL='https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz'
DIGEST='551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb'
archive=DIRECTORY/'gitleaks.tar.gz'
with urlopen(URL,timeout=90)as response,archive.open('wb')as output:
    total=0
    while block:=response.read(1024*1024):
        total+=len(block)
        if total>30000000:raise ValueError('Unexpected security-tool archive size')
        output.write(block)
assert hashlib.sha256(archive.read_bytes()).hexdigest()==DIGEST,'Security-tool checksum mismatch'
with tarfile.open(archive)as source:source.extract('gitleaks',DIRECTORY,filter='data')
executable=DIRECTORY/'gitleaks';executable.chmod(0o755)
(ROOT/'evidence').mkdir(exist_ok=True)
result=subprocess.run([str(executable),'git','--redact','--log-opts=--all','--report-format','json','--report-path',str(ROOT/'evidence/gitleaks-history.json')],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
(ROOT/'evidence/gitleaks-history.log').write_text(result.stdout)
(ROOT/'evidence/gitleaks-tool.json').write_text(json.dumps({'version':'8.30.1','sha256':DIGEST,'history':'all fetched refs','redaction':True,'exitCode':result.returncode},indent=2))
print('Gitleaks history scan exit code:',result.returncode)
raise SystemExit(result.returncode)
