# RBFOX2 Sauvestre 2025 | Original full-text cohort identities and clinical scope

**Reviewed:** 2026-11-09 by DevMap-GPT Agent 1.  
**Primary source:** Sauvestre et al., *Circulation: Genomic and Precision Medicine*, 2025, PMID **41221603**, DOI **10.1161/CIRCGEN.125.005231**, author manuscript [PMC12922010](https://pmc.ncbi.nlm.nih.gov/articles/PMC12922010/), Figure 1(A–D) and original source body.  
**Status:** **Source-level cohort audit**, independent Agent 2 check pending. This does not add accepted individual variant–phenotype records.

## Distinguish original cohort and figure

The **new study cohort** comprises **19 individuals from 12 unrelated families**. Its genomic alterations include **7 CNVs** (5 intragenic RBFOX2 deletions; 2 involving the entire gene) and **12 SNVs**. **14 of these 19** underwent WGS/WES/panel analyses excluding other known genetic CHD causes. The figures also review historical clinical and database cases.

**Figure 1A displays n=33 persons with RBFOX2 variants**, encompassing **19 new + 14 previously described or database-retrieved cases**. Do not use the Figure 1A n=33 denominator for the new 19-person cohort rates. Do not add the previously reported patients to the 19 as independent new persons in this paper's clinical claims without checking original case identifiers.

The paper reports original **19-person cohort denominators**:

| Cardiac abnormality category | Observations / 19 |
| --- | ---: |
| Hypoplastic left heart syndrome | 10 / 19 |
| Ascending aorta abnormality (coarctation/hypoplasia) | 10 / 19 |
| Mitral valve defects (stenosis/atresia) | 7 / 19 |
| Aortic valve defects (bicuspid, stenosis, atresia) | 6 / 19 |
| Ventricular septal defects | 8 / 19 |
| Atrial septal defects | 6 / 19 |

These category counts **overlap across persons** and should not be summed as unique subjects.

## Individual case identifiers and variant linkage

The main text explicitly reports **DORV** in subjects **P8, P9, P10 and P19** and **TOF** in **P18, family F11**. These are supported **patient ID to anatomical phenotype co-observations** at the level reported in the main text. To construct a *patient-variant-phenotype* observation, read **Figure 1A** (which displays individual variant and clinical fields) and any original supplementary data/clinical text. Do not pair an RBFOX2 variant with P8, P9, P10, P18 or P19 using an inferred row order, gene-level grouping or figure-level rates. No molecular individual identifiers have yet been extracted in this v01 audit.

The main text reports `P13` CNV discrepancy: AnnotSV **class 3** and Achropuce **class 5**. These are method-specific interpretations of one variant, not independent observations. Reference genome for Figure 1A is **hg38** and reference transcript **NM_001349999.2**.

The original paper describes additional database observations `R28–R33`. `R28–R31` have intragenic deletions in exons excluded from the **cardiac transcript ENST00000405409.6** and are described in the article as having no reported cardiac anomaly. `R32` and `R33` have frameshift SNVs in the cardiac transcript, but **individual phenotype information including cardiac status is unavailable**. Record `cardiac_phenotype_status=unknown` for R32/R33, not an asserted negative or a case of unaffected variant carriage.

The paper also mentions a previously reported de novo 111-kb CNV involving RBFOX2 in one HLHS patient from Glessner and three more HLHS individuals with de novo RBFOX2 LoF variants from Homsy. These historical patients belong to those original reports; cite the original publication for their origin. The 2025 retrospective collection must be tracked as a secondary appearance rather than counted as novel replication.

## What remains for precise DevMap clinical records

1. Extract the original 19 new cohort case IDs, original variant descriptions, CNV coordinates, genomic build/transcript relation, family identifiers and exact cardiac diagnoses **from Figure 1A and associated original source material**. Keep patient identity and cohort provenance exact.
2. Distinguish cohort patient `P1–P19` from previously reported/database `R` cases and the figure's 14 other persons. Confirm the actual Figure 1A membership before deriving a full 33-row table.
3. Keep the 7 CNVs (including the 5 intragenic events) distinct from the 12 SNVs. Link transcript-specific effects (especially cardiac isoform ENST00000405409.6) at original observed variant level.
4. Independently check figure-based case annotations and P13 classification discrepancy before any source-specific patient/variant records are recommended to the User.

**Previous independently reviewed context:** [CHD4 initial Claude source review](https://app.notion.com/p/412291878008814a9323f386cc51a647) already identified the **n=33 vs 19** denominator discrepancy. This document independently checks that distinction using the original author manuscript and puts detailed extraction gates on the remaining case pairs.

**Scientific status:** original source and cohort-level findings recorded. No user approval, new causal PAR or accepted gene disruption–phenotype relation. The SV-003/SV-004 approved ledger remains unchanged.
