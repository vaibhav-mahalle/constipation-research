# Audit notes (stage 2, 2026-10-30)

Codex reviewed the table of 44 sources and wrote this list from its own knowledge. It had no web access. Claude has not checked these points. Each point is open until a later plan checks it. Do not treat any of them as a fact.

## 1. Doubtful rows (from Codex)

| ID | Concern | Codex confidence | Status |
|---|---|---|---|
| C1 | Stool frequency and stool form measure bowel traits. They define an operational outcome. They do not establish Rome functional constipation. | high | open |
| C2 | IPUMS needs registration and an extract request. Access to IPUMS differs from access to the original NCHS files. | high | open |
| C3 | NAMCS and NHAMCS need separate rows. Setting, years, and public files differ. | high | open |
| C3 to C5 | Diagnosis records count diagnosed cases, visits, or discharges. They do not measure prevalence. | high | open |
| C3, C4 | Payer is not economic class. ZIP income describes an area, not the patient. | high | open |
| C4 | The name is "National Inpatient Sample" from 2012 and "Nationwide Inpatient Sample" before. The 2012 redesign affects trends. | high | open |
| C5 | Public MEPS condition codes can group constipation into a wider condition. Check each coding period. | high | open |
| C6 | GBD digestive burden is not a defensible constipation proxy unless a cause mapping shows it. | high | open (agrees with the "not confirmed" note in the row) |
| C7 | The row may mix separate Rome Foundation studies. Confirm that the two US surveys belong to the multinational sample. | medium | open |
| C8, C13, F12 | "Not applicable" is too broad for reuse terms. Press releases and contracts have terms. | high | open |
| C9 | The row joins independent studies. Each usable study needs its own row. | high | open |
| C10 | LASI includes spouses below age 45, so the sample is not only 45+. | high | open (the IIPS page lists the pilot as "45+ and their spouses") |
| C11 | SAGE covers adults 50+ and a smaller younger sample. | high | open |
| C12 | "A constipation code is rare" is unclear. Check whether a separate code exists. | high | open |
| F1 | The new FAOSTAT balance series starts in 2010. Check how far the old series runs. | medium | open |
| F3 | The name "What We Eat in America" applies from 2002. | high | open |
| F5 | Check that fibre is in the NNMB tables. | high | open |
| F6, E8 | NFHS food questions, age limits, and wealth measures change by round. District estimates also exist for NFHS-4. | high | open |
| F7 | CNNS food measures may be frequency and diversity, not a quantitative recall. | medium to high | open |
| F8 | 2020 is a publication year, not a survey year. It may overlap F5. | high | open |
| F11 | The Food Expenditure Series has national data before 1997. | high | open |
| P2 | Public NHANES files do not identify state or region. NHIS has public regional measures. Split this row. | high | open |
| P4 | Time-use codes do not always show sitting. Define the classification. | high | open |
| P5 | National YRBS and state or district surveys are separate samples. | high | open |
| P6 | Modelled prevalence is a separate type. Country income groups are not an individual class split. | high | open |
| P7 | A survey listed under India can cover selected sites only. | high | open |
| P8 | Codex says NNMS adults are 18 to 69. Muse said 15 to 69. This conflict is not resolved. | high | open |
| P9 | The four INDIAB study areas are not four representative regions. | high | open |
| E1 | ACS estimates and ACS PUMS have different release dates. | high | open |
| E3 | SAIPE gives modelled estimates. School district and county outputs differ. | high | open |
| E4 | The Gini page does not show all PIP measures, years, or licenses. Gini measures inequality, not individual class. | high | open |
| E5 | Household files have member demographics. Expenditure stays a household measure. | high | open |
| E7 | IHDS-3 fieldwork dates do not show that IHDS-3 is public. | high | open |
| E9 | Census assets, education, and occupation indicate class. They are not income or wealth. | high | open |

Rule from Codex: survey year, fieldwork year, and public release year differ. Rows that claim 2025 releases need a check for each product.

## 2. Structural gaps (Codex view; Claude agrees with the first two)

| Country and topic | Gap |
|---|---|
| US constipation | No listed source gives a consistent prevalence series for 1995-2025. NHANES has a short window. Public NHANES has no state detail. Children have no comparable direct source. |
| India constipation | No listed source gives a national repeated series. No confirmed source gives prevalence by age, sex, state, and class together. |
| US food and fibre | No individual intake data for 1995-1998 in the table (CSFII 1994-96 is a lead, F13). Public individual intake data have no state detail. |
| India food and fibre | Intake data are sparse between NNMB rounds. No national individual fibre source by age, sex, state, and class. |
| US activity | Device data cover selected years. Questionnaires change over time. |
| India activity | No national repeated series for 1995-1999 or a consistent series to 2025. |
| US class | CPS covers the full period. ACS starts about 2005. |
| India class | A gap in consumption benchmarks between 2011-12 and 2022-23. No one scale for income and consumption. |
| All topics | No listed source has all four topics for the same people over the full period. NHANES is the closest for the US in selected cycles. India has no equivalent. |

## 3. Merge risks (for plans 4 to 6)

- Keep constipation definitions apart: Rome criteria, self-report, stool form, stool frequency, diagnosis.
- Keep units apart: people, households, visits, discharges, purchases, national totals.
- Check for the same sample in two rows (F5 and F8, F6 and E8, P7 and P8).
- Use survey weights, strata, and sampling units. Join NHANES files inside the same cycle.
- Account for design changes: BRFSS in 2011, NIS in 2012, NHIS in 2019, and the ICD-9 to ICD-10 change in October 2015.
- Keep supply, purchase, spending, and recall measures apart. Old "crude fibre" does not equal total dietary fibre.
- Keep class measures apart: income, consumption, assets, education, occupation, caste, area deprivation.
- Mark interpolated values as estimates. Do not show modelled annual values as observations.
- Ecological fallacy: a state average does not show a person-level link.
- Cross-sectional links cannot show direction. Constipation can change diet, activity, and laxative use.
- Consider age, drugs, diabetes, nerve disease, pregnancy, disability, and care access as confounders.

Codex also advises new columns in a later table version: observation unit, eligible population, measurement definition, sample geography, and shared sample.
