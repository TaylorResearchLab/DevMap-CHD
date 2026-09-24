##Build

The public tables can be generated from a reviewed canonical matrix and the public source manifest.

python3 scripts/build_public_release.py \
  --matrix /path/to/canonical_chd_gene_matrix.tsv \
  --source-manifest sources/source_manifest.tsv \
  --output-dir /path/to/output_directory \
  --release-version <version>

The script verifies gene identifier uniqueness, approved HGNC symbols, membership values, source citations, source locations, and the expected gene count for each source set.
