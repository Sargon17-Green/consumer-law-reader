#!/usr/bin/env python3
"""Fetch an official AOSP standalone test provider supporting API 26; never bundle it in the app."""
from pathlib import Path
from urllib.request import urlopen
import base64,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
URL='https://android.googlesource.com/platform/external/chromium-webview/+/57206b62c3d8fded926bef051a219147e61c1dc1/133.0.6943.137/x86/webview.apk?format=TEXT'
SHA='605d9630c82a656617d512851cd74452c025fc4f47a7b3a711dffc14ca0d7f6a'
target=ROOT/'build/api26-test-webview.apk';target.parent.mkdir(exist_ok=True)
with urlopen(URL,timeout=120)as response:
    encoded=response.read(180000000)
data=base64.b64decode(encoded)
assert hashlib.sha256(data).hexdigest()==SHA,'AOSP WebView digest mismatch'
target.write_bytes(data)
(ROOT/'evidence').mkdir(exist_ok=True)
(ROOT/'evidence/api26-provider.json').write_text(json.dumps({'source':URL,'sha256':SHA,'version':'133.0.6943.137','minSdk':26,'scope':'Ephemeral emulator test component only; not an app dependency or user-device installation'},indent=2))
