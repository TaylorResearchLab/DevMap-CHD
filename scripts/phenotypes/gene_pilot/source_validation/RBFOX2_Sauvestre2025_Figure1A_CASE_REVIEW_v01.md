# RBFOX2 | Figure 1A clinical case evidence packet v01

**Status:** Original 2025 source case transcription by DevMap-Claude (independent Agent B) is assembled by DevMap-GPT (Agent A) into a machine-readable source review table, **pending independent verification of transcription into the ledger**. No biological acceptance or phenotype PAR is issued.

## Source

Sauvestre et al. 2025, *Circulation: Genomic and Precision Medicine*, DOI `10.1161/CIRCGEN.125.005231`, PMID `41221603`, author manuscript `PMC12922010`, **Figure 1A** and accompanying text. User-supplied original author PDF SHA-256 `9e46dd253a90184a8aaaf864925cf2673d770fe490d7c4f943fa43583e0b417d`. The original figure was inspected at native resolution by independent DevMap-Claude and all individual rows were transcribed in the [November 9 source review](https://app.notion.com/p/41329187800881d7bda2e57e66284612).

This source packet is constructed **from the reviewer's explicit Figure 1A transcription in Notion**, not from a new direct Agent A reading of the PDF. Read the published figure itself in any later independent source audit. The [machine-readable 33-record transcription](RBFOX2_Sauvestre2025_Figure1A_33_source_records_v01.json) preserves all patient markers and literal variant labels supplied in the reviewer record. Gene, source PMID, figure ID, original case identity and transcript are retained separately.

## Source population and phenotype counts

The original study recruited **19 P-labelled individuals from 12 families**. Figure 1A additionally shows **14 historical/database entries R20–R33**, totaling 33 displayed records before checking repeat individuals. The 19 new cohort records include **7 deletion CNVs and 12 SNVs by reported study count**. For family members the same variant can appear in multiple individual records and must not be treated as independent unique variants.

The machine-readable transcription reproduces these **reported counts over all 19 P rows** exactly:

| Feature | P row count |
| --- | ---: |
| HLHS | 10 |
| Coarctation | 10 |
| Mitral valve anomaly | 7 |
| Aortic valve anomaly | 6 |
| VSD | 8 |
| ASD | 6 |
| DORV | 4 |
| Tetralogy of Fallot | 1 |

Features overlap in individuals. Counts report how many source rows have a given feature, not numbers of distinct independent families or independent causal observations.

## Case-specific issues found by Claude

### P12, clinically unmarked variant carrier

Source figure **P12, family F7, female, RBFOX2 p.Arg249Cys**, has no cardiac or extracardiac phenotype field marked. The figure pedigree shows an unshaded variant carrier. Record `no_recorded_cardiac_feature` and **exclude P12 from the subset of patients with a documented cardiac phenotype**. This is a *figure-level absence of documentation*, rather than proof of a normal lifetime clinical phenotype. Preserve original 19-person Figure 1A denominator when reproducing the published statistics; report any phenotype-observed subgroup denominator separately.

### P18 / R24 identity and conflicting diagnoses

New case **P18, F11, female**, reported **TOF**, has a reported gross deletion `chr22:33,519,384-36,552,435` of approximately 3 Mb, inheritance NA, ACMG 5.

Historical **R24, DECIPHER 364039, female**, has a reported deletion with **base-identical genomic breakpoints** `chr22:33,519,384-36,552,435`, reported approximately 3.03 Mb. R24 has **HLHS with pulmonary arterial hypertension** rather than TOF. The source supports an **exact breakpoint match and differing phenotype descriptions**. It does not conclusively establish whether these are two records of the same individual. Mark `suspected_same_individual`, exclude P18/R24 from independent clinical replicate counts pending confirmation, and seek the original submitting center's or DECIPHER's provenance. An exploratory deduplication would give 32 rows, but the current observed unique patient count remains **unresolved**, not 32 confirmed.

### P17 deletion classification

Figure source label for **P17, F10** is `intragenic del 3 Mb chr22:32,863,077-35,939,011`. Preserve that exact wording in the `source_variant_text`. Separately record an interpretation flag `published_intragenic_label_questioned` because a 3 Mb deletion exceeds the genomic span of RBFOX2. Treat it as a **gross deletion candidate**, pending author confirmation of genomic coordinates and nomenclature.

### Historical case missing cardiac fields

For **R30, R31, R32 and R33**, every cardiac phenotype column in Figure 1A is **NR (not reported)**. Record `cardiac_status=NR`, not an explicit negative. Figure R28 is an inherited intragenic deletion from a normal parent with only extracardiac features marked; R29 similarly has only extracardiac features marked. Distinguish **not reported**, **not marked** and **explicitly absent** in the eventual data representation.

### Genotype key collisions across genes

RBFOX2 **P7** carries `c.352C>T p.Gln118*`, while the distinct MESP1 p.Q118X original source also uses `c.352C>T`. Never key variants on cDNA/protein string alone. Require **gene + transcript + source variant description**, with original primary source identity preserved.

### Other Figure 1A qualifications

P13's intragenic 5 kb deletion carries **ACMG class 3** under AnnotSV while Achropuce reports class 5; preserve method-specific interpretations separately. P8 has one heterozygote recorded in gnomAD v4; the exact figure label is retained as `1 htz`. R28 is reported inherited from a normal parent. Original figure coordinates are in **hg38**, with transcript **NM_001349999.2**. These metadata belong to the original source study rather than inferred generic RBFOX2 loci.

## Independent source review and human decision sequence

1. Agent A's 33-record JSON file transcribes each P and R row from Claude's Notion review, including family, sex, phenotype matrix, variant and inheritance for **all 19 P rows**; each R row retains the historical source and original reviewed clinical/variant summary.
2. Agent B independently checks this JSON against the original Figure 1A and notes any omissions or errors in variant type, family, pedigree interpretation, reported phenotype and source fields.
3. Investigate P18/R24 identity before interpreting the 33 displayed records as 33 people or interpreting TOF and HLHS as independent genotype associations.
4. Preserve P12 as a carrier without *recorded* cardiac malformation in the figure. Do not use P12 as a documented affected CHD individual.
5. Propose patient-specific observed clinical records to the User for acceptance only after source identity and phenotype specificity checks. Any user approval covers observed patient/variant/lesion co-observations; classification and causal PAR remain separate.

**Review record:** [Claude's 2026-11-09 independent Figure 1A transcription](https://app.notion.com/p/41329187800881d7bda2e57e66284612), with previous [Agent A 19-versus-33 cohort review](RBFOX2_Sauvestre2025_original_cohort_scope_AUDIT_v01.md). Approved SV-003 (MESP1 Werner) and SV-004 (ROCK2 PCGC) remain exactly **5** approved cases in the separate clinical ledger.
