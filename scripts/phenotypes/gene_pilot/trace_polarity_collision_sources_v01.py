#!/usr/bin/env python3
"""Trace legacy HPO polarity collisions to individual original HPOA annotations.

Read-only. Produces review tables for existing provisional disease-mediated
candidate IDs; neither rewrites the producer nor constructs direct PAR claims.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from audit_candidate_export_gate_v01 import verify_export
from export_gene_phenotype_par import checksum, polarity

SOURCE_FIELDS = (
    "group_index", "gene_id", "gene_symbol", "disease_id", "phenotype_id",
    "disruption_type", "candidate_id", "candidate_polarity",
    "evidence_id", "source_row_id", "source_resource", "source_release",
    "original_subject", "original_predicate", "original_object",
    "source_evidence_code", "original_reference", "primary_publication_id",
    "frequency", "qualifier", "onset", "sex", "modifier", "aspect",
    "source_lineage_key", "source_polarity_verified",
    "polarity_basis", "evidence_role",
)
GROUP_FIELDS = (
    "group_index", "gene_id", "gene_symbol", "disease_id", "phenotype_id",
    "disruption_type", "polarity_states", "candidate_count",
    "original_hpoa_evidence_rows", "distinct_original_hpoa_lines",
    "distinct_references", "pmid_bearing_evidence_rows", "source_absence_basis",
    "review_state",
)
REQUIRED_COLLISION_FIELDS = (
    "gene_id", "disruption_type", "phenotype_id", "disease_id",
    "polarity_states", "legacy_candidate_ids",
)

def tsv(path, required):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        missing = set(required).difference(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path}: missing {sorted(missing)}")
        yield from reader

def write_tsv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, delimiter="\t",
            extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)

def require_checksum_file(directory, names):
    hashes = {}
    for line in (directory / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        parts = line.split(None, 1)
        if len(parts) != 2:
            raise ValueError(f"Malformed SHA256SUMS line in {directory}")
        digest, name = parts[0], parts[1].strip()
        if Path(name).name != name or name in hashes:
            raise ValueError(f"Invalid checksum manifest name: {name}")
        hashes[name] = digest
    for name in names:
        if name not in hashes or checksum(directory / name) != hashes[name]:
            raise ValueError(f"Unverified audit source: {directory / name}")

def polarity_basis(row):
    freq = row.get("frequency", "").strip()
    qual = row.get("qualifier", "").strip().upper()
    state = polarity(row)
    if state == "asserted_absent":
        if qual == "NOT":
            return "explicit_NOT_qualifier"
        if freq in ("0%", "HP:0040285"):
            return "zero_frequency_value"
        if freq.startswith("0/"):
            return "zero_numerator"
        return "other_absent_rule"
    if state == "asserted_present":
        return "positive_frequency_value"
    if qual:
        return "non_NOT_qualifier_unresolved"
    if not freq:
        return "no_frequency_in_original_source_row"
    return "frequency_unresolved_by_legacy_profile"

def trace(candidate_dir, audit_dir, out):
    old = verify_export(candidate_dir)
    require_checksum_file(audit_dir, ("audit_manifest.json", "polarity_identity_collisions.tsv"))
    gate = json.loads((audit_dir / "audit_manifest.json").read_text(encoding="utf-8"))
    if not gate.get("gate_passed"):
        raise ValueError("Source conservation audit has not passed")
    if gate.get("producer_manifest_sha256") != checksum(candidate_dir / "manifest.json"):
        raise ValueError("Collision audit and source producer manifest disagree")

    candidates = {}
    for row in tsv(candidate_dir / "par_candidates.tsv",
                   ("candidate_id", "gene_id", "gene_symbol", "disease_id",
                    "phenotype_id", "disruption_type", "assertion_state")):
        cid = row["candidate_id"]
        if cid in candidates:
            raise ValueError(f"Duplicate candidate: {cid}")
        candidates[cid] = row

    collisions = list(tsv(audit_dir / "polarity_identity_collisions.tsv",
                          REQUIRED_COLLISION_FIELDS))
    if len(collisions) != gate["provisional_polarity_collisions_without_polarity"]:
        raise ValueError("Collision group count changed since source audit")
    selected_ids = set()
    groups = []
    for idx, row in enumerate(collisions, 1):
        ids = [v for v in row["legacy_candidate_ids"].split(";") if v]
        states = {v for v in row["polarity_states"].split(";") if v}
        if len(states) < 2 or len(ids) != len(states) or len(ids) != len(set(ids)):
            raise ValueError(f"Collision {idx}: candidate/state multiplicity mismatch")
        if set(ids) & selected_ids:
            raise ValueError("Candidate occurs in more than one collision group")
        observed_states = set()
        gene_symbol = None
        for cid in ids:
            candidate = candidates.get(cid)
            if candidate is None:
                raise ValueError(f"Collision {idx}: missing candidate {cid}")
            for field in ("gene_id", "disruption_type", "phenotype_id", "disease_id"):
                if candidate[field] != row[field]:
                    raise ValueError(f"Collision {idx}: mismatched {field}")
            if gene_symbol is None:
                gene_symbol = candidate["gene_symbol"]
            elif gene_symbol != candidate["gene_symbol"]:
                raise ValueError(f"Collision {idx}: inconsistent gene symbol")
            prefix = "disease_mediated_candidate_"
            if not candidate["assertion_state"].startswith(prefix):
                raise ValueError("Collision contains an unrecognized candidate state")
            observed_states.add(candidate["assertion_state"][len(prefix):])
        if observed_states != states:
            raise ValueError(f"Collision {idx}: stated polarity differs from candidates")
        groups.append((idx, row, ids, gene_symbol))
        selected_ids.update(ids)

    evidence_by_id = defaultdict(list)
    for e in tsv(candidate_dir / "par_evidence.tsv",
                 ("candidate_id", "evidence_id", "source_row_id",
                  "original_subject", "original_predicate", "original_object",
                  "evidence_role", "frequency", "qualifier", "aspect",
                  "source_evidence_code", "original_reference")):
        if e["candidate_id"] in selected_ids:
            evidence_by_id[e["candidate_id"]].append(e)

    evidence_rows = []
    group_rows = []
    missing_evidence_ids = []
    for idx, group, ids, gene_symbol in groups:
        group_evidence = []
        sources = set()
        distinct_refs = set()
        for cid in ids:
            c = candidates[cid]
            candidate_polarity = c["assertion_state"].removeprefix(
                "disease_mediated_candidate_"
            ) if hasattr(str, "removeprefix") else c["assertion_state"][len("disease_mediated_candidate_"):]
            if not evidence_by_id[cid]:
                missing_evidence_ids.append(cid)
            for e in evidence_by_id[cid]:
                observed = polarity(e)
                if observed != candidate_polarity:
                    raise ValueError(f"Source polarity mismatch for {cid} and {e['source_row_id']}")
                if (e["original_subject"] != group["disease_id"]
                        or e["original_object"] != group["phenotype_id"]
                        or e["original_predicate"] != "has_phenotype"
                        or e["evidence_role"] != "disease_phenotype_annotation"
                        or e["aspect"] != "P"):
                    raise ValueError(f"Source claim scope changed for {cid}")
                original_row = e["source_row_id"]
                sources.add(original_row)
                if e["original_reference"]:
                    distinct_refs.add(e["original_reference"])
                record = {
                    "group_index": idx, **{k: group[k] for k in (
                        "gene_id", "disease_id", "phenotype_id", "disruption_type")},
                    "gene_symbol": gene_symbol, "candidate_id": cid,
                    "candidate_polarity": candidate_polarity,
                    **e, "source_polarity_verified": observed,
                    "polarity_basis": polarity_basis(e),
                }
                group_evidence.append(record)
                evidence_rows.append(record)
        bases = sorted({r["polarity_basis"] for r in group_evidence
                        if r["candidate_polarity"] == "asserted_absent"})
        group_rows.append({
            "group_index": idx, "gene_id": group["gene_id"],
            "gene_symbol": gene_symbol, "disease_id": group["disease_id"],
            "phenotype_id": group["phenotype_id"],
            "disruption_type": group["disruption_type"],
            "polarity_states": group["polarity_states"],
            "candidate_count": len(ids),
            "original_hpoa_evidence_rows": len(group_evidence),
            "distinct_original_hpoa_lines": len(sources),
            "distinct_references": len(distinct_refs),
            "pmid_bearing_evidence_rows": sum(bool(r.get("primary_publication_id"))
                                              for r in group_evidence),
            "source_absence_basis": ";".join(bases),
            "review_state": "source_context_pending_independent_interpretation",
        })
    if missing_evidence_ids:
        raise ValueError(f"Missing original HPOA evidence for {len(missing_evidence_ids)} candidates")

    out.mkdir(parents=True, exist_ok=True)
    outputs = {
        "polarity_collision_source_rows.tsv": (SOURCE_FIELDS, evidence_rows),
        "polarity_collision_group_summary.tsv": (GROUP_FIELDS, group_rows),
    }
    for name, (fields, records) in outputs.items():
        write_tsv(out / name, fields, records)
    manifest = {
        "status": "read_only_source_evidence_extracted_pending_secondary_review",
        "source_audit_gate_passed": True,
        "group_count": len(groups), "candidate_count": len(selected_ids),
        "evidence_row_count": len(evidence_rows),
        "groups_with_absent_and_present": sum(
            set(row["polarity_states"].split(";")) == {"asserted_present", "asserted_absent"}
            for row in collisions),
        "groups_with_present_and_unspecified": sum(
            set(row["polarity_states"].split(";")) == {"asserted_present", "unspecified"}
            for row in collisions),
        "groups_with_all_three_states": sum(
            len(row["polarity_states"].split(";")) == 3 for row in collisions),
        "source_candidate_manifest_sha256": checksum(candidate_dir / "manifest.json"),
        "source_audit_manifest_sha256": checksum(audit_dir / "audit_manifest.json"),
        "original_hpoa_source_subject": "disease_CURIE",
        "direct_gene_phenotype_claims_accepted": 0,
        "interpretation": "Legacy polarity differences are annotation-level observations. Patient or cohort context and PAR Core identity policy require independent review.",
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    with (out / "SHA256SUMS.txt").open("w", encoding="utf-8") as handle:
        for name in (*outputs, "manifest.json"):
            handle.write(f"{checksum(out / name)}  {name}\n")
    return manifest

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-dir", required=True, type=Path)
    parser.add_argument("--audit-dir", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(trace(args.candidate_dir, args.audit_dir, args.out), indent=2))

if __name__ == "__main__":
    main()
