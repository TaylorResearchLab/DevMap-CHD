# Consolidated 662-gene phenotype annotation view

This step converts the 70,672 GenCC–HPO join rows into distinct HPO phenotype candidates with all supporting GenCC submission versions linked. It preserves source identity without multiplying candidate PAR records. A versioned GenCC gene–disease assertion is genetic curation. A linked HPO disease–phenotype assertion is disease phenotype curation. Their combination remains an inferred gene disruption → phenotype candidate until direct evidence establishes the relationship.

## HPC commands

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes

python3 -m unittest discover -s scripts/phenotypes/gene_pilot \
  -p 'test_consolidate_gencc_hpo_phenotypes.py' -v

python3 scripts/phenotypes/gene_pilot/consolidate_gencc_hpo_phenotypes.py \
  --hpo-dir results/phenotypes/par_candidates_v02 \
  --gencc-dir results/phenotypes/gencc_integration_v01 \
  --out results/phenotypes/consolidated_v01

cat results/phenotypes/consolidated_v01/consolidation_manifest.json
```

## Outputs

* `consolidated_phenotype_candidates.tsv`: one row per existing HPO candidate. Shows source GenCC submission count, classifications, inheritance and all submission versions. The candidate ID and asserted absence state remain unchanged.
* `gencc_source_links.tsv`: one row for each GenCC submission supporting an existing candidate through an identical disease CURIE. Retains issuer and original submission/version. This table can contain multiple rows per candidate.
* `combined_gene_coverage.tsv`: one row per frozen gene with HPO and GenCC coverage and one of four source categories.
* `genes_needing_source_discovery.tsv`: genes in neither HPO nor GenCC.
* `direct_phenotype_evidence_template.tsv`: header-only import contract for future independently verified gene disruption → phenotype observations. A source-specific disruption mechanism and original biological subject will be required. The template contains no invented or automatically promoted observations.
* `consolidation_manifest.json` and `SHA256SUMS.txt`: unique candidate counts and integrity checks.

Both input datasets are required to pass their recorded SHA256 manifest checks. The source files already reside on HPC. No external HTTPS download is required.

## Scientific interpretation

The prior 70,672 GenCC–HPO links are expected to reduce to fewer distinct candidate IDs because a single candidate may be linked to several independent GenCC submissions. The consolidation reports exactly how many *distinct* candidates have matched GenCC source support.

The direct-evidence template is intentionally empty. Neither GenCC gene–disease classification nor an inherited HPO gene–phenotype index establishes a direct disruption → phenotype molecular relationship by itself. Direct primary publication or mechanistically specific curated evidence can be added with its own provenance.

The candidate namespace remains internal. No canonical PAR GUIDs or public release are created by this step.
