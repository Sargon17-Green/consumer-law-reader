#!/usr/bin/env python3
"""Read only known QA files via authorized root on an isolated userdebug emulator."""
from pathlib import Path
import argparse,hashlib,json,re,subprocess,sys

PACKAGE='il.org.lawreader.consumer'
FILES={'qa-print-ready.json':'android-print-ready.json','qa-print-ready.png':'android-print-ready.png','qa-system-ui.json':'android-system-ui.json','qa-failure.png':'android-failure-at-assertion.png','qa-native-document.pdf':'android-native-document.pdf','qa-renderer-state.json':'android-renderer-state.json','qa-renderer-state.png':'android-renderer-state.png'}

def command(*args):
    return subprocess.run(['adb',*args],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)

def collect(output,require_pdf=False,pdf_log=None,require_renderer=False):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    report={'schema':1,'scope':'Known QA files only; emulator userdebug ADB root after the functional flow; production debuggable flag is unchanged','files':{},'missing':{},'errors':[]}
    try:
        report['qemu']=command('shell','getprop','ro.kernel.qemu').stdout.decode().strip()
        if report['qemu']!='1':raise RuntimeError('This collector is restricted to an isolated emulator')
        root=command('root');report['adbRoot']=(root.stdout+root.stderr).decode(errors='replace')[:1000].strip()
        if root.returncode:raise RuntimeError('Emulator does not allow the requested QA evidence access')
        command('wait-for-device').check_returncode()
        report['adbUid']=command('shell','id','-u').stdout.decode().strip()
        if report['adbUid']!='0':raise RuntimeError('ADB root was not actually granted by this emulator')
        report['buildType']=command('shell','getprop','ro.build.type').stdout.decode().strip()
        report['selinux']=command('shell','getenforce').stdout.decode().strip()
        if report['selinux']!='Enforcing':raise RuntimeError('Expected unchanged SELinux enforcing policy')
        for name,target in FILES.items():
            result=command('exec-out','cat','/data/user/0/'+PACKAGE+'/files/'+name)
            if result.returncode:
                report['missing'][name]=(result.stderr+result.stdout).decode(errors='replace')[:200].strip();continue
            body=result.stdout
            if not body or len(body)>32*1024*1024:raise ValueError('Invalid QA artifact size: '+name)
            if name.endswith('.png') and not body.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Invalid PNG bytes: '+name)
            if name.endswith('.json'):json.loads(body.decode('utf-8'))
            if name.endswith('.pdf') and (not body.startswith(b'%PDF-') or b'%%EOF' not in body[-1024:]):raise ValueError('Invalid PDF bytes')
            (output/target).write_bytes(body)
            report['files'][target]={'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest()}
        if require_renderer and not {'android-renderer-state.json','android-renderer-state.png'} <= report['files'].keys():raise ValueError('Successful renderer recovery must export actual JSON and PNG evidence')
        if require_pdf:
            pdf=report['files'].get('android-native-document.pdf')
            if not pdf:raise ValueError('A successful PDF test must export actual PDF evidence')
            expected=re.findall(r'PDF=PASS:[^\n]*sha256=([0-9a-f]{64})',Path(pdf_log).read_text()) if pdf_log else []
            if not expected or expected[-1]!=pdf['sha256']:raise ValueError('Collected PDF differs from the native PdfRenderer/MessageDigest report')
    except Exception as error:
        report['errors'].append(str(error))
    report['passed']=not report['errors']
    (output/'android-private-artifacts.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'files':len(report['files']),'errors':report['errors']}))
    return report

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='evidence');parser.add_argument('--require-pdf',action='store_true');parser.add_argument('--pdf-log');parser.add_argument('--require-renderer-state',action='store_true');args=parser.parse_args()
    sys.exit(0 if collect(args.output,args.require_pdf,args.pdf_log,args.require_renderer_state)['passed'] else 1)
