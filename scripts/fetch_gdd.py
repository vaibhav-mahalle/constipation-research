"""Fetch Global Dietary Database fibre CSV and codebook. Parse the list page."""
import argparse
import sys
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

SOURCE_ID = "gdd"
PAGE_URL = "https://gdd.nutrition.tufts.edu/available-gdd-2018-estimates-datafiles"
DATA_DOWNLOAD_URL = "https://gdd.nutrition.tufts.edu/data-download"
PAGE_URLS = [DATA_DOWNLOAD_URL, PAGE_URL]
ACCOUNT_PHRASES = ("Create Your New Account", "Login to Your Existing Account")
NEEDS_ACCOUNT_TEXT = (
    "GDD data need a free account. Register by hand, read the terms, "
    "then put the files in data/raw/gdd/."
)
TERMS_TEXT = (
    "Global Dietary Database (GDD) data.\n"
    "All data are property of Tufts University.\n"
    "Read the Terms and Conditions of Use on the GDD site before any use.\n"
    "Source: %s\n" % DATA_DOWNLOAD_URL
)


class LinkParser(HTMLParser):
    """Collect (href, text) pairs from anchor tags."""

    def __init__(self):
        super().__init__()
        self.links = []
        self._href = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href")
            self._text = []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text).strip()))
            self._href = None


def parse_gdd_links(html_text, base_url=PAGE_URL):
    """Return {'fibre': url or None, 'codebook': url or None} from page HTML."""
    parser = LinkParser()
    parser.feed(html_text)
    found = {"fibre": None, "codebook": None}
    for href, text in parser.links:
        label = (href + " " + text).lower()
        url = urllib.parse.urljoin(base_url, href)
        if urllib.parse.urlparse(url).scheme.lower() != "https":
            continue
        if found["codebook"] is None and "codebook" in label:
            found["codebook"] = url
        if "fibre" in label or "fiber" in label:
            # Prefer a CSV link. Keep the first CSV match.
            is_csv = ".csv" in urllib.parse.urlparse(url).path.lower()
            if found["fibre"] is None or (is_csv and ".csv" not in found["fibre"].lower()):
                found["fibre"] = url
    return found


def gdd_page_url():
    return PAGE_URL


def gdd_page_urls():
    return list(PAGE_URLS)


def has_data_link(html_text, base_url=PAGE_URL):
    """True if the page holds a CSV, ZIP, or codebook link."""
    parser = LinkParser()
    parser.feed(html_text)
    for href, text in parser.links:
        label = (href + " " + text).lower()
        path = urllib.parse.urlparse(urllib.parse.urljoin(base_url, href)).path.lower()
        if path.endswith((".csv", ".zip")) or "codebook" in label:
            return True
    return False


def is_needs_account_page(html_text, base_url=PAGE_URL):
    """True if the page asks for an account and holds no data link."""
    if not any(phrase in html_text for phrase in ACCOUNT_PHRASES):
        return False
    return not has_data_link(html_text, base_url=base_url)


# Short alias for tests and callers.
needs_account_page = is_needs_account_page


def _filename_from_url(url, fallback):
    name = Path(urllib.parse.urlparse(url).path).name
    return name or fallback


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fetch GDD fibre data and codebook.")
    common.add_common_args(parser)
    args = parser.parse_args(argv)
    if args.dry_run:
        for url in PAGE_URLS:
            print(url)
        print("fibre CSV and codebook URLs are found on that page at run time")
        return 0
    data_dir = common.resolve_data_dir(args.data_dir)
    logger, _ = common.setup_logging(SOURCE_ID, data_dir)
    manifest = common.Manifest(data_dir / "manifest.csv")
    dest_dir = common.safe_dest(data_dir, SOURCE_ID, "x").parent
    common.write_note(dest_dir / "TERMS_NOTE.txt", TERMS_TEXT, data_dir=data_dir)
    last_error = None
    missing_link = False
    for page_url in PAGE_URLS:
        try:
            html_text, status = common.fetch_text(page_url, logger=logger)
        except Exception as error:  # urllib errors: log the failure, try next.
            last_error = error
            logger.error("failed %s: %s", page_url, error)
            print("failed %s (%s)" % (page_url, error))
            continue
        if status in (401, 403) or not html_text:
            print("needs_login %s" % page_url)
            logger.warning("needs_login %s http_status=%s", page_url, status)
            return 0
        if is_needs_account_page(html_text, base_url=page_url):
            print("needs_account %s" % page_url)
            print(NEEDS_ACCOUNT_TEXT)
            logger.warning("needs_account %s", page_url)
            logger.warning(NEEDS_ACCOUNT_TEXT)
            return 0
        links = parse_gdd_links(html_text, base_url=page_url)
        if not links["fibre"] and not links["codebook"]:
            print("not_found fibre on %s" % page_url)
            logger.warning("not_found fibre on %s", page_url)
            missing_link = True
            continue
        failed = 0
        if not links["fibre"] or not links["codebook"]:
            missing_link = True
            failed += 1
        planned = [
            ("fibre", links["fibre"], "gdd_fibre_country.csv"),
            ("codebook", links["codebook"], "gdd_codebook.pdf"),
        ]
        for kind, url, fallback in planned:
            if not url:
                print("not_found %s on %s" % (kind, page_url))
                logger.warning("not_found %s on %s", kind, page_url)
                continue
            dest = common.safe_dest(data_dir, SOURCE_ID, _filename_from_url(url, fallback))
            dl_status = common.fetch_one(
                SOURCE_ID, url, dest, manifest, force=args.force,
                expected_min_bytes=64, data_dir=data_dir, logger=logger,
            )
            if dl_status in ("failed", "needs_login"):
                failed += 1
        print("gdd done, failed=%s" % failed)
        return 1 if failed else 0
    if last_error is not None:
        return 1
    if missing_link:
        print("gdd done, failed=1")
        return 1
    print("gdd done, failed=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
