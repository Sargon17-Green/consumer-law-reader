"""Never accept raw ADB error text as successful native test evidence."""
from pathlib import Path
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory
import hashlib,json,sys,unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import collect_android_private_evidence as collector

class AndroidEvidenceTests(unittest.TestCase):
    def collect(self,files,**options):
        def command(*args):
            key=' '.join(args)
            values={'shell getprop ro.kernel.qemu':b'1\n','root':b'restarting adbd as root\n','wait-for-device':b'','shell id -u':b'0\n','shell getprop ro.build.type':b'userdebug\n','shell getenforce':b'Enforcing\n'}
            if key in values:return CompletedProcess(args,0,values[key],b'')
            name=args[-1].rsplit('/',1)[-1]
            if args[:4]==('shell','stat','-c','%s'):
                return CompletedProcess(args,0,str(len(files[name])).encode(),b'') if name in files else CompletedProcess(args,1,b'',b'No such file')
            # Deliberately emulate exec-out's zero status on a remote cat error.
            return CompletedProcess(args,0,files.get(name,b'cat: No such file'),b'')
        with TemporaryDirectory() as directory,patch.object(collector,'command',side_effect=command):
            pdf_log=Path(directory)/'native.txt'
            pdf_log.write_text('PDF=PASS: pages=146 sha256='+options.pop('expected_hash','')+'\n')
            report=collector.collect(directory,pdf_log=pdf_log,**options)
            exported={p.name:p.read_bytes() for p in Path(directory).glob('android-*') if p.name!='android-private-artifacts.json'}
        return report,exported

    def test_missing_optional_raw_files_do_not_become_error_artifacts(self):
        data={'qa-renderer-state.json':b'{"current":"article_14"}','qa-renderer-state.png':b'\x89PNG\r\n\x1a\nexample'}
        report,files=self.collect(data,require_renderer=True)
        self.assertTrue(report['passed'],report)
        self.assertEqual(set(files),{'android-renderer-state.json','android-renderer-state.png'})
        self.assertEqual(len(report['missing']),5)

    def test_error_text_cannot_masquerade_as_png(self):
        report,files=self.collect({'qa-renderer-state.png':b'run-as: package not debuggable'})
        self.assertFalse(report['passed'])
        self.assertNotIn('android-renderer-state.png',files)

    def test_successful_pdf_export_must_match_native_validation_hash(self):
        pdf=b'%PDF-1.7\nexample\n%%EOF\n'
        report,files=self.collect({'qa-native-document.pdf':pdf},require_pdf=True,expected_hash=hashlib.sha256(pdf).hexdigest())
        self.assertTrue(report['passed'],report)
        self.assertEqual(files['android-native-document.pdf'],pdf)
        bad,_=self.collect({'qa-native-document.pdf':pdf},require_pdf=True,expected_hash='0'*64)
        self.assertFalse(bad['passed'])

    def test_required_pdf_cannot_be_missing(self):
        report,_=self.collect({},require_pdf=True)
        self.assertFalse(report['passed'])

    def test_physical_device_is_refused_before_requesting_root(self):
        with TemporaryDirectory() as directory,patch.object(collector,'command',return_value=CompletedProcess([],0,b'0\n',b'')) as command:
            report=collector.collect(directory)
        self.assertFalse(report['passed'])
        self.assertEqual(command.call_count,1)

if __name__=='__main__':unittest.main()
