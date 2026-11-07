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
