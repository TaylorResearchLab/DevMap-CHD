# DevMap-CHD polarity collision source review v01

**Status:** Agent 1 review preparation, committed for independent SCUTER Agent 2 challenge. Read-only source tracing; no accepted direct PAR.

## Observed collision pattern from the 2026-11-07 CHOP HPC manifest

The user supplied the complete `polarity_identity_collisions.tsv` containing 27 distinct legacy provisional identity groups and 55 candidate IDs from 16 HGNC genes. The groups contain:

- 14 `asserted_absent;asserted_present`
- 12 `asserted_present;unspecified`
- 1 `asserted_absent;asserted_present;unspecified` (TSC1 / OMIM:191100 / HP:0012798)

All groups include `asserted_present`. FLNA has 6 groups, TGFBR2 has 5 and TGFBR1 has 2. These 13 groups should be included in phenotype-specific clinical review, with structural malformations separated from physiology, cardiomyopathy and other traits.

## HPO's original source meaning

The HPO project explicitly distinguishes:

- `qualifier=NOT`: source-level negated disease–phenotype annotation, with Orphanet consensus use;
- `frequency=0/N`: a study-specific observation of zero affected individuals in a cohort of N, which does **not** establish universal absence in all individuals with the disease;
- `frequency=HP:0040285`: Excluded, 0%;
- `frequency=HP:0040280` through `HP:0040284`: positive categorical frequencies (Obligate, Very frequent, Frequent, Occasional, Very rare);
- `frequency` blank: the disease–phenotype annotation provides no quantitative frequency in that field, not an observation of phenotype absence.

Primary HPO definitions:
- [HPO phenotype.hpoa file specification](https://obophenotype.github.io/human-phenotype-ontology/annotations/phenotype_hpoa/)
- [HPO frequency and negative annotation semantics](https://obophenotype.github.io/human-phenotype-ontology/annotations/frequency/)

The original exporter `polarity()` labels nonzero categorical frequency terms and blank frequency as `unspecified`. Therefore `asserted_present;unspecified` candidate splits can represent **different degrees of frequency metadata** rather than opposite biological polarity. The exporter also assigns `asserted_absent` to `0/N` cohort observations and to `NOT` annotations, which are distinct evidence types. These are interpretation issues in the **legacy provisional candidate profile**, not authorization to silently rehash existing IDs.

## Focused source extraction

[trace_polarity_collision_sources_v01.py](https://github.com/TaylorResearchLab/DevMap-CHD/blob/feature/gene-phenotypes/scripts/phenotypes/gene_pilot/trace_polarity_collision_sources_v01.py) joins the frozen audit's 27 collision groups to `par_candidates.tsv` and original-scope `par_evidence.tsv`. It checks existing SHA256 manifests, candidate identity fields, exact disease and HPO subjects, original evidence roles and the legacy polarity calculation. It extracts all original HPOA source reference identifiers, frequencies, qualifiers, evidence codes, disease subjects, annotations and source locators. It also produces a separate field for HPO source frequency interpretation **without modifying the legacy candidate polarity field**.

Outputs:
- `polarity_collision_source_rows.tsv` — all original linked annotation rows for the 55 candidate IDs, including source line locators and original references;
- `polarity_collision_group_summary.tsv` — 27 groups with source evidence counts, PMID-bearing records, `NOT` qualifiers, study zero frequencies, categorical positive terms, blank frequencies and categorical positive cases that the legacy exporter called unspecified;
- `manifest.json` and `SHA256SUMS.txt`.

Neither the frozen 662 registry nor the 62,860 legacy provisional candidates are modified. This is a source evidence review table, not a direct observed gene–phenotype assertion export.

## Run on CHOP HPC

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes
python -m unittest discover -s scripts/phenotypes/gene_pilot -p 'test_trace_polarity_collision_sources_v01.py' -v
python scripts/phenotypes/gene_pilot/trace_polarity_collision_sources_v01.py \
  --candidate-dir results/phenotypes/par_candidates_v02 \
  --audit-dir results/phenotypes/candidate_export_integrity_v01 \
  --out results/phenotypes/polarity_collision_source_review_v01
```

The expected manifest from the user supplied collision file is 27 groups and 55 candidate IDs. The total number of original HPOA evidence rows is intentionally computed from the existing evidence file rather than assumed.

## Review and decision boundary

Claude Agent 2 should independently challenge whether `0/N`, `NOT` and positive categorical frequencies were semantically conserved. If warranted, compare original cited clinical cohorts and any affected patient or onset qualifiers. The original HPOA disease–phenotype record remains the source assertion. A separate direct gene disruption–phenotype observation requires a specific person, variant or mechanistic evidence and the project's independent review procedure.

The PAR Core claim identity and polarity policy remain with the user and PAR Core. Source evidence polarity can be retained independently from identity until that decision. SV-001 and SV-002 remain pending Agent 2 source review and the user's biological disposition.


## CHOP HPC real-input result, 2026-11-07

User supplied a completed source trace and synthetic regression output. All 3 tests passed. The source gate returned `source_audit_gate_passed=true`, with **27** collision groups, **55** legacy candidate IDs and **77** original HPOA evidence records. The reported source candidate manifest SHA-256 is `9f3f8bba6bbe4f4deb669ca2ac33b89148ddbe45276aa5f27f3f425839e376e6`; the prior audit manifest SHA-256 is `a8506e714b0aafc00b068893339b6de6059092623f2bb58e80611f07e45cf29d`.

All 15 groups with `asserted_absent` have `source_absence_basis=zero_numerator`; none has an HPOA `NOT` qualifier. These are study-specific `0/N` frequencies in the original disease–phenotype annotations, and are not universal disease negation. TSC1 / OMIM:191100 / HP:0012798 has all three legacy states and includes a positive categorical HPO frequency that the legacy exporter classified as `unspecified`. Four FLNA / OMIM:305620 groups (17, 18, 21 and 22) each have two evidence rows and only one distinct source reference, requiring source-level examination before interpreting the differing frequencies as biologically discordant.

The full `polarity_collision_source_rows.tsv` is retained on CHOP HPC under `results/phenotypes/polarity_collision_source_review_v01/`. Source context interpretation and independent Claude review remain pending. Original candidate identities, frozen gene registry and direct assertion promotion state remain unchanged. The 77 original evidence rows are not 77 independent clinical publications.


## Agent 1 analysis of the uploaded original HPOA evidence table, 2026-11-07

**Input custody:** The user supplied the original `polarity_collision_source_rows.tsv` produced by the successful CHOP HPC run. This analysis inspects that file, which contains 77 rows and 29 columns. The original file remains on private CHOP HPC in `results/phenotypes/polarity_collision_source_review_v01/`. No raw source file was added to GitHub. Evidence remains at the original HPOA disease–phenotype scope.

### Source-wide audit of the 77 annotations

| Measure | Count |
| --- | ---: |
| Unique HPOA evidence IDs and original source line locators | 77 each |
| Distinct source lineage keys | 72 |
| Source rows with explicit PMID | 69 |
| Distinct PMID identifiers | 43 |
| PCS / TAS / IEA evidence codes | 68 / 3 / 6 |
| Positive numerical study frequencies | 37 (36 fractions and one percentage) |
| Zero-numerator study frequencies | 27 |
| Positive categorical HPO frequency terms | 3 |
| Frequency field blank | 10 |
| Nonempty `qualifier` / explicit `NOT` | 0 / 0 |
| Sex-stratified rows | 13 |

There are 19 instances of `0/1`, three of `0/2`, one of `0/5`, two of `0/9`, and two of `0/11`. These are original study observations, not universal negations. All 13 legacy `unspecified` observations are either positive categorical frequency (3) or unreported frequency (10). In a non-negated disease–phenotype record, missing frequency is missing prevalence metadata, not absence of a disease–phenotype association. Of the 69 PMID-bearing rows, 68 are PCS and one is IEA. The remaining eight rows without an explicit PMID are three TAS and five IEA.

The 72 lineage keys are publication/phenotype lineage groupings and must not be treated as 72 independent original studies. A repeated paper across distinct phenotypes still represents one original publication. Distinct PMID count is 43, with potential patient/cohort reuse across papers not resolved by this table.

### FLNA exact sex-stratified observations

In `OMIM:305620`, the four original phenotype pairs below have **one source publication, PMID 16835913**, with the source sex field distinguishing male and female denominator groups.

| HPO | Female | Male | Source locator groups |
| --- | ---: | ---: | --- |
| HP:0000175 | 1/11 | 0/9 | 17 |
| HP:0001363 | 0/11 | 1/9 | 18 |
| HP:0004602 | 0/11 | 3/9 | 21 |
| HP:0009702 | 1/11 | 0/9 | 22 |

PMID [16835913](https://pubmed.ncbi.nlm.nih.gov/16835913/) is Robertson et al. (2006), *Frontometaphyseal dysplasia: mutations in FLNA and phenotypic diversity*. These extracted HPOA observations represent sex-stratified outcomes from the same clinical source, and the existing `source_lineage_key` correctly collapses within each phenotype at publication origin. Each original HPOA record has its own evidence ID and line locator. A future observation identity or frequency aggregation must include sex as part of its cohort stratum without counting male and female records as independent publications.

The separate `FLNA / OMIM:314400 / HP:0001634` group (19) describes mitral valve prolapse in PMID [17190868](https://pubmed.ncbi.nlm.nih.gov/17190868/): male 12/14 and female 4/30, plus a separate IEA OMIM annotation with unreported frequency. This supports a **disease–phenotype source annotation** for mitral valve prolapse. It is distinct from SV-002's shortened mitral and tricuspid chordae observations and cannot substitute for those phenotype-specific citations.

### TSC1 triple annotation and upstream HPO issue

The `TSC1 / OMIM:191100 / HP:0012798` group (9) is **pulmonary lymphangiomyomatosis**, a noncardiac phenotype. Original HPOA rows are PMID 10852420 (female 20/78), PMID 16485546 (male `HP:0040284`, Very rare), and PMID 29196670 (sex unspecified 0/5). This exact trio is documented in the open upstream [HPO issue #11301](https://github.com/obophenotype/human-phenotype-ontology/issues/11301), which reports that the derived `genes_to_phenotype.txt` export can retain only a single selected annotation for a disease/HPO pair despite multiple original HPOA rows. A maintainer noted on 2025-12-18 that the derived gene export should ignore sex differences while its source documentation is adjusted. Issue status was verified open on 2026-11-07.

Our source tracing retained all three HPOA evidence rows. The known upstream collapse is further support for using `genes_to_phenotype.txt` as a discovery index and preserving `phenotype.hpoa` as original disease–phenotype provenance. A comparison against the exact pinned 2026-09-01 G2P line, if subsequently needed, should be performed as a targeted source check rather than a full reprocessing of frozen analyses.

### Cardiac morphology cases within the collision set

- `TGFBR1 / OMIM:609192 / HP:0001631` (atrial septal defect): five original PCS annotations, including two positive frequencies `5/30` and `1/3` and three `0/1` studies. Disease-level variable prevalence is supported; no particular TGFBR1 variant or individual genotype was recovered by this source trace.
- `TGFBR1 / OMIM:609192 / HP:0001643` (patent ductus arteriosus): `2/4`, `10/30`, and `0/1` from three distinct PMIDs.
- `TGFBR2 / OMIM:610168 / HP:0001643` (patent ductus arteriosus): `1/1`, `5/9` and four zero numerator studies (`0/1`, `0/1`, `0/2`, `0/1`).
- `TGFBR2 / OMIM:610168 / HP:0001647` (bicuspid aortic valve): `2/8` and four zero numerator studies (`0/1` each).
- `TGFBR2 / OMIM:610168 / HP:0004970` (ascending tubular aorta aneurysm): one IEA annotation with no frequency and one PCS `17/40`. Aneurysm is a vascular phenotype; congenital origin requires phenotype-specific evidence.

These are source-specific *disease–phenotype* examples. The original studies may differ in ascertainment, age, sex and genotype. Their reported denominators should not be indiscriminately pooled. Structural cardiac phenotypes remain distinct from cardiovascular physiology, progressive vascular disease and noncardiac clinical features.

### Scientific determination proposed to Agent 2 and user

1. **Observation polarity should be separate from source frequency.** Preserve `source_qualifier`, `numerator`, `denominator`, categorical frequency, source PMID, sex and onset for every disease–phenotype source record. Source `0/N` has a cohort interpretation, not a universal `NOT`.
2. **Legacy candidate identity remains frozen and provisional.** The 27 collisions and 55 candidate IDs expose an implementation-level conflation of cohort prevalence and biological assertion status. They do not authorize a PAR Core claim identity change or direct gene disruption claim promotion.
3. **Preserve expert source evidence classes.** An expert PCS annotation with PMID is accepted as an original disease–phenotype source assertion under the approved 2026-11-07 policy. IEA retains electronic classification even with PMID. No PubMind AI-derived direct claim is accepted without secondary review.
4. **Source conservation is satisfied for this 77-row subset.** The uploaded trace shows 77 distinct evidence IDs and original source locators and an explicit one-to-many relationship between source publication and phenotype/sex observation. This does not establish independent biological source count or gene-disruption causality.
5. **Review boundary remains open.** Agent 2 should challenge these source interpretations and the upstream HPO export issue. The user retains final scientific decisions on direct PAR identity and promotion. SV-001 and SV-002 remain separate source validation cases pending Agent 2 independent review.

References: [HPO frequency interpretation](https://obophenotype.github.io/human-phenotype-ontology/annotations/frequency/), [HPO annotation file specification](https://obophenotype.github.io/human-phenotype-ontology/annotations/phenotype_hpoa/), [HPO issue #11301](https://github.com/obophenotype/human-phenotype-ontology/issues/11301).
