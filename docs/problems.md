# Problems and fixes

Add one entry for each technical problem. Newest first.

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
