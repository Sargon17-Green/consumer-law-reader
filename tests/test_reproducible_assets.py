"""Build the real bundle twice, with unrelated/stale files between builds."""
from pathlib import Path
import hashlib, shutil, subprocess, sys, tempfile, unittest

ROOT = Path(__file__).resolve().parents[1]

class ReproducibleAssets(unittest.TestCase):
    def test_editor_files_and_stale_outputs_cannot_enter_packages(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ['scripts', 'web', 'metadata', 'typed-sources']:
                shutil.copytree(ROOT / folder, root / folder, ignore=shutil.ignore_patterns('__pycache__'))
            (root / 'original').mkdir()
            for name in subprocess.check_output(['git', 'ls-files', '-z', 'original'], cwd=ROOT).decode().split('\0'):
                if name:
                    shutil.copy2(ROOT / name, root / name)
            def build():
                subprocess.run([sys.executable, 'scripts/build_web.py'], cwd=root, check=True, capture_output=True)
                return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (root / 'dist').iterdir() if p.is_file()}
            expected = build()
            (root / 'original/.editor-private.png').write_bytes(b'private editor temporary file')
            (root / 'original/notes.txt').write_text('not a reader resource')
            (root / 'dist/stale.js').write_text('obsolete script from an earlier build')
            self.assertEqual(expected, build())
            self.assertNotIn('.editor-private.png', expected)
