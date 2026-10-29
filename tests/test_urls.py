"""Offline tests: URL builders return the expected strings. No network."""
import sys
import unittest
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import fetch_faostat
import fetch_gdd
import fetch_nhanes
import fetch_who_gho
import fetch_worldbank

NHANES = "https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public"


class TestNhanesUrls(unittest.TestCase):
    def test_cycle_urls(self):
        cases = [
            (2005, "BHQ", "D", NHANES + "/2005/DataFiles/BHQ_D.xpt"),
            (2007, "DEMO", "E", NHANES + "/2007/DataFiles/DEMO_E.xpt"),
            (2009, "DR1TOT", "F", NHANES + "/2009/DataFiles/DR1TOT_F.xpt"),
            (2009, "PAQ", "F", NHANES + "/2009/DataFiles/PAQ_F.xpt"),
        ]
        for year, name, letter, expected in cases:
            self.assertEqual(fetch_nhanes.nhanes_url(year, name, letter), expected)

    def test_doc_url(self):
        self.assertEqual(
            fetch_nhanes.nhanes_url(2009, "BHQ", "F", "htm"),
            NHANES + "/2009/DataFiles/BHQ_F.htm",
        )

    def test_entries_cover_cycles_names_and_docs(self):
        entries = fetch_nhanes.nhanes_entries()
        self.assertEqual(len(entries), 3 * 4 * 2)  # cycles x names x (xpt + htm)
        urls = {entry["url"] for entry in entries}
        self.assertIn(NHANES + "/2005/DataFiles/BHQ_D.xpt", urls)
        self.assertIn(NHANES + "/2007/DataFiles/DR1TOT_E.htm", urls)
        bhq_f = [e for e in entries if e["filename"] == "BHQ_F.xpt"][0]
        self.assertGreater(bhq_f["expected_min_bytes"], 100_000)  # about 570 KB


class TestFaostatUrls(unittest.TestCase):
    def test_bulk_urls(self):
        self.assertEqual(
            fetch_faostat.faostat_url("FoodBalanceSheets_E_All_Data_(Normalized).zip"),
            "https://bulks-faostat.fao.org/production/"
            "FoodBalanceSheets_E_All_Data_(Normalized).zip",
        )
        urls = [entry["url"] for entry in fetch_faostat.faostat_entries()]
        self.assertEqual(urls, [
            "https://bulks-faostat.fao.org/production/"
            "FoodBalanceSheets_E_All_Data_(Normalized).zip",
            "https://bulks-faostat.fao.org/production/"
            "FoodBalanceSheetsHistoric_E_All_Data_(Normalized).zip",
        ])


class TestWorldBankUrls(unittest.TestCase):
    def test_indicator_urls(self):
        self.assertEqual(
            fetch_worldbank.worldbank_url("SI.POV.GINI"),
            "https://api.worldbank.org/v2/country/IND;USA/indicator/SI.POV.GINI"
            "?format=json&per_page=1000&date=1995:2025",
        )
        self.assertEqual(
            fetch_worldbank.worldbank_url("NY.GDP.PCAP.PP.KD"),
            "https://api.worldbank.org/v2/country/IND;USA/indicator/NY.GDP.PCAP.PP.KD"
            "?format=json&per_page=1000&date=1995:2025",
        )


class TestWhoUrls(unittest.TestCase):
    def test_indicator_list_url(self):
        url = fetch_who_gho.who_indicator_list_url()
        self.assertTrue(url.startswith("https://ghoapi.azureedge.net/api/Indicator?"))
        # The query is URL-encoded; decode before the text check.
        self.assertIn("contains(IndicatorName,'physical activity')",
                      urllib.parse.unquote(url))

    def test_data_url_filters_ind_and_usa(self):
        url = fetch_who_gho.who_data_url("MK_ABC_123")
        self.assertTrue(url.startswith("https://ghoapi.azureedge.net/api/MK_ABC_123?"))
        self.assertIn("SpatialDim eq 'IND' or SpatialDim eq 'USA'",
                      urllib.parse.unquote(url))

    def test_find_indicator_prefers_age_standardized_adults(self):
        rows = {"value": [
            {"IndicatorCode": "X1", "IndicatorName": "Physical activity in children"},
            {"IndicatorCode": "X2", "IndicatorName":
             "Prevalence of insufficient physical activity among adults aged 18+ years "
             "(age-standardized estimate) (%)"},
        ]}
        self.assertEqual(fetch_who_gho.find_indicator(rows)["IndicatorCode"], "X2")
        self.assertIsNone(fetch_who_gho.find_indicator({"value": []}))


class TestGddLinks(unittest.TestCase):
    def test_page_url(self):
        self.assertEqual(
            fetch_gdd.gdd_page_url(),
            "https://gdd.nutrition.tufts.edu/available-gdd-2018-estimates-datafiles",
        )

    def test_parse_fibre_and_codebook_links(self):
        html = """
        <a href="/files/fiber_country.csv">Dietary fibre, country level (CSV)</a>
        <a href="codebook2018.pdf">GDD 2018 Codebook</a>
        <a href="/files/sodium_country.csv">Sodium (CSV)</a>
        """
        links = fetch_gdd.parse_gdd_links(html)
        self.assertEqual(links["fibre"],
                         "https://gdd.nutrition.tufts.edu/files/fiber_country.csv")
        self.assertEqual(links["codebook"],
                         "https://gdd.nutrition.tufts.edu/codebook2018.pdf")

    def test_parse_no_fibre_link(self):
        links = fetch_gdd.parse_gdd_links('<a href="/x.csv">Sodium</a>')
        self.assertIsNone(links["fibre"])
        self.assertIsNone(links["codebook"])


if __name__ == "__main__":
    unittest.main()
