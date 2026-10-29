# 0002: Source audit method and result

- Date: 2026-10-30
- Status: accepted

## Context
The study needs data for India and the US on constipation, food, physical activity, and economic class. Many sources exist, and outside models can invent sources or give wrong URLs. The user asked for an exhaustive audit and for Muse and Codex to help.

## Options
| Option | For | Against |
|---|---|---|
| One searcher (Claude) | Simple; every page is read | Misses sources; slow |
| Three searchers, Claude checks every page (chosen) | More sources; independent finds raise trust | Costs more; outside rows stay leads until opened |
| Trust outside tables as they are | Fast | Muse gave a wrong URL in its first report |

## Decision
Use Claude, Muse (two passes), and Codex. Codex has no web access because of its approval hooks, so it reviews the table from its own knowledge. Claude opens pages. Each row in `docs/sources.md` has a `Checked` column. A source is used only after its page is opened and its license is read.

## Result
- 74 source rows: 21 constipation, 18 food, 18 activity, 17 economic class.
- Pass 1 (Muse) gave 42 sources. Pass 2 (Muse) and the Codex review added 30 rows. (The commit message of `8fd2f40` says 27. The correct number is 30.)
- Claude opened the pages of about 28 rows (see the `Checked` column). The other rows are leads.
- Pages that returned HTTP 403 or 404 for Claude: DHS terms, IHME terms, ICPSR, GHDx, PIB Time Use Survey. Their license cells say `not checked`.
- Codex raised about 35 doubts about rows. They are in `docs/audit-notes.md`, status open. They are not yet checked.

## Findings that change later plans
1. **Constipation data is the weak point.**
   - US: NHANES has stool frequency and Bristol form in 2005-2008 and self-reported constipation only in 2009-2010. The NHIS item runs to 1996 in IPUMS, and the later item is not comparable.
   - India: no national survey has a confirmed constipation item. LASI has it only inside a combined digestive item.
   - A 30-year constipation series does not exist in the listed sources. Plan 3 must use proxies and published prevalence studies, and label them.
2. **No source has all four topics for the same people over 1995-2025.** NHANES is the closest in the US, for selected cycles. India has no equivalent.
3. **Some licenses forbid linking.** NCHS and MEPS terms forbid linking identifiable records with other datasets. All of Us allows analysis only inside its workbench. The study must join at group level (year, age band, sex, region, class), not person level.
4. **India class data** is expenditure (HCES, NSS), wealth quintile (NFHS), and income (IHDS), and each measures something different.

## Effects
- Plan 3 (collect) starts with sources that are open and have the most direct data: NHANES (BHQ, diet, activity, income), BRFSS, FAOSTAT, GDD, WHO activity estimates, ACS, CPS, World Bank. Registration sources (LASI, NFHS, IHDS, NHATS) come after the user approves each registration.
- Open doubts in `docs/audit-notes.md` become checks at the start of plan 3.
- The user must decide about the weak constipation series before plan 5. Options: proxies only, a literature-based series, or a narrower period.
