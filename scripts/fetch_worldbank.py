"""Fetch World Bank API v2 indicators for IND and USA, 1995-2025."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

SOURCE_ID = "worldbank"
INDICATORS = ["SI.POV.GINI", "NY.GDP.PCAP.PP.KD"]
LICENSE_TEXT = (
    "World Bank data.\n"
    "Licence: CC BY 4.0\n"
    "Source: https://api.worldbank.org/v2/\n"
)


def worldbank_url(code):
    """Build one World Bank API URL."""
    return (
        "https://api.worldbank.org/v2/country/IND;USA/indicator/%s"
        "?format=json&per_page=1000&date=1995:2025" % code
    )


def worldbank_entries():
    return [
        {"url": worldbank_url(code), "filename": "%s.json" % code, "code": code}
        for code in INDICATORS
    ]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fetch World Bank indicators.")
    common.add_common_args(parser)
    args = parser.parse_args(argv)
    entries = worldbank_entries()
    if args.dry_run:
        for entry in entries:
            print(entry["url"])
        return 0
    data_dir = common.resolve_data_dir(args.data_dir)
    logger, _ = common.setup_logging(SOURCE_ID, data_dir)
    manifest = common.Manifest(data_dir / "manifest.csv")
    dest_dir = common.safe_dest(data_dir, SOURCE_ID, "x").parent
    common.write_note(dest_dir / "LICENSE_NOTE.txt", LICENSE_TEXT, data_dir=data_dir)
    failed = 0
    for entry in entries:
        dest = common.safe_dest(data_dir, SOURCE_ID, entry["filename"])
        status = common.fetch_one(
            SOURCE_ID, entry["url"], dest, manifest, force=args.force,
            expected_min_bytes=2, data_dir=data_dir, logger=logger,
        )
        if status in ("failed", "needs_login"):
            failed += 1
    print("worldbank done, failed=%s" % failed)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
