"""Fingerprint the code, resources and web files consumed by the APK compiler."""
import hashlib


def fingerprints(root):
    paths=[root/'VERSION',root/'android/AndroidManifest.xml']
    for directory in ('android/src','android/res','dist'):
        paths.extend(path for path in (root/directory).rglob('*') if path.is_file())
    return {str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(paths)}
