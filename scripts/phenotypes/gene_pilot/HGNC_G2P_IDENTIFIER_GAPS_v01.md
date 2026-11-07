# DevMap-CHD | HGNC to HPO identifier gap diagnostic v01

Status: Agent 1 code and synthetic tests committed. CHOP HPC execution and independent Agent 2 review pending.

## Verified inputs and starting observation

The initial 662-gene coverage analysis matched 519 by approved gene symbol and left 143 unmatched. A later archived HGNC/NCBI Gene ID crosswalk matched 519 and left the same 143, with zero newly recovered genes.

Archived HGNC September 4, 2026 SHA256: `6f43d6ff43aa9fdfa5fb2f20a20a7cace66e6e02e2a0dcf19d9b726e2e248d20`.

The original coverage script reports a prioritized match method and selects NCBI before symbol. Its reported zero SYMBOL_EXACT after the crosswalk does not measure exact symbol agreement independently.

## Scientific diagnostic

The new read-only script independently measures exact approved symbol matching and NCBI Gene ID matching for each of the 662 frozen genes. It also checks the archived HGNC approved symbol, status, Entrez ID, previous symbols and alias symbols. It classifies the 143 unresolved records by HGNC identifier availability and possible source symbol leads.

An HGNC historical alias appearing in the HPO G2P file is only a review lead. Original HPO NCBI IDs and other HGNC owners of the same symbol are retained for review. No gene reassignment, source annotation mutation, source scope expansion or direct gene-phenotype PAR promotion takes place.

Outputs include `gene_identifier_diagnostic_662.tsv`, `unresolved_143_identifier_diagnostic.tsv`, `historical_alias_source_leads.tsv`, `manifest.json` and `SHA256SUMS.txt`. All source checksum gates and the previous 519/143 source matching partition must match.

## CHOP HPC run

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes
python -m unittest discover -s scripts/phenotypes/gene_pilot -p 'test_audit_hgnc_g2p_identifier_gaps_v01.py' -v
python scripts/phenotypes/gene_pilot/audit_hgnc_g2p_identifier_gaps_v01.py \
  --registry data/releases/2026.09.08/genes.tsv \
  --g2p scripts/phenotypes/gene_pilot/inputs/genes_to_phenotype.txt \
  --hpoa scripts/phenotypes/gene_pilot/inputs/phenotype.hpoa \
  --hgnc scripts/phenotypes/gene_pilot/inputs/hgnc_complete_set_2026-09-04.txt \
  --coverage-dir results/phenotypes/hpo_coverage_hgnc_2026_09_04 \
  --out results/phenotypes/hpo_hgnc_identifier_gap_diagnostic_v01
(cd results/phenotypes/hpo_hgnc_identifier_gap_diagnostic_v01 && sha256sum -c SHA256SUMS.txt)
cat results/phenotypes/hpo_hgnc_identifier_gap_diagnostic_v01/manifest.json
```

## Review boundary

The frozen 662-gene registry and approved source/discovery identity scheme remain unchanged. The 143-gene unmatched set is a source matching result, not a biological null. Review any proposed alias reassignments independently by stable HGNC and NCBI Gene IDs. Submit the HGNC cause distribution and ambiguous alias leads to Claude. The original HPOA subject remains the disease and all derived gene associations remain discovery-only.

Sources: HPO v2026-09-01 pinned G2P/HPOA; HGNC archival complete set 2026-09-04; DevMap registry 2026.09.08. See the DevMap Communications Log November 7 crosswalk entry.

## Verified CHOP HPC results, 7 November 2026

The read-only diagnostic completed and all four output SHA-256 checks passed. The frozen registry comprises 662 genes. Exactly **519** match the pinned HPO gene summary by approved gene symbol and **519** match by NCBI Gene ID; they are **the same 519 genes**. The other **143** match by neither method. All 143 have HGNC Entrez IDs in the 2026-09-04 archive. The diagnostic scanned 333,983 G2P rows and 45,045 HGNC entries.

Of the 143 unresolved genes, **142** have no archived HGNC previous-symbol or alias-symbol match in the HPO gene summary. **One** unresolved gene has **14** candidate alias source symbols; every one of these also has another HGNC owner. Thus, the alias results are ambiguous source leads rather than recovered gene identities. No automatic remapping, gene reassignment or direct phenotype PAR promotion occurred. The 519/143 source coverage partition is stable, but does not measure whether these genes have biological phenotype associations outside the pinned HPO discovery index.

The diagnostic manifest reports `both_exact_symbol_and_ncbi_matched_genes=519`, `unmatched_without_HGNC_entrez=0`, `unmatched_with_alias_hpo_source_leads=1`, `unmatched_without_alias_hpo_source_leads=142`, `alias_source_leads_total=14` and `alias_leads_with_other_HGNC_owners=14`. The original coverage manifest digest is `356832cecec7b95657b377f5970c12ed9fa4b2f9b5f6a655780fc0e8d235e7`. The original pinned HGNC SHA-256 is `6f43d6ff43aa9fdfa5fb2f20a20a7cace66e6e02e2a0dcf19d9b726e2e248d20`.

**Next source check:** inspect `results/phenotypes/hpo_hgnc_identifier_gap_diagnostic_v01/historical_alias_source_leads.tsv` in full. For any candidate identity equivalence, independently establish the original HPO NCBI Gene ID and HGNC ownership before considering reassignment. Claude's independent review remains open. The user did not paste synthetic test stdout, so this note confirms real manifest and checksum evidence only.
