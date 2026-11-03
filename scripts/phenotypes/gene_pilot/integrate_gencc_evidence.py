#!/usr/bin/env python3
"""Join versioned GenCC gene-disease evidence to HPO phenotype candidate records.

Only identical native disease CURIEs are matched. Inheritance and classification
remain source claims; no direct gene-disruption phenotype assertion is created.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

GD_FIELDS = ["gene_id","gene_symbol","gencc_id","gencc_version","source_disease_id",
             "source_classification","source_inheritance","source_submitter",
             "source_report","source_pmids","source_release_sha256","evidence_role"]
JOIN_FIELDS = ["candidate_id","gene_id","gene_symbol","phenotype_id","disease_id",
               "gencc_id","gencc_version","source_classification","source_inheritance",
               "source_submitter","match_type","evidence_role"]
GAP_FIELDS = ["gene_id","gene_symbol","gencc_assertions","hpo_candidate_count",
              "status"]
def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1048576),b""):
            h.update(block)
    return h.hexdigest()
def table(path, delimiter="\t"):
    with open(path,encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f,delimiter=delimiter)
        if not r.fieldnames:
            raise ValueError(f"Missing header in {path}")
        for item in r:
            yield {k.strip().lower(): (v or "").strip() for k,v in item.items() if k is not None}
def field(row,*choices):
    for name in choices:
        v=row.get(name,"")
        if v:
            return v
    return ""
def output(path,fields,records):
    with open(path,"w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f,fieldnames=fields,delimiter="\t",lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)
def run(source_dir,gencc_file,out):
    manifest=json.loads((source_dir/"manifest.json").read_text(encoding="utf-8"))
    if manifest.get("reference_release")!="HPO:v2026-09-01" or manifest.get("registry_gene_count")!=662:
        raise ValueError("Expected frozen 662 gene HPO source")
    checks={}
    for line in (source_dir/"SHA256SUMS.txt").read_text().splitlines():
        sha,name=line.split(None,1)
        name=name.strip()
        if "/" in name or name.startswith(".") or digest(source_dir/name)!=sha:
            raise ValueError(f"Invalid or mismatched checksum: {name}")
        checks[name]=sha
    for name in ["gene_coverage.tsv","par_candidates.tsv"]:
        if name not in checks:
            raise ValueError("Unverified input "+name)
    coverage=list(table(source_dir/"gene_coverage.tsv"))
    if len(coverage)!=662 or len({r["gene_id"] for r in coverage})!=662:
        raise ValueError("Frozen gene registry mismatch")
    genes={r["gene_id"]:r for r in coverage}
    gene_disease=defaultdict(list)
    for r in table(source_dir/"par_candidates.tsv"):
        if r["gene_id"] not in genes:
            raise ValueError("Unknown candidate gene")
        gene_disease[(r["gene_id"],r["disease_id"])].append(r)
    sep="," if gencc_file.suffix.lower()==".csv" else "\t"
    gencc_sha=digest(gencc_file)
    gd=[]
    seen=set()
    columns_seen=set()
    for row in table(gencc_file,sep):
        columns_seen.update(row)
        gid=field(row,"gene_curie","gene_id")
        if gid not in genes:
            continue
        submission=field(row,"sgc_id")
        version=field(row,"version_number")
        if not submission or not version:
            raise ValueError("GenCC versioned SGC ID and version_number required")
        # Only source-submitted disease CURIEs can be joined to HPO native IDs.
        # MONDO replacement mappings are not assumed to be equivalent.
        disease=field(row,"disease_original_curie","disease_original_id","disease_curie")
        key=(submission,version)
        if key in seen:
            raise ValueError("Duplicate GenCC submission version "+str(key))
        seen.add(key)
        gd.append({
            "gene_id":gid,"gene_symbol":genes[gid]["gene_symbol"],
            "gencc_id":submission,"gencc_version":version,"source_disease_id":disease,
            "source_classification":field(row,"classification_title","classification_label","classification_name","classification"),
            "source_inheritance":field(row,"moi_title","moi_label","moi_name","mode_of_inheritance_title","mode_of_inheritance"),
            "source_submitter":field(row,"submitter_title","submitter_label","submitter_name","submitter"),
            "source_report":field(row,"submitted_as_public_report_url","public_report_url","report_url"),
            "source_pmids":field(row,"submitted_as_pmids","pmids","publication_ids"),
            "source_release_sha256":gencc_sha,
            "evidence_role":"independent_gene_disease_curation"})
    if not {"sgc_id","version_number","gene_curie"}.issubset(columns_seen):
        raise ValueError("GenCC new-format header required (sgc_id, version_number, gene_curie)")
    joins=[]
    by_gene=Counter()
    for r in gd:
        by_gene[r["gene_id"]]+=1
        if not r["source_disease_id"]:
            continue
        for c in gene_disease.get((r["gene_id"],r["source_disease_id"]),()):
            joins.append({
                "candidate_id":c["candidate_id"],"gene_id":r["gene_id"],
                "gene_symbol":r["gene_symbol"],"phenotype_id":c["phenotype_id"],
                "disease_id":c["disease_id"],"gencc_id":r["gencc_id"],
                "gencc_version":r["gencc_version"],
                "source_classification":r["source_classification"],
                "source_inheritance":r["source_inheritance"],
                "source_submitter":r["source_submitter"],
                "match_type":"identical_native_disease_curie",
                "evidence_role":"gene_disease_curation_not_direct_phenotype_evidence"})
    gaps=[{"gene_id":g,"gene_symbol":r["gene_symbol"],
           "gencc_assertions":by_gene[g],
           "hpo_candidate_count":r["candidate_count"],
           "status":"gencc_gene_disease_evidence_no_hpo_candidate"}
          for g,r in genes.items() if int(r["candidate_count"])==0 and by_gene[g]>0]
    gd.sort(key=lambda r:(r["gene_id"],r["gencc_id"],r["gencc_version"]))
    joins.sort(key=lambda r:(r["candidate_id"],r["gencc_id"]))
    gaps.sort(key=lambda r:r["gene_symbol"])
    out.mkdir(parents=True,exist_ok=True)
    files={"gencc_gene_disease_evidence.tsv":(GD_FIELDS,gd),
           "gencc_hpo_exact_disease_matches.tsv":(JOIN_FIELDS,joins),
           "gencc_missing_phenotype_genes.tsv":(GAP_FIELDS,gaps)}
    for name,(fields,rows) in files.items():
        output(out/name,fields,rows)
    summary={"source":"GenCC new format","source_sha256":gencc_sha,
             "hpo_candidate_count":manifest["candidate_count"],
             "gencc_assertions_for_registry_genes":len(gd),
             "genes_with_gencc_assertions":len(by_gene),
             "exact_disease_candidate_matches":len(joins),
             "genes_without_hpo_candidates_with_gencc_evidence":len(gaps),
             "evidence_interpretation":"GenCC gene-disease curation only. Exact source CURIE join to HPO disease-phenotype source is composite inference, not direct gene-disruption phenotype evidence."}
    (out/"gencc_integration_manifest.json").write_text(json.dumps(summary,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    with open(out/"SHA256SUMS.txt","w") as f:
        for name in list(files)+["gencc_integration_manifest.json"]:
            f.write(f"{digest(out/name)}  {name}\n")
    return summary
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--hpo-dir",type=Path,required=True)
    p.add_argument("--gencc",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(run(a.hpo_dir,a.gencc,a.out),indent=2))
if __name__=="__main__":
    main()
