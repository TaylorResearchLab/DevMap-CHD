# DevMap-CHD two-level exporter edge-case guard v01

Status: **CHOP HPC execution passed 2026-11-07; Agent 2 independent edge-guard code review remains open**. This additive read-only audit addresses the three residual observations in [Claude's 2026-11-07 exporter review](https://app.notion.com/4112918780088146b31ff402d7542e7f). It does not alter the validated `hpoa_disease_subject_two_level_v01` identity profile, historical IDs, source files or frozen registry.

## Scope and scientific distinctions

The two-level exporter has passed real CHOP validation and Claude's independent replication, with 62,832 provisional gene projections, 45,548 HPOA disease-subject source claim groups, and 63,012 evidence links. Claim polarity in that release is derived from the curator qualifier or excluded categorical frequency, while frequency outcomes remain evidence level.

Three future source cases still require explicit handling.

1. **`NOT` with a populated frequency.** The current source contains 40 original NOT disease–phenotype rows, all frequency blank. The current exporter could silently combine `NOT` with an observed-positive frequency on future inputs. The guard flags such source evidence by original evidence ID and source line for review.
2. **Literal `0%` versus `HP:0040285`.** Both indicate a zero-frequency concept, but the v01 exporter maps the former to an `observed_zero` evidence outcome under a `not_negated` claim and the latter to `categorical_excluded` under a `negated` claim. Neither occurred in the verified v01 source. The guard lists them separately and places affected cases on scientific hold. A future change to claim identity semantics must use a new versioned identity profile and requires the user's explicit acceptance.
3. **Manifest conservation field.** The original exporter uses `audit.get("four_fate_conservation")`. The guard requires a non-null `input_rows_conserved_from_prior_gate` field that exactly matches the verified producer integrity audit. It checks the input fate counts against original source row totals when available.

The audit verifies all seven original view output checksums plus original candidate evidence and audit manifests. It compares every HPOA evidence source field, qualifier, frequency and row locator against its preserved original source observation. It does not assume evidence link multiplicity means independent publications.

## Files and outputs

- `audit_two_level_edge_cases_v01.py` is the read-only guard.
- `test_audit_two_level_edge_cases_v01.py` includes synthetic controls for normal sources, NOT plus a positive frequency, 0% versus HP:0040285, missing mandatory conservation metadata, and source tampering.
- A successful HPC run creates `results/phenotypes/hpo_two_level_edge_audit_v01/edge_case_source_rows.tsv`, `manifest.json` and `SHA256SUMS.txt`.

If a future source contains a flagged edge case, the guard writes the review records and exits with code 2. The presence of a flagged source observation never modifies the source claim or promotes a direct biological assertion. The verified November 7 HPO inputs are expected to produce zero flagged edge cases, subject to a real run.

## CHOP HPC commands

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes
python -m unittest discover -s scripts/phenotypes/gene_pilot -p 'test_audit_two_level_edge_cases_v01.py' -v
python scripts/phenotypes/gene_pilot/audit_two_level_edge_cases_v01.py \
  --view-dir results/phenotypes/hpo_two_level_projection_v01 \
  --candidate-dir results/phenotypes/par_candidates_v02 \
  --integrity-dir results/phenotypes/candidate_export_integrity_v01 \
  --out results/phenotypes/hpo_two_level_edge_audit_v01
(cd results/phenotypes/hpo_two_level_edge_audit_v01 && sha256sum -c SHA256SUMS.txt)
```

The existing `hpo_two_level_projection_v01` output and SHA256SUMS should not be regenerated or overwritten for this audit.

## Biological decisions remain separate

Both agents support the proposed two-level source and discovery representation. The User retains final authority to adopt `dmpdsrc1` as source claim identity and `dmpview1` as a discovery projection with frequency in evidence rows. Existing v01 IDs remain internal provisional identifiers pending that decision.

SV-001 LZTR1–ASD is **supported with narrowing** to the DECIPHER-submitted phenotype term published for individual 303983 in Pagnamenta Table 1, without a separately documented ASD ascertainment method.

SV-002 OMIM:314400 is **supported at original disease–phenotype scope** for short mitral and tricuspid chordae from the 1993 neonatal necropsy, with a separate 2018 female FLNA carrier cohort supporting shortened mitral chordae. The 1993 individual has no sequence-confirmed FLNA variant in the original paper. Biological acceptance remains with the User.

Claude's audit of twelve historical entries, HGNC crosswalk, GenCC submitter and classification evaluation, onset-source missingness and custody of older PubMed screen artifacts remain separate.


## CHOP HPC execution result, 2026-11-07

The user ran the new read-only guard against the existing verified outputs after pulling branch `feature/gene-phenotypes` to commit `324132d1c3cbbbbe2048715fb5572ebcf334b002`. All five synthetic tests passed in 0.044 seconds. Real input audit returned `status=no_edge_cases_observed` and `issue_count=0`.

- `original_evidence_links_verified=63012`.
- `not_with_frequency_rows=0`.
- `zero_percent_rows=0`.
- `excluded_frequency_rows=0`.
- `source_fidelity_passed=true`.
- `input_conservation_ledger_verified=true`.
- `edge_cases_require_review=false`.
- `claim_identity_unchanged=true`; `direct_assertions_promoted=0`.
- Original view manifest SHA-256 `9b2dcad818fe0a7e609d2e58d9956ac8a2d7f3cf9887745bd47587beeca00e15`; original candidate manifest SHA-256 `9f3f8bba6bbe4f4deb669ca2ac33b89148ddbe45276aa5f27f3f425839e376e6`.

These results confirm that the three edge cases did not occur in the pinned source data. The previously approved identity profile and completed two-level export remain unchanged. The user-approved source identity and biological dispositions are recorded separately in the DevMap Communications Log.
