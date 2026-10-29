"""Static guarantees for the native iOS reader.

The real Swift/Xcode compilation is performed by .github/workflows/ios-ci.yml
on macOS. This file is intentionally runnable in ordinary Python environments.
"""
from pathlib import Path
import json
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
IOS = ROOT / "ios"
SOURCE = (IOS / "ConsumerLawReader/ConsumerLawReaderApp.swift").read_text(encoding="utf-8")
SPEC = (IOS / "project.yml").read_text(encoding="utf-8")


class IOSNativeSourceQA(unittest.TestCase):
    def test_genuine_native_app_and_sandboxed_local_law(self):
        for token in ("@main", "struct ConsumerLawReaderApp: App",
                      "WKWebView", "loadFileURL", "allowingReadAccessTo",
                      'subdirectory: "dist"', "NoRemoteLawResourcesV1"):
            self.assertIn(token, SOURCE)
        self.assertIn('url-filter":"^https?://', SOURCE)

    def test_native_ios_features(self):
        for token in ("UIActivityViewController", "UIPrintInteractionController",
                      "UIPasteboard.general", "fileImporter(",
                      "startAccessingSecurityScopedResource",
                      "confirmationDialog(", "importBackup(result:",
                      "exportSettings()", "shareCurrentSection()"):
            self.assertIn(token, SOURCE)

    def test_no_persisted_secret_or_unconsented_export(self):
        self.assertNotIn("api_key", SOURCE.lower())
        self.assertNotIn("password =", SOURCE.lower())
        self.assertIn("pendingSettings", SOURCE)
        self.assertIn("confirmImport = true", SOURCE)
        self.assertIn('key.startsWith("law-")', SOURCE)

    def test_dist_resource_folder_is_bundled(self):
        self.assertRegex(SPEC, r"- path: \.\./dist\s+type: folder\s+buildPhase: resources")
        self.assertIn("ASSETCATALOG_COMPILER_APPICON_NAME: AppIcon", SPEC)
        self.assertIn("PRODUCT_BUNDLE_IDENTIFIER:", SPEC)
        self.assertIn("CODE_SIGN_STYLE: Automatic", SPEC)

    def test_icon_catalog_and_signing_script(self):
        catalog = IOS / "ConsumerLawReader/Assets.xcassets/AppIcon.appiconset/Contents.json"
        data = json.loads(catalog.read_text(encoding="utf-8"))
        self.assertEqual(data["images"][0]["size"], "1024x1024")
        script = (IOS / "scripts/archive_for_testflight.sh").read_text()
        self.assertIn("APPLE_TEAM_ID", script)
        self.assertIn("IOS_BUNDLE_ID", script)
        self.assertIn("-allowProvisioningUpdates", script)
        self.assertIn("archive", script)

    def test_built_law_is_full_original(self):
        html = ROOT / "dist/index.html"
        if not html.exists():
            self.skipTest("Build web bundle first")
        self.assertGreater(html.stat().st_size, 9_000_000)


if __name__ == "__main__":
    unittest.main()
