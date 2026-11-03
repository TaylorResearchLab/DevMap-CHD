# Primary evidence annotation queue for 662 DevMap-CHD genes

This step consumes the successful real HPO candidate extraction and produces three working TSVs without creating unsupported direct biological claims.

1. `publication_gene_queue.tsv` contains one row per gene and original PMID cited by HPOA. These are literature leads for the subsequent gene disruption → phenotype evidence assessment, not confirmations of direct evidence.
2. `genes_without_hpo_candidates.tsv` lists genes with no HPO derived candidate. They are prioritized for independent genetic and clinical source coverage.
3. `unresolved_publication_queue.tsv` lists genes with disease phenotype observations whose HPOA references contain no PMID.

All input files are SHA256 verified against `SHA256SUMS.txt`, and output files receive their own checksums. Every result is provisional and internal. Publication lineages are collapsed by gene and PMID so repeated HPO annotations do not inflate independent publication counts. Explicit phenotype absence stays in original candidate/evidence tables and is omitted from the positive publication assessment queue.

## HPC execution after git pull

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes

python3 -m unittest discover -s scripts/phenotypes/gene_pilot \
  -p 'test_prepare_primary_evidence_queue.py' -v

python3 scripts/phenotypes/gene_pilot/prepare_primary_evidence_queue.py \
  --source-dir results/phenotypes/par_candidates_v02 \
  --out results/phenotypes/primary_evidence_queue_v01

cat results/phenotypes/primary_evidence_queue_v01/evidence_queue_manifest.json
```

The next source integration step will retrieve and interpret original gene-disruption observations from identified literature and clinical curation resources. Only evidence with a directly documented gene disruption and phenotype may justify promotion of a candidate to a source supported PAR. Preserve original phenotype granularity and disease or cohort context.
