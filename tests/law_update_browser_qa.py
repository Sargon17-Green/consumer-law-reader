"""Actual Chromium/WebView-compatible check for the GitHub law-revision banner.

Uses a mocked response at the *exact* approved HTTPS endpoint; makes no
external network requests and changes neither the law text nor preferences.
Run after scripts/build_web.py.
"""
from pathlib import Path
from urllib.parse import urlparse, unquote
from playwright.sync_api import sync_playwright
import json, mimetypes, os, shutil

ROOT = Path(__file__).resolve().parents[1]
URL = ("https://raw.githubusercontent.com/Sargon17-Green/consumer-law-reader/"
       "main/metadata/law_update_manifest.json")
remote = json.loads((ROOT / "metadata/law_update_manifest.json").read_text(encoding="utf-8"))
state = {"offline": False, "hits": 0}


def serve(route):
    url = urlparse(route.request.url)
    if route.request.url.startswith(URL) and url.path == "/Sargon17-Green/consumer-law-reader/main/metadata/law_update_manifest.json":
        state["hits"] += 1
        if state["offline"]:
            route.abort("internetdisconnected")
        else:
            route.fulfill(
                status=200, body=json.dumps(remote), content_type="application/json",
                headers={"Access-Control-Allow-Origin": "*", "Cache-Control": "no-store"}
            )
        return
    if url.hostname != "law.local":
        route.abort("internetdisconnected")
        return
    path = (ROOT / "dist" / unquote(url.path.lstrip("/") or "index.html")).resolve()
    assert path.is_relative_to((ROOT / "dist").resolve())
    if path.is_file():
        route.fulfill(status=200, body=path.read_bytes(),
                      content_type=mimetypes.guess_type(path.name)[0] or "application/octet-stream")
    else:
        route.fulfill(status=404, body="missing")


with sync_playwright() as pw:
    options = {"args": ["--no-sandbox", "--disable-dev-shm-usage"]}
    binary = os.environ.get("LAW_QA_CHROMIUM") or shutil.which("chromium")
    if binary:
        options["executable_path"] = binary
    browser = pw.chromium.launch(**options)
    ctx = browser.new_context(viewport={"width": 375, "height": 812}, service_workers="block")
    ctx.route("**/*", serve)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.goto("https://law.local/index.html", wait_until="load", timeout=90000)
    page.wait_for_function("document.documentElement.dataset.lawReady === 'true'", timeout=60000)

    # Verified same revision; future event alone must not prompt.
    page.evaluate("async () => await window.LawUpdate.check()")
    assert page.locator("#law-update-banner").is_hidden()
    assert state["hits"] >= 1

    # Legal editor has published a change but not yet a signed installable APK.
    remote["current_revision_sequence"] = 2
    remote["law_text_last_amended_on"] = "2026-11-14"
    page.evaluate("async () => await window.LawUpdate.check()")
    page.locator("#law-update-banner").wait_for(state="visible")
    assert "חובה לעדכן את נוסח החוק" in page.locator("#law-update-banner").inner_text()
    assert "טרם פורסמה" in page.locator("#law-update-detail").inner_text()
    assert page.locator("#law-update-releases").get_attribute("href") == (
        "https://sargon17-green.github.io/consumer-law-reader/reader/"
    )
    # Notice must remain in the visible viewport even for a resumed user
    # halfway through the document, not only at the very top of the law.
    page.evaluate("window.scrollTo(0, 3000)")
    notice_rect = page.locator("#law-update-banner").bounding_box()
    assert notice_rect is not None
    assert notice_rect["y"] >= 60, notice_rect
    assert notice_rect["y"] + notice_rect["height"] <= 812 - 60, notice_rect

    # A previously confirmed obsolete local text must remain marked offline.
    state["offline"] = True
    page.evaluate("async () => await window.LawUpdate.check()")
    assert page.locator("#law-update-banner").is_visible()
    page.reload(wait_until="load")
    page.wait_for_function("document.documentElement.dataset.lawReady === 'true'")
    assert page.locator("#law-update-banner").is_visible()
    assert "law-update" not in " ".join(errors), errors
    assert not errors, errors
    ctx.close()
    browser.close()
print(json.dumps({"result": "PASS", "actual_https_requests": state["hits"],
                  "coverage": ["CSP exact URL", "same revision", "new revision",
                               "not yet released", "offline retention", "offline reload"]}))
