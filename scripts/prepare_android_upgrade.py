#!/usr/bin/env python3
"""Re-sign a COPY of the public beta with the disposable QA identity for upgrade tests."""
from pathlib import Path
import hashlib,json,subprocess
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'downloads/latest.apk';metadata=json.loads((ROOT/'downloads/latest.json').read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()==metadata['sha256'],'Public APK checksum mismatch'
signer=ROOT/'.toolchain/build-tools-36.0.0/android-16/lib/apksigner.jar'
target=ROOT/'build/qa-upgrade-old.apk'
subprocess.run(['java','-jar',str(signer),'sign','--ks',str(ROOT/'build/qa-debug-keystore.p12'),'--ks-key-alias','qa-debug','--ks-pass','pass:qa-only-password','--v4-signing-enabled','false','--out',str(target),str(source)],check=True)
report={'sourceRelease':metadata['tag'],'sourceSha256':metadata['sha256'],'resignedCopySha256':hashlib.sha256(target.read_bytes()).hexdigest(),'identity':'Disposable QA only; this does not test original release signing or modify the public APK'}
(ROOT/'evidence/upgrade-test-identity.json').write_text(json.dumps(report,indent=2))
