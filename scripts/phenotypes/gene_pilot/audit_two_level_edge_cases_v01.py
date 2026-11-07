#!/usr/bin/env python3
"""Read-only edge-case guard for the verified two-level HPO source view.

This guard never changes an identity or rewrites the v01 source export.
Unexpected source semantics are reported as review holds, not silently corrected.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from export_two_level_phenotype_v01 import (
    EVIDENCE_SOURCE_FIELDS, checked_sources, records, sha256, write_rows,
)

VIEW_INPUTS = (
    "original_disease_phenotype_claims.tsv",
    "gene_disease_hpo_discovery_projections.tsv",
    "original_hpoa_observations.tsv",
    "original_g2p_discovery_links.tsv",
    "legacy_candidate_projection_map.tsv",
    "namespace_summary.tsv", "manifest.json",
)
EDGE_COLUMNS = (
    "evidence_id", "source_row_id", "source_claim_id", "projection_id",
    "original_subject", "original_object", "qualifier", "frequency",
    "claim_polarity", "evidence_outcome", "issue",
)

def validate_four_fate_ledger(ledger, original_audit):
    if not isinstance(ledger, dict) or ledger != original_audit.get("four_fate_conservation"):
        raise ValueError("Missing or inconsistent four-fate ledger in manifest")
    for source in ("g2p", "hpoa"):
        fates = ledger.get(source)
        if not isinstance(fates, dict):
            raise ValueError("Missing original source fate set")
        if any(not isinstance(fates.get(k), int) or fates[k] < 0
               for k in ("emitted", "merged", "held", "failed")):
            raise ValueError("Missing or invalid four-fate counts")
        expected = original_audit.get("source_row_counts", {}).get(source)
        if expected is not None and sum(fates[k] for k in
                                        ("emitted", "merged", "held", "failed")) != expected:
            raise ValueError("Original source row fate count is not conserved")

def audit(view_dir, candidate_dir, integrity_dir, out):
    view_dir, candidate_dir = Path(view_dir), Path(candidate_dir)
    integrity_dir, out = Path(integrity_dir), Path(out)
    if out.exists():
        raise ValueError("Output path exists; use a new audit location")
    checked_sources(view_dir, VIEW_INPUTS)
    checked_sources(candidate_dir, ("manifest.json", "par_evidence.tsv"))
    checked_sources(integrity_dir, ("audit_manifest.json",))
    manifest = json.loads((view_dir / "manifest.json").read_text(encoding="utf-8"))
    prior = json.loads((integrity_dir / "audit_manifest.json").read_text(encoding="utf-8"))
    if (manifest.get("status") != "provisional_source_scope_discovery_view"
            or manifest.get("identity_profile") != "hpoa_disease_subject_two_level_v01"
            or manifest.get("source_candidate_manifest_sha256") != sha256(candidate_dir / "manifest.json")
            or manifest.get("source_integrity_audit_sha256") != sha256(integrity_dir / "audit_manifest.json")
            or not prior.get("gate_passed")):
        raise ValueError("View or integrity source manifest mismatch")
    # Required key, never .get. An absent/null ledger blocks the audit.
    if "input_rows_conserved_from_prior_gate" not in manifest:
        raise ValueError("Required input_rows_conserved_from_prior_gate field missing")
    validate_four_fate_ledger(manifest["input_rows_conserved_from_prior_gate"], prior)

    originals = {}
    for row in records(candidate_dir / "par_evidence.tsv", EVIDENCE_SOURCE_FIELDS):
        evidence_id = row["evidence_id"]
        if evidence_id in originals:
            raise ValueError("Duplicate original evidence ID")
        originals[evidence_id] = row
    required = EVIDENCE_SOURCE_FIELDS + (
        "source_claim_id", "projection_id", "claim_polarity",
        "evidence_outcome",
    )
    exceptions = []
    seen = set()
    counts = Counter()
    for row in records(view_dir / "original_hpoa_observations.tsv", required):
        eid = row["evidence_id"]
        if eid in seen:
            raise ValueError("Duplicate observed evidence ID")
        seen.add(eid)
        original = originals.get(eid)
        if original is None or any(row[k] != original[k] for k in EVIDENCE_SOURCE_FIELDS):
            raise ValueError("Original source evidence field or locator changed")
        freq = row["frequency"].strip()
        qualifier = row["qualifier"].strip().upper()
        flagged = []
        if qualifier == "NOT" and freq:
            flagged.append("NOT_with_reported_frequency")
        if freq == "0%":
            flagged.append("zero_percent_claim_polarity_policy_pending")
            if row["claim_polarity"] != "not_negated" or row["evidence_outcome"] != "observed_zero":
                raise ValueError("Unexpected v01 zero-percent interpretation")
        if freq == "HP:0040285":
            flagged.append("excluded_frequency_claim_polarity_policy_pending")
            if row["claim_polarity"] != "negated" or row["evidence_outcome"] != "categorical_excluded":
                raise ValueError("Unexpected v01 excluded-frequency interpretation")
        for issue in flagged:
            counts[issue] += 1
            exceptions.append({
                "evidence_id": eid, "source_row_id": row["source_row_id"],
                "source_claim_id": row["source_claim_id"],
                "projection_id": row["projection_id"],
                "original_subject": row["original_subject"],
                "original_object": row["original_object"],
                "qualifier": row["qualifier"], "frequency": row["frequency"],
                "claim_polarity": row["claim_polarity"],
                "evidence_outcome": row["evidence_outcome"], "issue": issue,
            })
    if len(seen) != len(originals) or len(seen) != manifest.get("original_evidence_link_count"):
        raise ValueError("Original evidence link conservation failure")
    out.mkdir(parents=True)
    exceptions.sort(key=lambda r: (r["issue"], r["source_row_id"], r["evidence_id"]))
    write_rows(out / "edge_case_source_rows.tsv", EDGE_COLUMNS, exceptions)
    result = {
        "audit_version": "two_level_hpo_edge_guard_v01",
        "status": "review_hold" if exceptions else "no_edge_cases_observed",
        "original_evidence_links_verified": len(seen),
        "not_with_frequency_rows": counts["NOT_with_reported_frequency"],
        "zero_percent_rows": counts["zero_percent_claim_polarity_policy_pending"],
        "excluded_frequency_rows": counts["excluded_frequency_claim_polarity_policy_pending"],
        "issue_count": len(exceptions),
        "source_fidelity_passed": True,
        "input_conservation_ledger_verified": True,
        "edge_cases_require_review": bool(exceptions),
        "original_view_manifest_sha256": sha256(view_dir / "manifest.json"),
        "original_candidate_manifest_sha256": sha256(candidate_dir / "manifest.json"),
        "claim_identity_unchanged": True,
        "direct_assertions_promoted": 0,
        "interpretation": (
            "Reports NOT plus frequency, 0%, and HP:0040285 as separate source "
            "semantics requiring a policy decision if encountered."
        ),
    }
    (out / "manifest.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (out / "SHA256SUMS.txt").open("w", encoding="utf-8") as handle:
        for name in ("edge_case_source_rows.tsv", "manifest.json"):
            handle.write(f"{sha256(out / name)}  {name}\n")
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--view-dir", type=Path, required=True)
    p.add_argument("--candidate-dir", type=Path, required=True)
    p.add_argument("--integrity-dir", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = audit(args.view_dir, args.candidate_dir, args.integrity_dir, args.out)
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["edge_cases_require_review"]:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
