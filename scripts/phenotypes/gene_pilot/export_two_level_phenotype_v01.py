#!/usr/bin/env python3
"""Create a non-destructive two-level HPOA evidence and G2P discovery view.

Source claims retain the HPOA disease subject. Gene projections are discovery
indexes, never direct gene-disruption phenotype assertions or accepted PARs.
"""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

PROFILE = "hpoa_disease_subject_two_level_v01"
POSITIVE_FREQUENCY_TERMS = {f"HP:004028{i}" for i in range(5)}
EXCLUDED = "HP:0040285"
INPUTS = ("manifest.json", "par_candidates.tsv", "par_evidence.tsv",
          "source_discovery_links.tsv", "disease_context.tsv", "gene_coverage.tsv")
EVIDENCE_SOURCE_FIELDS = (
    "candidate_id", "evidence_id", "source_resource", "source_release",
    "source_row_id", "original_subject", "original_predicate", "original_object",
    "source_evidence_code", "original_reference", "primary_publication_id",
    "evidence_role", "frequency", "qualifier", "aspect", "onset", "sex",
    "modifier", "source_lineage_key",
)
DISCOVERY_SOURCE_FIELDS = (
    "candidate_id", "gene_id", "gene_symbol", "disease_id", "phenotype_id",
    "source_resource", "source_release", "source_row_id", "original_subject",
    "original_object", "evidence_role",
)
CLAIM_COLS = ("source_claim_id", "disease_id", "predicate", "phenotype_id",
              "claim_polarity", "source_claim_scope", "original_evidence_links",
              "distinct_original_hpoa_rows", "distinct_source_lineages")
PROJECTION_COLS = ("projection_id", "gene_id", "gene_symbol", "disruption_type",
                   "disease_id", "phenotype_id", "source_claim_id", "claim_polarity",
                   "projection_role", "legacy_candidate_count", "legacy_candidate_ids",
                   "hpoa_evidence_links", "g2p_discovery_links")
EVIDENCE_COLS = EVIDENCE_SOURCE_FIELDS + (
    "projection_id", "source_claim_id", "claim_polarity", "polarity_basis",
    "evidence_outcome", "frequency_numerator", "frequency_denominator",
    "frequency_percent", "categorical_frequency_term",
)
DISCOVERY_COLS = DISCOVERY_SOURCE_FIELDS + ("projection_id", "source_claim_id")
MAP_COLS = ("legacy_candidate_id", "legacy_candidate_state", "projection_id",
            "source_claim_id", "source_evidence_count", "discovery_link_count")
NAMESPACE_COLS = ("namespace", "legacy_candidates", "projections",
                  "not_negated_projections", "negated_projections", "unresolved_projections",
                  "source_evidence_links", "categorical_positive_observations",
                  "observed_zero_observations", "frequency_unreported_observations",
                  "unclassified_frequency_observations")


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def stable(prefix, *parts):
    value = json.dumps(parts, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return prefix + hashlib.sha256(value).hexdigest()[:24]


def checked_sources(folder, names):
    entries = {}
    with (folder / "SHA256SUMS.txt").open(encoding="utf-8") as f:
        for raw in f:
            pieces = raw.strip().split(None, 1)
            if len(pieces) != 2:
                raise ValueError("Malformed input checksum row")
            digest, name = pieces
            if Path(name).name != name or name in entries:
                raise ValueError("Invalid checksum filename")
            entries[name] = digest
    for name in names:
        if name not in entries or sha256(folder / name) != entries[name]:
            raise ValueError(f"Missing or altered input: {folder / name}")


def records(path, required):
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        missing = set(required) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"Missing columns in {path}: {sorted(missing)}")
        yield from reader


def write_rows(path, columns, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, delimiter="\t",
                                extrasaction="raise", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def interpret(row):
    """Keep claim negation separate from the frequency observation outcome."""
    qualifier = (row.get("qualifier") or "").strip().upper()
    freq = (row.get("frequency") or "").strip()
    if qualifier == "NOT":
        claim, basis = "negated", "NOT_qualifier"
    elif qualifier:
        claim, basis = "unresolved", "unrecognized_qualifier"
    elif freq == EXCLUDED:
        claim, basis = "negated", "HPO_excluded_frequency_term"
    else:
        claim, basis = "not_negated", "no_source_negation"
    observed = {"evidence_outcome": "frequency_unreported",
                "frequency_numerator": "", "frequency_denominator": "",
                "frequency_percent": "", "categorical_frequency_term": ""}
    if not freq:
        pass
    elif freq in POSITIVE_FREQUENCY_TERMS:
        observed.update(evidence_outcome="categorical_positive",
                        categorical_frequency_term=freq)
    elif freq == EXCLUDED:
        observed.update(evidence_outcome="categorical_excluded",
                        categorical_frequency_term=freq)
    elif re.fullmatch(r"[0-9]+/[1-9][0-9]*", freq):
        numerator, denominator = map(int, freq.split("/"))
        observed.update(frequency_numerator=str(numerator),
                        frequency_denominator=str(denominator),
                        evidence_outcome=("observed_positive" if 0 < numerator <= denominator
                                          else "observed_zero" if numerator == 0
                                          else "unclassified_frequency"))
    elif re.fullmatch(r"(?:[0-9]+(?:\.[0-9]+)?)%", freq):
        number = float(freq[:-1])
        observed.update(frequency_percent=freq[:-1],
                        evidence_outcome=("observed_zero" if number == 0 else
                                          "observed_positive" if number <= 100 else
                                          "unclassified_frequency"))
    else:
        observed["evidence_outcome"] = "unclassified_frequency"
    return claim, basis, observed


def namespace(disease_id):
    return disease_id.split(":", 1)[0] if ":" in disease_id else "UNNAMESPACED"


def export(candidate_dir, audit_dir, out):
    candidate_dir, audit_dir, out = Path(candidate_dir), Path(audit_dir), Path(out)
    if out.exists():
        raise ValueError("Output path exists; use a new versioned output directory")
    checked_sources(candidate_dir, INPUTS)
    checked_sources(audit_dir, ("audit_manifest.json",))
    original = json.loads((candidate_dir / "manifest.json").read_text())
    audit = json.loads((audit_dir / "audit_manifest.json").read_text())
    if (original.get("status") != "provisional_internal_candidates" or
            original.get("reference_release") != "HPO:v2026-09-01" or
            not audit.get("gate_passed") or
            not audit.get("source_record_conservation_passed") or
            audit.get("producer_manifest_sha256") != sha256(candidate_dir / "manifest.json")):
        raise ValueError("Unverified or unexpected upstream source export")
    candidates = {}
    for r in records(candidate_dir / "par_candidates.tsv",
                     ("candidate_id", "gene_id", "gene_symbol", "disruption_type",
                      "phenotype_id", "disease_id", "assertion_state", "evidence_count")):
        key = r["candidate_id"]
        if key in candidates:
            raise ValueError("Duplicate legacy candidate ID")
        candidates[key] = r
    if len(candidates) != original["candidate_count"] or len(candidates) != audit["original_candidate_count"]:
        raise ValueError("Legacy candidate count inconsistent")

    source_claims = {}
    projections = {}
    legacy_projection_ids = defaultdict(set)
    evidence_counts = Counter()
    observation_rows = []
    observation_keys = set()
    claim_original_rows = defaultdict(set)
    claim_lineages = defaultdict(set)
    nspace_evidence = defaultdict(Counter)
    for e in records(candidate_dir / "par_evidence.tsv", EVIDENCE_SOURCE_FIELDS):
        cid = e["candidate_id"]
        c = candidates.get(cid)
        if c is None or (e["original_subject"] != c["disease_id"] or
                          e["original_object"] != c["phenotype_id"] or
                          e["original_predicate"] != "has_phenotype" or
                          e["evidence_role"] != "disease_phenotype_annotation" or
                          e["aspect"] != "P" or e["source_resource"] != "HPOA"):
            raise ValueError(f"Altered disease subject or evidence role: {cid}")
        if e["evidence_id"] in observation_keys:
            raise ValueError("Repeated original evidence ID")
        observation_keys.add(e["evidence_id"])
        claim, basis, outcome = interpret(e)
        source_id = stable("dmpdsrc1:", PROFILE, e["original_subject"],
                           e["original_predicate"], e["original_object"], claim)
        projection_id = stable("dmpview1:", PROFILE, c["gene_id"], c["disruption_type"],
                               c["disease_id"], c["phenotype_id"], claim)
        source_claims[source_id] = (e["original_subject"], e["original_object"], claim)
        projection_tuple = (c["gene_id"], c["gene_symbol"], c["disruption_type"],
                            c["disease_id"], c["phenotype_id"], source_id, claim)
        if projection_id in projections and projections[projection_id] != projection_tuple:
            raise ValueError("Provisional projection ID collision")
        projections[projection_id] = projection_tuple
        legacy_projection_ids[cid].add((projection_id, source_id))
        evidence_counts[cid] += 1
        claim_original_rows[source_id].add(e["source_row_id"])
        claim_lineages[source_id].add(e["source_lineage_key"])
        nspace_evidence[namespace(c["disease_id"])][outcome["evidence_outcome"]] += 1
        observation_rows.append({**{name: e[name] for name in EVIDENCE_SOURCE_FIELDS},
                                 "projection_id": projection_id,
                                 "source_claim_id": source_id,
                                 "claim_polarity": claim, "polarity_basis": basis, **outcome})
    if len(observation_rows) != original["hpoa_evidence_records"]:
        raise ValueError("Original HPOA evidence row count changed")
    for cid, c in candidates.items():
        if evidence_counts[cid] != int(c["evidence_count"]):
            raise ValueError("Legacy candidate evidence count changed")
        if len(legacy_projection_ids[cid]) != 1:
            raise ValueError("Legacy candidate maps to multiple curator-level claim polarities")

    legacy_map = {}
    for cid, c in sorted(candidates.items()):
        projection_id, source_id = next(iter(legacy_projection_ids[cid]))
        legacy_map[cid] = (projection_id, source_id)
    discovery_counts = Counter()
    discovery_rows = []
    for d in records(candidate_dir / "source_discovery_links.tsv", DISCOVERY_SOURCE_FIELDS):
        cid = d["candidate_id"]
        if cid not in legacy_map:
            raise ValueError("Unmapped G2P discovery link")
        c = candidates[cid]
        for x in ("gene_id", "gene_symbol", "disease_id", "phenotype_id"):
            if d[x] != c[x]:
                raise ValueError(f"G2P discovery field altered: {x}")
        if (d["evidence_role"] != "disease_mediated_discovery_only" or
                d["original_subject"] != c["gene_id"] or
                d["original_object"] != c["phenotype_id"]):
            raise ValueError("G2P discovery source role altered")
        projection_id, source_id = legacy_map[cid]
        discovery_counts[cid] += 1
        discovery_rows.append({**{name: d[name] for name in DISCOVERY_SOURCE_FIELDS},
                               "projection_id": projection_id,
                               "source_claim_id": source_id})
    if len(discovery_rows) != original["g2p_discovery_records"]:
        raise ValueError("Original discovery link count changed")

    members = defaultdict(set)
    projection_evidence = Counter()
    projection_discovery = Counter()
    claim_evidence = Counter()
    for cid, (pid, source_id) in legacy_map.items():
        members[pid].add(cid)
        projection_evidence[pid] += evidence_counts[cid]
        projection_discovery[pid] += discovery_counts[cid]
        claim_evidence[source_id] += evidence_counts[cid]
    claims_output = []
    for source_id, (disease, phenotype, claim) in sorted(source_claims.items()):
        claims_output.append(dict(source_claim_id=source_id, disease_id=disease,
            predicate="has_phenotype", phenotype_id=phenotype, claim_polarity=claim,
            source_claim_scope="original_HPOA_disease_phenotype",
            original_evidence_links=claim_evidence[source_id],
            distinct_original_hpoa_rows=len(claim_original_rows[source_id]),
            distinct_source_lineages=len(claim_lineages[source_id])))
    projection_output = []
    summary = defaultdict(Counter)
    for pid, (gene_id, symbol, disruption, disease, phenotype, source_id, claim) in sorted(projections.items()):
        ns = namespace(disease)
        summary[ns]["projections"] += 1
        summary[ns][claim + "_projections"] += 1
        projection_output.append(dict(projection_id=pid, gene_id=gene_id,
            gene_symbol=symbol, disruption_type=disruption, disease_id=disease,
            phenotype_id=phenotype, source_claim_id=source_id, claim_polarity=claim,
            projection_role="disease_mediated_discovery_only",
            legacy_candidate_count=len(members[pid]),
            legacy_candidate_ids=";".join(sorted(members[pid])),
            hpoa_evidence_links=projection_evidence[pid],
            g2p_discovery_links=projection_discovery[pid]))
    for c in candidates.values():
        summary[namespace(c["disease_id"])]["legacy_candidates"] += 1
    namespaces = []
    for ns in sorted(summary):
        v = summary[ns]
        ec = nspace_evidence[ns]
        namespaces.append(dict(namespace=ns, legacy_candidates=v["legacy_candidates"],
            projections=v["projections"], not_negated_projections=v["not_negated_projections"],
            negated_projections=v["negated_projections"],
            unresolved_projections=v["unresolved_projections"],
            source_evidence_links=sum(ec.values()),
            categorical_positive_observations=ec["categorical_positive"],
            observed_zero_observations=ec["observed_zero"],
            frequency_unreported_observations=ec["frequency_unreported"],
            unclassified_frequency_observations=ec["unclassified_frequency"]))
    mapping_output = [dict(legacy_candidate_id=cid,
        legacy_candidate_state=candidates[cid]["assertion_state"],
        projection_id=legacy_map[cid][0], source_claim_id=legacy_map[cid][1],
        source_evidence_count=evidence_counts[cid],
        discovery_link_count=discovery_counts[cid]) for cid in sorted(candidates)]
    outputs = {
        "original_disease_phenotype_claims.tsv": (CLAIM_COLS, claims_output),
        "gene_disease_hpo_discovery_projections.tsv": (PROJECTION_COLS, projection_output),
        "original_hpoa_observations.tsv": (EVIDENCE_COLS, observation_rows),
        "original_g2p_discovery_links.tsv": (DISCOVERY_COLS, discovery_rows),
        "legacy_candidate_projection_map.tsv": (MAP_COLS, mapping_output),
        "namespace_summary.tsv": (NAMESPACE_COLS, namespaces),
    }
    counter = Counter(e["evidence_outcome"] for e in observation_rows)
    negation_bases = Counter(e["polarity_basis"] for e in observation_rows)
    conflicts = defaultdict(set)
    for claim in claims_output:
        conflicts[(claim["disease_id"], claim["phenotype_id"])].add(claim["claim_polarity"])
    conflict_count = sum("negated" in states and "not_negated" in states for states in conflicts.values())
    if sum(int(p["hpoa_evidence_links"]) for p in projection_output) != len(observation_rows):
        raise ValueError("Projected evidence link conservation failed")
    if sum(int(p["g2p_discovery_links"]) for p in projection_output) != len(discovery_rows):
        raise ValueError("Projected discovery link conservation failed")
    manifest = {
        "status": "provisional_source_scope_discovery_view",
        "identity_profile": PROFILE,
        "identity_state": "internal_view_only_pending_PAR_Core_user_decision",
        "source_claim_identity_fields": ["original_disease_subject", "has_phenotype", "HPO_ID", "curator_negation"],
        "gene_projection_identity_fields": ["HGNC_ID", "disruption_unspecified", "disease_id", "HPO_ID", "curator_negation"],
        "legacy_candidate_count": len(candidates),
        "provisional_projection_count": len(projection_output),
        "legacy_identity_splits_collapsed": len(candidates) - len(projection_output),
        "distinct_original_disease_phenotype_source_claims": len(claims_output),
        "original_evidence_link_count": len(observation_rows),
        "distinct_original_hpoa_source_rows": len({e["source_row_id"] for e in observation_rows}),
        "original_discovery_link_count": len(discovery_rows),
        "evidence_outcome_counts": dict(sorted(counter.items())),
        "claim_polarity_bases": dict(sorted(negation_bases.items())),
        "not_negated_negated_source_claim_key_conflicts": conflict_count,
        "unclassified_frequency_rows": counter["unclassified_frequency"],
        "unresolved_claim_qualifier_rows": negation_bases["unrecognized_qualifier"],
        "by_namespace": {r["namespace"]: r for r in namespaces},
        "source_candidate_manifest_sha256": sha256(candidate_dir / "manifest.json"),
        "source_integrity_audit_sha256": sha256(audit_dir / "audit_manifest.json"),
        "input_source_sha256": original.get("hpo_source_sha256"),
        "input_rows_conserved_from_prior_gate": audit.get("four_fate_conservation"),
        "original_disease_subject_retained": True,
        "direct_gene_phenotype_assertions_promoted": 0,
        "release_authorized": False,
        "warning": "Source claims and gene projections are provisional views. No accepted direct phenotype PARs are minted.",
    }
    out.mkdir(parents=True)
    for name, (columns, data) in outputs.items():
        write_rows(out / name, columns, data)
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with (out / "SHA256SUMS.txt").open("w", encoding="utf-8") as f:
        for name in (*outputs, "manifest.json"):
            f.write(f"{sha256(out / name)}  {name}\n")
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate-dir", type=Path, required=True)
    p.add_argument("--integrity-dir", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(export(a.candidate_dir, a.integrity_dir, a.out), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
