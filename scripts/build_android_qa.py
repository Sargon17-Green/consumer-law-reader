#!/usr/bin/env python3
"""Build a separate platform Instrumentation APK using the app's disposable CI key."""
from pathlib import Path
import subprocess,zipfile
ROOT=Path(__file__).resolve().parents[1]
TOOLS=ROOT/'.toolchain';SDK=TOOLS/'build-tools-36.0.0/android-16'
ANDROID=TOOLS/'platforms-android-36/android-36/android.jar'
BUILD=ROOT/'build/android-qa';BUILD.mkdir(parents=True,exist_ok=True)
CLASSES=BUILD/'classes';CLASSES.mkdir(exist_ok=True)
def run(*args):subprocess.run([str(x)for x in args],check=True)
run('java','-jar',TOOLS/'ecj.jar','-source','8','-target','8','-encoding','UTF-8','-warn:none','-classpath',ANDROID,'-d',CLASSES,*sorted((ROOT/'android/qa').rglob('*.java')))
run('java','-cp',SDK/'lib/d8.jar','com.android.tools.r8.D8','--min-api','26','--lib',ANDROID,'--output',BUILD,*sorted(CLASSES.rglob('*.class')))
run(SDK/'aapt2','link','-I',ANDROID,'--manifest',ROOT/'android/qa/AndroidManifest.xml','-A',ROOT/'tests/fixtures','-o',BUILD/'resources.apk')
with zipfile.ZipFile(BUILD/'resources.apk') as src,zipfile.ZipFile(BUILD/'unsigned.apk','w') as dst:
 for info in src.infolist():dst.writestr(info,src.read(info))
 dst.write(BUILD/'classes.dex','classes.dex')
run(SDK/'zipalign','-f','4',BUILD/'unsigned.apk',BUILD/'aligned.apk')
run('java','-jar',SDK/'lib/apksigner.jar','sign','--ks',ROOT/'build/qa-debug-keystore.p12','--ks-key-alias','qa-debug','--ks-pass','pass:qa-only-password','--v4-signing-enabled','false','--out',BUILD/'reader-qa.apk',BUILD/'aligned.apk')
