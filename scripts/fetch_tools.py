"""Download the SHA-pinned Linux Android toolchain without trusting the network.

Allow bounded retries for transient HTTP errors and *explicitly locked* source
fallbacks. Every source must provide exactly the same pinned SHA-256 bytes.
Permanent 403 and other failures are fatal, as are invalid bytes.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen
import hashlib
import json
import os
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(os.environ.get("LAW_ANDROID_TOOLS", str(ROOT / ".toolchain"))).resolve()
TOOLS.mkdir(exist_ok=True)
LOCK = json.loads((ROOT / "scripts/android_toolchain.lock.json").read_text())
TRANSIENT_HTTP = frozenset((429, 500, 502, 503, 504))
MAX_ATTEMPTS = 4


def retry_delay(error, attempt):
    """Bound retry duration even when the server sends a huge Retry-After."""
    retry_after = error.headers.get("Retry-After") if error.headers else None
    server_delay = int(retry_after) if retry_after and retry_after.isdecimal() else 0
    return min(30, max(2 ** (attempt + 1), server_delay))


def download_locked(item, path):
    """Fetch from a locked source or locked fallback, never accepting new bytes.

    A 404 from the first endpoint can be an edge/CDN failure even when the
    immutable artifact exists; only an explicitly approved fallback is tried.
    For 429/5xx, exhaust the bounded retry budget before trying a fallback.
    """
    sources = [item["url"], *item.get("fallback_urls", [])]
    temporary = path.with_suffix(path.suffix + ".partial")
    for source_index, url in enumerate(sources):
        for attempt in range(MAX_ATTEMPTS):
            try:
                with urlopen(url, timeout=90) as response, temporary.open("wb") as output:
                    while block := response.read(1024 * 1024):
                        output.write(block)
                actual = hashlib.sha256(temporary.read_bytes()).hexdigest()
                if actual != item["sha256"]:
                    raise ValueError("Toolchain digest mismatch: " + item["file"])
                temporary.replace(path)
                return
            except HTTPError as error:
                transient = error.code in TRANSIENT_HTTP
                if transient and attempt < MAX_ATTEMPTS - 1:
                    delay = retry_delay(error, attempt)
                    print("RETRY", item["file"], "HTTP", error.code,
                          "attempt", attempt + 1, "of", MAX_ATTEMPTS,
                          "wait_seconds", delay, flush=True)
                    time.sleep(delay)
                    continue
                if source_index + 1 < len(sources) and (error.code == 404 or transient):
                    print("LOCKED_SOURCE_FALLBACK", item["file"],
                          "after HTTP", error.code, "source", source_index + 1,
                          "of", len(sources), flush=True)
                    break
                raise
            finally:
                temporary.unlink(missing_ok=True)
    raise RuntimeError("All locked sources exhausted: " + item["file"])


def fetch(item):
    path = TOOLS / item["file"]
    if not path.is_file():
        download_locked(item, path)
    if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
        raise ValueError("Cached toolchain digest mismatch: " + item["file"])
    if item.get("directory"):
        directory = TOOLS / item["directory"]
        directory.mkdir(exist_ok=True)
        with zipfile.ZipFile(path) as archive:
            if any(not (directory / name).resolve().is_relative_to(directory.resolve())
                   for name in archive.namelist()):
                raise ValueError("Toolchain path traversal")
            archive.extractall(directory)
        for entry in directory.rglob("*"):
            if entry.is_file() and (entry.suffix == ".so" or "." not in entry.name):
                entry.chmod(0o755)
    print("READY", item["file"], item["sha256"], flush=True)


def main():
    with ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(fetch, LOCK["packages"]))


if __name__ == "__main__":
    main()
