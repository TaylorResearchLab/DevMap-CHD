# DevMap-CHD | Two-level HPO source and discovery view v01

**Status:** Scientific authority approved this versioned source/discovery identity representation on 2026-11-07. Real CHOP HPC and independent Agent 2 code reviews passed. Direct gene disruption–phenotype PAR promotion and public release remain separately gated. This is an additive, versioned, provisional view. No direct gene disruption–phenotype PAR is accepted or promoted.

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
          "not_negated_negated_source_claim_key_conflicts",
          "unclassified_frequency_rows", "unresolved_claim_qualifier_rows",
          "direct_gene_phenotype_assertions_promoted"):
    print(k, x[k], sep="\t")
for ns in ("OMIM", "ORPHA"):
    if ns in x["by_namespace"]:
        print(ns, x["by_namespace"][ns])
PY
```

The November 7 real HPC run verified 62,860 legacy candidate IDs, 62,832 provisional projections, 28 reconciled legacy identity splits, 63,012 linked original HPOA evidence records and 62,860 discovery links. All seven output checksums passed. The verified manifest reports 45,712 distinct original HPOA source rows and 45,548 distinct original disease–phenotype source claims. Frequency classification has zero unclassified rows, zero unresolved qualifiers and zero positive-versus-negated source claim key conflicts.

## Review gates

- Agent 2 independently examines source identity, categorical frequencies, preserved clinical denominators and the conservation manifest. User decides PAR Core identity.
- The 2026-11-07 expert curated PMID policy remains in effect only at original source claim scope. PubMind machine extracted gene–HPO associations retain secondary review requirements.
- SV-001 LZTR1–ASD is supported with narrowing in Claude's newer primary text review. SV-002 Le Tourneau 2018 shows statistically shorter mitral chordae in FLNA variant-positive women; Claude subsequently inspected the user-attached Newbury-Ecob 1993 scan, confirming a single neonatal necropsy observation of short and irregular chordae referring to both mitral and tricuspid valves. His review supports both original OMIM:314400 disease–phenotype HPOA assertions at that anatomical scope. See [Claude SV-002 1993 source review](https://app.notion.com/41129187800881349dcac526efbb82d8). User biological disposition remains pending.
- No direct gene–phenotype PARs may be promoted from these discovery projections; the manifest explicitly records zero accepted direct assertions.

Log all subsequent findings in the DevMap Communications Log. Keep R01 and CHD Spatial records separate.


## Real HPC result and reporting correction, November 7, 2026

Four synthetic tests passed. The versioned exporter completed on CHOP HPC. `sha256sum -c SHA256SUMS.txt` returned OK for all seven output files. The manifest reports:
- 62,860 legacy candidate IDs and 62,832 provisional discovery projections, with 28 legacy polarity splits reconciled.
- 63,012 original HPOA evidence links, representing 45,712 distinct original HPOA source lines. The difference reflects gene projection multiplicity, not additional independent clinical evidence.
- 45,548 distinct disease–phenotype source claim groups and 62,860 preserved G2P discovery links.
- 35,919 categorical-positive, 16,229 observed-positive, 422 observed-zero and 10,442 frequency-unreported evidence links. Their sum equals 63,012.
- 0 unclassified frequency rows, 0 unresolved claim qualifiers and 0 curator polarity key conflicts.
- OMIM 27,862 old IDs → 27,834 projections; ORPHA 34,998 old IDs → 34,998 projections.
- ORPHA 34,955 `not_negated` and 43 `negated` projections; OMIM 27,834 `not_negated` and zero `negated` projections.
- 0 accepted direct gene–phenotype PARs.

The original documentation's diagnostic referenced the old field `affirmed_negated_source_claim_key_conflicts`. The exporter correctly emits **`not_negated_negated_source_claim_key_conflicts`** after the source-state label changed from `affirmed` to `not_negated`. The field mismatch caused a KeyError in the postrun summary script after successful export and checksum verification. The corrected diagnostic follows.

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
python - <<'PY'
import json
from pathlib import Path
m=json.loads(Path("results/phenotypes/hpo_two_level_projection_v01/manifest.json").read_text())
for key in ("legacy_candidate_count", "provisional_projection_count",
            "legacy_identity_splits_collapsed", "original_evidence_link_count",
            "distinct_original_hpoa_source_rows", "original_discovery_link_count",
            "not_negated_negated_source_claim_key_conflicts",
            "unclassified_frequency_rows", "unresolved_claim_qualifier_rows",
            "direct_gene_phenotype_assertions_promoted"):
    print(f"{key}\t{m[key]}")
for ns in ("OMIM", "ORPHA"):
    print(ns, m["by_namespace"].get(ns))
PY
```

No exporter rerun is required. User and Agent 2 will review the verified source identities and the pending SV-001/SV-002 scientific dispositions. The existing historical outputs and frozen registry remain untouched.


## Scientific authority decision, 2026-11-07 (supersedes earlier identity-pending notes)

**Decision 1: APPROVED for internal DevMap original source assertions and discovery projections.** See the [user's DevMap Communications Log decision](https://app.notion.com/p/4112918780088115808ccc2a3dd5ea55).

- `dmpdsrc1` uses the pinned `hpoa_disease_subject_two_level_v01` profile to identify a source claim from (original disease identifier, `has_phenotype`, original HPO identifier, curator claim negation).
- `dmpview1` is the versioned gene-keyed `disease_mediated_discovery_only` projection referencing its `dmpdsrc1`. Gene keys on these projections are not observed direct biological claim subjects.
- Original HPOA source observations retain raw frequency, numerator/denominator, categorical term, onset, sex, qualifier, curator evidence code, publication reference, source line and lineage. `0/N` describes zero observations in a particular cohort, not curator negation. `not_negated` does not mean that every evidence row observed the phenotype.
- The accepted internal source/discovery identity vocabulary applies to the verified `hpoa_disease_subject_two_level_v01` profile. Changes to its identity semantics require a new versioned profile and appropriate scientific review. This approval does not automatically adopt identities for direct gene disruption or variant–phenotype PARs.

**Existing data custody:** The 662-gene registry, 62,860 historical candidate IDs and completed HPOA evidence and checksum manifests remain unchanged. The audited two-level view preserves 45,548 source claims, 62,832 discovery projections, 63,012 evidence links, and 62,860 legacy mapping rows. The user approved no direct gene disruption–phenotype PAR promotion and no public release.

**Other source dispositions:** [SV-001, narrowed patient observation](https://app.notion.com/p/41129187800881eeab02f31b9a936cc5); [SV-002a, accepted mitral disease–phenotype claim](https://app.notion.com/p/411291878008812794e3df5681283eaa); [SV-002b, accepted tricuspid disease–phenotype claim](https://app.notion.com/p/411291878008817cb890d2e89f4301a3). These decisions retain distinct primary evidence and are not permissions to relabel disease discovery projections as direct gene phenotype assertions.

Historical sections above describe the state before this user approval. The separate edge-case audit, GenCC and HGNC work remain subject to their own review.
