#!/usr/bin/env python3
"""Maintain a version-independent Android download path from PUBLIC GitHub releases.

Runs on GitHub Actions after a release or on its periodic reconciliation.
This copies only already published, signed public APK assets. No signing secrets.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPO = os.environ.get("GITHUB_REPOSITORY", "Sargon17-Green/consumer-law-reader")
TAG_VERSION = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:[-.].*)?$")
SHA256 = re.compile(r"^sha256:([0-9a-fA-F]{64})$")
FILE_NAME = re.compile(r"^Consumer_Law_Reader_.+_Android\.apk$")
MAX_BYTES = 80 * 1024 * 1024


def eligible(release):
    if release.get("draft") or not release.get("published_at"):
        return None
    tag = str(release.get("tag_name", ""))
    match = TAG_VERSION.fullmatch(tag)
    if not match:
        return None
    assets = [x for x in release.get("assets", []) if FILE_NAME.fullmatch(str(x.get("name", "")))]
    if len(assets) != 1:
        return None
    asset = assets[0]
    digest = SHA256.fullmatch(str(asset.get("digest", "")))
    if not digest or not (0 < int(asset.get("size", 0)) <= MAX_BYTES):
        return None
    return (tuple(map(int, match.groups())), not release.get("prerelease", False), release.get("published_at", ""), release, asset, digest.group(1).lower())


def select_release(releases):
    suitable = [entry for r in releases if (entry := eligible(r))]
    if not suitable:
        raise RuntimeError("No verifiable public Android APK release found")
    return max(suitable, key=lambda x: x[:3])


def run():
    response = subprocess.check_output(
        ["gh", "api", "-X", "GET", f"repos/{REPO}/releases?per_page=100"],
        text=True, timeout=60,
    )
    releases = json.loads(response)
    version, stable, published, release, asset, expected = select_release(releases)
    tag, name = release["tag_name"], asset["name"]
    folder = ROOT / "downloads"
    folder.mkdir(exist_ok=True)
    latest = folder / "latest.apk"
    metadata = folder / "latest.json"
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["gh", "release", "download", tag, "--repo", REPO, "--pattern", name, "--dir", tmp],
            check=True, timeout=180,
        )
        path = Path(tmp) / name
        assert path.is_file(), "GitHub release asset did not download"
        data = path.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        if actual != expected:
            raise RuntimeError(f"Release checksum mismatch: {actual}")
        with zipfile.ZipFile(path) as archive:
            if archive.testzip() is not None:
                raise RuntimeError("Corrupt APK archive")
            assert "AndroidManifest.xml" in archive.namelist() and "classes.dex" in archive.namelist()
        if not latest.exists() or latest.read_bytes() != data:
            latest.write_bytes(data)
    record = {
        "schema": 1,
        "version": ".".join(map(str, version)),
        "tag": tag,
        "prerelease": bool(release.get("prerelease")),
        "published_at": published,
        "asset_name": name,
        "sha256": expected,
        "release_url": release["html_url"],
        "source_asset_url": asset["browser_download_url"],
        "download_url": f"https://raw.githubusercontent.com/{REPO}/main/downloads/latest.apk",
    }
    new = json.dumps(record, ensure_ascii=False, indent=2) + "\n"
    if not metadata.exists() or metadata.read_text(encoding="utf-8") != new:
        metadata.write_text(new, encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False))
    return record


if __name__ == "__main__":
    run()
