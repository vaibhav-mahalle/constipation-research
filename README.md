# Constipation research: India and US, 1995-2025

This repo studies constipation, food choices, physical activity, and economic class in India and the US over 30 years.

## Goal
- Collect data on four topics: constipation, food, physical activity, economic class.
- Split the data by age group, sex, region, and economic class.
- Show 30-year trends.
- Find links. Test 1 to 3 causal ideas on held-out data.
- Other countries come later.

## Rules
1. **No raw data in git.** The folder `data/` is in `.gitignore`. Scripts download and rebuild it. Many sources forbid redistribution.
2. **Label proxy data.** Direct constipation data is rare. Each source in `docs/sources.md` is marked direct or proxy.
3. **Explore first, test second.** Causal ideas are written down before the test. The test uses data that the exploration did not use.
4. **Say "linked with", not "causes",** unless a causal test supports it.
5. **One commit for each step.** The message says what changed, why, and which options were rejected.

## Where things are
| Path | Content |
|---|---|
| `docs/sources.md` | Each data source: link, license, years, direct or proxy |
| `docs/decisions/` | One file for each decision, with the reason |
| `docs/problems.md` | Each technical problem: symptom, cause, fix |
| `CHANGELOG.md` | One line for each finished stage |
| `CONTRIBUTING.md` | Commit and decision rules |
| `data/` | Local only. Not in git. |

## Status
Stage 1 (repo setup) and stage 2 (data audit) are done. The audit found 74 sources for India and the US. Direct constipation data is thin: see `docs/decisions/0002-source-audit-method-and-result.md`.
Stage 3 (collect, batch 1) is done: run `python3 scripts/fetch_all.py` to rebuild `data/` (NHANES 2005-2010, FAOSTAT, World Bank, Strain et al. activity files), then `python3 scripts/verify.py`. See `docs/coverage.md` for what the data can and cannot show. The Global Dietary Database needs a free account, which you register by hand.
Next: decide how to handle the weak constipation series, then stage 4 (clean and join).

## License
Code: MIT (see `LICENSE`). Data: each source keeps its own license. See `docs/sources.md`.
