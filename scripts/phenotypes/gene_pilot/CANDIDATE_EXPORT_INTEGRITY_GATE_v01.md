# DevMap-CHD candidate source conservation and PAR identity audit v01

Status: **Agent 1 implementation for independent SCUTER review. Not yet run on CHOP HPC.** The frozen 662 gene registry and all existing HPO, GenCC, PubMind and candidate outputs remain unchanged. Existing discovery IDs retain their historical values. No direct biological PAR is promoted.

## Purpose

Claude's November 3 and November 5 reviews identified four distinct defects in the provisional HPO exporter: gene-subject identities created by a disease-mediated graph traversal, unversioned polarity identity, absent input conservation, and conflated causes of missing gene coverage. The November 7 source validation policy does not lift these findings.

`audit_candidate_export_gate_v01.py` adds a **read-only audit** of an already completed `par_candidates_v02` export. It is separate from `export_gene_phenotype_par.py` and does not regenerate the completed HPO, GenCC or PubMind analyses.

## Controls implemented

1. Verify the original exporter `SHA256SUMS.txt`, original manifest and input HPO source SHA256 values. Preserve the exact 662 HGNC ID and approved symbol registry.
2. Recompute only the **legacy provisional** candidate identity to check custody. The historical identity uses `(HGNC ID, unspecified_disruption, HPO ID, disease CURIE, HPOA polarity)`. This validation is not a PAR Core decision. A `polarity_function_sha256` records the code profile used by the read-only audit. No candidate ID is reissued.
3. Export a four-fate original-input ledger for every `genes_to_phenotype.txt` source record and every `phenotype.hpoa` source record. `emitted` means the source record appears in an original-scope evidence, context or discovery link. `held` means outside exact frozen scope or without the required exact join. `failed` records malformed keys or missing/mismatched links. `merged=0` because the producer preserves all original source line locators rather than dropping records through consolidation. Candidate-level identity collisions are reported separately.
4. Verify **source multiplicity** as well as source-row conservation. One original HPOA line can project to multiple provisional gene candidates. All projections must correspond to exact original disease–HPO and polarity evidence; original source row links and evidence roles remain intact. Check existing output record totals against the original manifest.
5. Report provisional ID collisions that would arise if polarity were omitted from the identity. This quantifies the consequences of the unresolved PAR Core decision without changing any identity.
6. Distinguish `candidate_available`, `no_exact_symbol_g2p_row_alias_unresolved`, and `exact_g2p_without_matching_hpoa_P`. The second state does not assert that a gene lacks HPO evidence under historical symbols. It explicitly leaves the HGNC crosswalk question open.
7. Report disease context C/I/M/H and separate `no_HPOA_P_rows_for_disease` from `P_rows_without_onset_field` and `at_least_one_P_onset_field`. Missing onset in a source is not coded as absent onset.
8. Emit output `SHA256SUMS.txt` and a manifest with `gate_passed`, input counts, identity anomalies and independent promotion status. Regardless of integrity result, **direct assertion promotion is blocked** until the PAR Core identity decision, independent source assessment and human scientific disposition.

The original disease–phenotype subject remains the HPOA disease identifier. A G2P traversal is discovery evidence. Source fidelity and successful integrity checks do not transform the provisional gene-subject record into directly observed genetic evidence.

## Test and CHOP HPC execution

All commands start from the existing repository root.

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
git fetch origin feature/gene-phenotypes
git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes
python -m unittest discover -s scripts/phenotypes/gene_pilot -p 'test_audit_candidate_export_gate_v01.py' -v
```

Then audit the existing results, without rerunning the upstream candidate producer.

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
python scripts/phenotypes/gene_pilot/audit_candidate_export_gate_v01.py \
  --registry data/releases/2026.09.08/genes.tsv \
  --g2p scripts/phenotypes/gene_pilot/inputs/genes_to_phenotype.txt \
  --hpoa scripts/phenotypes/gene_pilot/inputs/phenotype.hpoa \
  --candidate-dir results/phenotypes/par_candidates_v02 \
  --out results/phenotypes/candidate_export_integrity_v01
```

Verify `results/phenotypes/candidate_export_integrity_v01/audit_manifest.json`, `SHA256SUMS.txt`, `g2p_input_fates.tsv`, `hpoa_input_fates.tsv`, `gene_coverage_causal_states.tsv`, `disease_context_presence.tsv` and `polarity_identity_collisions.tsv`. If the command exits 2, the manifest and failure ledger explain the substantive integrity discrepancy. Preserve those results for independent review; do not modify the frozen upstream tables or silently change provisional identifiers.

## Open scientific and technical decisions

- **PAR identity.** The user and PAR Core must decide whether direct gene disruption claim identity can include source disease context and phenotype polarity. The current legacy IDs are strictly provisional and belong to the discovery collection.
- **Source ontology and subjects.** HPOA disease–HPO, GenCC gene–disease and PubMind proposed gene–HPO retain distinct source scopes. Direct human observed claims require independently reviewed evidence.
- **GenCC direction.** `consolidate_gencc_hpo_phenotypes.py` still uses match presence as `support`. Refuted, Disputed and No Known Disease Relationship classifications require separate direction or uncertainty strata. Submitter independence cannot be assumed from row count; Orphanet and OMIM provenance may overlap HPOA.
- **Source custody.** Old 11/55/67 PubMed review TSVs need durable reconstruction and hashes before reuse. Private Aditya PubMind variant-level source table remains awaited and must stay on private HPC.
- **Source validation.** SV-001 and SV-002 remain pending Claude's independent primary paper review and the user's scientific disposition.

All review and decision records belong in the DevMap Communications Log. CHD Spatial and R01 remain separate.
