#!/usr/bin/env python3
"""Audit frozen HPO source-to-discovery conservation without changing candidate IDs.

The producer's gene-subject IDs are legacy provisional discovery identifiers.
This audit is a read-only companion to an existing par_candidates_v02 output.
It does not create, revise, promote, or accept any direct phenotype assertion.
"""
import argparse
import csv
import hashlib
import inspect
import json
from collections import Counter, defaultdict
from pathlib import Path

from export_gene_phenotype_par import (
    G2P_SHA, HPOA_SHA, checksum, polarity, source_rows, stable_id,
)

G2P_REQUIRED = ("gene_symbol", "hpo_id", "disease_id")
HPOA_REQUIRED = (
    "database_id", "hpo_id", "aspect", "frequency",
    "qualifier", "reference", "evidence",
)
EXPORT_FILES = (
    "manifest.json", "par_candidates.tsv", "par_evidence.tsv",
    "source_discovery_links.tsv", "disease_context.tsv", "gene_coverage.tsv",
)
LEDGER_COLUMNS = (
    "source_row_id", "original_subject", "original_object", "disease_id",
    "aspect", "fate", "reason", "linked_candidate_count",
)
COVERAGE_COLUMNS = (
    "gene_id", "gene_symbol", "candidate_count", "source_g2p_rows",
    "coverage_state_v2",
)
DISEASE_COLUMNS = (
    "disease_id", "hpoa_p_rows", "context_C_rows", "context_I_rows",
    "context_M_rows", "context_H_rows", "p_rows_with_onset",
    "onset_source_state",
)
IDENTITY_COLUMNS = (
    "gene_id", "disruption_type", "phenotype_id", "disease_id",
    "polarity_states", "legacy_candidate_ids",
)

def rows(path, fields):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        missing = set(fields) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"{path}: missing columns {sorted(missing)}")
        yield from reader

def write_rows(path, fields, values):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=fields, delimiter="\t",
            extrasaction="ignore", lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(values)

def verify_export(directory):
    sums = {}
    for line in (directory / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        fields = line.split(None, 1)
        if len(fields) != 2:
            raise ValueError("Malformed exporter checksum line")
        digest, name = fields
        name = name.strip()
        if Path(name).name != name or name in sums:
            raise ValueError("Unsafe or duplicate exporter checksum name")
        sums[name] = digest
    for name in EXPORT_FILES:
        if name not in sums or checksum(directory / name) != sums[name]:
            raise ValueError(f"Exporter source custody check failed for {name}")
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("status") != "provisional_internal_candidates":
        raise ValueError("Expected provisional HPO discovery output")
    return manifest

def source_record_id(filename, line):
    return f"{filename}:{line}"

def audit(registry, g2p, hpoa, candidate_dir, out, skip_source_sha=False):
    old = verify_export(candidate_dir)
    hashes = {
        "genes_to_phenotype.txt": checksum(g2p),
        "phenotype.hpoa": checksum(hpoa),
    }
    if not skip_source_sha and (
        hashes["genes_to_phenotype.txt"] != G2P_SHA
        or hashes["phenotype.hpoa"] != HPOA_SHA
    ):
        raise ValueError("Pinned HPO source checksums differ")
    if hashes != old.get("hpo_source_sha256"):
        raise ValueError("Source checksums differ from original exporter manifest")
    genes = [r for _, r in source_rows(registry, ("hgnc_id", "approved_hgnc_symbol"))]
    symbols = {r["approved_hgnc_symbol"]: r["hgnc_id"] for r in genes}
    ids = {r["hgnc_id"] for r in genes}
    if len(genes) != 662 or len(symbols) != 662 or len(ids) != 662:
        raise ValueError("Registry integrity violation: expected 662 unique genes")

    candidates = list(rows(candidate_dir / "par_candidates.tsv",
                           ("candidate_id", "gene_id", "gene_symbol",
                            "disruption_type", "phenotype_id", "disease_id",
                            "assertion_state")))
    candidate_ids = {r["candidate_id"] for r in candidates}
    if len(candidate_ids) != len(candidates) or len(candidates) != old["candidate_count"]:
        raise ValueError("Duplicate or missing provisional candidates")
    legacy_identity_errors = []
    identities = defaultdict(lambda: defaultdict(set))
    for r in candidates:
        state_prefix = "disease_mediated_candidate_"
        if not r["assertion_state"].startswith(state_prefix):
            legacy_identity_errors.append(r["candidate_id"])
            continue
        state = r["assertion_state"][len(state_prefix):]
        if state not in ("asserted_present", "asserted_absent", "unspecified"):
            legacy_identity_errors.append(r["candidate_id"])
            continue
        expected = stable_id("dmpcand:", r["gene_id"], r["disruption_type"],
                             r["phenotype_id"], r["disease_id"], state)
        if (r["candidate_id"] != expected or r["gene_id"] not in ids
                or symbols.get(r["gene_symbol"]) != r["gene_id"]):
            legacy_identity_errors.append(r["candidate_id"])
        key = (r["gene_id"], r["disruption_type"], r["phenotype_id"], r["disease_id"])
        identities[key][state].add(r["candidate_id"])

    discovery_links = defaultdict(set)
    for r in rows(candidate_dir / "source_discovery_links.tsv",
                  ("source_row_id", "candidate_id", "original_subject",
                   "original_object", "evidence_role")):
        if r["candidate_id"] not in candidate_ids:
            raise ValueError("Discovery link references unknown candidate")
        if r["evidence_role"] != "disease_mediated_discovery_only":
            raise ValueError("Discovery link incorrectly labelled as direct evidence")
        discovery_links[r["source_row_id"]].add(r["candidate_id"])
    evidence_links = defaultdict(set)
    for r in rows(candidate_dir / "par_evidence.tsv",
                  ("source_row_id", "candidate_id", "original_subject",
                   "original_object", "evidence_role")):
        if r["candidate_id"] not in candidate_ids:
            raise ValueError("Evidence references unknown candidate")
        if r["evidence_role"] != "disease_phenotype_annotation":
            raise ValueError("Original HPOA evidence role changed")
        evidence_links[r["source_row_id"]].add(
            (r["candidate_id"], r["original_subject"], r["original_object"])
        )
    context_lines = set()
    for r in rows(candidate_dir / "disease_context.tsv", ("source_row_id", "disease_id", "aspect")):
        if r["source_row_id"] in context_lines:
            raise ValueError("Repeated disease context source row")
        context_lines.add(r["source_row_id"])

    g2p_input = list(source_rows(g2p, G2P_REQUIRED))
    hpoa_input = list(source_rows(hpoa, HPOA_REQUIRED))
    exact_g2p = defaultdict(set)
    g2p_counts = Counter()
    g2p_loci = set()
    for line, r in g2p_input:
        locus = source_record_id("genes_to_phenotype.txt", line)
        g2p_loci.add(locus)
        gene = symbols.get(r["gene_symbol"])
        if gene and r["hpo_id"].startswith("HP:") and r["disease_id"]:
            exact_g2p[(r["disease_id"], r["hpo_id"])].add(gene)
            g2p_counts[gene] += 1

    participating_diseases = {key[0] for key in exact_g2p}
    expected_evidence = defaultdict(set)
    expected_discovery = defaultdict(set)
    expected_candidates = set()
    hpoa_ledger = []
    disease_counts = defaultdict(Counter)
    for line, r in hpoa_input:
        locus = source_record_id("phenotype.hpoa", line)
        disease, hpo, aspect = r["database_id"], r["hpo_id"], r["aspect"]
        found_genes = exact_g2p.get((disease, hpo), set())
        expected = set()
        if aspect == "P" and found_genes:
            state = polarity(r)
            expected = {
                stable_id("dmpcand:", gene, "unspecified_disruption", hpo, disease, state)
                for gene in found_genes
            }
            expected_candidates.update(expected)
            for gene in found_genes:
                expected_discovery[(gene, disease, hpo)].add(
                    stable_id("dmpcand:", gene, "unspecified_disruption", hpo, disease, state)
                )
            expected_evidence[locus] = {(cid, disease, hpo) for cid in expected}
        if disease in participating_diseases:
            dc = disease_counts[disease]
            dc[f"aspect_{aspect}"] += 1
            if aspect == "P" and r.get("onset", "").strip():
                dc["p_with_onset"] += 1
        observed = evidence_links.get(locus, set())
        if expected:
            fate = "emitted" if expected_evidence[locus] == observed else "failed"
            reason = "hpoa_disease_phenotype_projection" if fate == "emitted" else "source_projection_mismatch"
        elif disease not in participating_diseases:
            fate, reason = "held", "disease_outside_exact_g2p_scope"
        elif aspect in ("C", "I", "M", "H"):
            fate = "emitted" if locus in context_lines else "failed"
            reason = "original_disease_context" if fate == "emitted" else "missing_context_row"
        else:
            fate, reason = "held", "no_gene_hpo_projection_or_nonphenotype_aspect"
        if observed and not expected:
            fate, reason = "failed", "unjustified_hpoa_evidence_projection"
        hpoa_ledger.append({
            "source_row_id": locus, "original_subject": disease,
            "original_object": hpo, "disease_id": disease, "aspect": aspect,
            "fate": fate, "reason": reason,
            "linked_candidate_count": len(observed),
        })

    g2p_ledger = []
    for line, r in g2p_input:
        locus = source_record_id("genes_to_phenotype.txt", line)
        gene = symbols.get(r["gene_symbol"])
        actual = discovery_links.get(locus, set())
        if not r["hpo_id"].startswith("HP:") or not r["disease_id"]:
            fate, reason = "failed", "malformed_discovery_key"
        elif gene is None:
            fate, reason = "held", "outside_exact_frozen_symbol_scope_alias_unresolved"
        else:
            expected = expected_discovery.get((gene, r["disease_id"], r["hpo_id"]), set())
            if expected != actual:
                fate, reason = "failed", "discovery_link_mismatch"
            elif expected:
                fate, reason = "emitted", "disease_mediated_discovery_only"
            else:
                fate, reason = "held", "no_exact_hpoa_P_observation"
        if actual and fate == "held":
            fate, reason = "failed", "unjustified_discovery_projection"
        g2p_ledger.append({
            "source_row_id": locus, "original_subject": r["gene_symbol"],
            "original_object": r["hpo_id"], "disease_id": r["disease_id"],
            "aspect": "", "fate": fate, "reason": reason,
            "linked_candidate_count": len(actual),
        })

    all_hpoa_loci = {r["source_row_id"] for r in hpoa_ledger}
    all_g2p_loci = {r["source_row_id"] for r in g2p_ledger}
    extraneous_links = (
        set(evidence_links) - all_hpoa_loci
    ) | (set(discovery_links) - all_g2p_loci) | (context_lines - all_hpoa_loci)
    if extraneous_links:
        raise ValueError(f"Output contains {len(extraneous_links)} unknown source locators")

    old_coverage = {
        r["gene_id"]: r for r in rows(candidate_dir / "gene_coverage.tsv",
                                       ("gene_id", "gene_symbol", "candidate_count", "source_g2p_rows"))
    }
    candidate_count_per_gene = Counter(r["gene_id"] for r in candidates)
    coverage = []
    coverage_errors = []
    for r in genes:
        gene = r["hgnc_id"]
        nc, ng = candidate_count_per_gene[gene], g2p_counts[gene]
        prev = old_coverage.get(gene)
        if prev is None or int(prev["candidate_count"]) != nc or int(prev["source_g2p_rows"]) != ng:
            coverage_errors.append(gene)
        state = ("candidate_available" if nc
                 else "no_exact_symbol_g2p_row_alias_unresolved" if not ng
                 else "exact_g2p_without_matching_hpoa_P")
        coverage.append({
            "gene_id": gene, "gene_symbol": r["approved_hgnc_symbol"],
            "candidate_count": nc, "source_g2p_rows": ng,
            "coverage_state_v2": state,
        })

    diseases = []
    for disease, dc in sorted(disease_counts.items()):
        p = dc["aspect_P"]
        source_state = ("at_least_one_P_onset_field" if dc["p_with_onset"]
                        else "P_rows_without_onset_field" if p
                        else "no_HPOA_P_rows_for_disease")
        diseases.append({
            "disease_id": disease, "hpoa_p_rows": p,
            "context_C_rows": dc["aspect_C"], "context_I_rows": dc["aspect_I"],
            "context_M_rows": dc["aspect_M"], "context_H_rows": dc["aspect_H"],
            "p_rows_with_onset": dc["p_with_onset"],
            "onset_source_state": source_state,
        })

    collisions = []
    for key, states in sorted(identities.items()):
        if len(states) > 1:
            collisions.append(dict(zip(
                ("gene_id", "disruption_type", "phenotype_id", "disease_id"), key
            )) | {
                "polarity_states": ";".join(sorted(states)),
                "legacy_candidate_ids": ";".join(sorted(cid for v in states.values() for cid in v)),
            })
    fates = {
        "g2p": dict(Counter(r["fate"] for r in g2p_ledger)),
        "hpoa": dict(Counter(r["fate"] for r in hpoa_ledger)),
    }
    for source in ("g2p", "hpoa"):
        for fate in ("emitted", "merged", "held", "failed"):
            fates[source].setdefault(fate, 0)
    conserved = (
        sum(fates["g2p"].values()) == len(g2p_input)
        and sum(fates["hpoa"].values()) == len(hpoa_input)
    )
    passed = (
        conserved and not legacy_identity_errors and not coverage_errors
        and candidate_ids == expected_candidates
        and fates["g2p"]["failed"] == 0 and fates["hpoa"]["failed"] == 0
    )
    out.mkdir(parents=True, exist_ok=True)
    outputs = {
        "g2p_input_fates.tsv": (LEDGER_COLUMNS, g2p_ledger),
        "hpoa_input_fates.tsv": (LEDGER_COLUMNS, hpoa_ledger),
        "gene_coverage_causal_states.tsv": (COVERAGE_COLUMNS, coverage),
        "disease_context_presence.tsv": (DISEASE_COLUMNS, diseases),
        "polarity_identity_collisions.tsv": (IDENTITY_COLUMNS, collisions),
    }
    for name, (columns, data) in outputs.items():
        write_rows(out / name, columns, data)
    manifest = {
        "gate_type": "read_only_provisional_candidate_integrity",
        "gate_passed": passed,
        "original_candidate_count": old["candidate_count"],
        "expected_candidate_count": len(expected_candidates),
        "source_row_counts": {"g2p": len(g2p_input), "hpoa": len(hpoa_input)},
        "four_fate_conservation": fates,
        "source_record_conservation_passed": conserved,
        "merged_fate_rule": "Zero; original source lines retained in discovery, evidence or context links. Candidate identity collapse is separately audited.",
        "coverage_errors": coverage_errors[:50],
        "legacy_candidate_identity_errors": legacy_identity_errors[:50],
        "provisional_polarity_collisions_without_polarity": len(collisions),
        "provisional_candidate_id_profile": {
            "name": "legacy_gene_disease_hpo_polarity_v01",
            "key_fields": ["gene_id", "unspecified_disruption", "phenotype_id", "disease_id", "polarity"],
            "polarity_function_sha256": hashlib.sha256(
                inspect.getsource(polarity).encode("utf-8")
            ).hexdigest(),
            "identity_decision": "pending_user_PAR_Core_decision",
        },
        "hpo_source_sha256": hashes,
        "registry_sha256": checksum(registry),
        "producer_manifest_sha256": checksum(candidate_dir / "manifest.json"),
        "direct_assertion_promotion": "blocked_pending_identity_review_and_human_disposition",
        "note": "This audit checks existing legacy discovery IDs and source conservation. It does not authorize direct gene phenotype claims.",
    }
    (out / "audit_manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    with (out / "SHA256SUMS.txt").open("w", encoding="utf-8") as handle:
        for name in (*outputs, "audit_manifest.json"):
            handle.write(f"{checksum(out / name)}  {name}\n")
    return manifest

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--g2p", type=Path, required=True)
    parser.add_argument("--hpoa", type=Path, required=True)
    parser.add_argument("--candidate-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--skip-source-sha", action="store_true",
                        help="Only for isolated synthetic tests")
    args = parser.parse_args()
    result = audit(args.registry, args.g2p, args.hpoa, args.candidate_dir,
                   args.out, skip_source_sha=args.skip_source_sha)
    print(json.dumps(result, sort_keys=True, indent=2))
    if not result["gate_passed"]:
        raise SystemExit(2)

if __name__ == "__main__":
    main()
