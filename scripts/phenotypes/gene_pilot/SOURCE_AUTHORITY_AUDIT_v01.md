# Source authority audit v01

Implements the user-approved DevMap source validation allocation policy of 2026-11-07. Expert-curated original claims with traceable PMIDs may be imported at original subject/predicate/object scope. PubMind is automated extraction and requires secondary review.

This report is an **audit**. It does not convert disease-mediated HPO annotation or GenCC gene–disease validity into directly verified gene disruption–phenotype assertions. Original source rows remain unchanged.

## HPC command

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD

git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes

python3 -m unittest discover \
  -s scripts/phenotypes/gene_pilot \
  -p 'test_audit_source_authority_v01.py' -v

python3 scripts/phenotypes/gene_pilot/audit_source_authority_v01.py \
  --hpo-evidence results/phenotypes/par_candidates_v02/par_evidence.tsv \
  --gencc-evidence results/phenotypes/gencc_integration_v01/gencc_gene_disease_evidence.tsv \
  --pubmind-hpo results/phenotypes/pubmind_v2_integration_v01/pubmind_hpo_to_devmap.tsv \
  --out results/phenotypes/source_authority_v01

cat results/phenotypes/source_authority_v01/source_authority_manifest.json
```

Expected source row totals from preceding frozen runs: 63,012 HPOA disease–phenotype evidence rows, 4,090 GenCC gene–disease submissions, 1,522 PubMind AI-extracted Gene–HPO pairs. Each table is written with original IDs, the source's curation/provenance class and DevMap disposition.

## Limitations to resolve through primary source metadata

- HPOA `primary_publication_id` records are extracted from `PMID:` references. Other identifiers and missing references remain in the original source reference field; they are classified as requiring provenance review here.
- `gencc_gene_disease_evidence.tsv` does not contain citation-level PMIDs. All GenCC records are marked for provenance review until full original submission citations can be linked. ClinGen submitter status is retained but is not equivalent to PMID verification.
- PubMind summary rows contain association publication counts, but no phenotype-specific PMID/PVID link. Every PubMind row stays `pending_secondary_review` until the full original Aditya export is validated and source reviews are completed.
- Any new direct gene disruption–phenotype inference remains subject to independent SCUTER review and user decision, regardless of source import authority.

Inputs and output files are separately checksummed. No private PubMind source tables are added to GitHub.
