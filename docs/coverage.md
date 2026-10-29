# What the data in hand can show (batch 1)

Date: 2026-10-30. Source: the files that `scripts/fetch_all.py` downloaded into `data/` (not in git), checked with `scripts/verify.py` (28 of 28 files match the manifest) and with short counts in Python.
All numbers below were measured on those files. Nothing here is an analysis result.

## Summary
- **US, person level, 2005-2010:** a good joint dataset. Constipation traits, fibre intake, activity questions, and an income ratio can be joined for the same adults. It has only three survey cycles over six years, so it cannot show a 30-year change.
- **Both countries, country level, 2000-2022:** activity, food supply, and income series exist. They show change over time, but they have no constipation series to compare with.
- **India constipation:** no data in hand. This is the main gap.
- **30-year constipation trend (the study goal):** not possible with batch 1. The sources in hand have no constipation series for 1995-2025 in either country.

## By topic

| Topic | Source (ID in `sources.md`) | Country | Years in hand | Splits in hand | What it is | Gap |
|---|---|---|---|---|---|---|
| Constipation | NHANES bowel health file (C1) | US | 2005-06, 2007-08, 2009-10 | age (20+), sex via DEMO, income ratio via DEMO | `BHQ`: 4,773 / 5,707 / 6,059 rows. Stool frequency (`BHD050`) and Bristol stool form (`BHQ060`) in all three cycles. Self-reported constipation (`BHQ080`) and laxative items (`BHQ100`, `BHQ110`) in 2009-10 only. | No data after 2010 in hand. India: none. |
| Food | NHANES dietary day 1 totals (F3) | US | same 3 cycles | age, sex, income ratio via DEMO | `DR1TOT`: 9,950 / 9,762 / 10,253 rows. Fibre (`DR1TFIBE`) non-missing for 9,169 / 9,118 / 9,623 people (all ages). One day of recall, not usual intake. | India: none. |
| Food | FAOSTAT food balance (F1) | Both | old series 1961-2013, new series 2010-2023 (both countries) | country only | National food supply by item (119 items), for example kcal per person per day. | Supply, not intake. The two series overlap in 2010-2013 and use different methods. No fibre column. |
| Food | Global Dietary Database (F2) | Both | not downloaded | (age, sex, education, urban or rural) | The script reports `needs_account`. A free account is needed. | Needs a decision: register by hand or not. |
| Activity | NHANES activity questionnaire (P2) | US | same 3 cycles | age, sex, income ratio via DEMO | `PAQ`: 9,424 / 9,359 / 9,771 rows. Variables not reviewed yet. | India: none. |
| Activity | Strain et al. 2024 estimates (P6) | Both | 2000-2022 | sex (both, female, male); age-standardised and crude | Modelled share of adults with insufficient activity. Both sexes, age-standardised: India 0.223 (2000), 0.337 (2010), 0.494 (2022). US 0.293 (2000), 0.319 (2010), 0.337 (2022). With lower and upper uncertainty bounds. | Modelled, not measured. No age bands in the estimates file. No state or class split. |
| Activity | Strain et al. survey inputs (P6) | Both | India: 6 surveys, start years 2003, 2007, 2008, 2009, 2011, 2017. US: 7 surveys, start years 2003, 2007, 2009, 2011, 2013, 2015, 2017. | age ranges and sex in each survey row | Survey-level inputs (GPAQ or IPAQ questionnaires). | Few surveys; none before 2003. |
| Economic class | NHANES income-to-poverty ratio (via `DEMO`) | US | same 3 cycles | person level | `INDFMPIR` non-missing for 9,814 / 9,255 / 9,541 people. | India: none. |
| Economic class | World Bank GDP per person, PPP (E4) | Both | 1995-2025 for both | country only | 31 values for each country. | One number for the whole country. |
| Economic class | World Bank Gini (E4) | Both | US 1995-2024 (30 values). India 2004-2023 (5 values). | country only | Income inequality. | India has only 5 points. |

## What can be joined at person level (US only)
NHANES files join on the person id `SEQN` inside one cycle. Adults with a bowel health record and an income ratio: 4,546 (2005-06), 5,177 (2007-08), 5,467 (2009-10), which is 15,190 in total. Stool frequency and stool form are non-missing for 4,308 / 5,177 / 5,277 adults.
Rules for later plans: use the survey weights, stratum, and sampling unit from `DEMO`. Do not mix the 2009-10 self-report item with the stool-based traits as if they were one measure.

## What cannot be done yet
1. A constipation trend from 1995 to 2025 in either country.
2. Any constipation analysis for India.
3. Fibre by age, sex, and education for India (the Global Dietary Database needs an account).
4. A person-level link of any kind for India.
5. State or county splits from NHANES. The Codex review says the public files do not carry state or region (not checked by Claude; see `docs/audit-notes.md`).

## Next decisions for the user
1. **Weak constipation series.** Options: (a) proxies only; (b) a series built from published prevalence studies, with every study labelled; (c) a shorter period, such as US 2005-2010 plus later proxies. I suggest (b) for the long view and (c) for the person-level analysis.
2. **Global Dietary Database.** Register by hand, or skip it. It is the only source in hand that has fibre by age, sex, and education for India.
3. **Batch 2 sources.** Candidates: BRFSS (activity and diet, 1991-2025), CPS and ACS (income), NHANES cycles after 2010, and the registration sources (LASI, NFHS, IHDS, NHATS). Each registration needs a decision.
