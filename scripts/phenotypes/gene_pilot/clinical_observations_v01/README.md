# Accepted individual clinical observations v01

**Status:** read-only structured documentation of scientific authority decisions SV-003 and SV-004. Source claims, original published data and the frozen 662-gene registry are unchanged. This ledger does not issue direct gene–phenotype causal PARs.

## Source scope and record classes

This is a deliberately small scientific evidence layer distinct from the existing approved HPOA disease-subject `dmpdsrc1` assertions and `dmpview1` disease-mediated gene discovery projections.

| File | Unit | Records |
| --- | --- | ---: |
| `approved_clinical_observations_v01.json` | One approved original patient/variant clinical observation | 5 |
| `hpo_mapping_candidates_v01.json` | One source diagnosis token mapped to a reviewed HPO candidate | 7 |
| `functional_evidence_v01.json` | One original MESP1 functional assay result linked to an accepted case | 6 |

The clinical ledger includes **MESP1 SV-003a/b/c** from one Werner et al. 2016 cohort and **ROCK2 SV-004a/b** from one original PCGC cohort, documented by Jin et al. 2017 with a variant reanalysis by Sevim Bayrak et al. 2020. Two publications describing a PCGC subject are **one patient**, not independent replicates.

Accepted clinical diagnosis strings remain in `original_diagnosis_field`. The JSON format is intentional because it preserves literal `| ` separator characters and **trailing spaces** in the ROCK2 `Cardiac Diagnoses` fields from the Jin 2017 original table.

- SV-004a `1-11926`, ROCK2 p.S39F, original diagnoses `AORTIC STENOSIS | BICOMMISSURAL (BICUSPID, BILEAFLET, BIFOLIATE) AORTIC VALVE | TETRALOGY OF FALLOT `.
- SV-004b `1-13760`, ROCK2 p.D255G, original diagnosis `PATENT DUCTUS ARTERIOSUS `.
- SV-003a/b/c have **no original source patient identifier entered**. Their `internal_case_key` values are variant-scoped source locators constructed for indexing and are expressly tagged `internal_variant_scoped_case_reference`. They are not presented as reported patient IDs.

## Evidence fields and clinical context

Each approved observation retains decision ID and date, source gene and original protein change, the source diagnosis field, source patient identification status, original source and locator, inheritance designation, genomic coordinates only where originally supplied, and clinical source metadata when documented.

For ROCK2, the genomic assembly remains null because Table S2 did not declare a build. De novo is qualified by the `filtered de novo variant` report in a trio cohort. For both PCGC patients, `EM=Yes` is a binary extracardiac indicator and does not enumerate extracardiac phenotypes; `NDD=No` is the original cohort label. The original study's `Cardiac Category` remains distinct from the individual `Cardiac Diagnoses` field.

Werner 2016's luciferase and two-hybrid assay values are in a **separate experimental evidence table**. `reported_plus_minus` preserves the published ± values without independently asserting their statistical definition. Functional measurements are not counted as additional clinical subjects.

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

The validator locks the five approved observation IDs, original source diagnosis strings (including trailing spaces), gene/variant identity, patient linkage, user disposition scope, seven HPO mappings and their specificity flags, and six functional measurements. Any alteration raises a `ValueError`.

**Development check:** seven synthetic and source integrity scenarios passed in a local equivalent validation fixture. The three GitHub JSON files also passed independent in-session direct content checks for all five identities, original diagnosis strings, mapped terms, source separation and functional record counts. The committed Python scripts still require a fresh run against the **repository checkout** on CHOP HPC before labeling the repository-level validation complete.

## Next independent review

DevMap-Claude should review the three JSON record classes against the original approved SV-003 and SV-004 evidence packets, verify the stable source patient identities and literal field fidelity, review the HPO specificity flags, and execute the committed validator and tests in an independent repository checkout. Canonical direct causal PAR generation remains outside this ledger's scope.
