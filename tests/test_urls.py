"""Offline tests: URL builders return the expected strings. No network."""
import hashlib
import io
import sys
import tempfile
import unittest
import unittest.mock
import zipfile
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


class TestGddSchemeFilter(unittest.TestCase):
    def test_file_link_labelled_fiber_gives_no_fibre(self):
        html = '<a href="file:///etc/passwd">fiber</a>'
        links = fetch_gdd.parse_gdd_links(html)
        self.assertIsNone(links["fibre"])


class TestNeedsLoginExits(unittest.TestCase):
    def _run(self, module):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            with unittest.mock.patch.object(
                module.common, "fetch_one", return_value="needs_login"
            ), redirect_stdout(io.StringIO()):
                return module.main(["--data-dir", str(data_dir)]), data_dir

    def test_nhanes_needs_login_exits_1(self):
        code, _ = self._run(fetch_nhanes)
        self.assertEqual(code, 1)

    def test_worldbank_needs_login_exits_1(self):
        code, _ = self._run(fetch_worldbank)
        self.assertEqual(code, 1)

    def test_strain_needs_login_exits_1(self):
        code, _ = self._run(fetch_strain_pa)
        self.assertEqual(code, 1)

    def test_faostat_needs_login_exits_1(self):
        code, _ = self._run(fetch_faostat)
        self.assertEqual(code, 1)


class TestNhanesTermsNote(unittest.TestCase):
    def test_note_written_with_mocked_downloads(self):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            with unittest.mock.patch.object(
                fetch_nhanes.common, "fetch_one", return_value="skip"
            ), redirect_stdout(io.StringIO()):
                code = fetch_nhanes.main(["--data-dir", str(data_dir)])
            self.assertEqual(code, 0)
            note = data_dir / "raw" / "nhanes" / "TERMS_NOTE.txt"
            self.assertTrue(note.exists())
            self.assertEqual(
                note.read_text(encoding="utf-8").strip(),
                "NHANES data, CDC NCHS. Terms (NCHS data use): use the data for "
                "statistical reporting and analysis only; make no attempt to learn "
                "the identity of any person; do not link this dataset with "
                "individually identifiable data from other datasets. Cite the "
                "NHANES cycle and file name.",
            )


class TestGddMissingLinks(unittest.TestCase):
    def _run_gdd(self, html, fetch_one_status="ok"):
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            with unittest.mock.patch.object(
                fetch_gdd.common, "fetch_text", return_value=(html, 200)
            ), unittest.mock.patch.object(
                fetch_gdd.common, "fetch_one", return_value=fetch_one_status
            ), redirect_stdout(io.StringIO()):
                return fetch_gdd.main(["--data-dir", str(data_dir)])

    def test_no_links_no_account_wall_exits_1(self):
        self.assertEqual(self._run_gdd("<html><body>hello</body></html>"), 1)

    def test_missing_codebook_exits_1(self):
        html = '<a href="/files/fiber_country.csv">Dietary fibre (CSV)</a>'
        self.assertEqual(self._run_gdd(html), 1)

    def test_needs_account_still_exits_0(self):
        html = ("<html><body><p>Create Your New Account</p>"
                "<p>Login to Your Existing Account</p></body></html>")
        self.assertEqual(self._run_gdd(html), 0)


class TestFaostatExtractedManifest(unittest.TestCase):
    def test_first_records_second_skips_changed_reextracts(self):
        import common as common_mod

        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            dest_dir = data_dir / "raw" / "faostat"
            dest_dir.mkdir(parents=True)
            members = {
                fetch_faostat.FILENAMES[0]: {"a.csv": b"a,b\n1,2\n"},
                fetch_faostat.FILENAMES[1]: {"b.csv": b"c,d\n3,4\n"},
            }
            for filename, files in members.items():
                with zipfile.ZipFile(dest_dir / filename, "w") as archive:
                    for name, data in files.items():
                        archive.writestr(name, data)

            def run():
                out = io.StringIO()
                with unittest.mock.patch.object(
                    fetch_faostat.common, "fetch_one", return_value="skip"
                ), redirect_stdout(out):
                    code = fetch_faostat.main(["--data-dir", str(data_dir)])
                return code, out.getvalue()

            code, _ = run()
            self.assertEqual(code, 0)
            manifest = common_mod.Manifest(data_dir / "manifest.csv")
            for filename, files in members.items():
                for name, data in files.items():
                    row = manifest.find(dest_dir / name)
                    self.assertIsNotNone(row, name)
                    self.assertEqual(row["source_id"], "faostat")
                    self.assertEqual(row["url"], fetch_faostat.faostat_url(filename) + "#" + name)
                    self.assertEqual(row["bytes"], str(len(data)))
                    self.assertEqual(row["sha256"], hashlib.sha256(data).hexdigest())
                    self.assertEqual(row["http_status"], "200")
                    self.assertEqual((dest_dir / name).read_bytes(), data)

            code, out = run()
            self.assertEqual(code, 0)
            self.assertIn("skip (complete)", out)

            (dest_dir / "a.csv").write_bytes(b"tampered longer content")
            code, _ = run()
            self.assertEqual(code, 0)
            self.assertEqual((dest_dir / "a.csv").read_bytes(), b"a,b\n1,2\n")


if __name__ == "__main__":
    unittest.main()
