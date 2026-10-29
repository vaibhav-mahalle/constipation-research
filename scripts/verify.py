"""Print each manifest row with exists, size-match, and SHA-256-match checks."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common


def check_row(data_dir, row):
    """Return (exists, size_ok, sha_ok) for one manifest row."""
    dest = Path(data_dir) / row.get("file", "")
    if not dest.is_file():
        return False, False, False
    try:
        size_ok = dest.stat().st_size == int(row.get("bytes", ""))
    except ValueError:
        size_ok = False
    sha_ok = bool(row.get("sha256")) and common.sha256_file(dest) == row["sha256"]
    return True, size_ok, sha_ok


def main(argv=None):
    parser = argparse.ArgumentParser(description="Verify files against the manifest.")
    parser.add_argument("--data-dir", default=None, help="data folder (default: repo data/)")
    args = parser.parse_args(argv)
    data_dir = common.resolve_data_dir(args.data_dir)
    manifest = common.Manifest(data_dir / "manifest.csv")
    if not manifest.rows:
        print("no manifest rows at %s" % manifest.path)
        return 1
    bad = 0
    for key in sorted(manifest.rows):
        row = manifest.rows[key]
        exists, size_ok, sha_ok = check_row(data_dir, row)
        ok = exists and size_ok and sha_ok
        bad += 0 if ok else 1
        print("%s file=%s exists=%s size_match=%s sha256_match=%s" % (
            "ok" if ok else "BAD", row.get("file", ""),
            "yes" if exists else "no", "yes" if size_ok else "no",
            "yes" if sha_ok else "no",
        ))
    print("verify done, bad=%s of %s" % (bad, len(manifest.rows)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
