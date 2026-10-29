"""Offline tests: URL builders return the expected strings. No network."""
import io
import sys
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import fetch_faostat
import fetch_gdd
import fetch_nhanes
import fetch_strain_pa
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


class TestStrainUrls(unittest.TestCase):
    BASE = "https://raw.githubusercontent.com/MLGlobalHealth/PinA/main/"

    def test_exact_urls(self):
        self.assertEqual(
            fetch_strain_pa.strain_url(
                "results/Strain et al 2024 country and region estimates - Github.xlsx"),
            self.BASE + "results/Strain%20et%20al%202024%20country%20and%20region"
            "%20estimates%20-%20Github.xlsx",
        )
        self.assertEqual(
            fetch_strain_pa.strain_url("data/pina_dataset.csv"),
            self.BASE + "data/pina_dataset.csv",
        )
        self.assertEqual(
            fetch_strain_pa.strain_url("data/readme.md"),
            self.BASE + "data/readme.md",
        )
        self.assertEqual(
            fetch_strain_pa.strain_url("results/readme.md"),
            self.BASE + "results/readme.md",
        )

    def test_file_list(self):
        entries = fetch_strain_pa.strain_entries()
        self.assertEqual(
            [entry["url"] for entry in entries],
            [
                self.BASE + "results/Strain%20et%20al%202024%20country%20and%20region"
                "%20estimates%20-%20Github.xlsx",
                self.BASE + "data/pina_dataset.csv",
                self.BASE + "data/readme.md",
                self.BASE + "results/readme.md",
            ],
        )
        self.assertEqual(
            [entry["filename"] for entry in entries],
            [
                "strain_et_al_2024_country_region_estimates.xlsx",
                "pina_dataset.csv",
                "data_readme.md",
                "results_readme.md",
            ],
        )
        self.assertEqual(
            [entry["expected_min_bytes"] for entry in entries],
            [1_000_000, 1_000_000, 10, 10],
        )


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

    def test_needs_account_page_no_download(self):
        html = (
            "<html><body><p>Create Your New Account</p>"
            "<p>Login to Your Existing Account</p></body></html>"
        )
        self.assertTrue(fetch_gdd.is_needs_account_page(html))
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            out = io.StringIO()
            with unittest.mock.patch.object(
                fetch_gdd.common, "fetch_text", return_value=(html, 200)
            ) as mock_fetch, unittest.mock.patch.object(
                fetch_gdd.common, "fetch_one"
            ) as mock_download, redirect_stdout(out):
                code = fetch_gdd.main(["--data-dir", str(data_dir)])
            self.assertEqual(code, 0)
            self.assertEqual(mock_fetch.call_count, 1)
            mock_download.assert_not_called()
            text = out.getvalue()
            self.assertIn(
                "needs_account https://gdd.nutrition.tufts.edu/data-download", text)
            self.assertIn(
                "GDD data need a free account. Register by hand, read the terms, "
                "then put the files in data/raw/gdd/.", text)
            dest_dir = data_dir / "raw" / "gdd"
            files = sorted(p.name for p in dest_dir.iterdir()) if dest_dir.exists() else []
            self.assertEqual(files, ["TERMS_NOTE.txt"])


if __name__ == "__main__":
    unittest.main()
