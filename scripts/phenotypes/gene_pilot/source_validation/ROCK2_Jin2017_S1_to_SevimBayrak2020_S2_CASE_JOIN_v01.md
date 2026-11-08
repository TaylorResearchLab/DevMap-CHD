# ROCK2 | Primary PCGC individual diagnoses linked to original ROCK2 de novo variants

> **Current authoritative disposition, 2026-11-08:** Deanne Taylor **ACCEPTED the documentation of both original ROCK2 PCGC patient observations while retaining original diagnosis strings**. The source join was independently verified by DevMap-Claude. SV-004a = p.S39F / proband 1-11926 (TOF, bicuspid aortic valve and aortic stenosis). SV-004b = p.D255G / proband 1-13760 (patent ductus arteriosus). This is acceptance at individual clinical co-observation scope. See the [user decision](https://app.notion.com/p/41229187800881d8bbd9d5297820290d) and [SV-004 accepted evidence packet](https://github.com/TaylorResearchLab/DevMap-CHD/blob/feature/gene-phenotypes/scripts/phenotypes/gene_pilot/source_validation/SV-004_ROCK2_PCGC_two_patient_observations_APPROVED.md). The earlier pending review sections below document the pre-decision audit history.


**Date:** 2026-11-08. **Current status:** source join independently verified by DevMap-Claude and original individual clinical observations **accepted by scientific authority as SV-004a and SV-004b**. Direct causal gene–phenotype PAR issuance remains a separate decision.

## Source identity and custody

**Jin et al. 2017**, *Nature Genetics*, PMID **28991257**, DOI [10.1038/ng.3970](https://doi.org/10.1038/ng.3970), original supplementary workbook `NIHMS906719-supplement-supp_datasets.xlsx`, **Supplementary Data Set 1: Phenotypes for each CHD proband**. User exported original table to TSV with filename `NIHMS906719-supplement-supp_datasets_TABLE_S1.tsv.txt`, conversation attachment `file_00000000785481f5bcae6ac78df7ada5`, reported file size **515,316 bytes**. The source was read directly using Files `find`; original text lines **2687** and **2740** correspond to two unique blinded PCGC subject IDs. This user's attachment is a tab-separated text file even though it ends in `.txt`. The alternate Python/container mount was absent and was not used to derive the findings.

**Sevim Bayrak et al. 2020**, *Genome Medicine*, DOI [10.1186/s13073-019-0709-8](https://doi.org/10.1186/s13073-019-0709-8), [original Springer XLSX Additional File 1](https://media.springernature.com/original/springer-static/esm/art%3A10.1186%2Fs13073-019-0709-8/MediaObjects/13073_2019_709_MOESM1_ESM.xlsx), **Table S2: Filtered de novo mutations in cases**. User-supplied TSV `13073_2019_709_MOESM1_ESM_TABLE_S2.tsv`, conversation attachment `file_00000000445881f592c11bb3e3a88732`, size 36,362 bytes. Original Table S2 source lines **245–246** report the two distinct variants and blinded IDs.

Both files are **published source datasets referring to the same original PCGC subjects**. The 2020 paper is a secondary variant reanalysis. ClinGen's 2024 Limited gene–disease curation is a third source interpretation, not independent new patients.

## Exact record linkage using original blinded patient ID

| Source field | ROCK2 p.S39F | ROCK2 p.D255G |
| --- | --- | --- |
| **Source gene** | ROCK2 (ENSG00000134318; HGNC:10252) | ROCK2 (ENSG00000134318; HGNC:10252) |
| **2020 S2 Blinded ID** | **1-11926** | **1-13760** |
| Original variant | p.S39F | p.D255G |
| Original chr/pos/ref/alt | `2:11484147 G>A` | `2:11367484 T>C` |
| 2020 S2 Cardiac Category | **CTD** | **other** |
| 2020 S2 EM / NDD | Yes / No | Yes / No |
| 2020 S2 family history CHD | Negative | Negative |
| 2017 S1 Cohort | PCGC | PCGC |
| 2017 S1 Sample Type | **Trio** | **Trio** |
| 2017 S1 Cardiac Category | **CTD** | **other** |
| **2017 S1 Cardiac Diagnoses, exact original terms** | **AORTIC STENOSIS**; **BICOMMISSURAL (BICUSPID, BILEAFLET, BIFOLIATE) AORTIC VALVE**; **TETRALOGY OF FALLOT** | **PATENT DUCTUS ARTERIOSUS** |
| 2017 S1 EM / NDD | Yes / No | Yes / No |
| 2017 S1 source line | **2687** | **2740** |
| 2020 S2 source line | **245** | **246** |

Source 2017 original row text (the ` | ` separators **occur within the source Cardiac Diagnoses field**, and have been preserved verbatim):

- **1-11926:** `1-11926 | PCGC | Trio | CTD | "AORTIC STENOSIS | BICOMMISSURAL (BICUSPID, BILEAFLET, BIFOLIATE) AORTIC VALVE | TETRALOGY OF FALLOT " | Yes | No`.
- **1-13760:** `1-13760 | PCGC | Trio | other | PATENT DUCTUS ARTERIOSUS | Yes | No`.

One file describes original diagnoses; the other attaches ROCK2 variants to the same blinded IDs. This is a **patient-level variant/diagnosis association by exact identifier**, stronger source specificity than the 2020 broad classification alone. Three diagnoses belong to the one p.S39F subject, while PDA belongs to the one p.D255G subject. No independent replication is implied by citing both files.

### Interpretation relative to ClinGen

The [ClinGen ROCK2 CHD validity curation CCID:008432](https://search.clinicalgenome.org/CCID:008432) is **Limited**, with curated case evidence of p.S39F **conotruncal defect HP:0001710** and p.D255G broad **abnormal heart morphology HP:0001627**. The primary 2017 source provides **more specific** original observations: tetralogy of Fallot, bicuspid aortic valve and aortic stenosis for p.S39F, and patent ductus arteriosus for p.D255G.

HPO mapping candidates, to be checked against the pinned `hp.obo` ontology and original phenotype semantics before acceptance:

- p.S39F tetralogy of Fallot: **HP:0001636** (previously verified in MESP1 source work).
- p.S39F bicuspid aortic valve: **candidate HP:0001647** (verify exact term against frozen HPO).
- p.S39F aortic stenosis: require precise source-concordant HPO term; the original report says `AORTIC STENOSIS` without location or mechanism, so avoid inferring valvar location from the accompanying bicuspid morphology.
- p.D255G PDA: **candidate HP:0001643** (verify precise ontology definition and onset scope). PDA is persistent patency of the fetal ductus arteriosus and should be categorized separately from congenital intracardiac structural defects. The reported original dataset lacks onset and treatment context.

The 2017 table's `EM = Yes` indicates extracardiac manifestations; it does **not enumerate the extracardiac phenotypes** for either patient. `NDD = No` is the source's cohort-level recorded value, not a complete negative neurological phenotype evaluation. The S2 family history field is `Negative` for both, distinct from de novo variant calling.

Original coordinate reference genome build must be documented before normalized genome variant representation. Use source literal coordinates and allele representations until verified.

### Biological decision and version discipline

**Source discovery:** confirmed two patient-specific ROCK2 variant/diagnosis records from exact join of original published datasets. **Biological interpretation:** rare de novo variation co-observed with the original cardiac diagnoses in a CHD ascertainment cohort. The original reports do not by themselves prove causal sufficiency of these ROCK2 variants; disease validity remains ClinGen Limited versus PanelApp Australia Moderate. The source-linked clinical observations are ready for independent DevMap-Claude original-table check and user `accept | narrow | defer | reject` at **observed individual scope**.

Preserve the frozen 662-gene registry, 2017/2020 original data, GenCC and HPOA source assertions, and approved `dmpdsrc1` original disease-subject and `dmpview1` gene-keyed discovery relationships. This source join adds no canonical direct causal PAR ID, makes no claim of a second patient sample and does not reassign accepted previous SV-003 MESP1 observations.

**Recommended review:** independently reproduce the two blinded ID matches and source diagnosis strings; verify candidate phenotype HPO identifiers, including separation of broad `AORTIC STENOSIS` from any particular valve stenosis; inspect published clinical reports if detailed severity or onset is required. Confirm no unintended cohort duplication before user disposition.

## Decision and independent reviewer integrity checkpoint

The user's exact acceptance was “I accept the documentation of both patient observations while retaining the original dx strings.” Documented in [SV-004 decision](https://app.notion.com/p/41229187800881d8bbd9d5297820290d). Independent review [DevMap-Claude's completed ROCK2 original-data review](https://app.notion.com/p/4122918780088142a658e15bb37de4d2) independently reproduced the S2 source XLSX and both Jin S1 original diagnosis rows, including source pipe separators and trailing whitespace, with **2,871 distinct blinded IDs**. Publisher S2 XLSX SHA-256 `1ee89cc19b7e88182e5c039e5a5621f6e488a3efaf9342d5cba63381362d9ab9`. Jin S1 user TSV SHA-256 `8089f313183d025f0ad9d5e58d554c5740a15dfb53172492cd03a8c6d3fe03ee`. **SV-004a and SV-004b accepted at original individual documentation scope.** The original diagnosis strings, source paths and patient IDs remain intact. Any HPO label is a separate mapping with an explicit aortic stenosis valvar-level qualification.
