# DevMap-CHD licensing

DevMap-CHD uses separate liberal licenses for derived data and software.

## Derived data and repository-produced metadata: CC0 1.0 Universal

The derived DevMap-CHD data tables, provenance tables, release metadata, schemas, and repository-produced documentation are made available under the **Creative Commons CC0 1.0 Universal** public-domain dedication, to the extent that the contributors have rights that can be dedicated.

See [LICENSE-DATA.md](LICENSE-DATA.md) and the canonical CC0 terms at:

https://creativecommons.org/publicdomain/zero/1.0/

This includes, unless otherwise noted:

- `data/current/`
- `data/releases/`
- `sources/source_manifest.tsv`
- `schemas/`
- DevMap-CHD-created documentation and release metadata

## Software: MIT

Code in `scripts/` is licensed under the **MIT License**.

See [LICENSE-CODE.md](LICENSE-CODE.md).

## Upstream sources are not relicensed

DevMap-CHD organizes and attributes information from published literature and public biomedical resources. Raw upstream source files are not automatically redistributed by this repository, and DevMap-CHD does not claim or relicense rights in upstream publications, databases, trademarks, or other third-party materials.

Each source remains attributable to its originating publication/resource as recorded in `sources/source_manifest.tsv`.

## Citation and license are separate

CC0 does not require attribution as a license condition. Nevertheless, for scientific reproducibility and provenance, users are asked to cite:

1. the DevMap-CHD release used; and
2. the originating publications/resources corresponding to the source memberships used in an analysis.

See `CITATION.cff` and `sources/source_manifest.tsv`.
