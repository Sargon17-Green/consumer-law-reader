"""Cross-platform release, legal-byte and portable-backup contracts."""
from pathlib import Path
import unittest,re,json,hashlib,xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
class MobileContracts(unittest.TestCase):
    def test_versions_and_package_identity(self):
        version=(ROOT/'VERSION').read_text().strip();core=(ROOT/'web/mobile-core.js').read_text();spec=(ROOT/'ios/project.yml').read_text()
        manifest=ET.parse(ROOT/'android/AndroidManifest.xml').getroot();ns='{http://schemas.android.com/apk/res/android}'
        self.assertEqual(manifest.get('package'),'il.org.lawreader.consumer')
        self.assertEqual(manifest.get(ns+'versionName'),version)
        self.assertIn("const VERSION = '"+version+"'",core)
        self.assertIn('MARKETING_VERSION: "'+version.split('-')[0]+'"',spec)
        self.assertIn('CURRENT_PROJECT_VERSION: "'+manifest.get(ns+'versionCode')+'"',spec)
        self.assertEqual(manifest.find('uses-sdk').get(ns+'minSdkVersion'),'26')
        self.assertIn('iOS: "16.0"',spec)
        self.assertNotIn('התשמ\\"א',spec,'A YAML single-quoted display name must not contain a literal backslash')
    def test_exact_legal_source_and_unchanged_editorial_date(self):
        self.assertEqual(hashlib.sha256((ROOT/'original/Consumer_Protection_Law.html').read_bytes()).hexdigest(),'de5240a877dd3830ec9ac80f8bc60bf001882b6e36e8615b991d7defcd8e2ed9')
        self.assertEqual(json.loads((ROOT/'metadata/editorial_status.json').read_text())['law_text_last_verified_on'],'2026-10-28')
    def test_shared_restore_and_no_prefix_wide_native_restore(self):
        for path in ['ios/ConsumerLawReader/ConsumerLawReaderApp.swift','android/src/il/org/lawreader/consumer/MainActivity.java']:
            value=(ROOT/path).read_text();self.assertIn('lawSettings.prepareImport',value);self.assertIn('lawSettings.applyImport',value)
            self.assertNotIn("key.startsWith('law-')",value)
    def test_public_reader_is_separate_from_existing_alpha(self):
        url='https://sargon17-green.github.io/consumer-law-reader/reader/'
        for path in ['ios/ConsumerLawReader/ConsumerLawReaderApp.swift','android/src/il/org/lawreader/consumer/MainActivity.java','web/mobile.js']:
            self.assertIn(url,(ROOT/path).read_text())
