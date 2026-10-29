"""Regression tests for the generated iPhone-capable browser application.

Run only after: python scripts/build_web.py
The tests do not claim real-device Safari verification or legal text accuracy.
"""
from pathlib import Path
import json
import unittest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"


class WebPagesReleaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html_path = DIST / "index.html"
        if not cls.html_path.exists():
            raise AssertionError("Build web app first: python scripts/build_web.py")
        cls.html = cls.html_path.read_text(encoding="utf-8")
        cls.soup = BeautifulSoup(cls.html, "lxml")
        cls.manifest = json.loads((DIST / "manifest.webmanifest").read_text(encoding="utf-8"))

    def test_original_law_present_in_built_document(self):
        self.assertGreater(self.html_path.stat().st_size, 9_000_000)
        self.assertIsNotNone(self.soup.select_one("#frame"))
        self.assertIsNotNone(self.soup.select_one("#index_content"))

    def test_iphone_standalone_metadata(self):
        viewport = self.soup.find("meta", attrs={"name": "viewport"})
        self.assertIsNotNone(viewport, "iPhone requires width=device-width")
        self.assertIn("width=device-width", viewport.get("content", ""))
        apple = self.soup.find("meta", attrs={"name": "apple-mobile-web-app-capable"})
        self.assertIsNotNone(apple)
        self.assertEqual(apple.get("content"), "yes")
        self.assertIsNotNone(self.soup.find("link", rel="apple-touch-icon"))
        self.assertIsNotNone(self.soup.find("link", rel="manifest"))

    def test_pwa_manifest_and_local_assets(self):
        m = self.manifest
        self.assertEqual(m["lang"], "he")
        self.assertEqual(m["dir"], "rtl")
        self.assertEqual(m["display"], "standalone")
        self.assertEqual(m["start_url"], "./")
        self.assertEqual(m["scope"], "./")
        self.assertTrue(m["name"].startswith("חוק הגנת הצרכן"))
        for icon in m["icons"]:
            self.assertTrue((DIST / icon["src"]).is_file(), icon["src"])
        for name in ("mobile.css", "mobile.js", "mobile-sources.js",
                     "mobile-topics.js", "typed-index.js", "sw.js"):
            self.assertTrue((DIST / name).is_file(), name)

    def test_offline_worker_has_local_app_shell(self):
        worker = (DIST / "sw.js").read_text(encoding="utf-8")
        self.assertIn("./index.html", worker)
        self.assertIn("./mobile.css", worker)
        self.assertIn("./manifest.webmanifest", worker)
        self.assertIn("OFFLINE_READY", worker)
        self.assertIn("cache.put", worker)

    def test_ios_safe_area_and_local_install_instructions(self):
        css = (DIST / "mobile.css").read_text(encoding="utf-8")
        js = (DIST / "mobile.js").read_text(encoding="utf-8")
        self.assertIn("safe-area-inset-bottom", css)
        self.assertIn("iPhone|iPad|iPod", js)
        self.assertIn("הוספה למסך הבית", js)

    def test_publisher_is_not_government(self):
        status = self.soup.select_one("#law-editorial-status")
        self.assertIsNotNone(status)
        metadata = json.loads(status.text)
        self.assertEqual(metadata["government_product"], False)
        self.assertEqual(metadata["editor_publisher"], "סרגון 17 גרין")


if __name__ == "__main__":
    unittest.main()
