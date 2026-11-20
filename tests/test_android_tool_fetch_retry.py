"""No-network regression tests for bounded Android toolchain downloads."""
import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "android_toolchain_fetch_under_test", ROOT / "scripts/fetch_tools.py"
)
fetch_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fetch_module)


def item_for(data):
    return {
        "file": "locked-test.bin",
        "url": "https://example.invalid/locked-test.bin",
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def http_error(code, retry_after=None):
    headers = {"Retry-After": str(retry_after)} if retry_after is not None else {}
    return HTTPError("https://example.invalid/locked-test.bin", code,
                     "simulated HTTP response", headers, None)


class AndroidToolchainRetryTests(unittest.TestCase):
    def test_two_transient_errors_then_verified_download(self):
        data = b"verified fixed input"
        with tempfile.TemporaryDirectory() as root:
            with patch.object(fetch_module, "TOOLS", Path(root)), \
                 patch.object(fetch_module, "urlopen", side_effect=[
                     http_error(429), http_error(503, retry_after=100),
                     io.BytesIO(data)] ) as open_mock, \
                 patch.object(fetch_module.time, "sleep") as sleep_mock:
                fetch_module.fetch(item_for(data))
                self.assertEqual(open_mock.call_count, 3)
                self.assertEqual([call.args[0] for call in sleep_mock.call_args_list],
                                 [2, 30])
            self.assertEqual((Path(root) / "locked-test.bin").read_bytes(), data)
            self.assertFalse((Path(root) / "locked-test.bin.partial").exists())

    def test_nontransient_error_fails_immediately(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(fetch_module, "TOOLS", Path(root)), \
                 patch.object(fetch_module, "urlopen",
                              side_effect=http_error(403)) as open_mock, \
                 patch.object(fetch_module.time, "sleep") as sleep_mock:
                with self.assertRaises(HTTPError):
                    fetch_module.fetch(item_for(b"data"))
                self.assertEqual(open_mock.call_count, 1)
                sleep_mock.assert_not_called()
            self.assertFalse((Path(root) / "locked-test.bin.partial").exists())

    def test_fourth_transient_error_is_fatal_without_fifth_request(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(fetch_module, "TOOLS", Path(root)), \
                 patch.object(fetch_module, "urlopen",
                              side_effect=http_error(429)) as open_mock, \
                 patch.object(fetch_module.time, "sleep") as sleep_mock:
                with self.assertRaises(HTTPError):
                    fetch_module.fetch(item_for(b"data"))
                self.assertEqual(open_mock.call_count, 4)
                self.assertEqual(sleep_mock.call_count, 3)
            self.assertFalse((Path(root) / "locked-test.bin.partial").exists())

    def test_digest_mismatch_fails_without_retry_or_cache_poison(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(fetch_module, "TOOLS", Path(root)), \
                 patch.object(fetch_module, "urlopen",
                              return_value=io.BytesIO(b"wrong data")) as open_mock, \
                 patch.object(fetch_module.time, "sleep") as sleep_mock:
                with self.assertRaisesRegex(ValueError, "digest mismatch"):
                    fetch_module.fetch(item_for(b"correct data"))
                self.assertEqual(open_mock.call_count, 1)
                sleep_mock.assert_not_called()
            self.assertFalse((Path(root) / "locked-test.bin").exists())
            self.assertFalse((Path(root) / "locked-test.bin.partial").exists())

    def test_good_cached_file_never_reaches_network(self):
        data = b"cached original bytes"
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "locked-test.bin").write_bytes(data)
            with patch.object(fetch_module, "TOOLS", Path(root)), \
                 patch.object(fetch_module, "urlopen") as open_mock:
                fetch_module.fetch(item_for(data))
                open_mock.assert_not_called()

    def test_corrupted_cached_file_never_falls_back_to_network(self):
        with tempfile.TemporaryDirectory() as root:
            (Path(root) / "locked-test.bin").write_bytes(b"tampered")
            with patch.object(fetch_module, "TOOLS", Path(root)), \
                 patch.object(fetch_module, "urlopen") as open_mock:
                with self.assertRaisesRegex(ValueError, "Cached toolchain digest mismatch"):
                    fetch_module.fetch(item_for(b"correct data"))
                open_mock.assert_not_called()


    def test_primary_404_uses_only_explicit_locked_fallback(self):
        data = b"immutable locked compiler"
        primary = item_for(data)
        fallback_url = "https://mirror.example.invalid/locked-test.bin"
        primary["fallback_urls"] = [fallback_url]
        with tempfile.TemporaryDirectory() as root:
            with patch.object(fetch_module, "TOOLS", Path(root)), \
                 patch.object(fetch_module, "urlopen",
                              side_effect=[http_error(404), io.BytesIO(data)]) as open_mock, \
                 patch.object(fetch_module.time, "sleep") as sleep_mock:
                fetch_module.fetch(primary)
                self.assertEqual(open_mock.call_count, 2)
                self.assertEqual(open_mock.call_args_list[0].args[0], primary["url"])
                self.assertEqual(open_mock.call_args_list[1].args[0], fallback_url)
                sleep_mock.assert_not_called()
            self.assertEqual((Path(root) / primary["file"]).read_bytes(), data)
            self.assertFalse((Path(root) / "locked-test.bin.partial").exists())

    def test_primary_404_without_fallback_fails_immediately(self):
        with tempfile.TemporaryDirectory() as root:
            with patch.object(fetch_module, "TOOLS", Path(root)), \
                 patch.object(fetch_module, "urlopen", side_effect=http_error(404)) as open_mock, \
                 patch.object(fetch_module.time, "sleep") as sleep_mock:
                with self.assertRaises(HTTPError):
                    fetch_module.fetch(item_for(b"correct"))
                self.assertEqual(open_mock.call_count, 1)
                sleep_mock.assert_not_called()
            self.assertFalse((Path(root) / "locked-test.bin.partial").exists())

    def test_primary_429_exhaustion_then_verified_locked_fallback(self):
        data = b"verified fallback bytes"
        item = item_for(data)
        fallback_url = "https://mirror.example.invalid/locked-test.bin"
        item["fallback_urls"] = [fallback_url]
        with tempfile.TemporaryDirectory() as root:
            with patch.object(fetch_module, "TOOLS", Path(root)), \
                 patch.object(fetch_module, "urlopen", side_effect=[
                     *[http_error(429) for _ in range(fetch_module.MAX_ATTEMPTS)],
                     io.BytesIO(data)]) as open_mock, \
                 patch.object(fetch_module.time, "sleep") as sleep_mock:
                fetch_module.fetch(item)
                self.assertEqual(open_mock.call_count, fetch_module.MAX_ATTEMPTS + 1)
                self.assertEqual(sleep_mock.call_count, fetch_module.MAX_ATTEMPTS - 1)
                self.assertEqual(open_mock.call_args_list[-1].args[0], fallback_url)
            self.assertEqual((Path(root) / "locked-test.bin").read_bytes(), data)

    def test_fallback_wrong_digest_is_rejected_and_not_cached(self):
        item = item_for(b"original canonical bytes")
        item["fallback_urls"] = ["https://mirror.example.invalid/locked-test.bin"]
        with tempfile.TemporaryDirectory() as root:
            with patch.object(fetch_module, "TOOLS", Path(root)), \
                 patch.object(fetch_module, "urlopen", side_effect=[
                     http_error(404), io.BytesIO(b"wrong bytes")]) as open_mock:
                with self.assertRaisesRegex(ValueError, "digest mismatch"):
                    fetch_module.fetch(item)
                self.assertEqual(open_mock.call_count, 2)
            self.assertFalse((Path(root) / "locked-test.bin").exists())
            self.assertFalse((Path(root) / "locked-test.bin.partial").exists())

    def test_fallback_does_not_bypass_forbidden_response(self):
        item = item_for(b"correct")
        item["fallback_urls"] = ["https://mirror.example.invalid/locked-test.bin"]
        with tempfile.TemporaryDirectory() as root:
            with patch.object(fetch_module, "TOOLS", Path(root)), \
                 patch.object(fetch_module, "urlopen", side_effect=http_error(403)) as open_mock:
                with self.assertRaises(HTTPError):
                    fetch_module.fetch(item)
                self.assertEqual(open_mock.call_count, 1)
            self.assertFalse((Path(root) / "locked-test.bin.partial").exists())


if __name__ == "__main__":
    unittest.main()
