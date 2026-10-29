"""Fetch WHO GHO physical-activity indicator data for IND and USA as JSON."""
import argparse
import json
import sys
import urllib.error
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common

SOURCE_ID = "who_gho"
BASE = "https://ghoapi.azureedge.net/api/"
INDICATOR_SEARCH = "physical activity"
TARGET_WORDS = ("insufficient physical activity", "adults")
TERMS_TEXT = (
    "WHO Global Health Observatory data.\n"
    "Read the WHO terms of use before use.\n"
    "Source: %s\n" % BASE
)


def who_indicator_list_url():
    """URL for the indicator list filtered by 'physical activity'."""
    query = urllib.parse.quote("$filter=contains(IndicatorName,'physical activity')", safe="$=,'()")
    return BASE + "Indicator?" + query


def who_data_url(indicator_code):
    """URL for one indicator, IND and USA only."""
    query = urllib.parse.quote(
        "$filter=SpatialDim eq 'IND' or SpatialDim eq 'USA'", safe="$=,'"
    )
    return BASE + urllib.parse.quote(indicator_code, safe="") + "?" + query


def find_indicator(indicator_list):
    """Pick the age-standardized adult insufficient-activity indicator, or None."""
    rows = indicator_list.get("value", []) if isinstance(indicator_list, dict) else []
    best = None
    for row in rows:
        name = (row.get("IndicatorName") or "").lower()
        if all(word in name for word in TARGET_WORDS):
            if "age-standardized" in name or "age-standardised" in name:
                return row
            best = best or row
    return best


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fetch WHO GHO indicator data.")
    common.add_common_args(parser)
    args = parser.parse_args(argv)
    list_url = who_indicator_list_url()
    if args.dry_run:
        print(list_url)
        print(BASE + "<IndicatorCode> (found at run time) "
              "?$filter=SpatialDim eq 'IND' or SpatialDim eq 'USA'")
        return 0
    data_dir = common.resolve_data_dir(args.data_dir)
    logger, _ = common.setup_logging(SOURCE_ID, data_dir)
    manifest = common.Manifest(data_dir / "manifest.csv")
    dest_dir = common.safe_dest(data_dir, SOURCE_ID, "x").parent
    common.write_note(dest_dir / "TERMS_NOTE.txt", TERMS_TEXT, data_dir=data_dir)

    list_dest = common.safe_dest(data_dir, SOURCE_ID, "indicator_list_physical_activity.json")
    status = common.fetch_one(
        SOURCE_ID, list_url, list_dest, manifest, force=args.force,
        expected_min_bytes=2, data_dir=data_dir, logger=logger,
    )
    if status == "needs_login":
        return 0
    if status == "failed":
        return 1
    try:
        indicator_list = json.loads(list_dest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        logger.error("bad indicator list JSON: %s", error)
        print("failed bad indicator list JSON (%s)" % error)
        return 1
    row = find_indicator(indicator_list)
    if not row or not row.get("IndicatorCode"):
        print("not_found insufficient physical activity indicator")
        logger.warning("not_found insufficient physical activity indicator")
        return 0
    code = row["IndicatorCode"]
    print("indicator %s: %s" % (code, row.get("IndicatorName", "")))
    data_dest = common.safe_dest(data_dir, SOURCE_ID, "%s_IND_USA.json" % code)
    status = common.fetch_one(
        SOURCE_ID, who_data_url(code), data_dest, manifest, force=args.force,
        expected_min_bytes=2, data_dir=data_dir, logger=logger,
    )
    print("who_gho done, failed=%s" % (1 if status == "failed" else 0))
    return 1 if status == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
