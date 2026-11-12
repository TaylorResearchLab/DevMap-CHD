# STENOSIS-001 | v02 source-onset and evidence-code reporting

This additive revision implements the two reporting corrections from [Claude's independently reproduced STENOSIS-001 review](https://app.notion.com/p/41529187800881c0912cf14cbcf1ae82). It does not modify v01, any pinned source, the frozen 662-gene registry, or the approved nine-term structural membership.

## Evidence distinctions

- **Phenotype row onset** is the literal onset column in an HPOA aspect-P source row. The reviewed v01 output has 2,813 of 2,931 distinct structural P rows with a blank onset column. This statistic describes source field completeness.
- **Disease onset context** is a separate HPOA aspect-C annotation for the disease subject. It may describe congenital, infantile, or another onset category for a disease. It is not direct evidence that the specific P phenotype was observed at that onset in an individual patient.
- **Evidence code** is a native source observation property. The LZTR1 mitral stenosis examples carry IEA and TAS codes with OMIM references. These are retained with the original reference and disease ID instead of being treated as direct patient-level PMID evidence.

Claude independently observed aspect-C onset for 312 of 762 union diseases, including 188 with congenital onset. v02 recomputes these numbers from the already verified original disease_context.tsv and retains each source row. The full context table stays on Isilon; the compact review ZIP includes only summary counts and revised examples.

## CHOP HPC commands

Run this code from the existing project root. The v01 output directory is required and stays unchanged.

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
git status --short
git fetch origin
git switch review/stenosis-001-structural-v01-20261111
git pull --ff-only origin review/stenosis-001-structural-v01-20261111

python -m unittest discover \
  -s scripts/phenotypes/gene_pilot \
  -p 'test_refine_stenosis_001_reporting_v02.py' -v

python scripts/phenotypes/gene_pilot/refine_stenosis_001_reporting_v02.py

(
  cd results/phenotypes/structural_coverage_stenosis_reporting_v02
  sha256sum -c SHA256SUMS.txt
  sha256sum -c review_bundle.sha256
  unzip -t STENOSIS-001_review_v02.zip
)
```

If the v02 output directory already exists, the script refuses to overwrite it. For any new run, choose a new explicit --out directory.

## Inputs and output custody

Inputs are the existing checksum-verified v01 full results, the pinned v2026-09-01 HPO ontology and the existing candidate source context output under results/phenotypes/par_candidates_v02. The candidate output's manifest and disease_context.tsv are checked against its SHA256SUMS and HPO release.

Full results on Isilon under results/phenotypes/structural_coverage_stenosis_reporting_v02:

- disease_onset_context.tsv preserves every selected original HPOA aspect-C disease onset source row with HPO ID, label, reference, evidence code, original row and disease ID.
- source_examples_v02.tsv preserves v01 example fields and adds original evidence code, phenotype-row onset column status, separately linked disease onset HPO identifiers/labels and source row IDs. It explicitly records patient_specific_onset_asserted=no.
- onset_summary.tsv reports eligible union disease count, disease onset context counts, congenital disease onset context counts, and phenotype row onset column completeness.
- coverage_summary.tsv and exception_decisions.tsv are copied byte-exact from v01.
- manifest.json, SHA256SUMS.txt and the minimal STENOSIS-001_review_v02.zip with review_SHA256SUMS.txt preserve auditability. The full disease onset context table is excluded from the review ZIP.

## Review and acceptance

GitHub Actions synthetic tests must pass and the real Isilon output must confirm original coverage is unchanged. Claude's earlier independent numerical verification remains valid for v01; v02 requires a bounded reviewer check of the new disease-level onset join and original IEA/TAS/PCS evidence fields. Scientific authority remains with the User. Keep PR #1 in draft until the reporting amendment is reviewed and the User chooses to merge.
