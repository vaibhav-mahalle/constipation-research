"""Shared helpers for the fetch scripts. Standard library only."""
import csv
import hashlib
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

USER_AGENT = "constipation-research-fetch/0.1 (public research; contact via GitHub repo)"
REQUEST_INTERVAL = 1.0  # seconds between requests
MANIFEST_COLUMNS = [
    "source_id", "file", "url", "bytes", "sha256", "downloaded_utc", "http_status",
]

_last_request_time = 0.0


class DownloadError(Exception):
    """A download failed after all retries."""


@dataclass
class DownloadResult:
    status: str  # ok, needs_login, failed
    url: str
    dest: Path
    bytes: int = 0
    sha256: str = ""
    http_status: int = 0


def repo_root():
    """Repo root is the parent of the scripts folder."""
    return Path(__file__).resolve().parent.parent


def default_data_dir():
    return repo_root() / "data"


def resolve_data_dir(value):
    """Return the data dir. A relative value is relative to the repo root."""
    if not value:
        return default_data_dir()
    path = Path(value)
    return path if path.is_absolute() else repo_root() / path


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def looks_like_html(first_bytes):
    text = first_bytes.lstrip().lower()
    return text.startswith(b"<!doctype html") or text.startswith(b"<html")


def looks_like_login(first_bytes):
    text = first_bytes.lower()
    if not looks_like_html(first_bytes):
        return False
    return b'type="password"' in text or b"type='password'" in text or b"<form" in text and b"login" in text


def _wait_for_slot():
    global _last_request_time
    now = time.monotonic()
    wait = REQUEST_INTERVAL - (now - _last_request_time)
    if _last_request_time and wait > 0:
        time.sleep(wait)
    _last_request_time = time.monotonic()


def _check_inside_data(dest, data_dir):
    if data_dir is None:
        return
    root = Path(data_dir).resolve()
    target = Path(dest).resolve()
    if root != target and root not in target.parents:
        raise ValueError("refuse to write outside data/: %s" % dest)


def safe_dest(data_dir, source_id, filename):
    """Build data/raw/<source_id>/<filename> and refuse path escapes."""
    if Path(filename).name != filename or filename in ("", ".", ".."):
        raise ValueError("bad file name: %r" % filename)
    dest = Path(data_dir) / "raw" / source_id / filename
    _check_inside_data(dest, data_dir)
    return dest


class Manifest:
    """Rows in data/manifest.csv, keyed by (source_id, file)."""

    def __init__(self, path):
        self.path = Path(path)
        self.data_dir = self.path.parent
        self.rows = {}  # (source_id, file) -> dict
        self.load()

    def load(self):
        self.rows = {}
        if not self.path.exists():
            return
        with open(self.path, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                if row.get("source_id") and row.get("file"):
                    self.rows[(row["source_id"], row["file"])] = row

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        _check_inside_data(self.path, self.data_dir)
        tmp = self.path.with_suffix(".csv.part")
        with open(tmp, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=MANIFEST_COLUMNS)
            writer.writeheader()
            for key in sorted(self.rows):
                writer.writerow({col: self.rows[key].get(col, "") for col in MANIFEST_COLUMNS})
        tmp.replace(self.path)

    def record(self, source_id, file, url, bytes_count, sha256, http_status,
               downloaded_utc=None):
        """Add or update one row. `file` is a path under the data dir or a name."""
        name = str(file)
        try:
            name = str(Path(file).resolve().relative_to(self.data_dir.resolve()))
        except (ValueError, OSError):
            pass
        self.rows[(source_id, name)] = {
            "source_id": source_id,
            "file": name,
            "url": url,
            "bytes": str(int(bytes_count)),
            "sha256": sha256,
            "downloaded_utc": downloaded_utc or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "http_status": str(http_status),
        }
        self.save()
        return self.rows[(source_id, name)]

    def find(self, dest):
        """Return the row for a destination path, or None."""
        try:
            name = str(Path(dest).resolve().relative_to(self.data_dir.resolve()))
        except (ValueError, OSError):
            name = Path(dest).name
        for row in self.rows.values():
            if row.get("file") == name or Path(row.get("file", "")).name == Path(dest).name and row.get("file") == name:
                return row
        # Fall back to a unique file-name match inside this data dir.
        matches = [r for r in self.rows.values() if Path(r.get("file", "")).name == Path(dest).name]
        return matches[0] if len(matches) == 1 else None


def is_complete(dest, manifest):
    """True if dest exists and its size and SHA-256 match the manifest row."""
    dest = Path(dest)
    if not dest.is_file():
        return False
    row = manifest.find(dest) if isinstance(manifest, Manifest) else None
    if row is None:
        return False
    try:
        if dest.stat().st_size != int(row["bytes"]):
            return False
    except (KeyError, ValueError):
        return False
    return bool(row.get("sha256")) and sha256_file(dest) == row["sha256"]


def setup_logging(source_id, data_dir):
    """Log to the console and to data/logs/<source_id>_<time>.log."""
    log_dir = Path(data_dir) / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    log_path = log_dir / ("%s_%s.log" % (source_id, stamp))
    logger = logging.getLogger(source_id)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    logger.propagate = False
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    for handler in (logging.StreamHandler(), logging.FileHandler(log_path, encoding="utf-8")):
        handler.setFormatter(fmt)
        logger.addHandler(handler)
    return logger, log_path


def download(url, dest, *, expected_min_bytes=1, retries=3, timeout=60, data_dir=None, logger=None):
    """Download url to dest. Write to dest.part first, then rename.

    Return a DownloadResult. A login page gives status needs_login and no
    exception. Other failures raise DownloadError after the retries.
    """
    log = logger or logging.getLogger("download")
    dest = Path(dest)
    _check_inside_data(dest, data_dir)
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_name(dest.name + ".part")
    last_error = None
    http_status = 0
    for attempt in range(1, retries + 1):
        try:
            _wait_for_slot()
            request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                http_status = response.getcode() or 200
                with open(part, "wb") as out:
                    while True:
                        chunk = response.read(1024 * 256)
                        if not chunk:
                            break
                        out.write(chunk)
            break
        except urllib.error.HTTPError as error:
            http_status = error.code
            last_error = error
            if error.code in (401, 403):
                log.warning("needs_login %s http_status=%s", url, error.code)
                part.unlink(missing_ok=True)
                return DownloadResult("needs_login", url, dest, http_status=http_status)
            log.warning("http %s for %s (attempt %s/%s)", error.code, url, attempt, retries)
        except (urllib.error.URLError, OSError, TimeoutError) as error:
            last_error = error
            log.warning("error for %s (attempt %s/%s): %s", url, attempt, retries, error)
        if attempt < retries:
            time.sleep(2 ** (attempt - 1))
    else:
        raise DownloadError("download failed for %s: %s" % (url, last_error))

    # Check the finished .part file before the rename.
    size = part.stat().st_size if part.exists() else 0
    with open(part, "rb") as handle:
        first = handle.read(4096)
    # A documentation page (.htm) is HTML on purpose; it may hold a search form.
    expects_html = dest.suffix.lower() in (".htm", ".html")
    if not expects_html and looks_like_login(first):
        log.warning("needs_login %s (login form)", url)
        part.unlink(missing_ok=True)
        return DownloadResult("needs_login", url, dest, http_status=http_status)
    if size < max(1, expected_min_bytes) or size == 0:
        part.unlink(missing_ok=True)
        raise DownloadError("file too small (%s bytes) for %s" % (size, url))
    if looks_like_html(first) and dest.suffix.lower() not in (".htm", ".html"):
        part.unlink(missing_ok=True)
        raise DownloadError("HTML page where a data file was expected: %s" % url)
    digest = sha256_file(part)
    part.replace(dest)
    return DownloadResult("ok", url, dest, bytes=size, sha256=digest, http_status=http_status)


def fetch_text(url, *, timeout=60, logger=None):
    """Fetch a small page as text. Return (text, http_status)."""
    log = logger or logging.getLogger("download")
    _wait_for_slot()
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace"), response.getcode() or 200
    except urllib.error.HTTPError as error:
        if error.code in (401, 403):
            log.warning("needs_login %s http_status=%s", url, error.code)
            return "", error.code
        raise


def fetch_one(source_id, url, dest, manifest, *, force=False, expected_min_bytes=1,
              data_dir=None, logger=None):
    """Download one file unless the manifest says it is complete.

    Return one of: ok, skip, needs_login, failed.
    """
    log = logger or logging.getLogger(source_id)
    dest = Path(dest)
    if not force and is_complete(dest, manifest):
        print("skip (complete) %s" % dest)
        log.info("skip (complete) %s", dest)
        return "skip"
    try:
        result = download(url, dest, expected_min_bytes=expected_min_bytes,
                          data_dir=data_dir, logger=log)
    except DownloadError as error:
        print("failed %s (%s)" % (url, error))
        log.error("failed %s: %s", url, error)
        return "failed"
    if result.status == "needs_login":
        print("needs_login %s" % url)
        log.warning("needs_login %s", url)
        return "needs_login"
    manifest.record(source_id, dest, url, result.bytes, result.sha256, result.http_status)
    print("ok %s (%s bytes)" % (dest, result.bytes))
    log.info("ok %s bytes=%s sha256=%s", dest, result.bytes, result.sha256)
    return "ok"


def add_common_args(parser):
    parser.add_argument("--dry-run", action="store_true", help="print URLs, download nothing")
    parser.add_argument("--force", action="store_true", help="download again")
    parser.add_argument("--data-dir", default=None, help="data folder (default: repo data/)")


def write_note(path, text, data_dir=None):
    """Write a licence or terms note inside the data folder."""
    path = Path(path)
    _check_inside_data(path, data_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
