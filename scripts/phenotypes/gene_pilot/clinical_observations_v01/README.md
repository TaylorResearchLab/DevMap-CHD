# Accepted individual clinical observations v01

**Status:** read-only structured documentation of scientific authority decisions SV-003, SV-004 and SV-005. Source claims, original published data and the frozen 662-gene registry are unchanged. This ledger does not issue direct gene–phenotype causal PARs.

## Source scope and record classes

This is a deliberately small scientific evidence layer distinct from the existing approved HPOA disease-subject `dmpdsrc1` assertions and `dmpview1` disease-mediated gene discovery projections.

| File | Unit | Records |
| --- | --- | ---: |
| `approved_clinical_observations_v01.json` | One approved original patient/variant clinical observation | 7 |
| `hpo_mapping_candidates_v01.json` | One source diagnosis token mapped to a reviewed HPO candidate | 11 |
| `functional_evidence_v01.json` | One original MESP1 functional assay result linked to an accepted case | 6 |
| `secondary_curation_records_v01.json` | ClinGen descriptions of **the same** two ROCK2 patients and one MESP1 sex discrepancy, without added independent patients | 3 |

The clinical ledger includes **MESP1 SV-003a/b/c** from one Werner et al. 2016 cohort, **ROCK2 SV-004a/b** from one original PCGC cohort and **HAND1 SV-005a / MESP1 SV-005b** from separately published 2017 index cases, documented by Jin et al. 2017 with a variant reanalysis by Sevim Bayrak et al. 2020. Two publications describing a PCGC subject are **one patient**, not independent replicates.

Accepted clinical diagnosis strings remain in `original_diagnosis_field`. The JSON format is intentional because it preserves literal `| ` separator characters and **trailing spaces** in the ROCK2 `Cardiac Diagnoses` fields from the Jin 2017 original table.

- SV-004a `1-11926`, ROCK2 p.S39F, original diagnoses `AORTIC STENOSIS | BICOMMISSURAL (BICUSPID, BILEAFLET, BIFOLIATE) AORTIC VALVE | TETRALOGY OF FALLOT `.
- SV-004b `1-13760`, ROCK2 p.D255G, original diagnosis `PATENT DUCTUS ARTERIOSUS `.
- SV-003a/b/c have **no original source patient identifier entered**. Their `internal_case_key` values are variant-scoped source locators constructed for indexing and are expressly tagged `internal_variant_scoped_case_reference`. They are not presented as reported patient IDs.

## Evidence fields and clinical context

Each approved observation retains decision ID and date, source gene and original protein change, the source diagnosis field, source patient identification status, original source and locator, inheritance designation, genomic coordinates only where originally supplied, and clinical source metadata when documented.

For ROCK2, the genomic assembly remains null because Table S2 did not declare a build. De novo is qualified by the `filtered de novo variant` report in a trio cohort. For both PCGC patients, `EM=Yes` is a binary extracardiac indicator and does not enumerate extracardiac phenotypes; `NDD=No` is the original cohort label. The original study's `Cardiac Category` remains distinct from the individual `Cardiac Diagnoses` field.

Werner 2016's luciferase and two-hybrid assay values are in a **separate experimental evidence table**. `reported_plus_minus` preserves the published ± values without independently asserting their statistical definition. Functional measurements are not counted as additional clinical subjects.

## Source metadata completed after Claude's independent review

The original Werner 2016 Table 2 provides an explicitly labelled **hg19** column for all three accepted MESP1 variants. The clinical ledger now retains the source genomic strings and cDNA alleles for transcript `NM_018670.3`, in addition to sex, original ethnicity designations and parental genotypes.

| Approved case | Source hg19 | Source cDNA | Sex | Father / Mother |
| --- | --- | --- | --- | --- |
| p.E104K | chr15:90294153C>T | c.310G>A | F | WT / Carrier |
| p.L120P | chr15:90294104A>G | c.359T>C | F | WT / WT |
| p.L147Pfs*9 | chr15:90294027_90294028delTC | c.436_437delAG | F | N/A / N/A |

Each of these rows records original Werner control counts `0/99 CA` and `0/97 AA`, with the original source ethnic classifications `CA`, `CA` and `AAm (no Hisp)` respectively. Original source allele strings remain distinct from a VCF-normalized representation. The ROCK2 source table does **not** declare its assembly, so ROCK2 genome builds remain null.

The separate secondary curator file records ClinGen `CCID:008432` broad `HP:0001710` for ROCK2 p.S39F and `HP:0001627` for p.D255G as **two curator descriptions of the same two original PCGC patients**, not independent clinical evidence.

## New independent 2017 index cases accepted under SV-005

[SV-005 scientific authority decision](https://app.notion.com/p/413291878008818c8aaacc09589dfa9a), November 9, 2026, approves two original case observations after [Claude's independent full-paper verification](https://app.notion.com/p/41329187800881d7bda2e57e66284612).

- **HAND1 p.K132X**, source `c.394A>T`, one 5-month-old boy, original report `congenital DORV, as well as VSD`, de novo from parental testing, PMID 28112363, original cohort 158 patients.
- **MESP1 p.Q118X**, source `c.352C>T`, one 3-month-old girl, original report `DORV and VSD`, de novo from parental testing, PMID 28677747, original cohort 178 patients.
- HPO candidates `HP:0001719` DORV and `HP:0001629` VSD are kept as separate mappings for each case.
- No published clinical patient ID was available in the reviewed text. The ledger uses internal **gene + cDNA variant + PMID** source keys, distinct from published patient identifiers. **RBFOX2 P7 `c.352C>T` is a different gene and person** from MESP1 p.Q118X.
- The MESP1 source identifies the patient as **female**; [ClinGen CCID:008509](https://search.clinicalgenome.org/CCID:008509) describes the same individual as **Male**. A separate secondary-curation record retains both values with the same-patient lineage and correction state `submitted_by_user_pending_clingen_response`. The user reported submitting the correction request on November 9, 2026. ClinGen acknowledgement and correction verification remain pending.

All seven approved records remain individual **source clinical co-observations**, not causal PARs. Functional evidence from Li and Zhang can be recorded separately from the six Werner assay values after direct original figure transcription if needed.

## HPO mapping discipline

`hpo_mapping_candidates_v01.json` retains the original clinical terms and reviewer-checked HPO candidates as a separate record type. The mapping status is **independent reviewer checked, not a replacement for source text**. The mapping checks target pinned HPO `v2026-09-01`.

- TOF maps to `HP:0001636`.
- Bicuspid aortic valve maps to parent term `HP:0001647` without assuming a particular raphe subtype.
- Source `cVSD` is broader-normalized to `HP:0001629` while retaining the conoventricular subtype.
- Source `AORTIC STENOSIS` is **unlevelled**. Candidate `HP:0001650` states *aortic valve stenosis*, adding a valvar level not specified in the original clinical text. It is explicitly flagged `flagged_candidate_adds_valvar_level` and remains outside the strict structural heart morphology branch used in the earlier coverage audit.
- PDA maps to `HP:0001643` (great artery vascular morphology), with gestational age and onset absent from the original source.

All five clinical records are accepted **at their original observation scope**. The separate HPO mappings remain candidate normalization records rather than additional accepted patient observations.

## Versioned source and authority references

**SV-003 MESP1:** [User approval](https://app.notion.com/p/4122918780088184992eee2eb51848c5), [approved evidence packet](../source_validation/SV-003_MESP1_Werner2016_three_patient_lesions_APPROVED.md), Werner et al. 2016 PMID `26694203`, original Table 2. The three cases derive from one CHD cohort (`n=647`).

**SV-004 ROCK2:** [User approval](https://app.notion.com/p/41229187800881d8bbd9d5297820290d), [approved evidence packet](../source_validation/SV-004_ROCK2_PCGC_two_patient_observations_APPROVED.md), [source case join](../source_validation/ROCK2_Jin2017_S1_to_SevimBayrak2020_S2_CASE_JOIN_v01.md).

- Jin 2017 S1 phenotype original TSV `NIHMS906719-supplement-supp_datasets_TABLE_S1.tsv.txt`, ChatGPT file `file_00000000785481f5bcae6ac78df7ada5`, SHA-256 `8089f313183d025f0ad9d5e58d554c5740a15dfb53172492cd03a8c6d3fe03ee`, source lines 2687 and 2740.
- Sevim Bayrak 2020 Table S2 variant original publisher XLSX [source URL](https://media.springernature.com/original/springer-static/esm/art%3A10.1186%2Fs13073-019-0709-8/MediaObjects/13073_2019_709_MOESM1_ESM.xlsx), SHA-256 `1ee89cc19b7e88182e5c039e5a5621f6e488a3efaf9342d5cba63381362d9ab9`, source lines 245 and 246. Original XLSX attached to [DevMap CHD4 log](https://app.notion.com/p/4122918780088122a501d23809e7e124).

The hashes above are from Claude's independent source review of the attached original files. They are **source checksums**, not checksums of these newly constructed JSON records.

## Read-only validation

From CHOP HPC:

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
python scripts/phenotypes/gene_pilot/clinical_observations_v01/validate_approved_clinical_v01.py
python -m unittest discover -s scripts/phenotypes/gene_pilot/clinical_observations_v01 -p 'test_*.py' -v
```

The validator locks the five approved observation IDs, source diagnosis strings (including trailing spaces), original Werner hg19/cDNA and parent metadata, gene/variant identity, two same-patient ClinGen curator assignments, user disposition scope, seven HPO mappings and six functional measurements. Alterations raise a `ValueError`.

**Prior development check:** seven initial tests passed on Claude\'s independent checkout. The updated ten ledger tests plus three direct source reconciliation tests, source metadata changes and secondary curator records require a fresh independent run before full review closure.

## Direct source comparison against original published files

The companion validator `verify_original_sources_v01.py` can check the accepted ROCK2 records against the actual **Jin 2017 S1 TSV** and original **Sevim Bayrak 2020 publisher XLSX**. It verifies the independent source SHA-256 digests from Claude's inspection before comparing the literal original S1 clinical fields and S2 variant values. The source comparison uses Python standard library TSV and XLSX XML reading. It reads source bytes without changing the original datasets.

```bash
python scripts/phenotypes/gene_pilot/clinical_observations_v01/verify_original_sources_v01.py \
  --s1-tsv /path/to/NIHMS906719-supplement-supp_datasets_TABLE_S1.tsv.txt \
  --s2-xlsx /path/to/13073_2019_709_MOESM1_ESM.xlsx
python -m unittest discover -s scripts/phenotypes/gene_pilot/clinical_observations_v01 -p 'test_*.py' -v
```

The source comparator uses original SHA-256 values `8089f313183d025f0ad9d5e58d554c5740a15dfb53172492cd03a8c6d3fe03ee` (Jin original S1 TSV) and `1ee89cc19b7e88182e5c039e5a5621f6e488a3efaf9342d5cba63381362d9ab9` (Sevim original XLSX). Direct source comparison is optional when those exact files are accessible and is additional to the fixed-value ledger validator. The companion `test_verify_original_sources_v01.py` supplies synthetic S1 and S2 sources with test-specific digests to exercise parsing and failed-checksum behavior.

**Validation status:** Claude confirmed the initial 7/7 tests and original ROCK2 source agreement on an independent checkout. The **updated** ten ledger tests, three source reconciliation tests and added metadata/lineage records have been committed for a fresh independent run. This documentation does not claim the updated scripts or the new source comparison have already been executed on HPC.

## Next independent review

DevMap-Claude should review the three JSON record classes against the original approved SV-003 and SV-004 evidence packets, verify the stable source patient identities and literal field fidelity, review the HPO specificity flags, and execute the committed validator and tests in an independent repository checkout. Canonical direct causal PAR generation remains outside this ledger's scope.

## Validation status after SV-005

The ledger includes **7 accepted cases, 11 candidate HPO mappings, 6 source functional assay entries and 3 separate secondary ClinGen curation entries**. The fixed-data validator and its Python tests were updated for the two accepted cases and the original-female versus curator-male conflict. The prior independent tests verified the earlier five-case source ledger. This expanded seven-case version requires a fresh independent repository execution before its automated verification status is claimed complete. The optional original file checksum comparator continues to validate the two ROCK2 PCGC cases against the original S1/S2 files.
