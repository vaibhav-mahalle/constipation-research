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
TERMS_TEXT = (
    "Global Dietary Database (GDD) data.\n"
    "All data are property of Tufts University.\n"
    "Read the Terms and Conditions of Use on the GDD site before any use.\n"
    "Source: %s\n" % PAGE_URL
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


def _filename_from_url(url, fallback):
    name = Path(urllib.parse.urlparse(url).path).name
    return name or fallback


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fetch GDD fibre data and codebook.")
    common.add_common_args(parser)
    args = parser.parse_args(argv)
    if args.dry_run:
        print(PAGE_URL)
        print("fibre CSV and codebook URLs are found on that page at run time")
        return 0
    data_dir = common.resolve_data_dir(args.data_dir)
    logger, _ = common.setup_logging(SOURCE_ID, data_dir)
    manifest = common.Manifest(data_dir / "manifest.csv")
    dest_dir = common.safe_dest(data_dir, SOURCE_ID, "x").parent
    common.write_note(dest_dir / "TERMS_NOTE.txt", TERMS_TEXT, data_dir=data_dir)
    try:
        html_text, status = common.fetch_text(PAGE_URL, logger=logger)
    except Exception as error:  # urllib errors: log the real failure, stop.
        logger.error("failed %s: %s", PAGE_URL, error)
        print("failed %s (%s)" % (PAGE_URL, error))
        return 1
    if status in (401, 403) or not html_text:
        print("needs_login %s" % PAGE_URL)
        logger.warning("needs_login %s http_status=%s", PAGE_URL, status)
        return 0
    links = parse_gdd_links(html_text)
    failed = 0
    planned = [
        ("fibre", links["fibre"], "gdd_fibre_country.csv"),
        ("codebook", links["codebook"], "gdd_codebook.pdf"),
    ]
    for kind, url, fallback in planned:
        if not url:
            print("not_found %s on %s" % (kind, PAGE_URL))
            logger.warning("not_found %s on %s", kind, PAGE_URL)
            continue
        dest = common.safe_dest(data_dir, SOURCE_ID, _filename_from_url(url, fallback))
        status = common.fetch_one(
            SOURCE_ID, url, dest, manifest, force=args.force,
            expected_min_bytes=64, data_dir=data_dir, logger=logger,
        )
        if status == "failed":
            failed += 1
    print("gdd done, failed=%s" % failed)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
