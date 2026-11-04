# Aditya Lahiri PubMind v2 integration for DevMap-CHD

Reuses the three PubMind v2 tables attached to the Notion page *Heart Defect Published Reference Work*: `CHD_gene_HPO_associations_ranked_v2.tsv`, `CHD_gene_MONDO_associations_ranked_v2.tsv`, `CHD_gene_publication_associations_ranked_v2.tsv`.

The Notion page documents 662 canonical genes, 1,522 unique Gene-HPO associations, 347 annotated genes and 844 HPO terms. Source provenance is PubMind SNV for HPO and SNV/CNV/SV/gene fusion for gene, disease and publication tables. Versioned source files must be retained on HPC; do not commit imported PubMind tables to the public repository. Use Aditya's local v2 source directory or download the three Notion attachments into a shared HPC project directory.

## Verify where the three files are available

From any working directory:

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD

PUBMIND_V2=/path/to/Aditya/PubMind_v2

ls -lh "$PUBMIND_V2"/CHD_gene_{HPO,MONDO,publication}_associations_ranked_v2.tsv
```

Replace `PUBMIND_V2` with the actual HPC directory that contains the three already prepared files. The Notion page contains those attachments, but the GitHub repository holds code only and does not have access to authenticated Notion attachments.

## Run

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes

python3 -m unittest discover -s scripts/phenotypes/gene_pilot \
  -p 'test_integrate_pubmind_v2.py' -v

PUBMIND_V2=/path/to/Aditya/PubMind_v2

python3 scripts/phenotypes/gene_pilot/integrate_pubmind_v2.py \
  --registry data/releases/2026.09.08/genes.tsv \
  --pubmind-hpo "$PUBMIND_V2/CHD_gene_HPO_associations_ranked_v2.tsv" \
  --pubmind-mondo "$PUBMIND_V2/CHD_gene_MONDO_associations_ranked_v2.tsv" \
  --pubmind-publications "$PUBMIND_V2/CHD_gene_publication_associations_ranked_v2.tsv" \
  --hpo-dir results/phenotypes/par_candidates_v02 \
  --gencc-dir results/phenotypes/gencc_integration_v01 \
  --out results/phenotypes/pubmind_v2_integration_v01

cat results/phenotypes/pubmind_v2_integration_v01/pubmind_v2_integration_manifest.json
```

## Outputs

* `pubmind_hpo_to_devmap.tsv`: one record per PubMind Gene-HPO association with the number of unique PubMind supporting publications and linked HPO candidate IDs. Reports separate matches to HPO reported presence, explicit absence and unspecified candidates. The 1,522 input pairs are not inflated by the number of matching disease-context HPO candidates.
* `pubmind_mondo_publication_sources.tsv`: source-native PubMind Gene-MONDO and Gene-Publication pairs with their original row positions, pathogenicity score aggregates and provenance. A Gene-Publication pair is NOT automatically evidence for an individual Gene-HPO pair.
* `pubmind_gene_coverage_662.tsv`: a row for each of the frozen 662 HGNC genes. Reports PubMind HPO, MONDO, publication, HPO candidate and GenCC availability.
* `pubmind_v2_integration_manifest.json`, `SHA256SUMS.txt`: source hashes, input validation and coverage statistics.

Every input PubMind table SHA256 is recorded. Existing HPO and GenCC source checksums are verified. The documented v2 HPO counts (1,522 pairs, 347 genes, 844 terms) are checked; a mismatch stops production rather than silently switching releases.

## Interpretation and next biological step

PubMind v2's Gene-HPO publication count is a valuable independently produced evidence index. The summary row does not itself carry the PVID or PMID for a specific HPO observation. The original PubMind positional mapping must supply those source records before treating a candidate as a direct variant/disruption–phenotype PAR. The PubMind gene-publication table cannot substitute for phenotype-specific lineage because one gene may have several different variants, diseases, phenotypes and cited studies.

The joined outputs are internal source annotations, not new accepted biological PARs. Use the PubMind PVID evidence for phenotype-specific source verification, avoiding double counting with HPO/GenCC material inherited from the same original publication. PubMind pathogenicity scores are evidence screening metadata rather than experimental conclusions.

No full PubMind archive or raw patient data is copied or published.
