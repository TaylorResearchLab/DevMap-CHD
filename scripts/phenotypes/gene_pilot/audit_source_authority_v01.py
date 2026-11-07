#!/usr/bin/env python3
"""Classify original HPOA, GenCC and PubMind source evidence by curation authority.

Preserves the original assertion level. HPOA evidence is disease -> phenotype;
GenCC evidence is gene -> disease; PubMind v2 is automated Gene-HPO discovery.
The outputs do not validate inferred direct Gene-HPO claims.
"""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

HPO_FIELDS=("record_id","candidate_id","original_subject","original_object",
            "source_resource","source_release","source_evidence_code",
            "primary_publication_id","source_reference","source_row_id",
            "evidence_role","reference_namespaces","source_curation_status","devmap_disposition",
            "reason")
GENCC_FIELDS=("gencc_id","gencc_version","gene_id","source_disease_id",
              "source_submitter","source_classification",
              "source_curation_status","devmap_disposition","pmid_status","reason")
PUBMIND_FIELDS=("gene_id","gene_symbol","hpo_id","pubmind_publication_count",
                "original_hpo_source_row","source_curation_status",
                "devmap_disposition","reason")

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):h.update(chunk)
    return h.hexdigest()

def read(path,required):
    with path.open(encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f,delimiter="\t")
        missing=set(required)-set(r.fieldnames or ())
        if missing:raise ValueError(f"Missing {sorted(missing)} in {path}")
        for row in r:
            if None in row:raise ValueError(f"Malformed row in {path}")
            yield row

def emit(path,columns,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=columns,delimiter="\t",lineterminator="\n")
        w.writeheader();w.writerows(rows)

def pmids(value):
    return sorted(set(re.findall(r"PMID:\s*([0-9]+)",value or "")))

def namespaces(reference):
    # Source namespaces are presence indicators; a record may cite several.
    labels=set()
    for token in re.split(r"[;,|]",reference or ""):
        token=token.strip()
        if not token:continue
        match=re.match(r"^([A-Za-z][A-Za-z0-9-]*):",token)
        labels.add(match.group(1).upper() if match else "OTHER")
    return ";".join(sorted(labels)) if labels else "EMPTY"

def audit(hpo_path,gencc_path,pubmind_path,out,strict=True):
    # HPOA annotates disease/phenotype, even when linked to a gene discovery row.
    hpo=[]
    seen_evidence=set()
    for row in read(hpo_path,("candidate_id","evidence_id","original_subject",
                              "original_object","source_resource","source_release",
                              "source_evidence_code","primary_publication_id",
                              "original_reference","source_row_id","evidence_role")):
        if row["evidence_id"] in seen_evidence:
            raise ValueError(f"Duplicate HPO source evidence ID: {row['evidence_id']}")
        seen_evidence.add(row["evidence_id"])
        ids=pmids(row["primary_publication_id"])
        # Citation provenance is retained; the original curated disease-HPO
        # observation may be imported, not promoted to direct gene-HPO.
        evidence_code=row["source_evidence_code"].upper()
        electronic=evidence_code=="IEA"
        ref_ns=namespaces(row["original_reference"])
        if ids:
            state="electronic_annotation_with_pmid" if electronic else "expert_curated_with_pmid"
        elif ref_ns!="EMPTY":
            state="electronic_annotation_with_source_reference" if electronic else "expert_curated_with_source_reference"
        else:
            state="electronic_annotation_without_reference" if electronic else "expert_curated_provenance_incomplete"
        hpo.append({
            "record_id":row["evidence_id"],"candidate_id":row["candidate_id"],
            "original_subject":row["original_subject"],
            "original_object":row["original_object"],
            "source_resource":row["source_resource"],
            "source_release":row["source_release"],
            "source_evidence_code":row["source_evidence_code"],
            "primary_publication_id":row["primary_publication_id"],
            "source_reference":row["original_reference"],
            "source_row_id":row["source_row_id"],
            "evidence_role":row["evidence_role"],
            "reference_namespaces":ref_ns,
            "source_curation_status":state,
            "devmap_disposition":("electronic_evidence_review" if electronic else
                                 "imported_source_assertion" if ids else
                                 "provenance_review"),
            "reason":"HPOA disease-phenotype curation; gene-HPO traversal remains discovery only"
        })
    gencc=[]
    seen_gencc=set()
    for row in read(gencc_path,("gencc_id","gencc_version","gene_id",
                               "source_disease_id","source_classification",
                               "source_submitter")):
        key=(row["gencc_id"],row["gencc_version"])
        if key in seen_gencc:raise ValueError(f"Duplicate GenCC source key: {key}")
        seen_gencc.add(key)
        submitter=row["source_submitter"]
        # The original GenCC integration does not carry citation-level PMIDs.
        # Also a ClinGen submitter flag is not itself full source verification.
        gencc.append({
            "gencc_id":key[0],"gencc_version":key[1],
            "gene_id":row["gene_id"],"source_disease_id":row["source_disease_id"],
            "source_submitter":submitter,
            "source_classification":row["source_classification"],
            "source_curation_status":"expert_curated_provenance_incomplete"
                if "clingen" in submitter.lower() else "unresolved_source_type",
            "devmap_disposition":"provenance_review",
            "pmid_status":"not_in_current_gencc_integration_export",
            "reason":"GenCC gene-disease classification; verify source issuer, PMID and version before authority acceptance"
        })
    pubmind=[]
    seen_pubmind=set()
    for row in read(pubmind_path,("gene_id","gene_symbol","hpo_id",
                                 "pubmind_publication_count","source_row")):
        key=(row["gene_id"],row["hpo_id"])
        if key in seen_pubmind:raise ValueError(f"Repeated PubMind association: {key}")
        seen_pubmind.add(key)
        pubmind.append({
            "gene_id":row["gene_id"],"gene_symbol":row["gene_symbol"],
            "hpo_id":row["hpo_id"],
            "pubmind_publication_count":row["pubmind_publication_count"],
            "original_hpo_source_row":row["source_row"],
            "source_curation_status":"automated_extraction",
            "devmap_disposition":"pending_secondary_review",
            "reason":"AI-extracted Gene-HPO association; PVID/HPO-specific PMID and independent review required"
        })
    if strict and (len(hpo)!=63012 or len(gencc)!=4090 or len(pubmind)!=1522):
        raise ValueError(f"Unexpected source counts HPOA={len(hpo)} GenCC={len(gencc)} PubMind={len(pubmind)}")
    out.mkdir(parents=True,exist_ok=True)
    files={
        "hpoa_source_authority.tsv":(HPO_FIELDS,hpo),
        "gencc_source_authority.tsv":(GENCC_FIELDS,gencc),
        "pubmind_source_authority.tsv":(PUBMIND_FIELDS,pubmind)
    }
    for name,(fields,rows) in files.items():emit(out/name,fields,rows)
    result={
        "source_rows":{"HPOA":len(hpo),"GenCC":len(gencc),"PubMind":len(pubmind)},
        "source_curation_status":{
            "HPOA":dict(Counter(x["source_curation_status"] for x in hpo)),
            "GenCC":dict(Counter(x["source_curation_status"] for x in gencc)),
            "PubMind":dict(Counter(x["source_curation_status"] for x in pubmind))},
        "hpoa_rows_with_traceable_pmid":sum(bool(pmids(x["primary_publication_id"])) for x in hpo),
        "hpoa_source_reference_namespaces":dict(sorted(Counter(
            ns for row in hpo for ns in row["reference_namespaces"].split(";") if ns).items())),
        "gencc_rows_with_pmid_in_this_export":0,
        "pubmind_rows_with_hpo_specific_pmid_in_this_export":0,
        "input_sha256":{"hpoa":sha(hpo_path),"gencc":sha(gencc_path),"pubmind":sha(pubmind_path)},
        "policy":"2026-11-07 approved: expert-curated original assertions with traceable PMID importable at original claim scope; PubMind AI extraction requires secondary review",
        "interpretation":"No new direct gene disruption-phenotype PARs approved. HPOA ORPHA/OMIM references are traceable source identifiers, not missing provenance or automatically PMID verified. HPO IEA remains electronically inferred. GenCC missing PMID data requires source-specific retrieval; HPOA original subject is disease."
    }
    manifest=out/"source_authority_manifest.json"
    manifest.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (out/"SHA256SUMS.txt").write_text("".join(
        f"{sha(out/name)}  {name}\n" for name in (*files,manifest.name)))
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hpo-evidence",required=True,type=Path)
    p.add_argument("--gencc-evidence",required=True,type=Path)
    p.add_argument("--pubmind-hpo",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    args=p.parse_args()
    print(json.dumps(audit(args.hpo_evidence,args.gencc_evidence,
                           args.pubmind_hpo,args.out),indent=2))
if __name__=="__main__":
    main()
