# DevMap-CHD | CHD4 GenCC reference and phenotype source review | 2026-11-08

**Status:** Agent 1 source review, for independent Agent 2 challenge and scientific authority disposition. This is a versioned review packet with no alteration of the original GenCC/HPO release, no new direct PARs and no frozen gene-registry changes.

## Scope and frozen source

The user ran the verified real CHOP HPC GenCC/MONDO census, `results/phenotypes/hpo_unmatched_gencc_mondo_v01/` and printed all nine GenCC submissions and their PMIDs for **HAND1, MESP1, RBFOX2 and ROCK2**. The original GenCC source snapshot is `scripts/phenotypes/gene_pilot/inputs/gencc-submissions-new.tsv`, SHA-256 `6b099f2497837c8bb0b62930bcfff13c952869dd52635511da181521ce1cde17`. The genes are four of the original 143 with no matching **HPO genes_to_phenotype.txt** gene-summary rows. HPO G2P absence is a source-index coverage state, not the absence of any curated clinical HPO observations.

| Gene | GenCC submissions | Source PMID mentions | Unique source PMIDs | PMIDs reused across submitters |
| --- | ---: | ---: | ---: | --- |
| HAND1 HGNC:4807 | 2 | 20 | 17 | 27942761, 28112363, 31286141 |
| MESP1 HGNC:29658 | 2 | 8 | 6 | 26694203, 28677747 |
| RBFOX2 HGNC:9906 | 3 | 16 | 13 | 26785492, 27485310, 35137168 |
| ROCK2 HGNC:10252 | 2 | 8 | 5 | 28554332, 30622330, 31941532 |

These PMID counts come only from the printed source bibliography fields. Same-publication repetition does not count as a separate original study. Cohort overlap and citation-to-patient linkage require separate source checks.

### Original gene–disease curation

- HAND1: ClinGen `SGC-105468` Moderate / MONDO:0005453; PanelApp Australia `SGC-179131` Moderate / same disease.
- MESP1: ClinGen `SGC-107264` Moderate / MONDO:0005453; PanelApp Australia `SGC-177013` Moderate / same disease.
- RBFOX2: Ambry Genetics `SGC-103593` Strong / MONDO:0000119, no PMIDs in frozen submission; ClinGen `SGC-107312` Strong / MONDO:0005453; PanelApp Australia `SGC-175980` Strong / MONDO:0100557. These three native disease IDs are retained as distinct submitted concepts.
- ROCK2: ClinGen `SGC-107591` Limited / MONDO:0005453; PanelApp Australia `SGC-120816` Moderate / same disease. Both cite the same three clinical PMIDs; ClinGen's evaluated evidence includes an experimental model. The `Moderate` claim is not a ClinGen expert panel evaluation.

The frozen source IDs above are **SGC ID without `.version`** because the user's printed table omitted `gencc_version`. Use the version-specific original output TSV for citation in a direct assertion.

## Source review: human clinical observations

### HAND1, Agent 1 original text reading; Agent 2 abstract-level verification

[Li et al. 2017, PMID 28112363, DOI 10.3892/ijmm.2017.2865, full-text Results: Discovery of a de novo HAND1 mutation](https://www.spandidos-publications.com/10.3892/ijmm.2017.2865?text=fulltext)

- **Source subject:** one 5-month-old male in a cohort of 158 unrelated patients with CHD.
- **Variant:** heterozygous `HAND1 c.394A>T, p.K132X`, absent from parents and 300 controls, reported as de novo.
- **Directly reported anatomical phenotypes:** double outlet right ventricle (DORV) and ventricular septal defect (VSD) in the same affected boy.
- **Experimental evidence:** K132X protein showed loss of transcriptional activation and reduced synergy with GATA4 in reporter assays.
- **Exact source locator:** Results, *Discovery of a de novo HAND1 mutation*, main article Figure 1 and Figure 2. This is **original clinical subject evidence**, eligible for a source-constrained candidate direct gene disruption–phenotype record after clinical review and user acceptance. Do not infer other CHD lesion types in this case from cohort Table II.

[Wang et al. 2017, PMID 27942761, DOI 10.1007/s00246-016-1547-8](https://pubmed.ncbi.nlm.nih.gov/27942761/)

- **Abstract-level case report:** one person with tetralogy of Fallot (TOF) and heterozygous `HAND1 p.R118C` in a screened cohort of 165 unrelated CHD patients. Reporter analyses showed reduced transcriptional activity. Full original case locator, variant nomenclature transcript and segregation should be checked before any direct record.

### MESP1, Agent 1 original text reading; Agent 2 abstract-level verification

[Zhang et al. 2017, PMID 28677747, DOI 10.3892/mmr.2017.6875, full-text Results: Identification of a novel MESP1 mutation in CHD](https://www.spandidos-publications.com/10.3892/mmr.2017.6875?text=fulltext)

- **Source subject:** one 3-month-old female in a cohort of 178 unrelated CHD patients.
- **Variant:** heterozygous `MESP1 c.352C>T, p.Q118X`, absent from unaffected parents and 200 controls, reported as de novo.
- **Directly reported anatomical phenotypes:** DORV and VSD in the same affected female.
- **Experimental evidence:** protein lost transcriptional activation in a reporter assay, with no evidence for dominant negative activity in the tested system.
- **Exact source locator:** Results, *Identification of a novel MESP1 mutation in CHD*, Figure 1 and Figure 2. The study's larger cohort Table II reports many lesions, but those cohort counts are **not all attributable to the MESP1 variant carrier**.

[Lahm et al. 2013, PMID 24056064, DOI 10.1016/j.ejmg.2013.09.001](https://pubmed.ncbi.nlm.nih.gov/24056064/) reports MESP1 sequencing in 215 CHD patients and functional activity tests. It establishes a gene/variant association lead; exact variant-to-lesion pairs need full paper review.

[Werner et al. 2016, PMID 26694203](https://pubmed.ncbi.nlm.nih.gov/26694203/) screened 647 patients ascertained for conotruncal and related lesions. **Claude independently checked the complete original paper, including Table 2 and the functional assay table.** Seven variant carriers have patient diagnoses and inheritance information, including three variants with substantial functional impairment and a matched structural lesion (p.E104K TOF, p.L120P TOF, p.L147Pfs*9 conoventricular VSD). See amendment below. Source-supported variant–lesion observations and evidence for molecular causation remain distinct.

### RBFOX2, mixed human clinical, mechanistic and newer primary cohort

[2025 international clinical study, Sauvestre et al., PMID 41221603, DOI 10.1161/CIRCGEN.125.005231, original article landing page](https://pmc.ncbi.nlm.nih.gov/articles/PMC12922010/). **This PMID was not printed among the frozen GenCC submission bibliographies and is an additive source lead, not an update to that snapshot.**

- **Reported new cohort:** 19 individuals from 12 unrelated families carrying RBFOX2 variants. **Figure 1A displays 33 individuals**, including 14 previously reported ClinVar, DECIPHER and literature cases. Claude verified this denominator in the original figure legend but the complete manuscript PDF remains pending. Reported abnormalities among these 19 include HLHS 10, ascending aortic coarctation/hypoplasia 10, mitral valve defects 7, aortic valve defects 6, VSD 8, ASD 6, DORV in patients P8–P10 and P19, and TOF in P18.
- **Interpretation:** counts overlap within patients. Original Figure 1 supplies case-specific genetic variants and lesion descriptions. CNVs can encompass RBFOX2 plus adjacent genes, requiring variant interval attribution. Several comparison cases have no complete cardiac phenotyping, which should remain unknown rather than coded as negative.
- **Original subject and lineage:** 19 newly reported patients, 12 unrelated families and the 33 people depicted in the combined figure are three distinct denominators. Source draws additionally on previously published cases and DECIPHER/ClinVar; deduplication requires patient/case tracking.

[Verma et al. 2022, PMID 35137168, DOI 10.1093/nar/gkac055](https://pmc.ncbi.nlm.nih.gov/articles/PMC8881802/) describes conditional Rbfox2 knockout mouse cardiac phenotypes, transcriptional changes and features resembling HLHS. This is **experimental model evidence**, not a second human clinical observation.

[RBFOX2 transcript changes in HLHS patient hearts, PMID 27485310](https://pubmed.ncbi.nlm.nih.gov/27485310/) documents effects of a previously observed RBFOX2 nonsense mutation on RNA processing. This is patient-tissue molecular evidence with clinical context, distinct from independent clinical cohort counting.

[ClinGen RBFOX2 curation](https://search.clinicalgenome.org/kb/genes/RBFOX2) lists several lesion types in the rationale for grouping under one broad CHD disease relationship. Those labels are useful **phenotype source leads**; exact patient-level source attribution remains separate.

### ROCK2, detailed secondary clinical curation

[ClinGen Congenital Heart Disease GCEP, CCID:008432, evaluated 2024-09-03](https://search.clinicalgenome.org/CCID:008432) is a **Limited** gene–disease assertion. Its original case evidence table specifies four variants/probands across three primary publications:

| Source variant | PMID | ClinGen-curated clinical features with exact HPO terms where present |
| --- | --- | --- |
| `NM_004850.5:c.2140C>T p.Arg714Ter` | 28554332 | ASD `HP:0001631`, PDA `HP:0001643`, VSD `HP:0001629`; syndromic additional abnormalities |
| `NM_004850.5:c.3724C>T p.Gln1242Ter` | 30622330 | Coarctation `HP:0001680`, dextrocardia `HP:0001651`, situs inversus totalis `HP:0001696`, VSD `HP:0001629`, abnormal inferior vena cava morphology `HP:0025576` |
| `NM_004850.5:c.764A>G p.Asp255Gly` | 31941532 | Abnormal heart morphology `HP:0001627` only, plus extracardiac anomaly description |
| `NM_004850.5:c.116C>T p.Ser39Phe` | 31941532 | Conotruncal defect `HP:0001710` plus extracardiac anomaly description |

**Evidence scope:** this table reports what ClinGen curators attributed to individual source cases, with original source PMIDs. Claude checked all three original main texts and verified the variant identifiers, but **none contains the specified lesion-level cardiac observations in its main text**. They require original supplementary patient tables. The p.Gln1242Ter (Q1242*) case was **inherited from a parent without reported significant cardiac disease**. The 2020 source reanalyzed existing PCGC patients; p.S39F was previously reported. The original PCGC study is the clinical cohort source, rather than the 2020 reanalysis. Thus all four specific ROCK2 lesion assignments remain pending supplementary patient-level review. In particular, `HP:0001627` is a nonspecific morphology term and does not identify a CHD lesion. `HP:0001696` is laterality, not automatically a specific intracardiac lesion.

[PanelApp Australia ROCK2](https://panelapp-aus.org/panels/76/gene/ROCK2/) reports the same broad disease, cites the same three PMIDs, and explicitly notes that ClinGen classified the relationship as Limited. It remains a **separate curation submission** rather than an independent patient cohort.

## Findings for DevMap scientific representation

1. Gene–disease classifications in GenCC and ClinGen refer to **MONDO:0005453 congenital heart disease** or other original submitted disease entities, whereas variant- or patient-specific malformations should become **separate observed clinical phenotype evidence**.
2. The original disease-subject HPOA `dmpdsrc1` and gene-keyed discovery `dmpview1` remain approved and unchanged. Their absence for a gene in HPO G2P does not preclude source-specific direct phenotype observations in ClinGen or primary papers.
3. Reused PMIDs are one publication each. Independent patients, studies and molecular alleles require original publication/case identifiers and careful cohort overlap assessment.
4. Each source must preserve evidence granularity: **original full-text individual**, **original abstract-level case**, **ClinGen curation of an individual**, **human cohort aggregate**, **patient-tissue molecular**, and **animal developmental model**.
5. This pilot establishes the value of disease and phenotype **separation** with a source-linked clinical phenotype layer. The user remains the final scientific authority for accepting new direct gene-disruption–phenotype assertions.

## Proposed focused review for DevMap-Claude

- Independently confirm the three original patient variants and lesion pairings: HAND1 `p.K132X` DORV/VSD; MESP1 `p.Q118X` DORV/VSD; HAND1 `p.R118C` TOF. Check any shared patient/cohort provenance.
- Inspect original ROCK2 PMID 28554332, 30622330 and 31941532 for precise clinical tables, laterality status and lesion specificity. Compare against the ClinGen curated four-proband table.
- Inspect the 2025 RBFOX2 full-text figure and appendices, original patient IDs, gene-overlapping CNVs and whether current DECIPHER records duplicate published cases. Preserve 19 person / 12 family denominators and all original HPO terms.
- Review the distinction between disease class, lesion observation, source PMID and functional variant mechanism; recommend **accept / narrow / defer / reject** for each proposed direct phenotype source claim.

**No direct phenotype PAR promoted; no original HPOA or GenCC source claims modified.**


## Independent Agent 2 challenge and packet corrections, 2026-11-08

[Claude's full independent review](https://app.notion.com/p/412291878008814a9323f386cc51a647) was filed after reading this packet. Reviewer exposure is **second check following exposure**: the Agent 2 reviewer read this construction packet first, then independently consulted full original text for Werner 2016, Bowling 2017, Li 2019 and Sevim Bayrak 2020. Agent 2 accessed abstract-level sources for HAND1 Li 2017, HAND1 Wang 2017, MESP1 Zhang 2017 and RBFOX2 Sauvestre 2025 (plus the latter's Figure 1 legend). Full publisher PDFs and inaccessible supplements are needed for independent confirmation of individual source locators in those items. GenCC snapshot source was unavailable to the reviewer, so PMID overlap numbers remain Agent 1's reproducible counts from the user's pinned snapshot printout rather than independent Agent 2 reproduction.

### MESP1 primary paper Werner 2016, PMID 26694203

**Reviewer correction:** the previous packet stopped at the abstract and incorrectly treated the seven variants as lacking case-specific lesions. Table 2 of the full source explicitly identifies each individual carrier's diagnosis, inheritance and controls. Gene transcript **NM_018670.3**, 647 unrelated CHD patients enriched for conotruncal defects (TOF 318, VSD 292, truncus arteriosus 21, interrupted aortic arch 16).

| Original protein variant | Individual phenotype | Inheritance | Luciferase activity (relative to WT) | Two-hybrid activity (relative to WT) | Control observation | Proposed evidence scope |
| --- | --- | --- | ---: | ---: | --- | --- |
| p.E104K | TOF (HP:0001636) | Maternal | 0.08 ± 0.04 | 0.56 ± 0.08 | Not seen | Single-patient observation, reduced function; penetrance unresolved |
| p.L120P | TOF (HP:0001636) | De novo | 0.06 ± 0.03 | 0.32 ± 0.06 | Not seen | Single-patient observation, reduced function |
| p.L147Pfs*9 | Conoventricular VSD (within HP:0001629) | Unavailable | 0.03 ± 0.02 | 0.05 ± 0.01 | Not seen | Single-patient observation, reduced function |
| p.P27_D29dup | Conoventricular VSD | Paternal | 0.77 ± 0.21 | 1.02 ± 0.13 | Not seen | Clinical observation retained; function close to WT |
| p.G70D | Conoventricular VSD | Unavailable | 0.92 ± 0.24 | 1.19 ± 0.21 | Not seen | Clinical observation retained; function close to WT |
| p.D168G | Conoventricular VSD | Unavailable | 0.97 ± 0.19 | 0.53 ± 0.11 | **Present in 6/97 African-American controls** | Clinical observation retained; weak functional prioritization |
| p.K268N | mVSD, coarctation, aortic aneurysm | Maternal | 1.17 ± 0.18 | 0.90 ± 0.26 | Not seen | Clinical observation retained; function close to WT |

All seven source observations should remain discoverable. **The first three** have direct patient–variant–lesion pairs and marked functional impairment, making them appropriate for **User accept / narrow / defer / reject review at original individual scope**. The other four remain recorded as variant-associated observations but do not satisfy the same functional-evidence rationale; they are **not discarded from the source ledger**. Maternal transmission of E104K needs a penetrance and parent phenotype annotation. The cVSD subtype must retain the author's original label in addition to any HPO mapping. TOF and conoventricular VSD are lesions in patients selected from a cohort already enriched for such lesions, so cohort ascertainment is material to any quantitative interpretation.

### ROCK2 source correction and lineage

- **Bowling 2017, PMID 28554332**: proband `00265-C` carries `c.2140C>T p.R714X`; the paper reports reduced ROCK2 protein by western blot in an intellectual-disability cohort. The main text does not report the ClinGen-curated ASD/PDA/VSD annotations for this patient.
- **Li 2019, PMID 30622330**: patient `LAT1349` carries `p.Q1242*`; main Table 1 gives **“Situs anomaly”** without specific lesions. The variant was **inherited**, from a parent with no reported history of significant cardiac disease. The original paper discusses dominant inheritance with incomplete penetrance, and the patient-level lesion details attributed by ClinGen await supplementary verification.
- **Sevim Bayrak 2020, PMID 31941532**: a reanalysis of the previously published 2,645-trio PCGC cohort. `p.D255G` is a de novo kinase-domain variant in a patient with syndromic CHD; `p.S39F` was reported in prior work. The earlier PCGC reports are the origin of these cases; specific congenital lesion information is reported in supplemental tables S16/S39, which were inaccessible to Agent 2.
- **Result:** ClinGen's four case-level HPO mappings are valid as *records of ClinGen's curated assessment*. Exact lesion observations remain **unresolved at original publication level**. Do not mint direct original-patient phenotype PARs from the current main-text evidence. PanelApp Moderate and ClinGen Limited are separate source assessments over overlapping primary case reports.

### RBFOX2 original cohort versus combined figure

The 2025 Sauvestre et al. report (PMID 41221603) describes **19 new individuals across 12 unrelated families**. Figure 1A displays **33 total individuals**, including 14 prior cases from published reports, DECIPHER and ClinVar. Cohort frequency denominators such as 10/19 HLHS and 8/19 VSD apply to the newly reported 19, not automatically to all 33. Case-level extraction should distinguish the new cohort from previously reported individuals and identify exact source variants, particularly overlapping CNVs. The P13 CNV was reported as **ACMG class 3**. Agent 2 saw the abstract and Figure 1 legend, not the gated full PDF.

### HAND1 and single-case MESP1 paper evidence bounds

HAND1 `p.K132X` DORV/VSD (PMID 28112363), HAND1 `p.R118C` TOF (PMID 27942761) and MESP1 `p.Q118X` DORV/VSD (PMID 28677747) agree with the paper abstracts. Agent 1 previously reported consultation of the available Spandidos full texts, while **Agent 2 could inspect only abstracts**. The three studies share a senior-author group and use separate CHD cohorts of 158, 165 and 178 patients; cross-cohort patient overlap has not been resolved. Retain as qualified clinical case leads, with independent full-text verification still pending. They are not equivalent to the fully independently checked Werner 2016 individual records.

### Reviewer dispositions and governance

| Evidence item | Recommended present disposition |
| --- | --- |
| MESP1 E104K–TOF, L120P–TOF, L147Pfs*9–conoventricular VSD | **Ready for User disposition** at original individual observed-association scope |
| HAND1 K132X, R118C and MESP1 Q118X | Defer direct acceptance pending independent full publisher texts; preserve abstract-concordant leads |
| ROCK2 four ClinGen-curated variant/HPO pair groups | Keep curated source assertions; original individual lesion-level verification pending supplements and earlier PCGC cohorts |
| RBFOX2 2025 cohort | Preserve 19 new / 12 families / 33 combined figure and study-level findings; individual direct claims pending complete full text |

No new direct gene disruption–phenotype PAR has been accepted, and no prior user decisions or original immutable source data have changed. Reviewer entry and its exposure status are documented in [DevMap Communications Log](https://app.notion.com/p/412291878008814a9323f386cc51a647).

## User disposition on Werner 2016 MESP1 observations, 2026-11-08

**Scientific authority APPROVED all three original patient/variant-associated congenital cardiac structural observations at their specific original clinical scope** after the complete-paper independent Agent 2 review. Source publication: Werner et al. 2016, PMID 26694203, Table 2 and associated functional assay table, a single cohort of 647 individuals ascertained for conotruncal and related CHD.

- **p.E104K -> tetralogy of Fallot** (HP:0001636), maternally inherited, luciferase activity 0.08 ± 0.04 versus wild type.
- **p.L120P -> tetralogy of Fallot** (HP:0001636), de novo, luciferase activity 0.06 ± 0.03.
- **p.L147Pfs*9 -> conoventricular ventricular septal defect**, original phenotype subtype preserved and mapped to broader HP:0001629, parental inheritance unreported, luciferase activity 0.03 ± 0.02.

The original patient is the subject of each clinical observation; variant identity, inheritance and the in vitro functional assay are accompanying source evidence, not independently accepted claims of genetic causal sufficiency. The four additional Werner source variant rows remain retained in their original evidence stratum and were not included in this three-item decision. Canonical direct causal PAR creation is a separate later step.

- [User's signed scientific decision record in DevMap Communications Log](https://app.notion.com/p/4122918780088184992eee2eb51848c5)
- [SV-003 evidence and decision packet](https://github.com/TaylorResearchLab/DevMap-CHD/blob/feature/gene-phenotypes/scripts/phenotypes/gene_pilot/source_validation/SV-003_MESP1_Werner2016_three_patient_lesions_APPROVED.md)
- [Independent Claude review](https://app.notion.com/p/412291878008814a9323f386cc51a647)

**Remaining CHD4 source tasks:** HAND1 original complete paper verification and cohort overlap; ROCK2 variant-specific patient clinical supplements and primary PCGC source lineage; RBFOX2 full primary paper and prior-case deduplication.
