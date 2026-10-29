# 0001: Public repo, no raw data in git

- Date: 2026-10-30
- Status: accepted

## Context
The repo is public on the personal GitHub. The study needs survey and statistics data from many sources (for example GBD, NHANES, NFHS, FAO). Some sources forbid redistribution, even of derived tables.

## Options
| Option | For | Against |
|---|---|---|
| Commit the data | Easy to reproduce | License risk. Large files. Hard to remove from git history. |
| Commit scripts and source links only | No license risk. Small repo. | A reader must run the scripts. Sources can move. |
| Private repo first | Safe while the audit runs | The user chose public. |

## Decision
Commit scripts, source links, and a data dictionary. Do not commit raw or derived data. Use the MIT license for code only.

## Reason
The user wants a public repo. Scripts give the same result for the reader and avoid a license breach. If the audit shows that a source allows redistribution, a later decision can add that one table.

## Effects
- `data/` and common data file types are in `.gitignore`.
- Each source needs a license check in `docs/sources.md` before use.
- Each data script must be re-runnable from a clean clone.
