"""Fetch FAOSTAT food balance bulk zip files. Check file names at run time."""
import argparse
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

SOURCE_ID = "faostat"
BULK_BASE = "https://bulks-faostat.fao.org/production/"
BULK_PAGE = "https://www.fao.org/faostat/en/#data/FBS"
# Past release names. The script logs the real HTTP status if a name changed.
FILENAMES = [
    "FoodBalanceSheets_E_All_Data_(Normalized).zip",
    "FoodBalanceSheetsHistoric_E_All_Data_(Normalized).zip",
]


def faostat_url(filename):
    return BULK_BASE + filename


def faostat_entries():
    return [{"url": faostat_url(name), "filename": name} for name in FILENAMES]


def license_text():
    year = datetime.now(timezone.utc).year
    return (
        "FAOSTAT food balance sheets.\n"
        "Licence: CC BY 4.0\n"
        "Citation format: FAO. [year]. [database: dataset]. Licence: CC-BY-4.0\n"
        "Citation for this download: FAO. %s. FAOSTAT: Food Balances. "
        "Licence: CC-BY-4.0\n"
        "Bulk page: %s\n" % (year, BULK_PAGE)
    )


def unzip_safe(zip_path, dest_dir, logger, manifest=None, zip_url=None):
    """Unzip into dest_dir. Refuse members that escape dest_dir.

    With a manifest, record each member. Skip a member that is complete.
    Extract via a .part file. Never write a partial file to its final name.
    """
    dest_dir = Path(dest_dir)
    base_url = zip_url if zip_url is not None else str(zip_path)
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.namelist():
            if member.endswith("/"):
                continue
            target = (dest_dir / member).resolve()
            if dest_dir.resolve() not in target.parents and target != dest_dir.resolve():
                logger.error("skip unsafe zip member %s", member)
                continue
            if manifest is not None and common.is_complete(target, manifest):
                print("skip (complete) %s" % target)
                logger.info("skip (complete) %s", target)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            part = target.with_name(target.name + ".part")
            if part.is_symlink():
                part.unlink()
            with archive.open(member) as source, open(part, "wb") as out:
                while True:
                    chunk = source.read(1024 * 256)
                    if not chunk:
                        break
                    out.write(chunk)
            digest = common.sha256_file(part)
            size = part.stat().st_size
            part.replace(target)
            if manifest is not None:
                manifest.record(
                    SOURCE_ID, target, "%s#%s" % (base_url, member),
                    size, digest, 200)
            print("unzipped %s" % target)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fetch FAOSTAT bulk files.")
    common.add_common_args(parser)
    args = parser.parse_args(argv)
    entries = faostat_entries()
    if args.dry_run:
        for entry in entries:
            print(entry["url"])
        return 0
    data_dir = common.resolve_data_dir(args.data_dir)
    logger, _ = common.setup_logging(SOURCE_ID, data_dir)
    manifest = common.Manifest(data_dir / "manifest.csv")
    dest_dir = common.safe_dest(data_dir, SOURCE_ID, "x").parent
    common.write_note(dest_dir / "LICENSE_NOTE.txt", license_text(), data_dir=data_dir)
    failed = 0
    for entry in entries:
        dest = common.safe_dest(data_dir, SOURCE_ID, entry["filename"])
        status = common.fetch_one(
            SOURCE_ID, entry["url"], dest, manifest, force=args.force,
            expected_min_bytes=1024, data_dir=data_dir, logger=logger,
        )
        if status in ("failed", "needs_login"):
            failed += 1
        elif dest.is_file():
            try:
                unzip_safe(dest, dest_dir, logger, manifest=manifest,
                           zip_url=entry["url"])
            except zipfile.BadZipFile as error:
                logger.error("bad zip %s: %s", dest, error)
                print("failed bad zip %s" % dest)
                failed += 1
    print("faostat done, failed=%s" % failed)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
