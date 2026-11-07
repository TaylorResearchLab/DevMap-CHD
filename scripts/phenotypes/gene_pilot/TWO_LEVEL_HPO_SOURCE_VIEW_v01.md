# DevMap-CHD | Two-level HPO source and discovery view v01

**Status:** Agent 1 implementation. Local synthetic tests passed. Real CHOP HPC output and Agent 2 code review pending. This is an additive, versioned, provisional view. No direct gene disruption–phenotype PAR is accepted or promoted.

## Scientific rationale

The November 7 independent Claude review reproduced the 27 legacy polarity collision groups, 55 IDs and 77 HPOA observations. It found that all absence-bearing collision groups originated from clinical cohort zero frequencies rather than HPOA `NOT` qualifiers. Most 0/N observations were single-person cohorts. Claude also independently identified a widespread legacy frequency parsing defect: HPO categorical frequencies HP:0040280–HP:0040284 were classified as unspecified, including all ORPHA candidates that should retain categorical-positive outcomes.

HPOA originally asserts **disease → phenotype**. The G2P gene–disease–phenotype traversal is a discovery projection, not a direct observed gene disruption claim. Accordingly, this v01 view separates original disease-subject claims from provisional gene-associated discovery projections and individual original evidence rows. It does not establish a final PAR Core identity rule.

## Data model

1. `original_disease_phenotype_claims.tsv` contains **source scope** HPOA disease-subject claim groups keyed by disease ID, predicate `has_phenotype`, HPO ID and curator negation. The `source_claim_id` is a versioned internal view identifier, not an accepted PAR ID.
2. `gene_disease_hpo_discovery_projections.tsv` contains provisional gene–disease–HPO projections that reference their original disease-subject claim. Every row is labeled `disease_mediated_discovery_only`. These `projection_id` values are not gene-subject direct assertions.
3. `original_hpoa_observations.tsv` retains every original HPOA source evidence link and its original evidence ID, source line locator, citation, evidence code, original disease subject, phenotype, frequency, qualifier, sex, onset, modifier and lineage key. It adds `evidence_outcome`, numerator, denominator, percent and categorical term without replacing original values.
4. `original_g2p_discovery_links.tsv` retains original G2P discovery rows, each linked to a source-scope claim and projection.
5. `legacy_candidate_projection_map.tsv` conserves every historical provisional candidate ID and records its new internal projection.
6. `namespace_summary.tsv`, `manifest.json` and `SHA256SUMS.txt` report the new representations and audit conservation, including OMIM and ORPHA.

**Source polarity** is `not_negated` when no `NOT` qualifier or excluded frequency term appears, `negated` for `NOT` and HP:0040285, and `unresolved` for unexpected qualifiers. `not_negated` does not imply that each study observed a positive phenotype. The observation can be `observed_zero`, `observed_positive`, `categorical_positive`, `frequency_unreported`, `categorical_excluded` or `unclassified_frequency`. In particular, `0/N` is `observed_zero` and keeps N. All five positive HPO categorical frequency terms are recognized as `categorical_positive`.

An original publication found in several source databases is still one original publication. Original evidence rows and lineage keys are preserved without increasing counts of independent clinical sources.

## Source and release controls

The exporter reads the **already completed** `par_candidates_v02` outputs and the successful `candidate_export_integrity_v01` audit. It verifies both input SHA256SUMS manifests, checks the source manifest relationship and enforces observation, candidate, G2P and projection conservation. It refuses to overwrite an existing output directory.

Existing `par_candidates_v02` data, the frozen 662 gene registry, the original HPO, GenCC, PubMind, and prior audit outputs remain unchanged. Private PubMind source files are not needed. This export never changes the old `polarity()` or reissues historical IDs.

## CHOP HPC execution

Run the synthetic tests and then derive only the new view from existing verified outputs:

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes
python -m unittest discover -s scripts/phenotypes/gene_pilot -p 'test_export_two_level_phenotype_v01.py' -v
python scripts/phenotypes/gene_pilot/export_two_level_phenotype_v01.py \
  --candidate-dir results/phenotypes/par_candidates_v02 \
  --integrity-dir results/phenotypes/candidate_export_integrity_v01 \
  --out results/phenotypes/hpo_two_level_projection_v01
```

Verify checksums and print the concise summary.

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
(cd results/phenotypes/hpo_two_level_projection_v01 && sha256sum -c SHA256SUMS.txt)
python - <<'PY'
import json
from pathlib import Path
p = Path("results/phenotypes/hpo_two_level_projection_v01/manifest.json")
x = json.loads(p.read_text())
for k in ("legacy_candidate_count", "provisional_projection_count",
          "legacy_identity_splits_collapsed", "original_evidence_link_count",
          "distinct_original_hpoa_source_rows", "original_discovery_link_count",
          "affirmed_negated_source_claim_key_conflicts",
          "unclassified_frequency_rows", "unresolved_claim_qualifier_rows",
          "direct_gene_phenotype_assertions_promoted"):
    print(k, x[k], sep="\t")
for ns in ("OMIM", "ORPHA"):
    if ns in x["by_namespace"]:
        print(ns, x["by_namespace"][ns])
PY
```

Expected from the already reproduced data: 62,860 original provisional candidate IDs, 62,832 provisional projections after collapsing 28 legacy polarity splits, and full conservation of all original evidence and discovery links. These numbers are **checks to validate**, not reports of a real run of the new exporter. The source evidence record count should match the old producer manifest, expected to be 63,012 linked records. Inspect any unexpected frequency value or curator qualifier rather than assigning a fabricated observation outcome.

## Review gates

- Agent 2 independently examines source identity, categorical frequencies, preserved clinical denominators and the conservation manifest. User decides PAR Core identity.
- The 2026-11-07 expert curated PMID policy remains in effect only at original source claim scope. PubMind machine extracted gene–HPO associations retain secondary review requirements.
- SV-001 LZTR1–ASD is supported with narrowing in Claude's newer primary text review. SV-002 Le Tourneau 2018 shows statistically shorter mitral chordae in FLNA variant-positive women; the original Newbury-Ecob 1993 neonatal scan remains pending Agent 2 inspection.
- No direct gene–phenotype PARs may be promoted from these discovery projections; the manifest explicitly records zero accepted direct assertions.

Log all subsequent findings in the DevMap Communications Log. Keep R01 and CHD Spatial records separate.
