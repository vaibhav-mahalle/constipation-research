"""Fetch Strain et al. 2024 physical-activity files from GitHub PinA."""
import argparse
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

SOURCE_ID = "strain_pa"
BASE = "https://raw.githubusercontent.com/MLGlobalHealth/PinA/main/"
LICENSE_TEXT = (
    "Strain et al. 2024, Lancet Global Health, "
    "doi 10.1016/S2214-109X(24)00150-5. "
    "Source: GitHub MLGlobalHealth/PinA. "
    "No LICENSE file was found in the repository on 2026-10-30. "
    "Do not redistribute the files. Cite the paper."
)
# (repo path, plain file name, minimum bytes)
FILES = [
    (
        "results/Strain et al 2024 country and region estimates - Github.xlsx",
        "strain_et_al_2024_country_region_estimates.xlsx",
        1_000_000,
    ),
    ("data/pina_dataset.csv", "pina_dataset.csv", 1_000_000),
    ("data/readme.md", "data_readme.md", 10),
    ("results/readme.md", "results_readme.md", 10),
]


def strain_url(repo_path):
    """Build one raw GitHub URL. Encode spaces as %20."""
    return BASE + urllib.parse.quote(repo_path)


def strain_entries():
    """Return dicts with url, filename, expected_min_bytes for all files."""
    return [
        {
            "url": strain_url(repo_path),
            "filename": filename,
            "expected_min_bytes": minimum,
        }
        for repo_path, filename, minimum in FILES
    ]


# Alias that matches the other fetchers' file-list helpers.
strain_files = strain_entries


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fetch Strain et al. 2024 files.")
    common.add_common_args(parser)
    args = parser.parse_args(argv)
    entries = strain_entries()
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
            expected_min_bytes=entry["expected_min_bytes"],
            data_dir=data_dir, logger=logger,
        )
        if status in ("failed", "needs_login"):
            failed += 1
    print("strain_pa done, failed=%s" % failed)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
