# Provisional gene disruption to phenotype PAR candidate export

The exporter starts from the frozen DevMap-CHD 662-gene registry and the pinned HPO v2026-09-01 disease-mediated gene-to-phenotype discovery index and disease-to-phenotype HPOA annotations.

It produces *candidate* gene disruption → phenotype relationships. A disease mediated G2P linkage does not constitute direct molecular evidence that disrupting a particular gene causes the phenotype. The disruption mechanism stays `unspecified_disruption` until a supporting primary source establishes it.

## Inputs

* `data/releases/2026.09.08/genes.tsv` from the DevMap-CHD repository
* HPO `genes_to_phenotype.txt`, SHA256 `507a17bff9c49e6329fbd88b1f91734fa7e9fdea5c06304044c0892eb6ab248c`
* HPO `phenotype.hpoa`, SHA256 `e89aa39c8f97bf5a52c5d160f9250a603681d630ade8ec2679d84ac5aece1f72`

The source files should be from the same HPO v2026-09-01 release. Production execution verifies both source checksums. The `--skip-sha` flag exists only for synthetic tests.

## Run from repository root after git pull

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes

python3 -m unittest discover -s scripts/phenotypes/gene_pilot -p 'test_export_gene_phenotype_par.py' -v

python3 scripts/phenotypes/gene_pilot/export_gene_phenotype_par.py \
  --registry data/releases/2026.09.08/genes.tsv \
  --g2p scripts/phenotypes/gene_pilot/inputs/genes_to_phenotype.txt \
  --hpoa scripts/phenotypes/gene_pilot/inputs/phenotype.hpoa \
  --out results/phenotypes/par_candidates_v02
```

Adjust the two HPO input paths to their existing local locations if needed. Do not transfer generated data or unlicensed source snapshots into the public repository.

## Output

* `par_candidates.tsv` contains one candidate per gene, unspecified disruption, phenotype, disease, and asserted presence/absence/unspecified state.
* `par_evidence.tsv` contains original HPOA disease-to-phenotype source rows, reference strings and publication lineage keys.
* `source_discovery_links.tsv` preserves each HPO gene-to-phenotype discovery index row, explicitly typed as a discovery link.
* `disease_context.tsv` retains source C (onset), I (inheritance), M and H disease annotation rows.
* `gene_coverage.tsv` has a row for each of the 662 frozen genes. A zero candidate count means no matching source association, rather than biological absence.
* `manifest.json` and `SHA256SUMS.txt` record the source checksums and result summaries.

## Evidence semantics

Presence versus explicit absence changes the candidate identity. Frequency magnitudes remain on evidence rows. HPOA source rows retain their native disease subject rather than being relabeled as direct gene observations. G2P discovery links are recorded separately and are not counted as independent evidence. Original PMID references support lineage tracing. A PMID inherited through multiple databases is not automatically counted multiple times as independent experimental confirmation. Additional direct clinical/functional evidence may support promotion to a gene disruption → phenotype PAR after review.

The candidate ID namespace `dmpcand:` is internal and provisional. It is not the canonical PAR GUID namespace. Neither the candidate records nor their source rights have been approved for public release.

## Current status

Exporter and synthetic test committed to `feature/gene-phenotypes`. Real HPC execution and independent SCUTER Agent 2 source audit remain to be completed.
