# Reproduce PubMind CHD association tables from existing OWLNETS data

PubMind has already been ingested into DDKG at the internal CHOP HPC path:

`/mnt/isilon/opentargets/U24KG/data/owlnets_nodes_and_edges/pubmind/`

The goal is to reconstruct three PubMind v2 association tables for the frozen 662 DevMap-CHD HGNC genes:

- Gene to MONDO associations, with original PubMind PVID and supporting publications
- Gene to publication associations, with PVID and source pathogenicity statistics
- Gene to HPO phenotype associations, retaining variant-specific PVID, publication and original evidence where available

The first step is a read-only schema inventory because file names, native graph predicates, identifier layouts and source columns have not yet been verified. Do not implement arbitrary graph traversals or infer causality from co-occurrence. Keep each gene → PVID → HPO/MONDO/publication path and original biological context. The ranked summary tables should be derived views, not substitutes for the underlying evidence.

## Run on CHOP HPC

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes

python3 -m unittest discover -s scripts/phenotypes/gene_pilot \
  -p 'test_inspect_pubmind_raw_tables.py' -v

python3 scripts/phenotypes/gene_pilot/inspect_pubmind_raw_tables.py \
  --root /mnt/isilon/opentargets/U24KG/data/owlnets_nodes_and_edges/pubmind \
  --registry data/releases/2026.09.08/genes.tsv \
  --out results/phenotypes/pubmind_raw_inventory_v01
```

The script prints a compact summary of files with potential HPO, MONDO, variant and publication fields. Detailed file paths, headers, formats and probable node/edge table roles are saved to `results/phenotypes/pubmind_raw_inventory_v01/pubmind_source_inventory.json`. It does not modify source data, export raw evidence or publish underlying data.

For the first review, share the compact command output and the inventory JSON if needed. After verifying source schemas, implement a deterministic all-662 extraction and compare its HPO and original publication associations with the previously generated 62,860 HPO candidates and 4,090 GenCC gene-disease assertions.

## Distinctions for evidence interpretation

A PubMind gene–HPO association reached through PVID may provide much more specificity than an HPO disease-mediated gene summary. The original source PMID, source statement and variant identity must still support the exact gene-disruption-to-phenotype claim before biological PAR acceptance. Separate clinical variants from GWAS associations and functional observations. Preserve the original PubMind source release and DDKG transformation. PubMind pathogenicity scores are prioritization information, not direct clinical validation.

Aditya's Notion page describes v1 data for 652 genes and planned v2 for 662 genes. This direct raw extraction should use the frozen 662-gene release and complement, not overwrite, Aditya's existing curated source work.
