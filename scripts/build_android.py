#!/usr/bin/env python3
"""Build and sign the offline APK with pinned Android command-line tools (Linux)."""
from pathlib import Path
import os,subprocess,zipfile,json,hashlib,shutil,sys
from android_build_inputs import fingerprints
from bundled_assets import zip_members
ROOT=Path(__file__).resolve().parents[1]
VERSION=(ROOT/'VERSION').read_text().strip()
QA_ISOLATED='--qa-isolated' in sys.argv
DEBUG='--debug' in sys.argv or QA_ISOLATED
UNSIGNED='--unsigned' in sys.argv
if DEBUG and UNSIGNED:raise SystemExit('Select only one of --debug, --unsigned and --qa-isolated')
if QA_ISOLATED and '--debug' in sys.argv:raise SystemExit('Use --qa-isolated alone; it implies disposable debug signing')
TOOLS=Path(os.environ.get('LAW_ANDROID_TOOLS',str(ROOT/'.toolchain'))).resolve()
BUILD=ROOT/'build';BUILD.mkdir(exist_ok=True)
OUT=ROOT/('qa-isolated-build' if QA_ISOLATED else 'unsigned-build' if UNSIGNED else 'debug-build' if DEBUG else 'release');OUT.mkdir(exist_ok=True)
sdk=TOOLS/'build-tools-36.0.0/android-16'
android=TOOLS/'platforms-android-36/android-36/android.jar'
def run(*args):subprocess.run([str(a) for a in args],check=True,cwd=ROOT)
if not android.exists() or not (sdk/'aapt2').exists():
    raise SystemExit('First run: python3 scripts/fetch_tools.py')
run(sys.executable,ROOT/'scripts/build_web.py')
# The canonical main endpoint is deliberately not published until protected
# branch checks pass. Only QA's generated dist/ assets use this pinned snapshot;
# product source web/law-update.js is never edited.
QA_MANIFEST_REF='5b0e537420a1c9eb968a5d1a66af00f17d27f7c3'
if QA_ISOLATED:
    rendered=ROOT/'dist/law-update.js'
    source_js=rendered.read_text(encoding='utf-8')
    old='https://raw.githubusercontent.com/Sargon17-Green/consumer-law-reader/main/metadata/law_update_manifest.json'
    new='https://raw.githubusercontent.com/Sargon17-Green/consumer-law-reader/'+QA_MANIFEST_REF+'/metadata/law_update_manifest.json'
    if source_js.count(old)!=1:raise SystemExit('QA generated JS endpoint contract changed')
    rendered.write_text(source_js.replace(old,new,1),encoding='utf-8')
    # The generated HTML CSP pins the same full endpoint; QA must patch
    # that authorization in its temporary asset copy, not in build_web.py.
    page=ROOT/'dist/index.html'
    html=page.read_text(encoding='utf-8')
    occurrences=html.count(old)
    if not 1<=occurrences<=3:raise SystemExit('QA rendered CSP endpoint contract changed: '+str(occurrences))
    page.write_text(html.replace(old,new),encoding='utf-8')
classes=BUILD/'classes';dex=BUILD/'dex'
for p in [classes,dex]:
    if p.exists():shutil.rmtree(p)
    p.mkdir()
java_sources=ROOT/'android/src'
if QA_ISOLATED:
    # Copy Java sources to a throwaway build path: QA telemetry must never be
    # compiled into the public APK, nor mutate the checked-in product sources.
    java_sources=BUILD/'qa-java-sources'
    if java_sources.exists():shutil.rmtree(java_sources)
    shutil.copytree(ROOT/'android/src',java_sources)
    main=java_sources/'il/org/lawreader/consumer/MainActivity.java'
    source=main.read_text(encoding='utf-8')
    for old,new in (
        ('if ("GET".equals(request.getMethod()) && isApprovedDateSource(uri)) return dateResponse(uri);',
         '''if ("GET".equals(request.getMethod()) && isApprovedDateSource(uri)) {
                        if ("raw.githubusercontent.com".equals(uri.getHost()) && "/Sargon17-Green/consumer-law-reader/main/metadata/law_update_manifest.json".equals(uri.getPath()))
                            android.util.Log.i("LAW_QA_REVISION","REQUEST");
                        return dateResponse(uri);
                    }'''),
        ('if("true".equals(result)){ready=true;return;}',
         'if("true".equals(result)){ready=true;android.util.Log.i("LAW_QA_REVISION","READER_READY");return;}'),
        ('return new WebResourceResponse("application/json","UTF-8",200,"OK",headers,new ByteArrayInputStream(bytes));',
         '''if (uri.getPath()!=null && uri.getPath().endsWith("/metadata/law_update_manifest.json"))
                android.util.Log.i("LAW_QA_REVISION","RESPONSE_200");
            return new WebResourceResponse("application/json","UTF-8",200,"OK",headers,new ByteArrayInputStream(bytes));'''),
        ('if (ready) web.evaluateJavascript("window.LawUpdate && window.LawUpdate.check()", null);',
         '''if (ready) {
                android.util.Log.i("LAW_QA_REVISION","RESUME_CHECK");
                web.evaluateJavascript("window.LawUpdate && window.LawUpdate.check()", null);
            }''')
    ):
        if source.count(old)!=1:raise SystemExit('QA instrumentation source contract changed: '+old)
        source=source.replace(old,new,1)
    old_path='/Sargon17-Green/consumer-law-reader/main/metadata/law_update_manifest.json'
    qa_path='/Sargon17-Green/consumer-law-reader/'+QA_MANIFEST_REF+'/metadata/law_update_manifest.json'
    if source.count(old_path)!=2:
        raise SystemExit('QA Java allowlist and logging path contract changed')
    source=source.replace(old_path,qa_path)
    # QA only: allow a single loopback ADB DevTools session to assert the
    # actual rendered legal text and synthetic update-warning banner.
    # This is NEVER compiled into the original release Java sources.
    debug_anchor='        web = new WebView(this);'
    if source.count(debug_anchor)!=1:
        raise SystemExit('Cannot locate isolated WebView debugging insertion point')
    source=source.replace(debug_anchor,
        '        WebView.setWebContentsDebuggingEnabled(true);\\n'+debug_anchor,1)
    main.write_text(source,encoding='utf-8')
run('java','-jar',TOOLS/'ecj.jar','-source','8','-target','8','-encoding','UTF-8','-warn:none','-classpath',android,'-d',classes,*sorted(java_sources.rglob('*.java')))
run('java','-cp',sdk/'lib/d8.jar','com.android.tools.r8.D8','--min-api','26','--lib',android,'--output',dex,*sorted(classes.rglob('*.class')))
run(sdk/'aapt2','compile','--dir',ROOT/'android/res','-o',BUILD/'resources.zip')
assets=BUILD/'assets'
if assets.exists():shutil.rmtree(assets)
shutil.copytree(ROOT/'dist',assets/'www')
manifest=ROOT/'android/AndroidManifest.xml'
if QA_ISOLATED:
    # The public release identity and manifest must remain byte-for-byte intact.
    # Android resolves absolute component classes from the original Java package.
    original=manifest.read_text(encoding='utf-8')
    qa=original
    for old,new in (
        ('package="il.org.lawreader.consumer"', 'package="il.org.lawreader.consumer.qa"'),
        ('android:name=".MainActivity"', 'android:name="il.org.lawreader.consumer.MainActivity"'),
        ('android:name=".AttachmentProvider"', 'android:name="il.org.lawreader.consumer.AttachmentProvider"'),
        ('android:authorities="il.org.lawreader.consumer.attachments"',
         'android:authorities="il.org.lawreader.consumer.qa.attachments"'),
        ('android:label="חוק הגנת הצרכן, התשמ&quot;א–1981"',
         'android:label="חוק הגנת הצרכן, התשמ&quot;א–1981 QA"'),
    ):
        if qa.count(old)!=1:raise SystemExit('Unexpected canonical Android manifest: '+old)
        qa=qa.replace(old,new,1)
    manifest=BUILD/'AndroidManifest.qa-isolated.xml'
    manifest.write_text(qa,encoding='utf-8')
run(sdk/'aapt2','link','-I',android,'--manifest',manifest,'-A',assets,'-0','doc','-o',BUILD/'resource-package.apk',BUILD/'resources.zip')
# aapt2 emits UTF-8 asset names without the ZIP UTF-8 flag. Normalize before
# Python writes the central directory, otherwise Hebrew names become mojibake.
with zipfile.ZipFile(BUILD/'resource-package.apk','r') as source, zipfile.ZipFile(BUILD/'unsigned.apk','w') as z:
    for name,info in zip_members(source).items():
        data=source.read(info)
        info.filename=name
        z.writestr(info,data)
    for p in dex.glob('*.dex'):z.write(p,p.name,compress_type=zipfile.ZIP_DEFLATED)
run(sdk/'zipalign','-f','-p','4',BUILD/'unsigned.apk',BUILD/'aligned.apk')
if UNSIGNED:
    apk=OUT/f'Consumer_Law_Reader_{VERSION}_UNSIGNED_NOT_INSTALLABLE.apk'
    shutil.copy2(BUILD/'aligned.apk',apk)
    sha=hashlib.sha256(apk.read_bytes()).hexdigest()
    (OUT/(apk.name+'.sha256.txt')).write_text(sha+'  '+apk.name+'\n')
    print(json.dumps({'apk':str(apk),'sha256':sha,'signature':'UNSIGNED; requires original release identity'}))
    sys.exit(0)
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
    apk=OUT/f'Consumer_Law_Reader_{VERSION}_SIDE_BY_SIDE_QA.apk' if QA_ISOLATED else OUT/f'Consumer_Law_Reader_{VERSION}_DEBUG_NOT_FOR_UPGRADE.apk'
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
if QA_ISOLATED:
    package_line=next((line for line in details.splitlines() if line.startswith('package: ')), '')
    if "name='il.org.lawreader.consumer.qa'" not in package_line:
        raise SystemExit('Refusing unsafe QA artifact with public package identity: '+package_line)
    # Ensure the packaged content provider cannot collide with the release.
    xmltree=subprocess.check_output([str(sdk/'aapt'),'dump','xmltree',str(apk),'AndroidManifest.xml'],text=True)
    if 'il.org.lawreader.consumer.qa.attachments' not in xmltree:
        raise SystemExit('QA content provider authority was not isolated')
    if 'il.org.lawreader.consumer.attachments"' in xmltree:
        raise SystemExit('Public provider authority leaked into isolated QA manifest')
    (OUT/'QA_ISOLATION_VERIFIED.json').write_text(json.dumps({
        'schema':1,'sourceManifestSHA256':hashlib.sha256((ROOT/'android/AndroidManifest.xml').read_bytes()).hexdigest(),
        'qaPackage':'il.org.lawreader.consumer.qa',
        'qaProviderAuthority':'il.org.lawreader.consumer.qa.attachments',
        'publicPackageUntouched':'il.org.lawreader.consumer',
        'signedWithDisposableDebugKey':True,
        'qaManifestPinnedCommit':QA_MANIFEST_REF,
        'qaOnlyFixedURL':True,
        'qaWebViewRemoteDebuggingEnabled':True,
        'installDoesNotReplacePublicApp':True
    },indent=2))
(ROOT/'evidence/apk-badging.txt').write_text(details)
sha=hashlib.sha256(apk.read_bytes()).hexdigest()
if DEBUG:
    (ROOT/'evidence/android-debug-inputs.json').write_text(json.dumps({'schema':1,'apkSHA256':sha,'inputs':fingerprints(ROOT)},indent=2))
(OUT/(apk.name+'.sha256.txt')).write_text(sha+'  '+apk.name+'\n')
print(json.dumps({'apk':str(apk),'bytes':apk.stat().st_size,'sha256':sha,'signature':'verified','min_sdk':26,'target_sdk':36,'qa_isolated':QA_ISOLATED}))
