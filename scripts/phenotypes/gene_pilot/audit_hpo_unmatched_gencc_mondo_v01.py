#!/usr/bin/env python3
"""Census MONDO-coded GenCC disease assertions for 143 HPO-unmatched genes.

GenCC source submissions, disease ontology mappings, and HPO absence are kept
distinct. This read-only census cannot generate direct gene-phenotype PARs.
"""
import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

from audit_662_hpo_coverage import sha256, write_tsv

REGISTRY_SHA = "523cd288c68608d4c1e277930685666895cfb5fd002ee99705e9a5b21caed43c"
GENCC_SHA = "6b099f2497837c8bb0b62930bcfff13c952869dd52635511da181521ce1cde17"
GAP_STATUS = "read_only_gene_identifier_diagnostic_pending_independent_review"
GENCC_FIELDS = (
    "sgc_id", "version_number", "gene_curie", "disease_curie", "disease_title",
    "disease_original_curie", "disease_original_title", "classification_title",
    "submitter_title", "moi_title",
)
OBS_COLUMNS = (
    "gene_id", "gene_symbol", "gencc_submission_id", "gencc_version",
    "submitted_disease_id", "submitted_disease_title", "gencc_mondo_id",
    "gencc_disease_title", "disease_mapping_status", "source_classification",
    "evidence_interpretation", "mode_of_inheritance", "submitter",
    "source_pmids", "source_report_url", "source_row_id",
)
GENE_COLUMNS = (
    "gene_id", "gene_symbol", "hpo_gene_summary_status",
    "gencc_submission_count", "gencc_disease_mondo_id_count",
    "gencc_source_disease_id_count", "clingen_submission_count",
    "strong_moderate_or_definitive_count", "supportive_count",
    "limited_count", "disputed_count", "refuted_count",
    "no_known_disease_relationship_count", "animal_model_only_count",
    "unrecognized_classification_count", "source_coverage_class",
    "disease_interpretation", "direct_gene_phenotype_PARs_promoted",
)
SUBMITTER_COLUMNS = (
    "submitter", "source_classification", "evidence_interpretation",
    "submission_versions", "distinct_genes", "distinct_mondo_diseases",
)

def read_tsv(path, required):
    with Path(path).open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        columns = set(reader.fieldnames or ())
        missing = set(required) - columns
        if missing:
            raise ValueError(f"{path}: missing fields {sorted(missing)}")
        yield from reader


def verified_files(directory, names):
    expected = {}
    for line in (directory / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        pieces = line.split(None, 1)
        if len(pieces) != 2:
            raise ValueError("Invalid checksum line")
        digest, name = pieces
        name = name.strip()
        if Path(name).name != name or name in expected:
            raise ValueError("Unsafe or duplicate checksum filename")
        expected[name] = digest
    for name in names:
        if name not in expected or sha256(directory / name) != expected[name]:
            raise ValueError(f"Missing or corrupted input: {directory / name}")


def classify(value):
    text = " ".join((value or "").casefold().split())
    mapping = {
        "definitive": "supports_curated",
        "strong": "supports_curated",
        "moderate": "supports_curated",
        "supportive": "supportive_ungraded",
        "limited": "limited_evidence",
        "disputed": "contested",
        "disputed evidence": "contested",
        "refuted": "refuted",
        "refuted evidence": "refuted",
        "no known disease relationship": "no_known_relationship",
        "animal model only": "animal_model_only",
    }
    return mapping.get(text, "classification_unrecognized")


def census(registry, gap_dir, gencc, out, synthetic=False):
    registry, gap_dir, gencc, out = map(Path, (registry, gap_dir, gencc, out))
    if out.exists():
        raise ValueError("Output directory exists; choose a new versioned path")
    verified_files(gap_dir, (
        "manifest.json", "gene_identifier_diagnostic_662.tsv",
        "unresolved_143_identifier_diagnostic.tsv",
    ))
    gap_manifest = json.loads((gap_dir / "manifest.json").read_text(encoding="utf-8"))
    registry_hash = sha256(registry)
    gencc_hash = sha256(gencc)
    if (gap_manifest.get("status") != GAP_STATUS or
            gap_manifest.get("source_sha256", {}).get("registry") != registry_hash or
            gap_manifest.get("original_matched_gene_count") is None):
        raise ValueError("Input gap census and registry custody disagree")
    if not synthetic and (registry_hash != REGISTRY_SHA or gencc_hash != GENCC_SHA):
        raise ValueError("Pinned registry or GenCC new-format snapshot SHA differs")

    genes = list(read_tsv(registry, ("hgnc_id", "approved_hgnc_symbol")))
    gene_symbols = {r["hgnc_id"]: r["approved_hgnc_symbol"] for r in genes}
    missing = list(read_tsv(gap_dir / "unresolved_143_identifier_diagnostic.tsv",
                            ("hgnc_id", "approved_symbol", "identifier_diagnostic_state")))
    missing_ids = {r["hgnc_id"] for r in missing}
    if (len(gene_symbols) != len(genes) or len(missing_ids) != len(missing)
            or not missing_ids.issubset(gene_symbols)
            or len(genes) != gap_manifest["frozen_gene_count"]
            or len(missing) != gap_manifest["original_unmatched_gene_count"]):
        raise ValueError("Frozen gene and HPO-unmatched membership mismatch")
    for r in missing:
        if (r["approved_symbol"] != gene_symbols[r["hgnc_id"]] or
                r["identifier_diagnostic_state"] == "matched_source"):
            raise ValueError("Unmatched gene identity disagrees with frozen registry")
    if not synthetic and (len(genes) != 662 or len(missing) != 143):
        raise ValueError("Expected the frozen 662 gene / 143 HPO-unmatched split")

    observations = []
    gene_submissions = defaultdict(list)
    full_gene_ids = set()
    frozen_submissions = set()
    source_rows = 0
    for line_number, r in enumerate(read_tsv(gencc, GENCC_FIELDS), 2):
        source_rows += 1
        gid = (r["gene_curie"] or "").strip()
        if gid not in gene_symbols:
            continue
        source_id = (r["sgc_id"] or "").strip()
        version = (r["version_number"] or "").strip()
        if not source_id or not version:
            raise ValueError("GenCC SGC ID and version are required")
        key = (source_id, version)
        if key in frozen_submissions:
            raise ValueError("Duplicate GenCC SGC ID and version within frozen genes")
        frozen_submissions.add(key)
        full_gene_ids.add(gid)
        if gid not in missing_ids:
            continue
        original_id = (r["disease_original_curie"] or "").strip()
        mondo_id = (r["disease_curie"] or "").strip()
        if mondo_id and not mondo_id.startswith("MONDO:"):
            disease_state = "gencc_harmonized_id_not_mondo"
        elif mondo_id:
            disease_state = "gencc_provided_MONDO_mapping_not_revalidated"
        else:
            disease_state = "no_gencc_mondo_id"
        outcome = classify(r["classification_title"])
        item = {
            "gene_id": gid, "gene_symbol": gene_symbols[gid],
            "gencc_submission_id": source_id, "gencc_version": version,
            "submitted_disease_id": original_id,
            "submitted_disease_title": r["disease_original_title"],
            "gencc_mondo_id": mondo_id, "gencc_disease_title": r["disease_title"],
            "disease_mapping_status": disease_state,
            "source_classification": r["classification_title"],
            "evidence_interpretation": outcome,
            "mode_of_inheritance": r["moi_title"],
            "submitter": r["submitter_title"],
            "source_pmids": r.get("submitted_as_pmids", ""),
            "source_report_url": r.get("submitted_as_public_report_url", ""),
            "source_row_id": f"gencc-submissions-new.tsv:L{line_number}",
        }
        observations.append(item)
        gene_submissions[gid].append(item)

    if not synthetic and (len(frozen_submissions) != 4090 or len(full_gene_ids) != 575):
        raise ValueError("Pinned GenCC full-registry census disagrees with verified 4090/575")

    summary = []
    for r in sorted(missing, key=lambda x: x["approved_symbol"]):
        gid = r["hgnc_id"]
        assertions = gene_submissions.get(gid, [])
        counts = Counter(a["evidence_interpretation"] for a in assertions)
        clingen = sum(a["submitter"].strip().casefold() == "clingen" for a in assertions)
        if not assertions:
            coverage_class = "no_GenCC_submission_in_pinned_snapshot"
        elif counts["supports_curated"]:
            coverage_class = "GenCC_definitive_strong_or_moderate_present"
        elif clingen:
            coverage_class = "ClinGen_submission_without_definitive_strong_or_moderate"
        else:
            coverage_class = "GenCC_other_classification_only"
        summary.append({
            "gene_id": gid, "gene_symbol": r["approved_symbol"],
            "hpo_gene_summary_status": "no_matched_G2P_gene_row_in_pinned_release",
            "gencc_submission_count": len(assertions),
            "gencc_disease_mondo_id_count": len({
                a["gencc_mondo_id"] for a in assertions
                if a["gencc_mondo_id"].startswith("MONDO:")
            }),
            "gencc_source_disease_id_count": len({
                a["submitted_disease_id"] for a in assertions if a["submitted_disease_id"]
            }),
            "clingen_submission_count": clingen,
            "strong_moderate_or_definitive_count": counts["supports_curated"],
            "supportive_count": counts["supportive_ungraded"],
            "limited_count": counts["limited_evidence"],
            "disputed_count": counts["contested"],
            "refuted_count": counts["refuted"],
            "no_known_disease_relationship_count": counts["no_known_relationship"],
            "animal_model_only_count": counts["animal_model_only"],
            "unrecognized_classification_count": counts["classification_unrecognized"],
            "source_coverage_class": coverage_class,
            "disease_interpretation": "GenCC_gene_disease_only;MONDO_harmonized_disease_identifier",
            "direct_gene_phenotype_PARs_promoted": 0,
        })
    genes_with_gencc = sum(int(r["gencc_submission_count"]) > 0 for r in summary)
    if not synthetic and genes_with_gencc != 63:
        raise ValueError("GenCC-only genes inconsistent with prior 63-gene result")
    by_submitter = defaultdict(list)
    for a in observations:
        key = (a["submitter"], a["source_classification"], a["evidence_interpretation"])
        by_submitter[key].append(a)
    submitters = [{
        "submitter": key[0],
        "source_classification": key[1], "evidence_interpretation": key[2],
        "submission_versions": len(items),
        "distinct_genes": len({x["gene_id"] for x in items}),
        "distinct_mondo_diseases": len({x["gencc_mondo_id"] for x in items
                                      if x["gencc_mondo_id"].startswith("MONDO:")}),
    } for key, items in sorted(by_submitter.items())]
    manifest = {
        "status": "read_only_143_gene_disease_source_census",
        "frozen_gene_count": len(genes),
        "hpo_unmatched_gene_count": len(missing),
        "hpo_unmatched_with_gencc_submissions": genes_with_gencc,
        "hpo_unmatched_without_gencc_submissions": len(missing) - genes_with_gencc,
        "gencc_submissions_for_hpo_unmatched": len(observations),
        "hpo_unmatched_with_clingen_submitter": sum(int(r["clingen_submission_count"]) > 0
                                                  for r in summary),
        "hpo_unmatched_with_definitive_strong_moderate": sum(
            int(r["strong_moderate_or_definitive_count"]) > 0 for r in summary),
        "frozen_gencc_regional_assertions": len(frozen_submissions),
        "frozen_gencc_registry_genes": len(full_gene_ids),
        "gencc_raw_rows_scanned": source_rows,
        "gencc_source_sha256": gencc_hash,
        "registry_sha256": registry_hash,
        "input_gap_manifest_sha256": sha256(gap_dir / "manifest.json"),
        "submitter_independence_inferred": False,
        "mondo_mappings_independently_validated": False,
        "direct_gene_phenotype_PARs_promoted": 0,
        "notes": ("GenCC gene-disease submissions and GenCC-provided MONDO disease IDs; "
                  "no inferred gene-phenotype association, no disease phenotype assignment."),
    }
    out.mkdir(parents=True)
    files = {
        "hpo_unmatched_143_gene_disease_coverage.tsv": (GENE_COLUMNS, summary),
        "gencc_mondo_submissions_for_143.tsv": (OBS_COLUMNS, sorted(
            observations, key=lambda x: (x["gene_symbol"], x["gencc_mondo_id"],
                                         x["gencc_submission_id"], x["gencc_version"]))),
        "gencc_classification_submitter_143.tsv": (SUBMITTER_COLUMNS, submitters),
        "hpo_unmatched_without_gencc.tsv": (GENE_COLUMNS, [
            x for x in summary if not int(x["gencc_submission_count"])
        ]),
    }
    for name, (fields, rows) in files.items():
        write_tsv(out / name, rows, fields)
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (out / "SHA256SUMS.txt").open("w", encoding="utf-8") as f:
        for name in (*files, "manifest.json"):
            f.write(f"{sha256(out / name)}  {name}\n")
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry", type=Path, required=True)
    p.add_argument("--gap-dir", type=Path, required=True)
    p.add_argument("--gencc", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(census(args.registry, args.gap_dir, args.gencc, args.out),
                     indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
