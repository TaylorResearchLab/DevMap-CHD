# First direct disruption–phenotype literature screen

This extracts a bounded set of HPO-linked PubMed records through NCBI E-utilities and identifies abstract sentences explicitly mentioning the same gene, a gene perturbation term, and the pinned HPO phenotype label. It is an automated lead finder. The original paper must establish that the phenotype was observed in a subject with the stated gene disruption before the record can be accepted as a biological PAR.

## Run from DevMap-CHD HPC repository root

```bash
cd /mnt/isilon/taylor_lab/data/projects/DevMap-CHD
git switch feature/gene-phenotypes
git pull --ff-only origin feature/gene-phenotypes

python3 -m unittest discover -s scripts/phenotypes/gene_pilot \
  -p 'test_screen_pubmed_disruption_phenotypes.py' -v

python3 scripts/phenotypes/gene_pilot/screen_pubmed_disruption_phenotypes.py \
  --hpo-dir results/phenotypes/par_candidates_v02 \
  --publication-queue results/phenotypes/primary_evidence_queue_v01/publication_gene_queue.tsv \
  --hpo-obo scripts/phenotypes/gene_pilot/inputs/hp.obo \
  --pubmed-xml results/phenotypes/pubmed_direct_screen_v01/pubmed_abstracts.xml \
  --ca-bundle /etc/pki/tls/certs/ca-bundle.crt \
  --max-gene-publication-pairs 150 \
  --fetch \
  --out results/phenotypes/pubmed_direct_screen_v01

cat results/phenotypes/pubmed_direct_screen_v01/abstract_screen_manifest.json
```

## Source integrity and semantics

* Input HPO candidate and evidence files are checksum verified against their source manifest.
* The publication queue is checksum verified against its own `SHA256SUMS.txt`.
* The HPO ontology `hp.obo` is required to match SHA256 `93dace952fcb3ec4728818857f6ba76bc2d5312f4d83266519b8694b8e798f22` for release v2026-09-01.
* NCBI EFetch retrieval uses an explicit CHOP trusted system certificate bundle. The batch size is at most 80 PMIDs per request and requests are spaced by at least one second. A retrieval may include multiple gene–PMID leads pointing to the same original article.
* The XML cache records exact retrieved PubMed records and its SHA256. Repeating the command with `--fetch` retrieves records again. Omit `--fetch` to screen the saved XML.
* Only candidates with explicitly asserted presence enter the positive screen. Absence and unspecified observations remain in the original source evidence tables.
* A matching sentence must contain the gene symbol, the exact pinned HPO term name, and a gene alteration lexeme. Common negation tokens are flagged. This heuristic can miss synonym expressions and can find noncausal co-mentions.
* All detected sentences have `evidence_decision=requires_original_article_verification`. There is **no automatic PAR promotion**, even if all three terms co-occur. A gene and phenotype in a review article may concern separate cohorts or distinct genotypes.

## Output

* `abstract_candidate_sentences.tsv` gives PMID, candidate ID, original evidence sentence, perturbation lexeme, negation marker and source XML checksum.
* `abstract_unresolved.tsv` records candidates not passing the lexical screen.
* `abstract_screen_manifest.json` summarizes retrieval and screening.
* `SHA256SUMS.txt` preserves output hashes.

A positive screen identifies the next high-yield original article to examine. Direct accepted PARs require source subject, perturbation mechanism, observed phenotype and provenance. GenCC/HPO evidence remains linked through the existing candidate ID and source tables.

Publication metadata and abstracts retrieved from PubMed are internal working source content. Respect source rights in downstream distributions.
