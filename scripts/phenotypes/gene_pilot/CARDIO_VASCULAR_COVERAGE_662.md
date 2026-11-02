# HPO cardiac and vascular morphology coverage audit for 662 DevMap-CHD genes

This script measures coverage **in HPO's derived gene–disease–phenotype discovery index**. It does not establish primary gene–phenotype associations. The HPO annotations and citations remain credited to HPO and upstream publishers.

## Pinned sources

- DevMap-CHD registry `data/releases/2026.09.08/genes.tsv` with 662 unique HGNC IDs.
- HPO `genes_to_phenotype.txt` from `v2026-09-01`, SHA-256 `507a17bff9c49e6329fbd88b1f91734fa7e9fdea5c06304044c0892eb6ab248c`.
- HPO `phenotype.hpoa` from `v2026-09-01`, SHA-256 `e89aa39c8f97bf5a52c5d160f9250a603681d630ade8ec2679d84ac5aece1f72`.
- HPO `hp.obo` from `v2026-09-01`, SHA-256 `93dace952fcb3ec4728818857f6ba76bc2d5312f4d83266519b8694b8e798f22`, obtained from the official GitHub release API asset digest.

## HPC commands

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes

PILOT=scripts/phenotypes/gene_pilot
curl -fL --retry 3 \
  -o "$PILOT/inputs/hp.obo" \
  https://github.com/obophenotype/human-phenotype-ontology/releases/download/v2026-09-01/hp.obo
printf '%s  %s\n' \
  93dace952fcb3ec4728818857f6ba76bc2d5312f4d83266519b8694b8e798f22 \
  "$PILOT/inputs/hp.obo" | sha256sum -c

python -m unittest discover -s tests/phenotypes -p test_cardio_vascular_662.py -v
python "$PILOT/audit_662_cardio_vascular.py"
cat "$PILOT/results/cardio_vascular_662/cardio_vascular_662_manifest.json"
```

If an HGNC complete-set TSV with `hgnc_id` and `entrez_id` is available, pass `--hgnc-complete-set /actual/file.tsv` and compare to the exact-symbol result. This is important because 143 of 662 genes did not match HPO's September 2026 summary by approved symbol alone.

## Coverage categories

All classes include the HPO root and every descendant through OBO `is_a` relationships. Only original `phenotype.hpoa` rows with `aspect=P` count, and a disease/HPO term must match a HPO gene-summary discovery key.

| Category | HPO root | Interpretation |
| --- | --- | --- |
| Broad cardiovascular | HP:0001626 | Includes structural and physiological or test abnormalities |
| Heart morphology | HP:0001627 | Structural heart changes and congenital defect related terms, but may contain acquired terms |
| Vascular morphology | HP:0025015 | Blood vessels and additional vascular morphology |
| Blood vessel morphology | HP:0033353 | Blood vessel subset |
| Great vessel morphology | HP:0030962 | Aorta and pulmonary/systemic great vessel subset |

The manifest also reports a disjoint gene count partition into `heart_only_positive_genes`, `vascular_only_positive_genes`, and `heart_and_vascular_positive_genes`; their sum equals the union count.

The roots are deliberately **not mutually exclusive**. Great vessel morphology is part of vascular morphology; a term may also fall under other roots. The merged heart-or-vascular total is computed using a gene-level logical union, not by adding root counts.

`positive` means a native `aspect=P` source annotation that is **not explicitly negative** under HPO's source encoding. `negative_only` means the disease/HPO key has only explicit 0/N, 0%, `HP:0040285` or `NOT` source annotations. `mixed` means both states were present and remain separately identified. These categories report the curated annotation state, not an independent validation of the cited human observations.

Cardiovascular morphology **is not interchangeable with congenital disease**, and HPO disease annotation **does not establish the gene caused the observation**. Pediatric onset, birth defect specificity, genotype dependence, and direct primary study support remain to be assessed. Use the lists to choose publications for primary-source review and compare with HPO as baseline, not to mint direct gene–phenotype PARs.

## Artifacts

- `gene_cardio_vascular_662.tsv`: all 662 genes, each category with positive/negative-only/mixed disease–phenotype key counts, match method and status.
- `cardio_vascular_disease_hpo_links.tsv`: original disease/HPO terms with categories and evidence states for transparent inspection. No author-created direct gene–phenotype claim.
- `genes_without_structural_heart_or_vascular_hpo.tsv`: includes the 143 general-HPO unmatched genes **plus** genes with general HPO annotations but no positive structural morphology link.
- `genes_with_general_hpo_but_no_structural_cardiovascular_hpo.tsv`: more informative gap candidates among the 519 general HPO matching genes.
- `cardio_vascular_662_manifest.json` and `SHA256SUMS.txt`: immutable source digests, exact matching scope, counts and interpretation.

## Follow-up use of PubMed and PMC

Use original PMID leads and selected HPO clinical citation records to examine primary evidence for each candidate gene. PubMed E-utilities provides citations and abstracts. For systematic full text, PMC makes content available through the PMC Cloud, OAI-PMH and BioC services according to per-article reuse rights. Preserve PMID/PMCID, paper section or table/figure locator, cohort and genotype definitions, source licenses and evidence independence.

Useful official APIs: https://www.ncbi.nlm.nih.gov/home/develop/api/ and https://pmc.ncbi.nlm.nih.gov/tools/developers .