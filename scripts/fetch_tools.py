"""Fetch the locked Linux Android toolchain, verifying SHA-256 before extraction.

A short, bounded retry is allowed only for transient HTTP server errors.
Permanent errors and checksum mismatches remain fatal.
"""
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(os.environ.get('LAW_ANDROID_TOOLS', str(ROOT / '.toolchain'))).resolve()
TOOLS.mkdir(exist_ok=True)
LOCK = json.loads((ROOT / 'scripts/android_toolchain.lock.json').read_text())
TRANSIENT_HTTP = frozenset((429, 500, 502, 503, 504))
MAX_ATTEMPTS = 4


def retry_delay(error, attempt):
    """Seconds, capped to avoid stalling every CI matrix member forever."""
    retry_after = error.headers.get('Retry-After') if error.headers else None
    server_delay = int(retry_after) if retry_after and retry_after.isdecimal() else 0
    return min(30, max(2 ** (attempt + 1), server_delay))


def fetch(item):
    path = TOOLS / item['file']
    if not path.is_file():
        temporary = path.with_suffix(path.suffix + '.partial')
        for attempt in range(MAX_ATTEMPTS):
            try:
                with urlopen(item['url'], timeout=90) as response, temporary.open('wb') as output:
                    while block := response.read(1024 * 1024):
                        output.write(block)
                actual = hashlib.sha256(temporary.read_bytes()).hexdigest()
                if actual != item['sha256']:
                    raise ValueError('Toolchain digest mismatch: ' + item['file'])
                temporary.replace(path)
                break
            except HTTPError as error:
                if error.code not in TRANSIENT_HTTP or attempt == MAX_ATTEMPTS - 1:
                    raise
                delay = retry_delay(error, attempt)
                print('RETRY', item['file'], 'HTTP', error.code,
                      'attempt', attempt + 1, 'of', MAX_ATTEMPTS,
                      'wait_seconds', delay, flush=True)
                time.sleep(delay)
            finally:
                temporary.unlink(missing_ok=True)
    if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
        raise ValueError('Cached toolchain digest mismatch: ' + item['file'])
    if item.get('directory'):
        directory = TOOLS / item['directory']
        directory.mkdir(exist_ok=True)
        with zipfile.ZipFile(path) as archive:
            if any(not (directory / name).resolve().is_relative_to(directory.resolve())
                   for name in archive.namelist()):
                raise ValueError('Toolchain path traversal')
            archive.extractall(directory)
        for entry in directory.rglob('*'):
            if entry.is_file() and (entry.suffix == '.so' or '.' not in entry.name):
                entry.chmod(0o755)
    print('READY', item['file'], item['sha256'], flush=True)


def main():
    with ThreadPoolExecutor(max_workers=3) as executor:
        list(executor.map(fetch, LOCK['packages']))


if __name__ == '__main__':
    main()
