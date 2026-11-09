# SV-003 | MESP1 Werner 2016 original clinical phenotype observations

**Scientific authority decision: APPROVED, 2026-11-08.** Deanne M. Taylor explicitly approved three variant-associated congenital structural heart phenotype observations **at original individual clinical observation scope** following independent review by DevMap-Claude.

## Original source and review provenance

- **Primary publication:** Werner et al. 2016, *Human Mutation*, PMID **26694203**, [PubMed](https://pubmed.ncbi.nlm.nih.gov/26694203/); original Table 2 (patient-level variants and cardiac diagnoses), accompanying functional assay table.
- **Original clinical cohort:** 647 individuals ascertained for conotruncal and related congenital heart defects. Original cohort lesion composition includes tetralogy of Fallot 318, VSD 292, truncus arteriosus 21, and interrupted aortic arch 16. This ascertainment context accompanies interpretation of observed case associations.
- **MESP1 transcript referenced by reviewer:** NM_018670.3.
- **Independent reviewer:** DevMap-Claude Agent 2, [CHD4 review, 2026-11-08](https://app.notion.com/p/412291878008814a9323f386cc51a647). Agent 2 read the full original paper following exposure to Agent 1's construction packet; reported exact patient variant/lesion pairings, inheritance and functional assay values.
- **Original construction and author response:** [CHD4 source validation packet](https://github.com/TaylorResearchLab/DevMap-CHD/blob/feature/gene-phenotypes/scripts/phenotypes/gene_pilot/source_validation/CHD4_GENCC_TO_PRIMARY_CLINICAL_EVIDENCE_20261108.md), updated after Claude's review at commit 96f84d1dbfd7932b447849190e3a99c8de19a236.

## Three approved observed patient–variant–lesion associations

| Approved clinical observation | Original structural phenotype | HPO mapping | Original inheritance | Source functional observation |
| --- | --- | --- | --- | --- |
| MESP1 p.E104K in one affected individual | Tetralogy of Fallot (TOF) | HP:0001636 | Maternal transmission | Luciferase activity 0.08 ± 0.04 relative to WT; two-hybrid 0.56 ± 0.08 |
| MESP1 p.L120P in one affected individual | Tetralogy of Fallot (TOF) | HP:0001636 | De novo | Luciferase activity 0.06 ± 0.03 relative to WT; two-hybrid 0.32 ± 0.06 |
| MESP1 p.L147Pfs*9 in one affected individual | Conoventricular ventricular septal defect (cVSD) | HP:0001629 VSD (broader normalized term; retain source subtype verbatim) | Not reported | Luciferase activity 0.03 ± 0.02 relative to WT; two-hybrid 0.05 ± 0.01 |

The three variants were absent in the tested source controls according to Werner 2016 Table 2 as transcribed by Agent 2. The quantitative luciferase and two-hybrid results are separate **experimental functional observations**, linked to but distinct from the individual human clinical malformation findings.

**Approved claim level:** each variant was *observed in an individual with the named structural cardiac lesion*, with original inheritance and source context. Acceptance includes the recorded clinical observation and source-derived functional information. Pathogenicity classification, causal sufficiency, penetrance and clinical disease validity are separate evidence dimensions. p.E104K's maternal inheritance requires retention of the mother's phenotype/penetrance as unknown until established from its source; p.L147Pfs*9's parental inheritance was not available.

## Original source conservation and other variant rows

Werner Table 2 contains four other variant/clinical phenotype combinations with different functional findings:
- p.P27_D29dup, cVSD, paternal, luciferase 0.77 ± 0.21 WT.
- p.G70D, cVSD, inheritance unavailable, 0.92 ± 0.24.
- p.D168G, cVSD, inheritance unavailable, 0.97 ± 0.19 and present in six of 97 African-American controls.
- p.K268N, mVSD / coarctation / **aortic atresia**, maternal, 1.17 ± 0.18. The original abbreviated `AA` is explicitly defined as *aortic atresia* in Zhang et al. 2017 Table III footnote (PMID 28677747), independently verified by DevMap-Claude on November 9, 2026. This is a correction to the contextual unapproved fourth variant, with no change to the three accepted SV-003 observations.

These four remain original source observations and were **not included in this three-item user acceptance decision**. They retain their original evidence and are considered separately when assessing biologically meaningful direct gene disruption relationships.

## Data governance

- Preserve original `dmpdsrc1` disease-subject HPOA source identity and `dmpview1` disease-mediated gene discovery projections.
- Preserve frozen 662-gene registry, original GenCC snapshot, HPOA source records and archived outputs.
- Record these three as **user-accepted clinical observation assertions with original patient/variant scope**. Distinguish accepting observed associations from issuing a canonical direct causal gene disruption–phenotype PAR. No canonical PAR ID is minted by this decision document.
- Source subject remains the original reported individual. Phenotype mapping uses HP:0001636 for TOF and broader HP:0001629 for VSD, while conoventricular subtype remains in the original text.
- Keep all three observations linked to **one** original publication; their clinical observations arise from one ascertained cohort. Reporter assay findings remain separate from clinical observations.

## Approval record

The user was presented the specific three pairs and qualifiers and responded on **November 8, 2026**, **"Yes, I approve."** Approval applies only to these defined original observations. Remaining HAND1, ROCK2 and RBFOX2 clinical extraction items stay in source review pending material described in the CHD4 packet.
