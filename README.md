# DevMap-CHD

DevMap-CHD is a congenital heart defect gene resource from the DevMap project. It compiles gene memberships from published studies and public biomedical resources. Each membership retains its source provenance, and gene identifiers are normalized to current HGNC identifiers.

## FAIR statement

Every published membership must resolve to a citable source record. That record identifies the publication or resource, the table or subset used, the source version or extraction date when relevant, and the information needed to interpret the membership set.

## Source structure

A publication or resource may contribute more than one membership set. Each set has a `source_id`. Sets from the same publication or resource share a `source_group_id`.

A positive membership means that a gene occurs in the named source set under that source's stated definition.

The source manifest is `sources/source_manifest.tsv`. It provides the citation, public source location, set definition, relevant dates, and expected gene count for each membership set.

## Public tables

Each release contains

- `genes.tsv` with gene identifiers
- `gene_source_membership.tsv` with one row for each gene and source set membership
- `source_membership_matrix.tsv` with the same memberships in a wide matrix
- `source_manifest.tsv` with source metadata
- `release_metadata.json` with release counts and identifier totals
- `SHA256SUMS.txt` with file checksums

Schemas are provided in `schemas/`.

## Gene identifiers

HGNC identifiers are used as stable gene keys. Approved HGNC symbols are used as display labels. Historical or source symbols are retained when needed to document normalization. Ensembl gene identifiers are also provided.


## Releases

Published releases are stored under `data/releases/`.

## Citation

Citation metadata are provided in `CITATION.cff`. Scientific users should cite the DevMap-CHD release they used and the original publications or resources represented in their analyses.

## License

Derived data, provenance tables, schemas, metadata, and documentation are released under CC0 1.0 Universal. Code in `scripts/` is released under the MIT License.

The original publications and databases retain their own rights and are not relicensed by DevMap-CHD.
