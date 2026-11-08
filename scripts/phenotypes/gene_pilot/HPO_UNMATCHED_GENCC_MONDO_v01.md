# DevMap-CHD | MONDO and GenCC disease source census for 143 HPO-unmatched genes v01

Status: Agent 1 read-only diagnostic committed for CHOP HPC execution and independent Agent 2 review. No real output for this diagnostic has been reported.

## Scientific question

Of the 143 frozen genes lacking matches in HPO v2026-09-01 `genes_to_phenotype.txt`, which have gene–disease assertions in GenCC, which diseases do those submissions name and map to MONDO, and what classifications and submitters support each relationship?

MONDO is a harmonized **disease identity** ontology, not a substitute for observed HPO phenotypes. Its disease mappings are recorded separately from evidence for a gene–disease assertion. GenCC is a source of versioned gene–disease **submissions**, including disputed and refuted classes. ClinGen is a submitter to GenCC. A GenCC-provided MONDO disease identifier is distinguished from the original submitted OMIM, ORPHA or MONDO identifier; this census does not independently validate disease mapping equivalence.

Previous real source counts are **143** HPO-unmatched genes. The earlier GenCC integration reports **63** with GenCC submissions and **80** without, but these 63 need classification and submitted-disease stratification. Existing previous GenCC counts were 4,090 submissions for 575 of 662 genes. Some GenCC submissions may be Limited, Disputed, Refuted, Supportive or No Known Disease Relationship. They must not all be called positive gene–disease support.

## Pinned inputs

- Frozen 662-gene registry `data/releases/2026.09.08/genes.tsv`, SHA256 `523cd288c68608d4c1e277930685666895cfb5fd002ee99705e9a5b21caed43c`.
- Verified HPO/HGNC identifier audit `results/phenotypes/hpo_hgnc_identifier_gap_diagnostic_v01` including the 143-row unresolved file and checksum manifest.
- Archived GenCC snapshot `scripts/phenotypes/gene_pilot/inputs/gencc-submissions-new.tsv`, SHA256 `6b099f2497837c8bb0b62930bcfff13c952869dd52635511da181521ce1cde17`.

## Data representation

- `hpo_unmatched_143_gene_disease_coverage.tsv`: all 143 genes, per-gene GenCC submission counts, distinct harmonized MONDO IDs, distinct submitted source disease IDs, ClinGen submission counts and classification summaries.
- `gencc_mondo_submissions_for_143.tsv`: each original SGC ID and version, HGNC ID, **original submitted disease CURIE**, GenCC-provided **MONDO disease CURIE**, both disease titles, classification, inheritance, submitter, PMID field and original report link when available. It is a source submission record, not an inferred HPO phenotype.
- `gencc_classification_submitter_143.tsv`: evidence classification and submitter distribution. Multiple submitters are not counted as independent primary clinical evidence without shared-reference review.
- `hpo_unmatched_without_gencc.tsv`: the subset with no versioned submissions in this pinned GenCC snapshot, previously 80 genes.
- `manifest.json` and `SHA256SUMS.txt`: verified input hashes, immutable source-count reconciliation and no direct PAR promotion.

Classifications are retained verbatim alongside interpretive classes: Definitive/Strong/Moderate as curated support; Supportive as an ungraded source classification; Limited as limited evidence; Disputed as contested; Refuted as refuted; No Known Disease Relationship as its own status; Animal Model Only as nonhuman. Unknown classifications are reported explicitly rather than mapped to positive support.

## CHOP HPC execution

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes

python -m unittest discover -s scripts/phenotypes/gene_pilot -p 'test_audit_hpo_unmatched_gencc_mondo_v01.py' -v

python scripts/phenotypes/gene_pilot/audit_hpo_unmatched_gencc_mondo_v01.py \
  --registry data/releases/2026.09.08/genes.tsv \
  --gap-dir results/phenotypes/hpo_hgnc_identifier_gap_diagnostic_v01 \
  --gencc scripts/phenotypes/gene_pilot/inputs/gencc-submissions-new.tsv \
  --out results/phenotypes/hpo_unmatched_gencc_mondo_v01

(cd results/phenotypes/hpo_unmatched_gencc_mondo_v01 && sha256sum -c SHA256SUMS.txt)
cat results/phenotypes/hpo_unmatched_gencc_mondo_v01/manifest.json
```

## Interpretation and follow-up

The census uses only approved HGNC identity from the frozen registry. The GenCC-provided harmonized disease identifier is a mapping assertion from GenCC and must retain the original source disease CURIE. Avoid equating disease IDs by lexical label or a broad parent in MONDO. Review strict equivalence mappings separately if joining OMIM/ORPHA phenotype annotations. For genes with no GenCC submissions, possible next sources include ClinGen's direct gene–disease validity downloads, MONDO's OMIM-derived gene associations, OMIM phenotype records (with reuse controls), and primary developmental clinical or experimental evidence.

DevMap source claim identity `dmpdsrc1` and discovery projection `dmpview1` remain approved and unchanged. GenCC association evidence does not automatically create a new directly observed gene disruption–phenotype PAR. No frozen registry modifications, no synthetic disease assignments and no public release are authorized by this diagnostic.

Sources: [MONDO ontology](https://mondo.monarchinitiative.org/), [GenCC downloads](https://thegencc.org/download), [ClinGen gene-disease validity](https://search.clinicalgenome.org/kb/downloads).