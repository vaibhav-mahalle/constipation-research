"""Fetch NHANES files (CDC NCHS) for 2005-2010. Check each URL at run time."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

SOURCE_ID = "nhanes"
BASE = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public"
CYCLES = [(2005, "D"), (2007, "E"), (2009, "F")]  # (start year, file letter)
NAMES = ["BHQ", "DEMO", "DR1TOT", "PAQ"]


def nhanes_url(year, name, letter, ext="xpt"):
    """Build one NHANES file URL. YEAR in the path is the cycle start year."""
    return "%s/%s/DataFiles/%s_%s.%s" % (BASE, year, name, letter, ext)


def nhanes_entries():
    """Return dicts with url, filename, expected_min_bytes for all files."""
    entries = []
    for year, letter in CYCLES:
        for name in NAMES:
            for ext in ("xpt", "htm"):
                filename = "%s_%s.%s" % (name, letter, ext)
                # BHQ_F.xpt is about 570 KB. Use a lower safe bound.
                minimum = 400_000 if filename == "BHQ_F.xpt" else (512 if ext == "htm" else 1024)
                entries.append({
                    "url": nhanes_url(year, name, letter, ext),
                    "filename": filename,
                    "expected_min_bytes": minimum,
                })
    return entries


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fetch NHANES files.")
    common.add_common_args(parser)
    args = parser.parse_args(argv)
    entries = nhanes_entries()
    if args.dry_run:
        for entry in entries:
            print(entry["url"])
        return 0
    data_dir = common.resolve_data_dir(args.data_dir)
    logger, _ = common.setup_logging(SOURCE_ID, data_dir)
    manifest = common.Manifest(data_dir / "manifest.csv")
    failed = 0
    for entry in entries:
        dest = common.safe_dest(data_dir, SOURCE_ID, entry["filename"])
        status = common.fetch_one(
            SOURCE_ID, entry["url"], dest, manifest, force=args.force,
            expected_min_bytes=entry["expected_min_bytes"], data_dir=data_dir, logger=logger,
        )
        if status == "failed":
            failed += 1
    print("nhanes done, failed=%s" % failed)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
