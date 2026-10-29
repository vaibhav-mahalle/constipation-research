"""Offline tests for scripts/common.py. No network: file:// URLs only."""
import csv
import hashlib
import io
import sys
import tempfile
import unittest
import unittest.mock
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import common


class CommonTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmp.name) / "data"
        (self.data_dir / "raw" / "test").mkdir(parents=True)
        common.REQUEST_INTERVAL = 0  # no polite wait in tests
        self._saved_schemes = common.ALLOWED_SCHEMES
        common.ALLOWED_SCHEMES = {"https", "file"}

    def tearDown(self):
        common.ALLOWED_SCHEMES = self._saved_schemes
        self.tmp.cleanup()

    def manifest(self):
        return common.Manifest(self.data_dir / "manifest.csv")

    def dest(self, name="a.csv"):
        return common.safe_dest(self.data_dir, "test", name)


class TestHash(unittest.TestCase):
    def test_sha256_known_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.bin"
            path.write_bytes(b"abc")
            self.assertEqual(
                common.sha256_file(path),
                "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
            )
            self.assertEqual(common.sha256_file(path), hashlib.sha256(b"abc").hexdigest())

    def test_html_and_login_detection(self):
        self.assertTrue(common.looks_like_html(b"  <!DOCTYPE html><html>"))
        self.assertTrue(common.looks_like_html(b"<html><body>"))
        self.assertFalse(common.looks_like_html(b"a,b,c\n1,2,3\n"))
        self.assertTrue(common.looks_like_login(b'<html><form><input type="password"></form>'))
        self.assertFalse(common.looks_like_login(b"<html><p>hello</p>"))


class TestManifest(CommonTestCase):
    def test_record_adds_row_with_columns(self):
        manifest = self.manifest()
        manifest.record("test", self.dest(), "https://example.invalid/a.csv", 3, "abc123", 200)
        with open(self.data_dir / "manifest.csv", newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            list(rows[0].keys()),
            ["source_id", "file", "url", "bytes", "sha256", "downloaded_utc", "http_status"],
        )
        self.assertEqual(rows[0]["source_id"], "test")
        self.assertEqual(rows[0]["file"], "raw/test/a.csv")
        self.assertEqual(rows[0]["bytes"], "3")
        self.assertEqual(rows[0]["sha256"], "abc123")
        self.assertEqual(rows[0]["http_status"], "200")

    def test_record_updates_same_file(self):
        manifest = self.manifest()
        dest = self.dest()
        manifest.record("test", dest, "https://example.invalid/a.csv", 3, "one", 200)
        manifest.record("test", dest, "https://example.invalid/a.csv", 5, "two", 200)
        self.assertEqual(len(manifest.rows), 1)
        row = manifest.find(dest)
        self.assertEqual(row["bytes"], "5")
        self.assertEqual(row["sha256"], "two")


class TestIsComplete(CommonTestCase):
    def test_skip_if_complete(self):
        dest = self.dest()
        dest.write_bytes(b"a,b\n1,2\n")
        manifest = self.manifest()
        manifest.record("test", dest, "file:///unused", dest.stat().st_size,
                        common.sha256_file(dest), 200)
        self.assertTrue(common.is_complete(dest, manifest))

    def test_not_complete_when_missing_tampered_or_unknown(self):
        manifest = self.manifest()
        dest = self.dest()
        self.assertFalse(common.is_complete(dest, manifest))  # missing file
        dest.write_bytes(b"hello")
        self.assertFalse(common.is_complete(dest, manifest))  # no manifest row
        manifest.record("test", dest, "file:///unused", 5, common.sha256_file(dest), 200)
        self.assertTrue(common.is_complete(dest, manifest))
        dest.write_bytes(b"HELLO")  # same size, new hash
        self.assertFalse(common.is_complete(dest, manifest))
        dest.write_bytes(b"hello world")  # new size
        self.assertFalse(common.is_complete(dest, manifest))


class TestDownload(CommonTestCase):
    def source(self, name, data):
        path = Path(self.tmp.name) / name
        path.write_bytes(data)
        return path.as_uri()

    def test_download_file_url(self):
        dest = self.dest("ok.csv")
        result = common.download(self.source("src.csv", b"a,b\n1,2\n"), dest,
                                 data_dir=self.data_dir)
        self.assertEqual(result.status, "ok")
        self.assertEqual(dest.read_bytes(), b"a,b\n1,2\n")
        self.assertEqual(result.sha256, hashlib.sha256(b"a,b\n1,2\n").hexdigest())
        self.assertFalse(Path(str(dest) + ".part").exists())

    def test_empty_file_refused(self):
        dest = self.dest("empty.csv")
        with self.assertRaises(common.DownloadError):
            common.download(self.source("empty.csv", b""), dest, data_dir=self.data_dir)
        self.assertFalse(dest.exists())
        self.assertFalse(Path(str(dest) + ".part").exists())

    def test_too_small_file_refused(self):
        dest = self.dest("small.csv")
        with self.assertRaises(common.DownloadError):
            common.download(self.source("small.csv", b"ab"), dest,
                            expected_min_bytes=10, data_dir=self.data_dir)
        self.assertFalse(dest.exists())

    def test_html_refused_for_data_file(self):
        dest = self.dest("page.xpt")
        with self.assertRaises(common.DownloadError):
            common.download(self.source("page.html", b"<html><body>no</body></html>"),
                            dest, data_dir=self.data_dir)
        self.assertFalse(dest.exists())

    def test_html_allowed_for_htm_file(self):
        dest = self.dest("doc.htm")
        result = common.download(self.source("doc.html", b"<html><body>doc</body></html>"),
                                 dest, data_dir=self.data_dir)
        self.assertEqual(result.status, "ok")

    def test_doc_page_with_login_link_and_form_is_saved(self):
        # Claude review fix: a .htm doc with a search form and a login link is not a login wall.
        dest = self.dest("doc2.htm")
        html = b'<html><form action="/search"><input name="q"></form><a href="/login">Login</a></html>'
        result = common.download(self.source("doc2.html", html), dest, data_dir=self.data_dir)
        self.assertEqual(result.status, "ok")
        self.assertTrue(dest.exists())

    def test_login_page_is_needs_login_not_error(self):
        dest = self.dest("secret.json")
        html = b'<html><form action="/login"><input type="password"></form></html>'
        result = common.download(self.source("login.html", html), dest, data_dir=self.data_dir)
        self.assertEqual(result.status, "needs_login")
        self.assertFalse(dest.exists())

    def test_refuse_write_outside_data(self):
        outside = Path(self.tmp.name) / "outside.csv"
        with self.assertRaises(ValueError):
            common.download(self.source("src2.csv", b"x"), outside, data_dir=self.data_dir)
        with self.assertRaises(ValueError):
            common.safe_dest(self.data_dir, "test", "../escape.csv")


class TestFetchOneSkip(CommonTestCase):
    def test_fetch_one_skips_complete_without_download(self):
        dest = self.dest()
        dest.write_bytes(b"done")
        manifest = self.manifest()
        manifest.record("test", dest, "https://example.invalid/never.csv", 4,
                        common.sha256_file(dest), 200)
        # An invalid URL proves no download happens for a complete file.
        status = common.fetch_one("test", "https://example.invalid/never.csv", dest,
                                  manifest, data_dir=self.data_dir)
        self.assertEqual(status, "skip")


class FakeHeaders(dict):
    def get_content_charset(self, failobj=None):
        return failobj


class FakeResponse:
    def __init__(self, body, headers=None, code=200):
        self._body = io.BytesIO(body)
        self.headers = FakeHeaders(headers or {})
        self._code = code

    def getcode(self):
        return self._code

    def read(self, n=-1):
        return self._body.read(n)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestSymlinks(CommonTestCase):
    def test_symlinked_part_does_not_write_outside(self):
        outside = Path(self.tmp.name) / "outside.txt"
        outside.write_bytes(b"original")
        dest = self.dest("linked.csv")
        part = Path(str(dest) + ".part")
        part.symlink_to(outside)
        result = common.download(
            self._src(b"a,b\n1,2\n"), dest, data_dir=self.data_dir)
        self.assertEqual(result.status, "ok")
        self.assertEqual(outside.read_bytes(), b"original")
        self.assertEqual(dest.read_bytes(), b"a,b\n1,2\n")
        self.assertFalse(part.is_symlink())

    def _src(self, data):
        path = Path(self.tmp.name) / "src.csv"
        path.write_bytes(data)
        return path.as_uri()

    def test_symlinked_manifest_part_does_not_write_outside(self):
        outside = Path(self.tmp.name) / "outside.csv"
        outside.write_text("original", encoding="utf-8")
        manifest = self.manifest()
        tmp_part = self.data_dir / "manifest.csv.part"
        tmp_part.symlink_to(outside)
        manifest.record("test", self.dest(), "https://example.invalid/a.csv", 3, "abc", 200)
        self.assertEqual(outside.read_text(encoding="utf-8"), "original")
        self.assertTrue((self.data_dir / "manifest.csv").exists())

    def test_symlinked_log_dir_refused(self):
        outside = Path(self.tmp.name) / "outside_logs"
        outside.mkdir()
        (self.data_dir / "logs").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            common.setup_logging("test", self.data_dir)


class TestMockedResponses(CommonTestCase):
    def test_truncated_response_is_refused(self):
        body = b"a,b\n1,2\n"
        fake = FakeResponse(body, {"Content-Length": str(len(body) + 10)})
        dest = self.dest("trunc.csv")
        with unittest.mock.patch("urllib.request.urlopen", return_value=fake):
            with self.assertRaises(common.DownloadError):
                common.download("https://example.invalid/trunc.csv", dest,
                                retries=1, data_dir=self.data_dir)
        self.assertFalse(dest.exists())
        self.assertFalse(Path(str(dest) + ".part").exists())

    def test_html_content_type_refused_for_data_file(self):
        body = b"plain,text\n1,2\n"
        fake = FakeResponse(body, {
            "Content-Length": str(len(body)),
            "Content-Type": "text/html; charset=utf-8",
        })
        dest = self.dest("ctype.csv")
        with unittest.mock.patch("urllib.request.urlopen", return_value=fake):
            with self.assertRaises(common.DownloadError) as ctx:
                common.download("https://example.invalid/ctype.csv", dest,
                                retries=1, data_dir=self.data_dir)
        self.assertIn("HTML page where a data file was expected", str(ctx.exception))
        self.assertFalse(dest.exists())
        self.assertFalse(Path(str(dest) + ".part").exists())


class TestHttpsOnly(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmp.name) / "data"
        (self.data_dir / "raw" / "test").mkdir(parents=True)
        common.REQUEST_INTERVAL = 0
        self._saved = common.ALLOWED_SCHEMES
        common.ALLOWED_SCHEMES = {"https"}

    def tearDown(self):
        common.ALLOWED_SCHEMES = self._saved
        self.tmp.cleanup()

    def test_http_and_file_refused_by_default(self):
        dest = common.safe_dest(self.data_dir, "test", "x.csv")
        with self.assertRaises(common.DownloadError):
            common.download("http://example.invalid/x.csv", dest, data_dir=self.data_dir)
        with self.assertRaises(common.DownloadError):
            common.download("file:///etc/passwd", dest, data_dir=self.data_dir)
        with self.assertRaises(ValueError):
            common.fetch_text("http://example.invalid/page")
        with self.assertRaises(ValueError):
            common.fetch_text("file:///etc/passwd")

    def test_redirect_handler_refuses_cross_host_and_http(self):
        handler = common.SameHostHttpsRedirectHandler()

        class FakeReq:
            full_url = "https://example.com/start"
            headers = {}

            def get_full_url(self):
                return self.full_url

        for newurl in ("https://evil.example/x", "http://example.com/x"):
            with self.assertRaises(urllib.error.URLError):
                handler.redirect_request(FakeReq(), None, 302, "Found", {}, newurl)


if __name__ == "__main__":
    unittest.main()
