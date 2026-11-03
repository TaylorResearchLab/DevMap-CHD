#!/usr/bin/env python3
"""Prepare publication-level evidence assessment and unsupported-gene queues from HPO candidates.

Every PMID is a source lead, not yet direct gene-disruption evidence.
"""
import argparse
import csv
import json
import hashlib
from collections import defaultdict, Counter
from pathlib import Path

def read_tsv(path, required):
    with open(path, encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        missing = set(required) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path}: missing required columns {sorted(missing)}")
        yield from reader

def emit(path, fields, rows):
    with open(path, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, delimiter="\t", extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()

def produce(source_dir, out):
    manifest_file = source_dir / "manifest.json"
    upstream = json.loads(manifest_file.read_text(encoding="utf-8"))
    if upstream.get("reference_release") != "HPO:v2026-09-01" or upstream.get("registry_gene_count") != 662:
        raise ValueError("Input manifest is not the frozen 662-gene HPO v2026-09-01 extraction")
    checksums = source_dir / "SHA256SUMS.txt"
    verified = {}
    for line in checksums.read_text(encoding="utf-8").splitlines():
        expected, name = line.split(None, 1)
        name = name.strip().lstrip("*")
        if "/" in name or name.startswith("."):
            raise ValueError("Unsafe input checksum path")
        if digest(source_dir / name) != expected:
            raise ValueError(f"Input checksum mismatch: {name}")
        verified[name] = expected
    for name in ("par_candidates.tsv", "par_evidence.tsv", "gene_coverage.tsv", "manifest.json"):
        if name not in verified:
            raise ValueError(f"Unverified source table: {name}")
    candidates = {}
    for item in read_tsv(source_dir / "par_candidates.tsv", ("candidate_id", "gene_id", "gene_symbol", "phenotype_id", "disease_id", "assertion_state")):
        cid = item["candidate_id"]
        if cid in candidates:
            raise ValueError(f"Duplicate candidate ID: {cid}")
        candidates[cid] = item
    if len(candidates) != upstream.get("candidate_count"):
        raise ValueError("Candidate denominator differs from source manifest")
    coverage = list(read_tsv(source_dir / "gene_coverage.tsv", ("gene_id", "gene_symbol", "candidate_count")))
    if len(coverage) != 662 or len({x["gene_id"] for x in coverage}) != 662:
        raise ValueError("Coverage denominator or uniqueness mismatch")
    by_pub = defaultdict(lambda: {"ids": set(), "diseases": set(), "phenotypes": set(), "source_rows": set(), "codes": set()})
    unresolved = defaultdict(lambda: {"ids": set(), "diseases": set(), "phenotypes": set(), "source_rows": set()})
    evidence_rows = 0
    for e in read_tsv(source_dir / "par_evidence.tsv", ("candidate_id", "primary_publication_id", "source_row_id", "source_evidence_code", "original_subject", "original_object", "evidence_role", "original_reference")):
        evidence_rows += 1
        cid = e["candidate_id"]
        candidate = candidates.get(cid)
        if candidate is None:
            raise ValueError(f"Orphan evidence record {cid}")
        if e["evidence_role"] != "disease_phenotype_annotation" or e["original_subject"] != candidate["disease_id"] or e["original_object"] != candidate["phenotype_id"]:
            raise ValueError(f"Source biological subject mismatch {cid}")
        if candidate["assertion_state"].endswith("asserted_absent"):
            continue  # absence remains in source outputs; no positive evidence queue
        pids = [p.strip() for p in e["primary_publication_id"].split(";") if p.strip()]
        for pid in pids:
            if not pid.startswith("PMID:") or not pid[5:].isdigit():
                raise ValueError(f"Malformed PMID {pid}")
            key = (candidate["gene_id"], candidate["gene_symbol"], pid)
            group = by_pub[key]
            group["ids"].add(cid); group["diseases"].add(candidate["disease_id"])
            group["phenotypes"].add(candidate["phenotype_id"]); group["source_rows"].add(e["source_row_id"])
            group["codes"].add(e["source_evidence_code"])
        if not pids:
            key = (candidate["gene_id"], candidate["gene_symbol"])
            group = unresolved[key]
            group["ids"].add(cid); group["diseases"].add(candidate["disease_id"])
            group["phenotypes"].add(candidate["phenotype_id"]); group["source_rows"].add(e["source_row_id"])
    publication = []
    for (gid, gene, pid), g in by_pub.items():
        publication.append({"gene_id": gid, "gene_symbol": gene, "publication_id": pid,
            "candidate_count": len(g["ids"]), "phenotype_count": len(g["phenotypes"]),
            "disease_count": len(g["diseases"]), "hpoa_source_rows": len(g["source_rows"]),
            "hpo_evidence_codes": ";".join(sorted(g["codes"])),
            "source_role": "publication_lead_from_disease_phenotype_curation",
            "direct_gene_disruption_evidence": "NOT_ASSESSED",
            "assessment_status": "pending_primary_source_examination"})
    publication.sort(key=lambda r: (-r["phenotype_count"], r["gene_symbol"], r["publication_id"]))
    missing = [{"gene_id": x["gene_id"], "gene_symbol": x["gene_symbol"],
                "source_g2p_rows": x.get("source_g2p_rows", ""),
                "next_source": "independent_genetic_and_clinical_sources",
                "status": "no_HPO_candidate"}
               for x in coverage if int(x["candidate_count"]) == 0]
    missing.sort(key=lambda x: x["gene_symbol"])
    unresolved_rows = []
    for (gid,gene), group in unresolved.items():
        unresolved_rows.append({"gene_id": gid, "gene_symbol": gene,
            "candidate_count": len(group["ids"]),
            "phenotype_count": len(group["phenotypes"]),
            "disease_count": len(group["diseases"]),
            "source_rows": len(group["source_rows"]),
            "status": "reference_requires_source_resolution"})
    unresolved_rows.sort(key=lambda r: (-r["candidate_count"], r["gene_symbol"]))
    out.mkdir(parents=True, exist_ok=True)
    file_fields = {
        "publication_gene_queue.tsv": (publication, ["gene_id", "gene_symbol", "publication_id", "candidate_count", "phenotype_count", "disease_count", "hpoa_source_rows", "hpo_evidence_codes", "source_role", "direct_gene_disruption_evidence", "assessment_status"]),
        "genes_without_hpo_candidates.tsv": (missing, ["gene_id","gene_symbol","source_g2p_rows","next_source","status"]),
        "unresolved_publication_queue.tsv": (unresolved_rows, ["gene_id","gene_symbol","candidate_count","phenotype_count","disease_count","source_rows","status"])
    }
    for name, (rows, fields) in file_fields.items():
        emit(out / name, fields, rows)
    summary = {"input_release": upstream["reference_release"],
       "input_candidate_count": len(candidates),
       "input_hpoa_evidence_rows": evidence_rows,
       "publication_gene_review_pairs": len(publication),
       "genes_with_publication_leads": len({r["gene_id"] for r in publication}),
       "genes_without_hpo_candidates": len(missing),
       "genes_with_unresolved_publication_references": len(unresolved),
       "interpretation": "Publication leads are inherited from disease-to-phenotype curation; independent direct gene-disruption phenotype assertions require primary-source examination."}
    (out / "evidence_queue_manifest.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with open(out / "SHA256SUMS.txt", "w", encoding="utf-8") as fh:
        for name in [*file_fields, "evidence_queue_manifest.json"]:
            fh.write(f"{digest(out / name)}  {name}\n")
    return summary

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(produce(args.source_dir, args.out), indent=2))

if __name__ == "__main__":
    main()
