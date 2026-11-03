#!/usr/bin/env python3
"""Export provisional gene-disruption to HPO phenotype candidates with source lineage."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

G2P_SHA = "507a17bff9c49e6329fbd88b1f91734fa7e9fdea5c06304044c0892eb6ab248c"
HPOA_SHA = "e89aa39c8f97bf5a52c5d160f9250a603681d630ade8ec2679d84ac5aece1f72"
CANDIDATE_COLUMNS = ["candidate_id","gene_id","gene_symbol","disruption_type","predicate","phenotype_id","disease_id","assertion_state","evidence_count","source_release"]
EVIDENCE_COLUMNS = ["candidate_id","evidence_id","source_resource","source_release","source_row_id","original_subject","original_predicate","original_object","source_evidence_code","original_reference","primary_publication_id","evidence_role","frequency","qualifier","aspect","onset","sex","modifier","source_lineage_key"]
DISCOVERY_COLUMNS = ["candidate_id","gene_id","gene_symbol","disease_id","phenotype_id","source_resource","source_release","source_row_id","original_subject","original_object","evidence_role"]
COVERAGE_COLUMNS = ["gene_id","gene_symbol","candidate_count","source_g2p_rows","coverage_state"]
CONTEXT_COLUMNS = ["disease_id","source_row_id","aspect","hpo_id","reference","evidence","primary_publication_id"]

def checksum(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest()

def source_rows(path, required):
    with open(path, encoding="utf-8-sig", newline="") as handle:
        header = None
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            cells = next(csv.reader([line], delimiter="\t"))
            if header is None:
                header = [cell.lstrip("#").strip() if i == 0 else cell for i, cell in enumerate(cells)]
                missing = set(required) - set(header)
                if missing:
                    raise ValueError(f"{path}: missing columns {sorted(missing)}")
                continue
            if line.startswith("#"):
                continue
            if len(cells) != len(header):
                raise ValueError(f"{path}:{line_number}: malformed source row")
            yield line_number, dict(zip(header, cells))

def stable_id(prefix, *parts):
    encoded = json.dumps(parts, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return prefix + hashlib.sha256(encoded).hexdigest()[:24]

def polarity(row):
    frequency = row.get("frequency", "").strip()
    qualifier = row.get("qualifier", "").strip().upper()
    if qualifier == "NOT" or frequency in ("0%", "HP:0040285") or re.fullmatch(r"0/[1-9][0-9]*", frequency):
        return "asserted_absent"
    if qualifier:
        return "unspecified"
    match = re.fullmatch(r"([0-9]+)/([1-9][0-9]*)", frequency)
    if match and 0 < int(match.group(1)) <= int(match.group(2)):
        return "asserted_present"
    if re.fullmatch(r"(?:100|[0-9]{1,2}(?:\.[0-9]+)?)%", frequency) and float(frequency[:-1]) > 0:
        return "asserted_present"
    return "unspecified"

def publications(reference):
    found = re.findall(r"PMID:\s*([0-9]+)", reference or "")
    return ";".join("PMID:" + value for value in sorted(set(found)))

def write_table(path, columns, records):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns, delimiter="\t", extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)

def export(registry, g2p, hpoa, out, skip_sha=False):
    source_hashes = {"genes_to_phenotype.txt": checksum(g2p), "phenotype.hpoa": checksum(hpoa)}
    if not skip_sha and (source_hashes["genes_to_phenotype.txt"] != G2P_SHA or source_hashes["phenotype.hpoa"] != HPOA_SHA):
        raise ValueError("Pinned HPO v2026-09-01 source SHA256 mismatch")
    genes = [record for _, record in source_rows(registry, ("hgnc_id", "approved_hgnc_symbol"))]
    if len(genes) != 662 or len({g["hgnc_id"] for g in genes}) != 662:
        raise ValueError("Expected exactly 662 distinct frozen HGNC IDs")
    by_symbol = {g["approved_hgnc_symbol"]: g for g in genes}
    by_id = {g["hgnc_id"]: g for g in genes}
    if len(by_symbol) != 662:
        raise ValueError("Duplicate approved gene symbols in frozen registry")
    associations = defaultdict(set)
    discovery_lines = defaultdict(list)
    gene_source_counts = Counter()
    diseases = set()
    for line, record in source_rows(g2p, ("gene_symbol", "hpo_id", "disease_id")):
        gene = by_symbol.get(record["gene_symbol"])
        if gene is None or not record["hpo_id"].startswith("HP:") or not record["disease_id"]:
            continue
        gene_id, disease_id, hpo_id = gene["hgnc_id"], record["disease_id"], record["hpo_id"]
        associations[(disease_id, hpo_id)].add(gene_id)
        discovery_lines[(gene_id, disease_id, hpo_id)].append(line)
        gene_source_counts[gene_id] += 1
        diseases.add(disease_id)

    candidates, evidence, discovery, disease_context = {}, [], [], []
    for line, record in source_rows(hpoa, ("database_id", "hpo_id", "aspect", "frequency", "qualifier", "reference", "evidence")):
        disease_id, hpo_id, aspect = record["database_id"], record["hpo_id"], record["aspect"]
        if disease_id not in diseases:
            continue
        reference = record.get("reference", "")
        publication_id = publications(reference)
        if aspect != "P":
            if aspect in ("C", "I", "M", "H"):
                disease_context.append({"disease_id": disease_id, "source_row_id": f"phenotype.hpoa:{line}",
                    "aspect": aspect, "hpo_id": hpo_id, "reference": reference,
                    "evidence": record.get("evidence", ""), "primary_publication_id": publication_id})
            continue
        for gene_id in sorted(associations.get((disease_id, hpo_id), ())):
            state = polarity(record)
            candidate_id = stable_id("dmpcand:", gene_id, "unspecified_disruption", hpo_id, disease_id, state)
            candidates[candidate_id] = {
                "candidate_id": candidate_id, "gene_id": gene_id,
                "gene_symbol": by_id[gene_id]["approved_hgnc_symbol"],
                "disruption_type": "unspecified_disruption", "predicate": "associated_with",
                "phenotype_id": hpo_id, "disease_id": disease_id,
                "assertion_state": "disease_mediated_candidate_" + state, "source_release": "HPO:v2026-09-01"}
            for g2p_line in discovery_lines[(gene_id, disease_id, hpo_id)]:
                discovery.append({"candidate_id": candidate_id, "gene_id": gene_id,
                    "gene_symbol": by_id[gene_id]["approved_hgnc_symbol"],
                    "disease_id": disease_id, "phenotype_id": hpo_id, "source_resource": "HPO-G2P",
                    "source_release": "v2026-09-01", "source_row_id": f"genes_to_phenotype.txt:{g2p_line}",
                    "original_subject": gene_id, "original_object": hpo_id,
                    "evidence_role": "disease_mediated_discovery_only"})
            evidence.append({"candidate_id": candidate_id,
                "evidence_id": stable_id("dmpev:", candidate_id, "HPOA", line, record),
                "source_resource": "HPOA", "source_release": "v2026-09-01",
                "source_row_id": f"phenotype.hpoa:{line}",
                "original_subject": disease_id, "original_predicate": "has_phenotype",
                "original_object": hpo_id, "source_evidence_code": record.get("evidence", ""),
                "original_reference": reference, "primary_publication_id": publication_id,
                "evidence_role": "disease_phenotype_annotation",
                "frequency": record.get("frequency", ""), "qualifier": record.get("qualifier", ""),
                "aspect": aspect, "onset": record.get("onset", ""), "sex": record.get("sex", ""),
                "modifier": record.get("modifier", ""),
                "source_lineage_key": stable_id("origin:", disease_id, hpo_id, publication_id or reference)})

    evidence.sort(key=lambda row: (row["candidate_id"], row["evidence_id"]))
    discovery = list({tuple(row[c] for c in DISCOVERY_COLUMNS): row for row in discovery}.values())
    discovery.sort(key=lambda row: (row["candidate_id"], row["source_row_id"]))
    disease_context.sort(key=lambda row: (row["disease_id"], row["source_row_id"]))
    evidence_count = Counter(row["candidate_id"] for row in evidence)
    candidate_rows = [{**candidate, "evidence_count": evidence_count[identifier]}
                      for identifier, candidate in sorted(candidates.items())]
    by_gene = Counter(row["gene_id"] for row in candidate_rows)
    coverage_rows = [{"gene_id": g["hgnc_id"], "gene_symbol": g["approved_hgnc_symbol"],
                      "candidate_count": by_gene[g["hgnc_id"]],
                      "source_g2p_rows": gene_source_counts[g["hgnc_id"]],
                      "coverage_state": "candidate_available" if by_gene[g["hgnc_id"]] else "no_matched_hpoa_candidate"}
                     for g in genes]
    out.mkdir(parents=True, exist_ok=True)
    filenames = {
        "par_candidates.tsv": (CANDIDATE_COLUMNS, candidate_rows),
        "par_evidence.tsv": (EVIDENCE_COLUMNS, evidence),
        "source_discovery_links.tsv": (DISCOVERY_COLUMNS, discovery),
        "disease_context.tsv": (CONTEXT_COLUMNS, disease_context),
        "gene_coverage.tsv": (COVERAGE_COLUMNS, coverage_rows)}
    for name, (columns, records) in filenames.items():
        write_table(out / name, columns, records)
    manifest = {
        "status": "provisional_internal_candidates", "reference_release": "HPO:v2026-09-01",
        "registry_gene_count": len(genes), "hpo_source_sha256": source_hashes,
        "genes_with_candidates": sum(by_gene[g] > 0 for g in by_id),
        "candidate_count": len(candidate_rows), "hpoa_evidence_records": len(evidence),
        "g2p_discovery_records": len(discovery), "disease_context_records": len(disease_context),
        "explicit_absence_candidates": sum(row["assertion_state"].endswith("asserted_absent") for row in candidate_rows),
        "interpretation": "Disease mediated discovery candidates. Direct gene disruption mechanism evidence awaits primary source confirmation.",
        "lineage_rule": "HPO G2P discovery and HPOA curation derived from the same publication count as one original publication."}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    names = list(filenames) + ["manifest.json"]
    (out / "SHA256SUMS.txt").write_text("".join(f"{checksum(out / name)}  {name}\n" for name in names), encoding="utf-8")
    return manifest

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--g2p", type=Path, required=True)
    parser.add_argument("--hpoa", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--skip-sha", action="store_true", help="Synthetic fixture tests only")
    args = parser.parse_args()
    print(json.dumps(export(args.registry, args.g2p, args.hpoa, args.out, args.skip_sha), indent=2))

if __name__ == "__main__":
    main()
