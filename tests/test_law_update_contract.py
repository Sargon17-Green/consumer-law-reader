"""Regression contract for editorially published law revisions.

No authoritative legal amendment is inferred from timestamps or Git history.
This test verifies the app's version protocol, not legislative accuracy.
"""
import hashlib
import json
import re
import unittest
from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "original/Consumer_Protection_Law.html"
EDITORIAL = ROOT / "metadata/editorial_status.json"
REMOTE = ROOT / "metadata/law_update_manifest.json"
EXPECTED_LAW = "israel-consumer-protection-law-1981"
BASE_SOURCE_SHA = "de5240a877dd3830ec9ac80f8bc60bf001882b6e36e8615b991d7defcd8e2ed9"
DATA_URL = ("https://raw.githubusercontent.com/Sargon17-Green/consumer-law-reader/"
            "main/metadata/law_update_manifest.json")


class LawUpdateContractTest(unittest.TestCase):
    def test_baseline_versions_are_editor_approved_and_separate(self):
        local = json.loads(EDITORIAL.read_text(encoding="utf-8"))
        live = json.loads(REMOTE.read_text(encoding="utf-8"))
        self.assertEqual(local["law_id"], EXPECTED_LAW)
        self.assertEqual(live["law_id"], EXPECTED_LAW)
        self.assertEqual(live["schema_version"], 1)
        self.assertEqual(live["revision_status"], "editor_approved")
        self.assertEqual(local["law_revision_sequence"], 1)
        self.assertEqual(live["current_revision_sequence"], local["law_revision_sequence"])
        self.assertEqual(live["published_revision_sequence_by_platform"], {"android": 1, "ios": 0, "web": 1})
        self.assertEqual(local["law_text_last_amended_on"], "2026-09-30")
        self.assertEqual(live["law_text_last_amended_on"], local["law_text_last_amended_on"])
        self.assertEqual(local["law_text_last_verified_on"], "2026-10-28")
        self.assertEqual(live["law_text_last_verified_on"], local["law_text_last_verified_on"])
        self.assertEqual(live["next_scheduled_change_on"], "2027-03-22")
        self.assertEqual(live["next_scheduled_change_on"], local["next_scheduled_change_on"])
        self.assertGreaterEqual(live["current_revision_sequence"], 1)
        for available in live["published_revision_sequence_by_platform"].values():
            self.assertLessEqual(available, live["current_revision_sequence"])
        self.assertNotEqual(local["law_text_last_amended_on"], local["law_text_last_verified_on"])
        self.assertGreater(live["next_scheduled_change_on"], live["law_text_last_verified_on"])

    def test_legal_source_was_not_changed(self):
        self.assertEqual(hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(), BASE_SOURCE_SHA)

    def test_compiled_mobile_and_browser_bundles_embed_local_revision(self):
        output = ROOT / "dist"
        self.assertTrue((output / "law-update.js").is_file())
        soup = BeautifulSoup((output / "index.html").read_text(encoding="utf-8"), "lxml")
        embedded = json.loads(soup.select_one("#law-editorial-status").text)
        self.assertEqual(embedded["law_revision_sequence"], 1)
        self.assertEqual(embedded["law_text_last_amended_on"], "2026-09-30")
        self.assertIsNotNone(soup.select_one("#law-update-banner[hidden][role=alert]"))
        self.assertIn("law-update.js", (output / "sw.js").read_text(encoding="utf-8"))
        self.assertIn(DATA_URL, (output / "index.html").read_text(encoding="utf-8"))

    def test_exact_urls_and_resume_hooks_only(self):
        android = (ROOT / "android/src/il/org/lawreader/consumer/MainActivity.java").read_text(encoding="utf-8")
        ios_policy = (ROOT / "ios/ConsumerLawReader/ReaderPolicy.swift").read_text(encoding="utf-8")
        ios_app = (ROOT / "ios/ConsumerLawReader/ConsumerLawReaderApp.swift").read_text(encoding="utf-8")
        web = (ROOT / "web/mobile.js").read_text(encoding="utf-8")
        engine = (ROOT / "web/law-update.js").read_text(encoding="utf-8")
        self.assertIn("/Sargon17-Green/consumer-law-reader/main/metadata/law_update_manifest.json", android)
        self.assertIn("/Sargon17-Green/consumer-law-reader/main/metadata/law_update_manifest.json", ios_policy)
        self.assertIn("window.LawUpdate && window.LawUpdate.check()", android)
        self.assertIn("window.LawUpdate && window.LawUpdate.check()", ios_app)
        self.assertIn("window.LawUpdate?.install()", web)
        self.assertIn("visibilitychange", engine)
        self.assertIn("pageshow", engine)
        self.assertIn("cache: 'no-store'", engine)
        self.assertIn("חובה לעדכן את נוסח החוק", (ROOT / "web/mobile-shell.html").read_text(encoding="utf-8"))
        self.assertIn(DATA_URL, (ROOT / "docs/LAW_UPDATE_CONTRACT_HE.md").read_text(encoding="utf-8"))
        self.assertIn(DATA_URL, (ROOT / "web/privacy.json").read_text(encoding="utf-8"))

    def test_remote_feed_is_not_executable(self):
        source = (ROOT / "web/law-update.js").read_text(encoding="utf-8")
        self.assertNotIn("eval(", source)
        self.assertNotIn("innerHTML", source)
        self.assertNotIn("window.location =", source)
        self.assertIn("referrerPolicy: 'no-referrer'", source)
        self.assertIn("remote.current_revision_sequence", source)
        self.assertIn("remote.published_revision_sequence_by_platform", source)


if __name__ == "__main__":
    unittest.main()
