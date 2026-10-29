"""Run the five fetchers in order. Print a summary. Exit 1 if any failed."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common
import fetch_faostat
import fetch_gdd
import fetch_nhanes
import fetch_who_gho
import fetch_worldbank

FETCHERS = [
    ("nhanes", fetch_nhanes),
    ("faostat", fetch_faostat),
    ("gdd", fetch_gdd),
    ("who_gho", fetch_who_gho),
    ("worldbank", fetch_worldbank),
]


def main(argv=None):
    parser = argparse.ArgumentParser(description="Run all fetchers in order.")
    common.add_common_args(parser)
    args = parser.parse_args(argv)
    forwarded = []
    if args.dry_run:
        forwarded.append("--dry-run")
    if args.force:
        forwarded.append("--force")
    if args.data_dir:
        forwarded += ["--data-dir", args.data_dir]

    results = []
    for name, module in FETCHERS:
        print("== %s ==" % name)
        try:
            code = module.main(forwarded)
        except Exception as error:  # keep going; record the failure
            print("%s raised: %s" % (name, error))
            code = 1
        results.append((name, "ok" if code == 0 else "failed"))
    print("summary:")
    for name, status in results:
        print("  %s: %s" % (name, status))
    failed = [name for name, status in results if status != "ok"]
    print("fetch_all done, failed=%s" % len(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
