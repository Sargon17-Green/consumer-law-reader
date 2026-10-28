#!/usr/bin/env python3
"""Restore the EXACT original CRLF bytes, only when both SHA-256 proofs match."""
from pathlib import Path
import hashlib
SOURCE=Path(__file__).resolve().parents[1]/'original/Consumer_Protection_Law.html'
EXPECTED_LF='2213e44785bbd3fa2a0824000ff60f3dcf1e7d13e8f13ea0efae657542724f39'
EXPECTED_ORIGINAL='e046bc015b1e1a7c0fe471f821cdbc53ca0b120f343929418ac393d004a424d4'
def sha(b): return hashlib.sha256(b).hexdigest()
def restore():
    b=SOURCE.read_bytes()
    if sha(b)==EXPECTED_ORIGINAL:
        print('Original exact bytes already preserved.');return False
    if sha(b)!=EXPECTED_LF or b'\r' in b:
        raise SystemExit('Unexpected law source bytes; no modification permitted.')
    restored=b.replace(b'\n',b'\r\n')
    if sha(restored)!=EXPECTED_ORIGINAL:
        raise SystemExit('Reconstruction hash mismatch; refusing modification.')
    SOURCE.write_bytes(restored)
    print('Restored exact original HTML SHA256',sha(restored));return True
if __name__=='__main__':restore()
