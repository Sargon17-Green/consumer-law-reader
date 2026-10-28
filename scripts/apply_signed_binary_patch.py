#!/usr/bin/env python3
"""Reconstruct the already-signed release APK from the exact unsigned build and public diff.

The binary diff contains public APK signature material and packaging adjustments.
It contains NO private signing key or signing password. All digests are hard-pinned.
"""
import argparse, base64, hashlib, struct, zlib
from pathlib import Path

UNSIGNED_SHA="a2fc048c0898ec34a407df9db56af2fe3f0c87474beeab9b49a37a58d5e71a37"
SIGNED_SHA="099bca2c4f3f1e1c226529c516b810082e16130ca6407b765ca976a4221b3552"
MAX_APK=8*1024*1024
def digest(data):return hashlib.sha256(data).hexdigest()
def apply(unsigned, delta):
    if len(unsigned)>MAX_APK or digest(unsigned)!=UNSIGNED_SHA:
        raise ValueError("Input APK is not the exact unsigned CI artifact")
    raw=zlib.decompress(base64.b64decode(delta, validate=True))
    if not raw.startswith(b"LAWDIFF1") or len(raw)>256*1024:
        raise ValueError("Invalid public delta format")
    original=raw[8:40].hex();target=raw[40:72].hex()
    if original!=UNSIGNED_SHA or target!=SIGNED_SHA:
        raise ValueError("Public delta digest mismatch")
    size,n=struct.unpack_from("<QI",raw,72)
    if size>MAX_APK or n>10000:raise ValueError("Unreasonable patch size")
    pos=84;result=bytearray()
    for _ in range(n):
        mode=raw[pos:pos+1];pos+=1
        if mode==b"A":
            amount=struct.unpack_from("<I",raw,pos)[0];pos+=4
            if amount>MAX_APK or pos+amount>len(raw):raise ValueError("Invalid literal extent")
            result.extend(raw[pos:pos+amount]);pos+=amount
        elif mode==b"C":
            offset,amount=struct.unpack_from("<II",raw,pos);pos+=8
            if offset+amount>len(unsigned):raise ValueError("Invalid copy extent")
            result.extend(unsigned[offset:offset+amount])
        else:raise ValueError("Invalid patch command")
        if len(result)>size:raise ValueError("Patch output overflow")
    if len(result)!=size or pos!=len(raw) or digest(result)!=SIGNED_SHA:
        raise ValueError("Signed APK reconstruction did not match signed local output")
    return bytes(result)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("unsigned")
    p.add_argument("delta")
    p.add_argument("output")
    a=p.parse_args()
    signed=apply(Path(a.unsigned).read_bytes(),Path(a.delta).read_text().strip())
    Path(a.output).write_bytes(signed)
    print("Exact signed APK reconstructed; SHA256:",digest(signed))
