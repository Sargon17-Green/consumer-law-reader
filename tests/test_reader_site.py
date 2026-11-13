from pathlib import Path
import importlib.util,tempfile,unittest
spec=importlib.util.spec_from_file_location('reader_site',Path(__file__).resolve().parents[1]/'scripts/prepare_reader_site.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
class ReaderSiteTests(unittest.TestCase):
    def test_preserves_existing_alpha_and_downloads_and_replaces_only_owned_reader(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);bundle=root/'bundle';site=root/'site';bundle.mkdir();site.mkdir()
            (site/'index.html').write_bytes(b'alpha 0.17 original public page');(site/'release.json').write_bytes(b'original public metadata');(site/'downloads').mkdir();(site/'downloads/latest.apk').write_bytes(b'original signed apk')
            (bundle/'index.html').write_bytes(b'original mobile law');(bundle/'mobile.js').write_bytes(b'js')
            before=module.manifest(site);report=module.prepare(bundle,site,'1234')
            self.assertEqual(report['existingFilesPreserved'],3);self.assertFalse(report['outsideReaderChanged'])
            self.assertEqual(module.manifest(site,True),before)
            (bundle/'mobile.js').write_bytes(b'updated');module.prepare(bundle,site,'5678')
            self.assertEqual((site/'reader/mobile.js').read_bytes(),b'updated')
            self.assertEqual(module.manifest(site,True),before)
    def test_refuses_unknown_directory_and_missing_bundle(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'site/reader').mkdir(parents=True);(root/'bundle').mkdir();(root/'bundle/index.html').write_bytes(b'law')
            with self.assertRaises(ValueError):module.prepare(root/'bundle',root/'site','1')
            self.assertTrue((root/'site/reader').is_dir())
