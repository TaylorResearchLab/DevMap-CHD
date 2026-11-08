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

### HAND1, primary original full text

[Li et al. 2017, PMID 28112363, DOI 10.3892/ijmm.2017.2865, full-text Results: Discovery of a de novo HAND1 mutation](https://www.spandidos-publications.com/10.3892/ijmm.2017.2865?text=fulltext)

- **Source subject:** one 5-month-old male in a cohort of 158 unrelated patients with CHD.
- **Variant:** heterozygous `HAND1 c.394A>T, p.K132X`, absent from parents and 300 controls, reported as de novo.
- **Directly reported anatomical phenotypes:** double outlet right ventricle (DORV) and ventricular septal defect (VSD) in the same affected boy.
- **Experimental evidence:** K132X protein showed loss of transcriptional activation and reduced synergy with GATA4 in reporter assays.
- **Exact source locator:** Results, *Discovery of a de novo HAND1 mutation*, main article Figure 1 and Figure 2. This is **original clinical subject evidence**, eligible for a source-constrained candidate direct gene disruption–phenotype record after clinical review and user acceptance. Do not infer other CHD lesion types in this case from cohort Table II.

[Wang et al. 2017, PMID 27942761, DOI 10.1007/s00246-016-1547-8](https://pubmed.ncbi.nlm.nih.gov/27942761/)

- **Abstract-level case report:** one person with tetralogy of Fallot (TOF) and heterozygous `HAND1 p.R118C` in a screened cohort of 165 unrelated CHD patients. Reporter analyses showed reduced transcriptional activity. Full original case locator, variant nomenclature transcript and segregation should be checked before any direct record.

### MESP1, primary original full text

[Zhang et al. 2017, PMID 28677747, DOI 10.3892/mmr.2017.6875, full-text Results: Identification of a novel MESP1 mutation in CHD](https://www.spandidos-publications.com/10.3892/mmr.2017.6875?text=fulltext)

- **Source subject:** one 3-month-old female in a cohort of 178 unrelated CHD patients.
- **Variant:** heterozygous `MESP1 c.352C>T, p.Q118X`, absent from unaffected parents and 200 controls, reported as de novo.
- **Directly reported anatomical phenotypes:** DORV and VSD in the same affected female.
- **Experimental evidence:** protein lost transcriptional activation in a reporter assay, with no evidence for dominant negative activity in the tested system.
- **Exact source locator:** Results, *Identification of a novel MESP1 mutation in CHD*, Figure 1 and Figure 2. The study's larger cohort Table II reports many lesions, but those cohort counts are **not all attributable to the MESP1 variant carrier**.

[Lahm et al. 2013, PMID 24056064, DOI 10.1016/j.ejmg.2013.09.001](https://pubmed.ncbi.nlm.nih.gov/24056064/) reports MESP1 sequencing in 215 CHD patients and functional activity tests. It establishes a gene/variant association lead; exact variant-to-lesion pairs need full paper review.

[Werner et al. 2015, PMID 26694203](https://pubmed.ncbi.nlm.nih.gov/26694203/) screened 647 patients with conotruncal and related lesions and found MESP1 variants with functional effects. The abstract does not identify the anatomical diagnosis of each variant carrier; retain as **cohort/genetic and functional evidence** pending detailed case extraction.

### RBFOX2, mixed human clinical, mechanistic and newer primary cohort

[2025 international clinical study, Sauvestre et al., PMID 41221603, DOI 10.1161/CIRCGEN.125.005231, original full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC12922010/). **This PMID was not printed among the frozen GenCC submission bibliographies and is an additive source lead, not an update to that snapshot.**

- **Cohort:** 19 individuals from 12 unrelated families carrying RBFOX2 variants. Reported abnormalities among these 19 include HLHS 10, ascending aortic coarctation/hypoplasia 10, mitral valve defects 7, aortic valve defects 6, VSD 8, ASD 6, DORV in patients P8–P10 and P19, and TOF in P18.
- **Interpretation:** counts overlap within patients. Original Figure 1 supplies case-specific genetic variants and lesion descriptions. CNVs can encompass RBFOX2 plus adjacent genes, requiring variant interval attribution. Several comparison cases have no complete cardiac phenotyping, which should remain unknown rather than coded as negative.
- **Original subject and lineage:** 19 patients are the reported cohort; 12 unrelated families are a different denominator. Source draws additionally on previously published cases and DECIPHER/ClinVar; deduplication requires patient/case tracking.

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

**Evidence scope:** this table reports what ClinGen curators attributed to individual source cases, with original source PMIDs. The primary papers still need exact clinical table and variant matching before a direct primary-case PAR. In particular, `HP:0001627` is a nonspecific morphology term and does not identify a CHD lesion. `HP:0001696` is laterality, not automatically a specific intracardiac lesion.

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
