#!/usr/bin/env python3
"""Audit OMIM bibliography provenance for HPOA disease–phenotype evidence.

Input: existing HPOA source authority audit. Output: a source-faithful OMIM
reference queue, not a synthetic OMIM-PMID-phenotype association.
"""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

OMIM_RE = re.compile(r"(?<![A-Za-z0-9])OMIM:\s*([0-9]{6})(?![0-9])",re.I)
PMID_RE = re.compile(r"(?<![A-Za-z0-9])PMID:\s*([0-9]+)(?![0-9])",re.I)
EVIDENCE_COLUMNS = [
    "omim_record_id","hpoa_evidence_id","hpoa_candidate_id",
    "disease_id","phenotype_id","hpoa_evidence_code","hpoa_original_reference",
    "hpoa_explicit_pmids","hpoa_source_row_id","hpoa_source_release",
    "original_biological_subject","source_record_role",
    "publication_mapping_status","omim_bibliography_pmids",
    "phenotype_specific_verified_pmids","verification_location"
]
UNIQUE_COLUMNS = [
    "omim_record_id","evidence_rows","distinct_disease_hpo_pairs",
    "disease_ids","evidence_codes","explicit_hpoa_pmids",
    "bibliography_retrieval_status"
]
CLAIM_COLUMNS = [
    "omim_record_id","disease_id","phenotype_id","evidence_rows",
    "source_evidence_codes","hpoa_explicit_pmids","source_row_ids",
    "review_status"
]

def file_sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1<<20),b""):
            h.update(b)
    return h.hexdigest()

def read(path,required):
    with path.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f,delimiter="\t")
        if not reader.fieldnames or not set(required).issubset(reader.fieldnames):
            raise ValueError(f"Missing required HPOA source fields: {sorted(set(required)-set(reader.fieldnames or []))}")
        for row in reader:
            if None in row:raise ValueError("Malformed HPOA authority row")
            yield row

def write(path,fields,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields,delimiter="\t",lineterminator="\n")
        writer.writeheader();writer.writerows(rows)

def audit(source,out,strict=True):
    required=("record_id","candidate_id","original_subject","original_object",
              "source_evidence_code","source_reference","primary_publication_id",
              "source_row_id","source_release","evidence_role")
    evidence=[];per_omim=defaultdict(list);per_claim=defaultdict(list)
    matched_source_rows=0;seen_keys=set()
    for r in read(source,required):
        ids=sorted(set("OMIM:"+m for m in OMIM_RE.findall(r["source_reference"])))
        if not ids:continue
        matched_source_rows+=1
        pmids=sorted(set("PMID:"+m for m in PMID_RE.findall(
            r["source_reference"]+";"+r["primary_publication_id"])))
        for omim in ids:
            k=(r["record_id"],omim)
            if k in seen_keys:raise ValueError(f"Repeated evidence identifier for OMIM record: {k}")
            seen_keys.add(k)
            row={
                "omim_record_id":omim,
                "hpoa_evidence_id":r["record_id"],
                "hpoa_candidate_id":r["candidate_id"],
                "disease_id":r["original_subject"],
                "phenotype_id":r["original_object"],
                "hpoa_evidence_code":r["source_evidence_code"],
                "hpoa_original_reference":r["source_reference"],
                "hpoa_explicit_pmids":";".join(pmids),
                "hpoa_source_row_id":r["source_row_id"],
                "hpoa_source_release":r["source_release"],
                "original_biological_subject":r["original_subject"],
                "source_record_role":r["evidence_role"],
                "publication_mapping_status":(
                    "explicit_hpoa_pmid_present" if pmids else
                    "omim_bibliography_phenotype_specific_citation_unresolved"),
                "omim_bibliography_pmids":"",
                "phenotype_specific_verified_pmids":"",
                "verification_location":""
            }
            evidence.append(row);per_omim[omim].append(row)
            per_claim[(omim,r["original_subject"],r["original_object"])].append(row)
    if strict and matched_source_rows!=9714:
        raise ValueError(f"Expected 9714 HPOA rows with OMIM reference, found {matched_source_rows}")
    uniq=[]
    for omim,rows in sorted(per_omim.items()):
        uniq.append({
            "omim_record_id":omim,
            "evidence_rows":len(rows),
            "distinct_disease_hpo_pairs":len({(r["disease_id"],r["phenotype_id"]) for r in rows}),
            "disease_ids":";".join(sorted({r["disease_id"] for r in rows})),
            "evidence_codes":";".join(sorted({r["hpoa_evidence_code"] for r in rows})),
            "explicit_hpoa_pmids":";".join(sorted(set(
                p for r in rows for p in r["hpoa_explicit_pmids"].split(";") if p))),
            "bibliography_retrieval_status":"not_retrieved"
        })
    claims=[]
    for (omim,disease,hpo),rows in sorted(per_claim.items()):
        claims.append({
            "omim_record_id":omim,"disease_id":disease,"phenotype_id":hpo,
            "evidence_rows":len(rows),
            "source_evidence_codes":";".join(sorted({r["hpoa_evidence_code"] for r in rows})),
            "hpoa_explicit_pmids":";".join(sorted(set(
                p for r in rows for p in r["hpoa_explicit_pmids"].split(";") if p))),
            "source_row_ids":";".join(sorted({r["hpoa_source_row_id"] for r in rows})),
            "review_status":"original_hpoa_source_import_only"
        })
    out.mkdir(parents=True,exist_ok=True)
    files={
        "omim_hpoa_source_evidence.tsv":(EVIDENCE_COLUMNS,sorted(
            evidence,key=lambda r:(r["omim_record_id"],r["disease_id"],r["phenotype_id"],r["hpoa_evidence_id"]))),
        "omim_bibliography_retrieval_queue.tsv":(UNIQUE_COLUMNS,uniq),
        "omim_disease_phenotype_claims.tsv":(CLAIM_COLUMNS,claims)
    }
    for name,(fields,rows) in files.items():write(out/name,fields,rows)
    stats={
        "hpoa_source_input_sha256":file_sha(source),
        "hpoa_rows_with_omim_reference":matched_source_rows,
        "omim_evidence_links":len(evidence),
        "distinct_omim_records":len(uniq),
        "unique_omim_disease_phenotype_claims":len(claims),
        "hpoa_rows_with_omim_and_explicit_pmid":sum(
            bool(PMID_RE.search(r["hpoa_original_reference"]+";"+r["hpoa_explicit_pmids"]))
            for r in evidence),
        "evidence_codes":dict(sorted(Counter(r["hpoa_evidence_code"] for r in evidence).items())),
        "bibliography_links_verified":0,
        "publication_mapping_status":"No OMIM bibliography retrieved; full OMIM bibliography must not be cross-joined with HPO phenotypes.",
        "evidence_scope":"Original HPOA disease-phenotype annotations only; no gene-to-phenotype assertion generated."
    }
    manifest=out/"omim_provenance_manifest.json"
    manifest.write_text(json.dumps(stats,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    (out/"SHA256SUMS.txt").write_text("".join(
        f"{file_sha(out/name)}  {name}\n" for name in (*files,manifest.name)))
    return stats

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hpoa-authority",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(audit(a.hpoa_authority,a.out),indent=2))
if __name__=="__main__":
    main()
