# DevMap-CHD gene phenotype pilot v0.1

## Scope

This pilot includes **16 verified human genes** from DevMap-CHD `v2026.09.08`, pinned to gene-list GitHub blob `92143728ae7b5d1105bbdd59c6f08892ec031c0b`. It addresses **gene phenotype associations only**. Variant-specific extraction is deferred at User direction.

The HPO `genes_to_phenotype.txt` source is a **disease-mediated gene-to-phenotype summary**, not direct patient-level gene-phenotype evidence. Its `disease_id` is retained. When supplied, `phenotype.hpoa` provides the underlying **disease-to-phenotype** source annotations with their qualifiers and source evidence. The original HPOA `aspect` must be `P` to qualify as a clinical phenotypic abnormality. `aspect=I` denotes inheritance. Explicit `NOT` annotations remain distinct from unreported phenotypes. This pipeline does not construct a new direct gene–phenotype biological claim by traversing a disease association.

Direct independently supported gene–phenotype assertions will be developed from separately validated sources later. Every gene reports `NOT_ASSESSED_FROM_INDEPENDENT_SOURCES` for direct evidence in this pilot. Zero rows in an HPO summary means no row in that specific source release, not a biological negative.

## Pinned official source files

HPO official release [`v2026-09-01`](https://github.com/obophenotype/human-phenotype-ontology/releases/tag/v2026-09-01), published September 3, 2026.

- `genes_to_phenotype.txt` 20,821,704 bytes, SHA-256 `507a17bff9c49e6329fbd88b1f91734fa7e9fdea5c06304044c0892eb6ab248c`
- `phenotype.hpoa` 35,816,037 bytes, SHA-256 `e89aa39c8f97bf5a52c5d160f9250a603681d630ade8ec2679d84ac5aece1f72`

Use the official release assets rather than `latest` to preserve source reproducibility.

## Run on CHOP HPC or another computer with HTTPS access

```bash
mkdir -p inputs results
curl -fL --retry 3 -o inputs/genes_to_phenotype.txt \
  https://github.com/obophenotype/human-phenotype-ontology/releases/download/v2026-09-01/genes_to_phenotype.txt
curl -fL --retry 3 -o inputs/phenotype.hpoa \
  https://github.com/obophenotype/human-phenotype-ontology/releases/download/v2026-09-01/phenotype.hpoa

printf '%s  %s\n' \
  507a17bff9c49e6329fbd88b1f91734fa7e9fdea5c06304044c0892eb6ab248c inputs/genes_to_phenotype.txt \
  e89aa39c8f97bf5a52c5d160f9250a603681d630ade8ec2679d84ac5aece1f72 inputs/phenotype.hpoa | sha256sum -c

python run_gene_phenotype_pilot.py \
  --genes pilot_genes.tsv \
  --gene-phenotype inputs/genes_to_phenotype.txt \
  --phenotype-hpoa inputs/phenotype.hpoa \
  --expected-gene-sha256 507a17bff9c49e6329fbd88b1f91734fa7e9fdea5c06304044c0892eb6ab248c \
  --expected-hpoa-sha256 e89aa39c8f97bf5a52c5d160f9250a603681d630ade8ec2679d84ac5aece1f72 \
  --source-release v2026-09-01 \
  --out results

python -m unittest discover -s tests -v
```

## Outputs

- `hpo_disease_mediated_gene_view.tsv` is a source-native gene summary with the mediating disease and annotation class.
- `matched_hpoa_disease_phenotype.tsv` holds source HPOA evidence rows matched to those summarized gene/disease/phenotype triples. Retains `NOT`, evidence and aspect.
- `gene_coverage.tsv` reports all 16 genes, including zero source rows and direct-evidence `NOT_ASSESSED` state.
- `parse_findings.tsv` retains parsing failures and missing identifiers.
- `run_manifest.json` gives source checksums and denominator-based audit counts.
- `SHA256SUMS.txt` records output hashes.

Any gene summary line without a matching HPOA disease term is marked `UNMATCHED_HPOA` instead of being silently treated as direct evidence. A gene-level file is a *navigation view* over clinical disease annotations and is not evidence that all patients with a gene alteration manifest a phenotype.

## Execution status at handoff

- Two synthetic unit tests passed in the current execution container.
- Both official asset SHA-256 digests were independently retrieved from the GitHub release metadata.
- The current execution container could not resolve public download hosts. **The full official files were not downloaded or parsed and real phenotype yields for the 16 genes are NOT MEASURED.** The lack of a source file is an access failure, not zero biological coverage.
- No GitHub source changes, Notion dataset imports or public DevMap-CHD release were performed.
