#!/usr/bin/env python3
"""Prepare an unsigned Play bundle and a disposable, non-upgradeable QA APK.

Run after build_android.py --debug. No release signing key is read or generated.
"""
from pathlib import Path
from urllib.request import urlopen
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
import xml.etree.ElementTree as ET
from bundled_assets import zip_members
from android_build_inputs import fingerprints

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/'build'
TOOLS=Path(os.environ.get('LAW_ANDROID_TOOLS',str(ROOT/'.toolchain'))).resolve()
SDK=TOOLS/'build-tools-36.0.0/android-16'
ANDROID=TOOLS/'platforms-android-36/android-36/android.jar'
VERSION=(ROOT/'VERSION').read_text().strip()
BUNDLETOOL_VERSION='1.18.3'
BUNDLETOOL_SHA256='a099cfa1543f55593bc2ed16a70a7c67fe54b1747bb7301f37fdfd6d91028e29'
BUNDLETOOL_URL=f'https://github.com/google/bundletool/releases/download/{BUNDLETOOL_VERSION}/bundletool-all-{BUNDLETOOL_VERSION}.jar'


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def run(*args):
    return subprocess.run([str(x) for x in args],cwd=ROOT,check=True,capture_output=True,text=True).stdout


def acquire_tool():
    cache=BUILD/'tools'
    cache.mkdir(parents=True,exist_ok=True)
    jar=cache/f'bundletool-all-{BUNDLETOOL_VERSION}.jar'
    if not jar.exists():
        temporary=jar.with_suffix('.download')
        try:
            with urlopen(BUNDLETOOL_URL,timeout=45) as response,temporary.open('wb') as output:
                total=0
                while chunk:=response.read(1024*1024):
                    total+=len(chunk)
                    if total>40*1024*1024:raise ValueError('Oversized build tool download')
                    output.write(chunk)
            if sha256(temporary.read_bytes())!=BUNDLETOOL_SHA256:
                raise ValueError('Official bundletool digest mismatch')
            temporary.replace(jar)
        finally:
            temporary.unlink(missing_ok=True)
    if sha256(jar.read_bytes())!=BUNDLETOOL_SHA256:
        raise ValueError('Cached bundletool digest mismatch')
    return jar


def payload(path,prefix=''):
    with zipfile.ZipFile(path) as archive:
        result={}
        for original,entry in zip_members(archive).items():
            if entry.is_dir() or not original.startswith(prefix):continue
            name=original[len(prefix):]
            if name.startswith('dex/'):name=name[len('dex/'):]
            if name.startswith('assets/www/') or name.endswith('.dex'):
                result[name]=sha256(archive.read(entry))
        return result


def main():
    debug=ROOT/'debug-build'/f'Consumer_Law_Reader_{VERSION}_DEBUG_NOT_FOR_UPGRADE.apk'
    key=BUILD/'qa-debug-keystore.p12'
    if not debug.is_file() or not key.is_file() or not (BUILD/'resources.zip').is_file():
        raise SystemExit('First build the app with scripts/build_android.py --debug')
    inputs=json.loads((ROOT/'evidence/android-debug-inputs.json').read_text())
    if inputs.get('inputs')!=fingerprints(ROOT) or inputs.get('apkSHA256')!=sha256(debug.read_bytes()):
        raise ValueError('Stale APK inputs: rebuild the debug APK from the current source before packaging')
    stage=BUILD/'android-bundle'
    if stage.is_symlink():raise ValueError('Refusing a symlink build directory')
    if stage.exists():shutil.rmtree(stage)
    stage.mkdir()
    tool=acquire_tool()
    evidence=ROOT/'evidence';evidence.mkdir(exist_ok=True)
    unsigned=ROOT/'unsigned-build';unsigned.mkdir(exist_ok=True)
    aab=unsigned/f'Consumer_Law_Reader_{VERSION}_UNSIGNED_NOT_FOR_UPLOAD.aab'
    aab.unlink(missing_ok=True)
    proto=stage/'proto.apk'
    def link_proto(output,resources):
        run(SDK/'aapt2','link','--proto-format','--exclude-sources','-I',ANDROID,'--manifest',ROOT/'android/AndroidManifest.xml',
            '-A',BUILD/'assets','-0','doc','-o',output,resources)
    link_proto(proto,BUILD/'resources.zip')
    # Exercise identical resources compiled from a genuinely different path.
    # Absolute source paths otherwise enter resources.pb and break reproduction.
    relocated=stage/'relocated-source'
    shutil.copytree(ROOT/'android/res',relocated)
    alternate_resources=stage/'relocated-resources.zip'
    run(SDK/'aapt2','compile','--dir',relocated,'-o',alternate_resources)
    alternate_proto=stage/'relocated-proto.apk'
    link_proto(alternate_proto,alternate_resources)
    with zipfile.ZipFile(proto) as first,zipfile.ZipFile(alternate_proto) as second:
        original_entries=zip_members(first);relocated_entries=zip_members(second)
        if original_entries.keys()!=relocated_entries.keys() or any(
                first.read(info)!=second.read(relocated_entries[name]) for name,info in original_entries.items()):
            raise ValueError('Relocating identical resource sources changed the linked bundle payload')
    module=stage/'base.zip'
    with zipfile.ZipFile(proto) as source,zipfile.ZipFile(module,'w') as target:
        for name,info in sorted(zip_members(source).items()):
            if name=='AndroidManifest.xml':name='manifest/AndroidManifest.xml'
            elif name!='resources.pb' and not name.startswith(('res/','assets/','lib/')):
                raise ValueError('Unexpected proto APK entry: '+name)
            entry=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0))
            entry.compress_type=zipfile.ZIP_DEFLATED
            target.writestr(entry,source.read(info))
        for dex in sorted((BUILD/'dex').glob('*.dex')):
            entry=zipfile.ZipInfo('dex/'+dex.name,date_time=(1980,1,1,0,0,0))
            entry.compress_type=zipfile.ZIP_DEFLATED
            target.writestr(entry,dex.read_bytes())
    run('java','-jar',tool,'build-bundle','--modules='+str(module),'--output='+str(aab))
    validation=run('java','-jar',tool,'validate','--bundle='+str(aab))
    (evidence/'aab-validation.txt').write_text(validation,encoding='utf-8')
    manifest=run('java','-jar',tool,'dump','manifest','--bundle='+str(aab),'--module=base')
    (evidence/'aab-manifest.xml').write_text(manifest,encoding='utf-8')
    actual=ET.fromstring(manifest);expected=ET.parse(ROOT/'android/AndroidManifest.xml').getroot()
    ns='{http://schemas.android.com/apk/res/android}'
    for key_name in ('package',ns+'versionCode',ns+'versionName'):
        if actual.get(key_name)!=expected.get(key_name):raise ValueError('AAB identity differs: '+key_name)
    for key_name in (ns+'minSdkVersion',ns+'targetSdkVersion'):
        if actual.find('uses-sdk').get(key_name)!=expected.find('uses-sdk').get(key_name):raise ValueError('AAB OS compatibility differs')
    if payload(aab,'base/')!=payload(debug):raise ValueError('AAB code or offline assets differ from the tested APK')
    with zipfile.ZipFile(aab) as archive:
        if any(name.upper().endswith(('.SF','.RSA','.DSA','.EC')) for name in archive.namelist() if name.startswith('META-INF/')):
            raise ValueError('Candidate AAB must remain unsigned')
    apks=stage/'qa.apks'
    run('java','-jar',tool,'build-apks','--bundle='+str(aab),'--output='+str(apks),'--mode=universal',
        '--aapt2='+str(SDK/'aapt2'),'--ks='+str(key),'--ks-key-alias=qa-debug','--ks-pass=pass:qa-only-password')
    universal=ROOT/'debug-build'/f'Consumer_Law_Reader_{VERSION}_DEBUG_NOT_FOR_UPGRADE_BUNDLE.apk'
    with zipfile.ZipFile(apks) as archive:universal.write_bytes(archive.read('universal.apk'))
    if payload(universal)!=payload(debug):raise ValueError('Bundle-generated APK code or offline assets differ')
    verification=run('java','-jar',SDK/'lib/apksigner.jar','verify','--verbose','--print-certs',universal)
    debug_signature=run('java','-jar',SDK/'lib/apksigner.jar','verify','--print-certs',debug)
    signer_pattern=r'certificate SHA-256 digest: ([0-9a-fA-F]{64})'
    expected_signers={digest.lower() for digest in re.findall(signer_pattern,debug_signature)}
    actual_signers={digest.lower() for digest in re.findall(signer_pattern,verification)}
    if len(expected_signers)!=1 or actual_signers!=expected_signers or '2625ebe860cb0bfac105196b24aeedf3a948ce18c6f836478fd8ea38d0b937dc' in actual_signers:
        raise ValueError('Universal QA APK must use only the existing disposable QA identity')
    (evidence/'aab-universal-apk-signature.txt').write_text(verification,encoding='utf-8')
    run(sys.executable,ROOT/'scripts/verify_release.py','--apk',universal)
    provenance=json.loads((evidence/'content-manifest.json').read_text())
    result={'schema':1,'appVersion':VERSION,'sourceCommit':provenance.get('sourceCommit'),
            'sourceTree':provenance.get('sourceTree'),
            'sourceDirty':provenance.get('sourceDirty'),
            'bundletool':BUNDLETOOL_VERSION,'bundletoolSHA256':BUNDLETOOL_SHA256,
            'aab':aab.name,'aabSHA256':sha256(aab.read_bytes()),'aabSigned':False,
            'universalQA':universal.name,'universalQASHA256':sha256(universal.read_bytes()),
            'qaSignerSHA256':next(iter(actual_signers)),
            'exactCodeAndAssetsMatch':True,'payloadEntries':len(payload(debug)),
            'reproducibleResourcesAcrossSourcePaths':True,
            'limitations':'Unsigned AAB; disposable QA APK cannot upgrade the public release; no Play upload'}
    for artifact in (aab,universal):
        artifact.with_suffix(artifact.suffix+'.sha256.txt').write_text(sha256(artifact.read_bytes())+'  '+artifact.name+'\n')
    (evidence/'aab-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result))


if __name__=='__main__':
    try:main()
    except subprocess.CalledProcessError as error:
        print(error.stdout or '',file=sys.stderr)
        print(error.stderr or '',file=sys.stderr)
        raise
