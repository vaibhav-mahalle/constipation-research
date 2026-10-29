# Problems and fixes

Add one entry for each technical problem. Newest first.

## 2026-10-30: Muse quota ran out during the literature search
- **Symptom:** The Muse research run ended with status `failed` and "API error 429 ... Subscription quota exhausted" after 31 searches and 14 page fetches. No table was written.
- **Cause:** `muse usage` showed the window at 84% before the start. Earlier Muse rounds in the same window had used the rest.
- **Fix:** No Muse output is used. The second independent search did not happen, so the study list has one searcher. A rerun after the window resets is possible.
- **Prevent:** Start a research run only if the window is below about 60%, or wait for the reset.

## 2026-10-30: A research agent's table had errors that only the full text showed
- **Symptom:** The agent said the Kerala study (IN09) had no constipation split. Table 6 of the paper has splits by age, sex, education, and residence. The agent also missed that a 12-city study gives 19.7% in its text and 12.2% in its table.
- **Cause:** The agent read mostly abstracts through an API. A claim of "not reported" is a claim about the whole paper.
- **Fix:** Claude opened 19 papers and corrected the rows. Each row now says what Claude read.
- **Prevent:** Treat "no split found" and "not reported" as unchecked until the full text is read.

## 2026-10-30: WHO retired the Global Health Observatory API
- **Symptom:** `fetch_who_gho.py` failed with HTTP 500 on all three tries. `ghoapi.azureedge.net` returned 500 even for `Indicator?$top=2`. `ghoapi.who.int` did not resolve (curl exit 6).
- **Cause:** WHO's legacy page says the old API is retired. A search found no confirmed new endpoint.
- **Fix:** The same insufficient-activity estimates (Strain et al., Lancet Global Health 2024) are public in the authors' GitHub repo `MLGlobalHealth/PinA`. `fetch_strain_pa.py` takes the country estimates and the survey inputs from there. The repo has no LICENSE file, so the note says "do not redistribute".
- **Prevent:** The brief for each source named a URL that nobody had opened. A later plan checks each URL with a HEAD request before the build.

## 2026-10-30: The Global Dietary Database download needs an account
- **Symptom:** `fetch_gdd.py` printed "not_found fibre" on both pages.
- **Cause:** The audit row said "open download". The page `data-download` shows only "Create Your New Account" and "Login to Your Existing Account" and has no file links.
- **Fix:** The script prints `needs_account` and writes no data. `docs/sources.md` row F2 is corrected. Registration is the owner's decision.
- **Prevent:** Open the download page, not only the description page, before the audit marks a source "open".

## 2026-10-30: A documentation page looked like a login wall
- **Symptom:** None in a live run. Claude found it while reading Muse's code.
- **Cause:** The login check looked for `<form` and the word `login` in the first 4 KB. A NHANES `.htm` page with a search form and a login link would match, and the script would skip the file.
- **Fix:** The login check does not apply to `.htm` and `.html` files. A new test covers it.
- **Prevent:** Read outside-model code line by line. The first round of tests had no HTML page that is legitimate.

## 2026-10-30: Codex review of the scripts: seven real defects
- **Symptom:** A read-only Codex review found 8 points. Claude checked each against the code. 7 were real.
- **Cause (main ones):** A truncated download was saved as complete (no `Content-Length` check) and skipped on every later run. FAOSTAT unzipped files had no manifest rows, so 2 GB was extracted again on each run. A run where all requests returned HTTP 403 reported "ok". Symlinked temp files could write outside `data/`. Redirects to other hosts and `file:` links were not refused. NHANES had no terms note.
- **Fix:** Muse round 3 (medium effort) with a failing test for each item. 17 new tests. A live rerun then passed: 41 of 41 manifest files match.
- **Not fixed on purpose:** two fetchers running at the same time can lose manifest rows. The runs are sequential.
- **Prevent:** Run the Codex review after the first build, not only at the end.

## 2026-10-30: An outside model could not do web research (Codex)
- **Symptom:** Codex stopped and wrote: "The plan gate blocked web access." It also asked the user a question about the goal instead of doing the task.
- **Cause:** Codex runs the same local approval hooks as the main assistant. The approval is kept for each session, so a new Codex session has none. A local "goal first" rule also made it ask a question.
- **Fix:** Codex got a brief that states the goal and says "do not ask questions". Codex does not search the web. It reviews a table that Claude gives it, from its own knowledge. Claude opens each page.
- **Prevent:** Use Codex for review, not for web research. A change to the gate is a separate decision for the repo owner.

## 2026-10-30: An outside model gave a wrong page URL (Muse)
- **Symptom:** Muse listed the NHANES bowel questionnaire with the URL of the physical-activity monitor file (`PAX80_G`). A second URL went through a university library proxy.
- **Cause:** The model joined a source name to a nearby page without checking that the page matches. Its own report said that several pages did not open.
- **Fix:** Claude opened the real bowel files (`BHQ_D`, `BHQ_E`, `BHQ_F`) and wrote the URLs from them. Rows that Claude did not open say `Muse` in the Checked column.
- **Prevent:** The Checked column in `docs/sources.md`. A source enters use only after its page is opened.

## 2026-10-30: Muse run ended with an empty output file
- **Symptom:** `muse exec` exited with code 0, but `out.md` had 0 bytes.
- **Cause:** Not proven. The plain run ended with no output and no error in its log. A second run with `--json` worked, so the final answer was in the event log.
- **Fix:** Run with `--json` and read the final text from the event log with a short script.
- **Prevent:** After each outside-model run, check that the output file is not empty, and read the log for errors.

## Template
### YYYY-MM-DD: <short title>
- **Symptom:** what we saw (include the exact error text).
- **Cause:** what was wrong, and how we know.
- **Fix:** what we changed. Link the commit.
- **Prevent:** a test or a rule that stops it from coming back.
