# STENOSIS-001 structural phenotype coverage v01

Scientific decision: https://app.notion.com/p/41429187800881c39a35f60c6dbaa45e

Status: Agent 1 code authored. Real HPC execution, real counts, Agent 2 independent verification, and public release remain pending.

## Scientific scope

The versioned classification includes descendants (and root) of HP:0030680 under native HPO is_a relationships plus the nine approved stenosis exceptions. The six deferred regurgitation terms are excluded from the explicit exception set. If one is a native morphology descendant, its inclusion is attributed to that ancestry rather than to the exception decision. All original ontology relationships remain unchanged.

Source coverage derives from the completed two-level HPOA source/discovery export. Disease-to-phenotype source annotations remain distinct from gene-to-disease-mediated discovery projections. No new direct gene disruption assertion is created. A source claim that is not negated can retain 0/N or unreported frequency. The table and manifest retain these observations and separately report original positive-frequency source rows. Onset is reported only where the source supplied it.

## Pinned inputs

- Frozen 662-gene registry, data/releases/2026.09.08/genes.tsv, SHA-256 523cd288c68608d4c1e277930685666895cfb5fd002ee99705e9a5b21caed43c.
- HPO hp.obo v2026-09-01, SHA-256 93dace952fcb3ec4728818857f6ba76bc2d5312f4d83266519b8694b8e798f22.
- HPO genes_to_phenotype.txt, SHA-256 507a17bff9c49e6329fbd88b1f91734fa7e9fdea5c06304044c0892eb6ab248c.
- HPO phenotype.hpoa, SHA-256 e89aa39c8f97bf5a52c5d160f9250a603681d630ade8ec2679d84ac5aece1f72.
- Verified two-level export in results/phenotypes/hpo_two_level_projection_v01 with its existing SHA256SUMS.txt.

The runner verifies the above hashes, the two-level output hashes, source profile and prior 63,012 evidence links and 62,832 projections. Mismatches stop the analysis.

## HPC commands

All commands begin from the project root. Inspect uncommitted local work before switching branches.

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
git status --short
git fetch origin
git switch review/stenosis-001-structural-v01-20261111
git pull --ff-only origin review/stenosis-001-structural-v01-20261111
git rev-parse HEAD

python -m unittest discover \
  -s scripts/phenotypes/gene_pilot \
  -p 'test_structural_coverage_stenosis_v01.py' -v

python scripts/phenotypes/gene_pilot/structural_coverage_stenosis_v01.py \
  --out results/phenotypes/structural_coverage_stenosis_v01

(
  cd results/phenotypes/structural_coverage_stenosis_v01
  sha256sum -c SHA256SUMS.txt
  sha256sum -c review_bundle.sha256
  unzip -t STENOSIS-001_review_v01.zip
)
```

The runner refuses to overwrite an existing versioned results directory. For a rerun, supply a distinct --out directory and compare SHA256SUMS. Preserve all full analysis tables on Isilon.

## Full outputs on Isilon

- structural_membership.tsv has HPO membership, pinned label, native is_a parents and ancestors, two independent routes, rationale, authority, decision and review state.
- selected_gene_disease_hpo_projections.tsv preserves source projections with canonical HPO ID and structural inclusion route.
- selected_original_hpoa_observations.tsv preserves all original evidence columns and adds the inclusion route and a separate source-onset-reporting field.
- coverage_summary.tsv separates morphology, all approved exceptions, exceptions newly added outside morphology, union and net-new unique sets. Units are unique genes, diseases, HPO IDs, original disease-phenotype source claims, original HPOA source rows, projection evidence links, and positive-frequency original rows.
- exception_decisions.tsv contains all nine approved and six deferred terms with original ancestry and decision provenance.
- source_examples.tsv retains up to five CIC and five LZTR1 original HPOA observations, including source disease, HPO term, reference and reported onset. A missing marker is used where no qualifying observation exists.
- manifest.json has input and output provenance, source hashes, code hash, Git commit and result counts. SHA256SUMS.txt verifies the full tables.

The small STENOSIS-001_review_v01.zip includes only manifest.json, coverage_summary.tsv, exception_decisions.tsv, source_examples.tsv and review_SHA256SUMS.txt. Its SHA-256 appears in review_bundle.sha256. The ZIP is intentionally small and does not contain all source evidence tables.

## Counting and review logic

Coverage uses the not_negated source claim state as annotation coverage. Observed-zero and frequency-unreported rows retain their actual evidence outcomes. The positive_source_rows metric reports an additional restricted observation set. A source row repeated under multiple gene projections counts once as an original source row using resource, release and source row ID. No source onset is inferred from structural membership. Explicit approved-exception membership is distinguished from native morphology inheritance even when both apply.

Agent 2 should independently check pinned HPO term labels, all nine inclusions, all six deferred exception statuses, source preservation, overlap deduplication, CIC/LZTR1 provenance, coverage calculations and checksums. Report discrepancies to the DevMap Communications Log before claiming independent verification. The user retains scientific acceptance authority.
