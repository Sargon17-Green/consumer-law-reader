"""Test that the permanent APK points to the newest *installable* release."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from sync_latest_download import eligible, select_release


def release(version, date, *, prerelease=True, digest="a" * 64, asset=True, draft=False):
    return {
        "tag_name": "v" + version,
        "draft": draft,
        "prerelease": prerelease,
        "published_at": date,
        "html_url": "https://github.com/example/repo/releases/tag/v" + version,
        "assets": [{
            "name": "Consumer_Law_Reader_" + version + "_Beta_Android.apk",
            "size": 2500000,
            "digest": "sha256:" + digest,
            "browser_download_url": "https://github.com/example/asset"
        }] if asset else [],
    }


class StableDownloadSelectionTests(unittest.TestCase):
    def test_includes_betas_and_selects_highest_version(self):
        versions = [
            release("1.3.4-beta", "2026-10-28T12:00:00Z"),
            release("1.3.5-beta", "2026-10-28T13:00:00Z"),
            release("1.3.3", "2026-10-28T15:00:00Z", prerelease=False)
        ]
        self.assertEqual(select_release(versions)[3]["tag_name"], "v1.3.5-beta")

    def test_stable_wins_same_version(self):
        pre=release("1.3.6-beta", "2026-10-28T12:00:00Z")
        stable=release("1.3.6", "2026-10-28T13:00:00Z", prerelease=False)
        self.assertEqual(select_release([pre, stable])[3]["tag_name"], "v1.3.6")

    def test_skip_drafts_invalid_checksums_and_missing_apks(self):
        candidates=[
            release("3.1.0", "2026-10-28T16:00:00Z", draft=True),
            release("3.0.0", "2026-10-28T15:00:00Z", digest="INVALID"),
            release("2.5.0", "2026-10-28T14:00:00Z", asset=False),
            release("1.3.5-beta", "2026-10-28T13:00:00Z"),
        ]
        self.assertEqual(select_release(candidates)[3]["tag_name"], "v1.3.5-beta")

    def test_does_not_silently_fall_back_when_no_valid_asset(self):
        with self.assertRaises(RuntimeError):
            select_release([release("1.3.6-beta", "2026-10-28T12:00:00Z", asset=False)])

    def test_bad_version_ignored(self):
        x=release("1.3.5-beta", "2026-10-28T13:00:00Z")
        x["tag_name"]="latest"
        self.assertIsNone(eligible(x))


if __name__ == "__main__":
    unittest.main()
