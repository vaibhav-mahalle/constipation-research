# constipation-research: facts that no file shows

Public repo. Constipation, food, activity, and economic class data for India and the US. Goal and rules: `README.md`. Working rules: `CONTRIBUTING.md`.

- **Tests:** `python3 -I -m unittest discover -s tests`. Do not use `python -m unittest tests.test_common`; `tests/` is not a package.
- **Hook:** `git config core.hooksPath .githooks` once per clone. The hook refuses a staged `data/` file, a failing test, and a gitleaks finding.
- **Rebuild data:** `python3 scripts/fetch_all.py`, then `python3 scripts/verify.py`. Run one fetcher at a time (the manifest has no lock). `--force` on `fetch_faostat.py` downloads the two zips (127 MB) again; complete unzipped files are skipped.
- **Never commit `data/`.** Check the license cell in `docs/sources.md` before you use a source. The Global Dietary Database needs a free account; register by hand.
- **Full text of papers:** PMC and Springer block WebFetch. Use `https://www.ebi.ac.uk/europepmc/webservices/rest/<PMCID>/fullTextXML`.
- **Check "not reported" claims.** A model's "no split found" is unchecked until you read the full text (`docs/problems.md`).
- **Where things go:** a decision in `docs/decisions/` (next number), a solved problem in `docs/problems.md`, a source in `docs/sources.md`. One commit for each step, with the reason in the message.
- **Map:** `docs/coverage.md` (what the data can show), `docs/research/` (published studies), `docs/audit-notes.md` (open doubts).
