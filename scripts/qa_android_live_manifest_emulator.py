#!/usr/bin/env python3
"""Disposable emulator acceptance for the *live* canonical Android law manifest.

This script is QA-only. It installs a separate package into a fresh emulator,
reads the app's purpose-built QA log markers, then uninstalls that package.
It must never install/uninstall/touch the public Android package.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evidence" / "law-update-emulator"
OUT.mkdir(parents=True, exist_ok=True)
QA_PACKAGE = "il.org.lawreader.consumer.qa"
PUBLIC_PACKAGE = "il.org.lawreader.consumer"
ACTIVITY = QA_PACKAGE + "/il.org.lawreader.consumer.MainActivity"
MANIFEST = (
    "https://raw.githubusercontent.com/Sargon17-Green/"
    "consumer-law-reader/main/metadata/law_update_manifest.json"
)
MARKERS = ("REQUEST", "RESPONSE_200", "READER_READY", "RESUME_CHECK")


def adb(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["adb", *args],
        text=True,
        capture_output=True,
        check=check,
        timeout=30,
    )


def marker_snapshot() -> tuple[dict[str, int], str]:
    raw = adb("logcat", "-d", "-v", "brief", "-s",
              "LAW_QA_REVISION:I", "*:S").stdout
    counts = {name: 0 for name in MARKERS}
    for line in raw.splitlines():
        # Count only tagged QA Java events; never infer 200 from a URL or text.
        match = re.search(r"LAW_QA_REVISION(?:\(\s*\d+\))?\s*:\s*(REQUEST|RESPONSE_200|READER_READY|RESUME_CHECK)(?:\s|$)", line)
        if match:
            counts[match.group(1)] += 1
    return counts, raw


def await_events(phase: str, required: tuple[str, ...], seconds: int = 100) -> dict[str, int]:
    deadline = time.monotonic() + seconds
    latest: dict[str, int] = {}
    while time.monotonic() < deadline:
        latest, raw = marker_snapshot()
        if all(latest[k] >= 1 for k in required):
            (OUT / (phase + "-logcat.txt")).write_text(raw, encoding="utf-8")
            return latest
        time.sleep(2)
    (OUT / (phase + "-logcat.txt")).write_text(raw, encoding="utf-8")
    raise AssertionError(f"{phase} lacked {required}; observed {latest}")


def main() -> None:
    apk_list = list((ROOT / "qa-isolated-build").glob("*_SIDE_BY_SIDE_QA.apk"))
    assert len(apk_list) == 1, f"Expected a single disposable QA APK, got {apk_list}"
    apk = apk_list[0]
    evidence = json.loads(
        (ROOT / "qa-isolated-build" / "QA_ISOLATION_VERIFIED.json").read_text()
    )
    assert evidence["qaPackage"] == QA_PACKAGE
    assert evidence["publicPackageUntouched"] == PUBLIC_PACKAGE
    assert evidence["qaUsesCanonicalLiveManifest"] is True
    assert evidence["qaManifestURL"] == MANIFEST
    assert evidence["signedWithDisposableDebugKey"] is True
    assert hashlib.sha256(apk.read_bytes()).hexdigest() == (
        ROOT / "qa-isolated-build" / (apk.name + ".sha256.txt")
    ).read_text().split()[0]
    assert not adb("shell", "pm", "path", PUBLIC_PACKAGE).stdout.strip(), (
        "Refuse to use an emulator with the public app installed"
    )
    (OUT / "apk-sha256.txt").write_text(hashlib.sha256(apk.read_bytes()).hexdigest())
    installed = False
    report: dict[str, object] = {
        "schema": 1,
        "package": QA_PACKAGE,
        "manifest": MANIFEST,
        "publicPackageUnchanged": True,
        "realDevice": False,
        "result": "NOT_RUN",
    }
    try:
        adb("install", str(apk))
        installed = True
        adb("logcat", "-c")
        adb("shell", "am", "start", "-n", ACTIVITY)
        report["cold"] = await_events(
            "cold", ("READER_READY", "REQUEST", "RESPONSE_200")
        )
        # Clear only the QA emulator logcat buffer between phases. This
        # avoids invalid deltas from Android's ring-buffer rotation.
        adb("shell", "input", "keyevent", "KEYCODE_HOME")
        time.sleep(3)
        adb("logcat", "-c")
        adb("shell", "am", "start", "-n", ACTIVITY)
        report["resume"] = await_events(
            "resume", ("RESUME_CHECK", "REQUEST", "RESPONSE_200")
        )
        report["result"] = "PASS"
    finally:
        if installed:
            adb("uninstall", QA_PACKAGE, check=False)
        report["qaUninstalled"] = not bool(
            adb("shell", "pm", "path", QA_PACKAGE, check=False).stdout.strip()
        )
        report["publicPackageStillAbsent"] = not bool(
            adb("shell", "pm", "path", PUBLIC_PACKAGE, check=False).stdout.strip()
        )
        (OUT / "result.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        assert report["qaUninstalled"] and report["publicPackageStillAbsent"], (
            "Cleanup or public package isolation failed: " + repr(report)
        )
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
