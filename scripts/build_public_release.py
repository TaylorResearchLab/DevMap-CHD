#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Build DevMap-CHD public tables from a reviewed canonical registry."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from pathlib import Path


GENE_COLUMN_MAP = [
    ("HGNC ID", "hgnc_id"),
    ("Gene", "gene"),
    ("Ensembl gene ID", "ensembl_gene_id"),
    ("Approved HGNC symbol", "approved_hgnc_symbol"),
    ("Previous matrix gene symbol", "previous_matrix_gene_symbol"),
    ("Source symbol(s)", "source_symbols"),
    ("Normalization status", "normalization_status"),
    ("ID mapping status", "id_mapping_status"),
    ("ID mapping source", "id_mapping_source"),
]

MANIFEST_REQUIRED = [
    "source_id",
    "source_group_id",
    "membership_column",
    "display_name",
    "source_class",
    "analysis_role",
    "universe_expands",
    "expected_public_memberships",
    "citation_text",
    "doi",
    "pmid",
    "stable_url",
    "source_locator",
    "source_version_or_date",
    "extraction_date",
    "redistribution_status",
    "notes",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_tsv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def write_tsv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fieldnames, delimiter="\t", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def require_columns(rows: list[dict[str, str]], required: list[str], label: str) -> None:
    if not rows:
        raise ValueError(f"{label} is empty")
    missing = [name for name in required if name not in rows[0]]
    if missing:
        raise ValueError(f"{label} is missing columns: {missing}")


def load_manifest(path: Path) -> list[dict[str, str]]:
    rows = read_tsv(path)
    require_columns(rows, MANIFEST_REQUIRED, "source manifest")

    source_ids = [row["source_id"].strip() for row in rows]
    membership_columns = [row["membership_column"].strip() for row in rows]

    if len(source_ids) != len(set(source_ids)):
        raise ValueError("source_manifest.tsv has duplicate source_id values")
    if len(membership_columns) != len(set(membership_columns)):
        raise ValueError("source_manifest.tsv has duplicate membership_column values")

    incomplete = []
    for row in rows:
        has_identifier = any(row[key].strip() for key in ("doi", "pmid", "stable_url"))
        if (
            not row["citation_text"].strip()
            or not has_identifier
            or not row["stable_url"].strip()
            or not row["source_locator"].strip()
        ):
            incomplete.append(row["source_id"])

    if incomplete:
        raise ValueError(
            "Public source metadata are incomplete for " + ", ".join(incomplete)
        )

    return rows


def parse_membership(value: str, column: str, gene: str) -> str:
    normalized = value.strip()
    if normalized in {"0", "0.0", ""}:
        return "0"
    if normalized in {"1", "1.0"}:
        return "1"
    raise ValueError(
        f"Unexpected membership value {value!r} for gene={gene!r}, column={column!r}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--source-manifest", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--release-version", required=True)
    args = parser.parse_args()

    matrix_path = args.matrix.resolve()
    manifest_path = args.source_manifest.resolve()
    output_dir = args.output_dir.resolve()

    if not matrix_path.is_file():
        raise FileNotFoundError(f"Canonical matrix does not exist: {matrix_path}")

    manifest = load_manifest(manifest_path)
    matrix = read_tsv(matrix_path)

    required_matrix = [source for source, _ in GENE_COLUMN_MAP] + [
        row["membership_column"] for row in manifest
    ]
    require_columns(matrix, required_matrix, "canonical matrix")

    genes: list[dict[str, str]] = []
    memberships: list[dict[str, str]] = []
    wide_rows: list[dict[str, str]] = []
    counts = {row["source_id"]: 0 for row in manifest}

    hgnc_seen: set[str] = set()
    symbol_seen: set[str] = set()

    for row in matrix:
        public_gene = {public: row[source].strip() for source, public in GENE_COLUMN_MAP}
        hgnc_id = public_gene["hgnc_id"]
        gene = public_gene["gene"]

        if not hgnc_id or not gene:
            raise ValueError("Every canonical row must have an HGNC ID and gene symbol")
        if hgnc_id in hgnc_seen:
            raise ValueError(f"Duplicate HGNC ID: {hgnc_id}")
        if gene in symbol_seen:
            raise ValueError(f"Duplicate canonical gene symbol: {gene}")

        hgnc_seen.add(hgnc_id)
        symbol_seen.add(gene)

        if public_gene["approved_hgnc_symbol"] != gene:
            raise ValueError(
                f"Gene and approved HGNC symbol differ for {hgnc_id}: "
                f"{gene!r} vs {public_gene['approved_hgnc_symbol']!r}"
            )

        genes.append(public_gene)
        wide = {"hgnc_id": hgnc_id, "gene": gene}

        for source in manifest:
            column = source["membership_column"]
            member = parse_membership(row[column], column, gene)
            wide[source["source_id"]] = member

            if member == "1":
                counts[source["source_id"]] += 1
                memberships.append(
                    {
                        "hgnc_id": hgnc_id,
                        "gene": gene,
                        "source_id": source["source_id"],
                        "source_group_id": source["source_group_id"],
                        "membership": "1",
                        "membership_column": column,
                        "source_symbols": public_gene["source_symbols"],
                    }
                )

        wide_rows.append(wide)

    for source in manifest:
        expected = int(source["expected_public_memberships"])
        actual = counts[source["source_id"]]
        if actual != expected:
            raise ValueError(
                f"Membership count mismatch for {source['source_id']}: "
                f"got {actual}, expected {expected}"
            )

    generated = [
        output_dir / "genes.tsv",
        output_dir / "gene_source_membership.tsv",
        output_dir / "source_membership_matrix.tsv",
        output_dir / "source_manifest.tsv",
        output_dir / "release_metadata.json",
        output_dir / "SHA256SUMS.txt",
    ]

    collisions = [path for path in generated if path.exists()]
    if collisions:
        raise FileExistsError(
            "Refusing to overwrite generated files:\n"
            + "\n".join(str(path) for path in collisions)
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    gene_fields = [public for _, public in GENE_COLUMN_MAP]
    membership_fields = [
        "hgnc_id",
        "gene",
        "source_id",
        "source_group_id",
        "membership",
        "membership_column",
        "source_symbols",
    ]
    wide_fields = ["hgnc_id", "gene"] + [row["source_id"] for row in manifest]

    genes_path = output_dir / "genes.tsv"
    membership_path = output_dir / "gene_source_membership.tsv"
    wide_path = output_dir / "source_membership_matrix.tsv"
    manifest_out = output_dir / "source_manifest.tsv"

    write_tsv(genes_path, gene_fields, genes)
    write_tsv(membership_path, membership_fields, memberships)
    write_tsv(wide_path, wide_fields, wide_rows)
    shutil.copyfile(manifest_path, manifest_out)

    metadata = {
        "resource": "DevMap-CHD",
        "release_version": args.release_version,
        "canonical_genes": len(genes),
        "source_groups": len({row["source_group_id"] for row in manifest}),
        "source_sets": len(manifest),
        "gene_source_memberships": len(memberships),
        "source_membership_counts": counts,
        "identifier_counts": {
            "unique_hgnc_ids": len(hgnc_seen),
            "unique_gene_symbols": len(symbol_seen),
            "ensembl_gene_ids_nonempty": sum(
                bool(row["ensembl_gene_id"]) for row in genes
            ),
        },
        "interpretation": (
            "A source membership links a gene to a specific source set "
            "under that source's stated definition."
        ),
    }

    metadata_path = output_dir / "release_metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    checksum_paths = [
        genes_path,
        membership_path,
        wide_path,
        manifest_out,
        metadata_path,
    ]
    sums_path = output_dir / "SHA256SUMS.txt"
    sums_path.write_text(
        "".join(f"{sha256(path)}  {path.name}\n" for path in checksum_paths),
        encoding="utf-8",
    )

    print("DEVMAP-CHD PUBLIC TABLE BUILD: PASS")
    print(json.dumps(metadata, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
