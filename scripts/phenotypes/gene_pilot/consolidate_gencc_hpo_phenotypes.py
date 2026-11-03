#!/usr/bin/env python3
"""Consolidate HPO phenotype candidates and GenCC source support without inflating PAR counts.

The outputs are internal association views. Direct disruption->phenotype evidence
requires a separately verified, source-specific assertion.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ASSOCIATION_FIELDS = (
    "candidate_id","gene_id","gene_symbol","disruption_type","phenotype_id",
    "disease_id","assertion_state","hpo_evidence_count","gencc_submission_count",
    "gencc_submitters","gencc_classifications","gencc_inheritance",
    "gencc_assertion_ids","genetic_support","par_status"
)
SOURCE_FIELDS = (
    "candidate_id","source","source_assertion_id","source_version","source_issuer",
    "source_classification","source_inheritance","source_role"
)
GENE_FIELDS = ("gene_id","gene_symbol","hpo_candidate_count","gencc_assertion_count","coverage_category")
DIRECT_FIELDS = (
    "gene_id","disruption_type","phenotype_id","disease_id","source_resource",
    "source_assertion_id","source_version","original_publication_id",
    "original_biological_subject","evidence_type","observation_description",
    "curation_status"
)

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def require_verified(directory, names):
    manifest_path = directory / "SHA256SUMS.txt"
    if not manifest_path.is_file():
        raise ValueError(f"Missing SHA256SUMS.txt in {directory}")
    entries = {}
    for raw in manifest_path.read_text(encoding="utf-8").splitlines():
        chunks = raw.split(None, 1)
        if len(chunks) != 2:
            raise ValueError("Malformed SHA256SUMS.txt line")
        checksum, name = chunks
        name = name.strip()
        if Path(name).name != name or name.startswith("."):
            raise ValueError(f"Unsafe checksum filename: {name}")
        entries[name] = checksum
    for name in names:
        if name not in entries or sha(directory / name) != entries[name]:
            raise ValueError(f"Unverified or modified input: {directory / name}")

def tsv(path, fields):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        missing = set(fields) - set(reader.fieldnames or ())
        if missing:
            raise ValueError(f"{path}: missing {sorted(missing)}")
        yield from reader

def emit(path, fields, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, delimiter="\t",
                                extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

def summarize(hpo_dir, gencc_dir, out):
    require_verified(hpo_dir, ("manifest.json", "par_candidates.tsv", "par_evidence.tsv", "gene_coverage.tsv"))
    require_verified(gencc_dir, ("gencc_integration_manifest.json",
                                 "gencc_gene_disease_evidence.tsv",
                                 "gencc_hpo_exact_disease_matches.tsv"))
    hm = json.loads((hpo_dir / "manifest.json").read_text())
    gm = json.loads((gencc_dir / "gencc_integration_manifest.json").read_text())
    if hm.get("reference_release") != "HPO:v2026-09-01" or hm.get("registry_gene_count") != 662:
        raise ValueError("Expected pinned 662 gene HPO source")
    if gm.get("hpo_candidate_count") != hm.get("candidate_count"):
        raise ValueError("GenCC integration references different HPO candidate collection")

    candidates = {}
    for r in tsv(hpo_dir / "par_candidates.tsv",
                 ("candidate_id","gene_id","gene_symbol","disruption_type",
                  "phenotype_id","disease_id","assertion_state","evidence_count")):
        if r["candidate_id"] in candidates:
            raise ValueError("Duplicate candidate ID")
        candidates[r["candidate_id"]] = r
    if len(candidates) != hm["candidate_count"]:
        raise ValueError("HPO candidate count mismatch")
    coverage = list(tsv(hpo_dir / "gene_coverage.tsv",
                        ("gene_id","gene_symbol","candidate_count")))
    if len(coverage) != 662 or len({g["gene_id"] for g in coverage}) != 662:
        raise ValueError("HPO gene coverage denominator mismatch")

    # Every GenCC version remains a separate source assertion.
    gencc_by_gene = defaultdict(set)
    source_keys = set()
    for r in tsv(gencc_dir / "gencc_gene_disease_evidence.tsv",
                 ("gene_id","gencc_id","gencc_version","source_disease_id",
                  "source_classification","source_inheritance","source_submitter")):
        key = (r["gencc_id"], r["gencc_version"])
        if key in source_keys:
            raise ValueError("Duplicate GenCC source assertion version")
        source_keys.add(key)
        gencc_by_gene[r["gene_id"]].add(key)
    if len(source_keys) != gm["gencc_assertions_for_registry_genes"]:
        raise ValueError("GenCC source count mismatch")

    matches = defaultdict(dict)
    for r in tsv(gencc_dir / "gencc_hpo_exact_disease_matches.tsv",
                 ("candidate_id","gene_id","phenotype_id","disease_id",
                  "gencc_id","gencc_version","source_classification",
                  "source_inheritance","source_submitter","match_type")):
        cid = r["candidate_id"]
        c = candidates.get(cid)
        if c is None:
            raise ValueError(f"Unknown matched candidate {cid}")
        for field in ("gene_id","phenotype_id","disease_id"):
            if c[field] != r[field]:
                raise ValueError(f"Source join disagrees on {field} for {cid}")
        if r["match_type"] != "identical_native_disease_curie":
            raise ValueError("Unexpected mapping relation")
        key = (r["gencc_id"], r["gencc_version"])
        if key not in gencc_by_gene[r["gene_id"]]:
            raise ValueError("GenCC match without original source assertion")
        if key in matches[cid]:
            raise ValueError("Repeated identical GenCC submission join")
        matches[cid][key] = r
    if sum(map(len, matches.values())) != gm["exact_disease_candidate_matches"]:
        raise ValueError("Join count mismatch")

    assoc = []
    source_links = []
    for cid,c in sorted(candidates.items()):
        submissions = matches.get(cid, {})
        values = list(submissions.values())
        ids = sorted(f"{k[0]}@{k[1]}" for k in submissions)
        status = ("disease_mediated_with_gencc_gene_disease_support"
                  if submissions else "disease_mediated_hpo_only")
        assoc.append({
            **{k:c[k] for k in ("candidate_id","gene_id","gene_symbol",
                               "disruption_type","phenotype_id","disease_id","assertion_state")},
            "hpo_evidence_count": c["evidence_count"],
            "gencc_submission_count": len(submissions),
            "gencc_submitters": ";".join(sorted({r["source_submitter"] for r in values if r["source_submitter"]})),
            "gencc_classifications": ";".join(sorted({r["source_classification"] for r in values if r["source_classification"]})),
            "gencc_inheritance": ";".join(sorted({r["source_inheritance"] for r in values if r["source_inheritance"]})),
            "gencc_assertion_ids": ";".join(ids),
            "genetic_support": "exact_gene_disease_curie_match" if submissions else "not_linked",
            "par_status": status
        })
        for key,r in sorted(submissions.items()):
            source_links.append({
                "candidate_id":cid, "source":"GenCC",
                "source_assertion_id":key[0], "source_version":key[1],
                "source_issuer":r["source_submitter"],
                "source_classification":r["source_classification"],
                "source_inheritance":r["source_inheritance"],
                "source_role":"gene_disease_curation"
            })
    gene_rows=[]
    count_by_gene=Counter(c["gene_id"] for c in assoc)
    for r in coverage:
        gid=r["gene_id"]
        hc=count_by_gene[gid]
        gc=len(gencc_by_gene[gid])
        if hc and gc: category="both_sources"
        elif hc: category="hpo_only"
        elif gc: category="gencc_only"
        else: category="neither_source"
        gene_rows.append({"gene_id":gid,"gene_symbol":r["gene_symbol"],
                          "hpo_candidate_count":hc,"gencc_assertion_count":gc,
                          "coverage_category":category})
    if sum(int(r["hpo_candidate_count"]) for r in gene_rows)!=len(assoc):
        raise ValueError("Coverage conservation failure")
    categories=Counter(r["coverage_category"] for r in gene_rows)
    out.mkdir(parents=True,exist_ok=True)
    files={
        "consolidated_phenotype_candidates.tsv":(ASSOCIATION_FIELDS,assoc),
        "gencc_source_links.tsv":(SOURCE_FIELDS,source_links),
        "combined_gene_coverage.tsv":(GENE_FIELDS,gene_rows),
        "genes_needing_source_discovery.tsv":(GENE_FIELDS,[r for r in gene_rows if r["coverage_category"]=="neither_source"]),
    }
    for name,(fields,records) in files.items():
        emit(out / name,fields,records)
    # Header-only source contract for verified direct disruption-to-phenotype evidence.
    # No fabricated examples or promoted records.
    emit(out / "direct_phenotype_evidence_template.tsv",DIRECT_FIELDS,[])
    result={
        "registry_genes":len(gene_rows),"unique_hpo_candidates":len(assoc),
        "gencc_source_links":len(source_links),
        "unique_candidates_with_gencc_support":len(matches),
        "unique_candidates_hpo_only":len(assoc)-len(matches),
        "coverage_categories":dict(sorted(categories.items())),
        "direct_disruption_phenotype_records_accepted":0,
        "interpretation":"GenCC gene-disease curation plus HPO disease-phenotype context. No direct disruption phenotype PARs promoted."
    }
    (out / "consolidation_manifest.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    with open(out / "SHA256SUMS.txt","w") as f:
        for name in (*files,"direct_phenotype_evidence_template.tsv","consolidation_manifest.json"):
            f.write(f"{sha(out / name)}  {name}\n")
    return result

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--hpo-dir",type=Path,required=True)
    p.add_argument("--gencc-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(summarize(a.hpo_dir,a.gencc_dir,a.out),indent=2))
if __name__=="__main__":
    main()
