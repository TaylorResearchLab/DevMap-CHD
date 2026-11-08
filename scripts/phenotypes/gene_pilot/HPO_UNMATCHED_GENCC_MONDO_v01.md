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
## Real CHOP HPC census, 8 November 2026

User verified fast-forward pull to commit `242f2552ad58648ab491196f050da9785c33224c`; all **5 synthetic tests passed**. Real read-only source census completed on CHOP HPC and printed the same manifest twice, first on stdout and then read from the saved `manifest.json`.

| Real manifest quantity | Count |
| --- | ---: |
| Frozen DevMap gene roster | 662 |
| HPO G2P unmatched genes | 143 |
| Unmatched genes with any GenCC submission | 63 |
| Unmatched genes with no GenCC submission | 80 |
| GenCC submission versions for those 63 genes | 112 |
| Unmatched genes with any ClinGen-submitted record | 45 |
| Unmatched genes with one or more Definitive/Strong/Moderate GenCC submissions | **19** |
| All registry GenCC assertion versions | 4,090 |
| Registry genes with a GenCC submission | 575 |
| Source GenCC rows scanned | 30,362 |
| Direct gene-phenotype PARs promoted | 0 |

The saved manifest reports pinned registry SHA-256 `523cd288c68608d4c1e277930685666895cfb5fd002ee99705e9a5b21caed43c`, pinned GenCC SHA-256 `6b099f2497837c8bb0b62930bcfff13c952869dd52635511da181521ce1cde17` and validated input gap manifest SHA-256 `505bb48050566e3d545600acef9ecb84cba1fbe29c5f25ae44226628e25df256`.

**Interpretation:** 19 genes have at least one GenCC submission with a positive expert-curation classification, which is a **gene–disease** evidence result. They do not consequently acquire a direct phenotype observation. The group of 45 genes with ClinGen submissions is not necessarily contained within or inclusive of those 19; evaluate intersection from the per-gene output. Mapping `disease_curie` to MONDO comes from GenCC and has not independently been revalidated. Multiple submitters may cite the same studies, so independence requires evidence review.

The user did not include the output directory `SHA256SUMS.txt` verification stdout. Request that check before treating the output artifact package as fully verified. Next enumerate the 19 genes and their original submitted disease CURIEs, MONDO mapping, classifications and source references. Review original source scope before any phenotype-level inference, preserving frozen registry and existing approved `dmpdsrc1` / `dmpview1` identities.

## Source-level interpretation after the full 112-submission review, 8 November 2026

The user verified **all five** output file checksums. Their output listed 19 distinct genes having at least one GenCC Definitive, Strong or Moderate gene–disease submission: AGMO, BMP10, BMP7, EZH1, FOXP4, HAND1, ITSN2, LEO1, LHX2, MAP4K4, MESP1, MYH10, NFATC1, NRG1, PRDM9, RBFOX2, ROCK2, WDR5, ZMYND8. Across all 112 original GenCC submissions: Definitive 4, Strong 16, Moderate 18, Limited 53, Disputed Evidence 15, No Known Disease Relationship 5, Supportive 1. The first three classes sum to **38 submissions across 19 genes**, not 38 independent studies and not 19 directly observed congenital cardiac lesion relationships.

Among the positively graded submissions only HAND1, MESP1, RBFOX2 and ROCK2 had an explicitly submitted **MONDO:0005453 congenital heart disease** relationship. RBFOX2 also has more specific disease assertions under MONDO:0000119 and MONDO:0100557; native distinct disease identifiers are preserved. Several other positive submissions represent neurodevelopmental disease, pulmonary arterial hypertension, inborn errors of immunity, Hirschsprung disease or other medical domains.

**Important source-classification disagreement:** GenCC [ROCK2](https://thegencc.org/genes/HGNC%3A10252/disease) lists **PanelApp Australia Moderate** but **ClinGen CHD-GCEP Limited** for the same broad MONDO:0005453 relation. [ClinGen SGC-107591.2](https://thegencc.org/submissions/SGC-107591.2) and [PanelApp SGC-120816.2](https://thegencc.org/submissions/SGC-120816.2) share PMIDs 28554332, 30622330 and 31941532. They represent multiple source assessments drawing upon overlapping underlying literature, so do not infer independent studies.

ClinGen expert curations for the remaining three are [HAND1 Moderate](https://search.clinicalgenome.org/kb/gene-validity/CGGV%3Aassertion_7a70bdb1-a3fc-45c5-aabb-4d2829fa6f29-2023-04-04T16%3A00%3A00.000Z?page=1&size=25), [MESP1 Moderate](https://search.clinicalgenome.org/kb/gene-validity/CGGV%3Aassertion_8e86e873-749f-4d44-a1c8-d28405d7dace-2024-09-09T160000.000Z) and [RBFOX2 Strong](https://search.clinicalgenome.org/kb/gene-validity/CGGV%3Aassertion_ed2c6ea3-402b-482d-ba7e-24e8cf2fb681-2024-05-14T160000.000Z?page=1&size=25). RBFOX2's ClinGen rationale lists potential congenital structural lesions but those source statements require primary individual case validation before direct phenotype PAR acceptance.

All 38 graded positive disease IDs printed are already MONDO native identifiers on both the original submitted and GenCC harmonized fields. The census has not independently validated MONDO equivalence across non-MONDO identifiers. Next obtain source PMIDs and original case-level anatomical phenotypes for HAND1, MESP1, RBFOX2 and ROCK2. Compare disease classifications by submitter and original case cohorts. No change to the frozen 662-gene registry or approved source/discovery identities.
