# PubMed publication type and multi-gene citation audit

This audit uses the PubMed XML already retrieved for the first 150 HPO gene–publication leads. It checks the source records' `PublicationTypeList` annotations and identifies the number of DevMap genes referencing each PMID. There is no additional PubMed download.

A publication appearing with multiple genes is not intrinsically a review. PubMed `Review`, `Systematic Review` and `Meta-Analysis` are grouped as `review_or_meta_analysis`. Explicit study types such as `Case Reports`, `Clinical Study` and `Clinical Trial` are grouped as `primary_study_type`. Generic `Journal Article` is `journal_article_unresolved` because this designation alone does not determine primary versus secondary research. Editorials, letters and guidance are kept in another category. Mixed or missing metadata remains unclassified where appropriate. Every original publication type is retained in the output.

## Run on CHOP HPC

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes

python3 -m unittest discover -s scripts/phenotypes/gene_pilot \
  -p 'test_audit_pubmed_publication_types.py' -v

python3 scripts/phenotypes/gene_pilot/audit_pubmed_publication_types.py \
  --pubmed-xml results/phenotypes/pubmed_direct_screen_v01/pubmed_abstracts.xml \
  --publication-queue results/phenotypes/primary_evidence_queue_v01/publication_gene_queue.tsv \
  --screen-dir results/phenotypes/pubmed_direct_screen_v01 \
  --max-gene-publication-pairs 150 \
  --out results/phenotypes/pubmed_publication_type_audit_v01

cat results/phenotypes/pubmed_publication_type_audit_v01/publication_type_manifest.json
```

## Outputs

* `publication_types.tsv` has one row per retrieved PMID, title, exact PubMed publication types, study type category, number and identity of linked DevMap genes, and screened sentence count.
* `publication_gene_membership.tsv` preserves one row per HPO gene–PMID lead, its publication type and candidate sentence count.
* `screened_sentences_with_publication_type.tsv` adds publication classification to each previously extracted candidate sentence. Its `review_disposition` remains `requires_original_article_verification` regardless of the publication type.
* `publication_type_manifest.json` summarizes primary study types, reviews, generic journal articles, multi-gene PMIDs and sentence support.
* `SHA256SUMS.txt` preserves the new output integrity.

The script validates the previously recorded XML SHA256 and the source TSV checksums. It uses the same deterministic first-150 lead selection as the original PubMed screen. It does not promote any candidate to a biological PAR.

The publication type category is a screening attribute. Original articles must still link an actual gene perturbation to the phenotype in the relevant individuals, family, cohort or experimental system. For a review, trace the underlying original study. For an abstract reporting a multi-gene study, verify the gene-specific row or patient group before accepting the gene disruption → phenotype relationship.
