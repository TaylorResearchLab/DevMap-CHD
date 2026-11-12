#!/usr/bin/env python3
"""STENOSIS-001 v02 reporting correction; preserve frozen v01 counts and outputs.

Add HPOA aspect-C disease onset context without attributing it to an individual
phenotype or patient. Expose original source evidence codes for review examples.
This is a read-only refinement of the checksum-verified v01 results.
"""
from __future__ import annotations
import argparse
import csv
import json
import shutil
import subprocess
import zipfile
from collections import defaultdict
from pathlib import Path

from structural_coverage_stenosis_v01 import (
    PINNED, RELEASE, digest, parse_obo, read_tsv, write_tsv,
    verify_manifest as verify_two_level_manifest,
)

ORIGINAL = "STENOSIS-001_structural_coverage_v01"
IDENTITY = "STENOSIS-001_reporting_refinement_v02"
COLS = ("disease_id", "source_row_id", "hpo_id", "hpo_label", "reference",
        "evidence", "primary_publication_id", "aspect",
        "source_scope", "hpo_release")


def verify_checksum_folder(folder, names):
    folder = Path(folder)
    found = {}
    with (folder / "SHA256SUMS.txt").open(encoding="utf-8") as handle:
        for line in handle:
            parts = line.split(None, 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid checksum line in {folder}")
            checksum, basename = parts
            basename = basename.strip().lstrip("*")
            if Path(basename).name != basename or basename in found:
                raise ValueError("Unexpected checksum path or duplicate")
            found[basename] = checksum
    if not set(names).issubset(found):
        raise ValueError(f"Missing required checksums in {folder}: "
                             f"{sorted(set(names) - set(found))}")
    for name in names:
        if digest(folder / name) != found[name]:
            raise ValueError(f"Source checksum mismatch: {folder / name}")
    return {n: found[n] for n in names}


def write_review_zip(folder, members):
    target = folder / "STENOSIS-001_review_v02.zip"
    with zipfile.ZipFile(target, mode="w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=9) as archive:
        for filename in members:
            info = zipfile.ZipInfo(filename, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            archive.writestr(info, (folder / filename).read_bytes(),
                             compress_type=zipfile.ZIP_DEFLATED,
                             compresslevel=9)
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None:
            raise ValueError("Invalid review archive")
    (folder / "review_bundle.sha256").write_text(
        f"{digest(target)}  {target.name}\n", encoding="utf-8")


def refine(original, candidate, obo, out, *, strict=True, commit=None):
    original, candidate, obo, out = (Path(x) for x in
                                     (original, candidate, obo, out))
    if out.exists():
        raise FileExistsError(f"Versioned output path exists: {out}")
    needed = ("manifest.json", "coverage_summary.tsv",
              "exception_decisions.tsv", "source_examples.tsv",
              "selected_original_hpoa_observations.tsv",
              "selected_gene_disease_hpo_projections.tsv")
    original_hashes = verify_checksum_folder(original, needed)
    manifest = json.loads((original / "manifest.json").read_text())
    if (manifest.get("analysis") != ORIGINAL or
        manifest.get("frozen_registry_genes") != 662 or
        (strict and manifest.get("input_sha256") != PINNED)):
        raise ValueError("v01 source profile/release/registry inconsistent")
    context_hashes = verify_checksum_folder(
        candidate, ("manifest.json", "disease_context.tsv"))
    candidate_manifest = json.loads((candidate / "manifest.json").read_text())
    if candidate_manifest.get("reference_release") != f"HPO:{RELEASE}":
        raise ValueError("Unexpected upstream HPOA release")
    if strict and digest(obo) != PINNED["hp_obo"]:
        raise ValueError("Pinned HPO ontology checksum mismatch")
    terms, alt = parse_obo(obo)
    projections = list(read_tsv(original /
                            "selected_gene_disease_hpo_projections.tsv",
                            {"projection_id", "disease_id",
                             "claim_polarity", "resolved_hpo_id"}))
    eligible = [p for p in projections
                if p["claim_polarity"] == "not_negated"]
    diseases = {p["disease_id"] for p in eligible}
    expected = manifest["output_counts"]["union"]["diseases"]
    if len(diseases) != expected:
        raise ValueError("Eligible union disease count differs from v01")
    selected = {p["projection_id"] for p in eligible}
    source_onset_rows = set()
    original_evidence = defaultdict(set)
    for e in read_tsv(original / "selected_original_hpoa_observations.tsv",
                      {"projection_id", "original_subject", "original_object",
                       "source_row_id", "source_evidence_code", "onset"}):
        if e["projection_id"] not in selected:
            continue
        key = (e["source_resource"], e["source_release"], e["source_row_id"])
        if not e["onset"].strip():
            source_onset_rows.add(key)
        exact = (e["original_subject"], e["original_object"], e["source_row_id"])
        original_evidence[exact].add(e["source_evidence_code"])
    expected_blank = manifest["union_source_rows_onset_unspecified"]
    if len(source_onset_rows) != expected_blank:
        raise ValueError("HPOA phenotype-row onset blank count differs from v01")

    disease_context = []
    by_disease = defaultdict(list)
    seen_context = set()
    for entry in read_tsv(candidate / "disease_context.tsv",
                          {"disease_id", "source_row_id", "aspect", "hpo_id",
                           "reference", "evidence", "primary_publication_id"}):
        if entry["aspect"] != "C" or entry["disease_id"] not in diseases:
            continue
        pair = (entry["disease_id"], entry["source_row_id"])
        if pair in seen_context:
            raise ValueError("Repeated disease onset source row")
        seen_context.add(pair)
        hp = alt.get(entry["hpo_id"], entry["hpo_id"])
        if hp not in terms or terms[hp].get("obsolete"):
            raise ValueError(f"Unresolved onset context term: {hp}")
        d = {
            **{k: entry[k] for k in
               ("disease_id", "source_row_id", "reference",
                "evidence", "primary_publication_id", "aspect")},
            "hpo_id": hp, "hpo_label": terms[hp]["name"],
            "source_scope": "original_HPOA_disease_onset_context",
            "hpo_release": RELEASE,
        }
        disease_context.append(d)
        by_disease[d["disease_id"]].append(d)
    disease_context.sort(key=lambda d: (d["disease_id"], d["source_row_id"]))
    disease_with_context = set(by_disease)
    congenital_ids = {
        d["disease_id"] for d in disease_context
        if d["hpo_label"] == "Congenital onset"
    }

    examples = []
    for row in read_tsv(original / "source_examples.tsv",
                        {"gene_symbol", "disease_id",
                         "original_hpo_id", "original_source_row"}):
        d = row["disease_id"]
        c = by_disease[d]
        key = (d, row["original_hpo_id"], row["original_source_row"])
        codes = sorted(original_evidence.get(key, set()))
        if row["source_scope"] == "HPOA_disease_phenotype_discovery" and not codes:
            raise ValueError("Example source evidence code missing")
        status = ("disease_level_C_onset_present" if c else
                  "no_disease_level_C_onset_in_pinned_context")
        examples.append({
            **row,
            "source_evidence_code": ";".join(codes),
            "phenotype_row_onset_column_status":
                ("reported" if row["source_onset"].strip() else "blank"),
            "disease_onset_annotation_status": status,
            "disease_onset_hpo_ids":
                ";".join(sorted({x["hpo_id"] for x in c})),
            "disease_onset_hpo_labels":
                ";".join(sorted({x["hpo_label"] for x in c})),
            "disease_onset_original_source_rows":
                ";".join(sorted({x["source_row_id"] for x in c})),
            "patient_specific_onset_asserted": "no",
        })

    summary = [
        {"metric": "eligible_union_diseases", "count": len(diseases),
         "unit": "distinct_disease_identifiers"},
        {"metric": "diseases_with_aspect_C_onset", "count": len(disease_with_context),
         "unit": "distinct_disease_identifiers"},
        {"metric": "diseases_with_congenital_onset_aspect_C",
         "count": len(congenital_ids), "unit": "distinct_disease_identifiers"},
        {"metric": "original_phenotype_source_rows_with_blank_onset_column",
         "count": len(source_onset_rows), "unit": "distinct_original_P_source_rows"},
        {"metric": "total_distinct_original_phenotype_source_rows",
         "count": manifest["output_counts"]["union"]["original_source_rows"],
         "unit": "distinct_original_P_source_rows"},
    ]
    out.mkdir(parents=True)
    shutil.copyfile(original / "coverage_summary.tsv", out / "coverage_summary.tsv")
    shutil.copyfile(original / "exception_decisions.tsv", out / "exception_decisions.tsv")
    write_tsv(out / "disease_onset_context.tsv", disease_context, COLS)
    write_tsv(out / "source_examples_v02.tsv", examples, tuple(examples[0]))
    write_tsv(out / "onset_summary.tsv", summary, ("metric", "count", "unit"))
    if commit is None:
        p = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                           text=True, check=False)
        commit = p.stdout.strip() if p.returncode == 0 else "not_available"
    latest = {
        "analysis": IDENTITY,
        "status": "Agent_1_reporting_corrections_pending_Agent_2_review",
        "parent_analysis": ORIGINAL,
        "parent_output_manifest_sha256": digest(original / "manifest.json"),
        "parent_file_sha256": original_hashes,
        "context_file_sha256": context_hashes,
        "pinned_hpo_sha256": digest(obo),
        "script_sha256": digest(Path(__file__)),
        "git_commit": commit,
        "frozen_genes": 662,
        "coverage_counts_unchanged_from_v01": True,
        "original_union_count": manifest["output_counts"]["union"],
        "original_row_onset_column_blank_count": len(source_onset_rows),
        "disease_level_onset_count": len(disease_with_context),
        "congenital_disease_level_onset_count": len(congenital_ids),
        "disease_onset_is_not_patient_or_phenotype_onset": True,
        "review_archive": "STENOSIS-001_review_v02.zip",
    }
    (out / "manifest.json").write_text(
        json.dumps(latest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    outputs = ("manifest.json", "coverage_summary.tsv", "exception_decisions.tsv",
               "source_examples_v02.tsv", "onset_summary.tsv",
               "disease_onset_context.tsv")
    (out / "SHA256SUMS.txt").write_text(
        "".join(f"{digest(out / n)}  {n}\n" for n in outputs),
        encoding="utf-8")
    review = outputs[:5]
    (out / "review_SHA256SUMS.txt").write_text(
        "".join(f"{digest(out / n)}  {n}\n" for n in review),
        encoding="utf-8")
    write_review_zip(out, (*review, "review_SHA256SUMS.txt"))
    return latest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, default=Path(
        "results/phenotypes/structural_coverage_stenosis_v01"))
    parser.add_argument("--candidate", type=Path, default=Path(
        "results/phenotypes/par_candidates_v02"))
    parser.add_argument("--obo", type=Path, default=Path(
        "scripts/phenotypes/gene_pilot/inputs/hp.obo"))
    parser.add_argument("--out", type=Path, default=Path(
        "results/phenotypes/structural_coverage_stenosis_reporting_v02"))
    args = parser.parse_args()
    result = refine(args.original, args.candidate, args.obo, args.out)
    print(json.dumps({
        "output": str(args.out),
        "counts": {
            "disease_onset": result["disease_level_onset_count"],
            "congenital_disease_onset":
                result["congenital_disease_level_onset_count"],
            "phenotype_row_onset_column_blank":
                result["original_row_onset_column_blank_count"],
        },
        "review_zip_sha256": (args.out / "review_bundle.sha256").read_text().strip(),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
