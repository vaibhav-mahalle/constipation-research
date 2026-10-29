# 0003: Collect batch 1 with Muse-built scripts

- Date: 2026-10-30
- Status: accepted

## Context
Batch 1 downloads the open sources found in the audit (decision 0002). The user asked that Muse does the downloading work, at medium reasoning effort, and that long jobs run detached.

## Options
| Option | For | Against |
|---|---|---|
| Claude writes and runs the scripts | One author; fast | The user asked for Muse; no second view |
| Muse builds, Claude reads every line and runs (chosen) | Offloads the work; Claude reads all code before it runs | Costs Muse quota (about 10% per round); Claude still reviews |
| Use the `nhanes` packages from PyPI or CRAN | Less code | Extra dependencies and licences; does not cover the other sources |

## Decision
Muse builds the scripts from a no-code brief, in a clean folder, with `--contributor-mode off`, at medium effort, as a detached job. Claude reads the whole diff before any script enters the repo, then runs the scripts detached. Codex reviews the scripts read-only, with no web. Standard library only. Data goes to `data/` (not in git) and each file has a SHA-256 in `data/manifest.csv`.

## Result
- Three Muse rounds: build (1,141 lines, 25 tests), a fix for two live failures, and a fix for seven review findings. 43 tests pass.
- Claude found one bug in the first build (a documentation page could count as a login wall). Codex found 7 real defects in the scripts. See `docs/problems.md`.
- Downloaded and verified: 41 of 41 manifest files match (NHANES 2005-2010: 24 files; FAOSTAT food balance: 2 zips and 9 unzipped files; World Bank: 2 indicators; Strain et al. activity files: 4).
- Not downloaded: Global Dietary Database (needs a free account).
- Replaced: the WHO API is retired, so the activity estimates come from the authors' GitHub repo (no LICENSE file; do not redistribute).
- `docs/coverage.md` shows what the data can show: a person-level US join for 2005-2010 (15,190 adults with bowel traits and an income ratio), and country-level series for 2000-2022. There is no constipation series for either country over 1995-2025, and no India constipation data at all.

## Effects
- The study cannot show a 30-year constipation trend with batch 1. The user must choose how to handle this before plan 5 (see `docs/coverage.md`, "Next decisions").
- Plan 4 (clean and join) can start with the US NHANES join and the country series.
- Scripts must be run one at a time (no manifest lock).
- Each new source needs a HEAD request check of its URL before the build.
