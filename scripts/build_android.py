#!/usr/bin/env python3
"""Build and sign the offline APK with pinned Android command-line tools (Linux)."""
from pathlib import Path
import os,subprocess,zipfile,json,hashlib,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
VERSION=(ROOT/'VERSION').read_text().strip()
DEBUG='--debug' in sys.argv
TOOLS=Path(os.environ.get('LAW_ANDROID_TOOLS',str(ROOT/'.toolchain'))).resolve()
BUILD=ROOT/'build';BUILD.mkdir(exist_ok=True)
OUT=ROOT/('debug-build' if DEBUG else 'release');OUT.mkdir(exist_ok=True)
sdk=TOOLS/'build-tools-36.0.0/android-16'
android=TOOLS/'platforms-android-36/android-36/android.jar'
def run(*args):subprocess.run([str(a) for a in args],check=True,cwd=ROOT)
if not android.exists() or not (sdk/'aapt2').exists():
    raise SystemExit('First run: python3 scripts/fetch_tools.py')
run('python3',ROOT/'scripts/build_web.py')
classes=BUILD/'classes';dex=BUILD/'dex'
for p in [classes,dex]:
    if p.exists():shutil.rmtree(p)
    p.mkdir()
run('java','-jar',TOOLS/'ecj.jar','-source','8','-target','8','-encoding','UTF-8','-warn:none','-classpath',android,'-d',classes,*sorted((ROOT/'android/src').rglob('*.java')))
run('java','-cp',sdk/'lib/d8.jar','com.android.tools.r8.D8','--min-api','26','--lib',android,'--output',dex,*sorted(classes.rglob('*.class')))
run(sdk/'aapt2','compile','--dir',ROOT/'android/res','-o',BUILD/'resources.zip')
assets=BUILD/'assets'
if assets.exists():shutil.rmtree(assets)
shutil.copytree(ROOT/'dist',assets/'www')
run(sdk/'aapt2','link','-I',android,'--manifest',ROOT/'android/AndroidManifest.xml','-A',assets,'-0','doc','-o',BUILD/'resource-package.apk',BUILD/'resources.zip')
# aapt2 emits UTF-8 asset names without the ZIP UTF-8 flag. Normalize before
# Python writes the central directory, otherwise Hebrew names become mojibake.
with zipfile.ZipFile(BUILD/'resource-package.apk','r') as source, zipfile.ZipFile(BUILD/'unsigned.apk','w') as z:
    for info in source.infolist():
        data=source.read(info)
        if not info.flag_bits & 0x800:
            try:info.filename=info.filename.encode('cp437').decode('utf-8')
            except UnicodeDecodeError:pass
        z.writestr(info,data)
    for p in dex.glob('*.dex'):z.write(p,p.name,compress_type=zipfile.ZIP_DEFLATED)
run(sdk/'zipalign','-f','-p','4',BUILD/'unsigned.apk',BUILD/'aligned.apk')
# Release signing never generates an unrelated signing identity.
# QA debug builds use a disposable certificate and cannot upgrade the release APK.
if DEBUG:
    key=BUILD/'qa-debug-keystore.p12'
    if key.exists():key.unlink()
    run('keytool','-genkeypair','-keystore',key,'-storetype','PKCS12',
        '-storepass','qa-only-password','-keypass','qa-only-password',
        '-alias','qa-debug','-keyalg','RSA','-keysize','2048','-validity','2',
        '-dname','CN=Temporary CI Test Build, O=Non Release, C=IL','-noprompt')
    alias='qa-debug';pass_argument='pass:qa-only-password'
    apk=OUT/f'Consumer_Law_Reader_{VERSION}_DEBUG_NOT_FOR_UPGRADE.apk'
else:
    signing=ROOT/'signing'
    key=signing/'law-reader-release.p12';password=signing/'key-password.txt'
    if not key.is_file() or not password.is_file():
        raise SystemExit('Missing original private signing credentials: build stopped. Do NOT generate a replacement key for an in-place upgrade.')
    alias='law-reader';pass_argument='file:'+str(password)
    apk=OUT/f'Consumer_Law_Reader_{VERSION}_Android.apk'
run('java','-jar',sdk/'lib/apksigner.jar','sign','--ks',key,'--ks-key-alias',alias,'--ks-pass',pass_argument,'--v4-signing-enabled','false','--out',apk,BUILD/'aligned.apk')
verify=subprocess.check_output(['java','-jar',str(sdk/'lib/apksigner.jar'),'verify','--verbose','--print-certs',str(apk)],text=True)
(ROOT/'evidence/apk-verification.txt').write_text(verify)
run(sdk/'zipalign','-c','-p','4',apk)
details=subprocess.check_output([str(sdk/'aapt'),'dump','badging',str(apk)],text=True)
(ROOT/'evidence/apk-badging.txt').write_text(details)
sha=hashlib.sha256(apk.read_bytes()).hexdigest()
(OUT/(apk.name+'.sha256.txt')).write_text(sha+'  '+apk.name+'\n')
print(json.dumps({'apk':str(apk),'bytes':apk.stat().st_size,'sha256':sha,'signature':'verified','min_sdk':26,'target_sdk':35}))
