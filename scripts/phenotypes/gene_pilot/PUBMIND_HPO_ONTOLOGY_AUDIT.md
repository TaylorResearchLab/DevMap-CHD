# PubMind v2 HPO ontology audit

Reads the frozen PubMind v2 Gene–HPO integration and the pinned September 2026 `hp.obo` file. Produces ontology annotations for the 844 distinct HPO identifiers and all 1,522 Gene–HPO pairs. Tracks the 947 pairs new relative to the HPO disease-mediated discovery index.

The audit uses transitive `is_a` paths from the pinned ontology, not label keywords. Cardiovascular root `HP:0001626`, cardiovascular morphology `HP:0030680`, heart morphology `HP:0001627`, and cardiovascular physiology `HP:0011025`. These flags are nonexclusive ancestry indicators. Structural cardiac abnormality is not synonymous with congenital onset. Generic severity terms are flagged conservatively by exact source label. Alternate IDs are resolved for classification while the input ID is preserved. Obsolete terms are reported with `replaced_by` and `consider`, without automatic remapping.

## HPC execution

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD

git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes

python3 -m unittest discover \
  -s scripts/phenotypes/gene_pilot \
  -p 'test_audit_pubmind_hpo_ontology_v01.py' -v

python3 scripts/phenotypes/gene_pilot/audit_pubmind_hpo_ontology_v01.py \
  --pubmind-hpo results/phenotypes/pubmind_v2_integration_v01/pubmind_hpo_to_devmap.tsv \
  --obo scripts/phenotypes/gene_pilot/inputs/hp.obo \
  --out results/phenotypes/pubmind_hpo_ontology_v01

cat results/phenotypes/pubmind_hpo_ontology_v01/pubmind_hpo_ontology_manifest.json
```

## Inspect novel cardiovascular Gene–HPO annotations

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD

python3 - <<'PY'
import csv
from pathlib import Path
p=Path("results/phenotypes/pubmind_hpo_ontology_v01/pubmind_gene_hpo_cardiovascular_annotations.tsv")
with p.open(newline="") as f:
    rows=list(csv.DictReader(f,delimiter="\\t"))
selected=[r for r in rows if r["integration_status"]=="new_pubmind_gene_hpo" and r["cardiovascular"]=="1"]
print("Gene\\tHPO\\tPhenotype\\tHeart morphology\\tCardiovascular physiology\\tPubMind publications")
for r in sorted(selected,key=lambda r:(r["gene_symbol"],r["hpo_id"])):
    print(r["gene_symbol"],r["hpo_id"],r["hpo_name"],r["heart_morphology"],
          r["cardiovascular_physiology"],r["pubmind_publication_count"],sep="\\t")
print(f"Novel cardiovascular Gene-HPO pairs: {len(selected)}")
PY
```

Outputs are `pubmind_hpo_terms_ontology_audit.tsv`, `pubmind_gene_hpo_cardiovascular_annotations.tsv`, `pubmind_hpo_ontology_manifest.json` and `SHA256SUMS.txt`. The original PubMind tables remain private. This analysis uses the previously derived PubMind summary data and produces provisional phenotype classifications rather than accepted PARs.
