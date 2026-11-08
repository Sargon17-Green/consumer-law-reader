#!/usr/bin/env python3
"""Verify deployed reader bytes, preserved public files and the original APK."""
from pathlib import Path
import argparse
import hashlib
import json
import time
from urllib.parse import quote
from urllib.request import Request, urlopen

BASE = "https://sargon17-green.github.io/consumer-law-reader/"
APK_URL = "https://raw.githubusercontent.com/Sargon17-Green/consumer-law-reader/main/downloads/latest.apk"
APK_SHA256 = "2772e3d8195de2d9a66edc8cdbc9e0940ac71f8cb55f1597dcc7c122120101af"
MAX_BYTES = 50 * 1024 * 1024


def prepare(site, commit, apk):
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise ValueError("Expected an immutable source commit")
    site = Path(site)
    checks = []
    for path in sorted(site.rglob("*")):
        relative = path.relative_to(site)
        if path.is_file() and not any(part.startswith(".") for part in relative.parts):
            checks.append({"url": BASE + quote(relative.as_posix(), safe="/"),
                           "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    if not checks or not any(c["url"] == BASE + "reader/index.html" for c in checks):
        raise ValueError("Missing public reader")
    if hashlib.sha256(Path(apk).read_bytes()).hexdigest() != APK_SHA256:
        raise ValueError("Original signed public APK changed")
    checks.append({"url": APK_URL, "sha256": APK_SHA256})
    return {"schema": 1, "sourceCommit": commit, "checks": checks}


def verify_check(check):
    request = Request(check["url"], headers={"Accept-Encoding": "identity",
                                            "Cache-Control": "no-cache",
                                            "User-Agent": "consumer-law-reader-deployment-verification"})
    with urlopen(request, timeout=15) as response:
        if response.status != 200 or response.geturl() != check["url"]:
            raise ValueError("Unexpected status or redirected public asset: " + check["url"])
        if response.headers.get("Content-Encoding", "identity") != "identity":
            raise ValueError("Expected exact uncompressed public bytes")
        body = response.read(MAX_BYTES + 1)
    if len(body) > MAX_BYTES:
        raise ValueError("Public file exceeds verification bound")
    digest = hashlib.sha256(body).hexdigest()
    if digest != check["sha256"]:
        raise ValueError("Public digest mismatch: " + check["url"])
    return {"url": check["url"], "sha256": digest, "bytes": len(body)}


def verify(expected, output, timeout=300):
    if expected.get("schema") != 1 or not expected.get("checks"):
        raise ValueError("Missing deployment expectations")
    pending = list(expected["checks"])
    results = []
    errors = {}
    deadline = time.monotonic() + timeout
    while pending:
        remaining = []
        for check in pending:
            try:
                results.append(verify_check(check))
                errors.pop(check["url"], None)
            except Exception as error:
                remaining.append(check)
                errors[check["url"]] = str(error)
        pending = remaining
        report = {"schema": 1, "sourceCommit": expected["sourceCommit"],
                  "passed": not pending, "verified": results, "errors": errors}
        Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        if not pending:
            return report
        if time.monotonic() >= deadline:
            raise RuntimeError("Public deployment verification failed: " + json.dumps(errors))
        time.sleep(5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "verify"])
    parser.add_argument("--site", default="build/public-site")
    parser.add_argument("--commit")
    parser.add_argument("--apk", default="downloads/latest.apk")
    parser.add_argument("--expectations", default="evidence/public-site-expectations.json")
    parser.add_argument("--output", default="evidence/public-site-http-verification.json")
    args = parser.parse_args()
    if args.mode == "prepare":
        result = prepare(args.site, args.commit, args.apk)
        Path(args.expectations).write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(json.dumps({"sourceCommit": args.commit, "publicFiles": len(result["checks"])}))
    else:
        result = verify(json.loads(Path(args.expectations).read_text(encoding="utf-8")), args.output)
        print(json.dumps({"sourceCommit": result["sourceCommit"], "verifiedFiles": len(result["verified"]), "passed": result["passed"]}))
