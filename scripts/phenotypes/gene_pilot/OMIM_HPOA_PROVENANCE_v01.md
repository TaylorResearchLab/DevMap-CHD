# OMIM-linked HPOA provenance audit v01

This audit reads the already verified `results/phenotypes/source_authority_v02/hpoa_source_authority.tsv`. It extracts the exact OMIM source identifiers carried by HPOA records. It does **not** assume an OMIM bibliography citation supports every HPO phenotype attached to the OMIM entry. It does not reclassify expert curation or mint direct gene–phenotype PARs.

## HPC execution

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD

git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes

python3 -m unittest discover \
  -s scripts/phenotypes/gene_pilot \
  -p 'test_audit_omim_hpoa_provenance_v01.py' -v

python3 scripts/phenotypes/gene_pilot/audit_omim_hpoa_provenance_v01.py \
  --hpoa-authority results/phenotypes/source_authority_v02/hpoa_source_authority.tsv \
  --out results/phenotypes/omim_hpoa_provenance_v01

cat results/phenotypes/omim_hpoa_provenance_v01/omim_provenance_manifest.json
```

## Files

- `omim_hpoa_source_evidence.tsv`: every original HPOA evidence row with an OMIM reference, preserving original disease subject, HPO term, original evidence code, HPOA PMID if present, source record locator, and a separate blank bibliography PMID mapping field.
- `omim_bibliography_retrieval_queue.tsv`: distinct OMIM IDs to consult once through an approved OMIM resource, with counts and all linked disease context IDs. Do not treat a bibliography link as phenotype-specific merely because it occurs within an OMIM entry.
- `omim_disease_phenotype_claims.tsv`: deduplicated (OMIM reference, original disease subject, HPO ID) keys, retaining counts and original source locators. Review is at the original disease–phenotype claim scope.
- `omim_provenance_manifest.json` and `SHA256SUMS.txt`: input file digest and quantitative audit summary.

An OMIM entry may support multiple disease–phenotype statements, and a single HPOA row may cite more than one OMIM ID. The script retains these multiplicities explicitly.

## Publication mapping acceptance

1. Recover the original OMIM entry and its cited literature using the institutionally licensed OMIM interface or an authorized local resource.
2. Attach each PMID only when an OMIM text passage, phenotype table or original publication supports the exact disease–phenotype association.
3. Preserve OMIM entry ID, source release, citation locator, PMID, and match confidence. A bibliography-only PMID is merely an unassigned lead.
4. Keep electronically inferred HPOA annotations marked `IEA`, even with a source reference.
5. Maintain independent PubMind secondary-review queue and the SCUTER user approval process for novel direct gene-disruption assertions.

The audit does not download, redistribute or publish OMIM text. The same applies to private PubMind source files.
