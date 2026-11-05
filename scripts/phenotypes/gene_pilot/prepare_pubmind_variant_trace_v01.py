#!/usr/bin/env python3
"""Prepare PubMind variant-level review queue without conflating gene-level sources.

The PubMind v2 tables preserve Gene-HPO publication counts but lack the original
HPO-specific PVID/PMID pairs. This script records the target source summary
and gene-level publication candidates explicitly as *unlinked* leads.
"""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

TARGETS=(("HAND1","HP:0001961"),("GJC1","HP:0001631"),("ID2","HP:0012248"))
GENE_SOURCE_FIELDS=("source_type","gene_symbol","source_identifier")
FIELDS=("gene","hpo_id","hpo_label","hpo_unique_publications",
        "griffin_status","pubmind_status","gene_publication_leads",
        "gene_mondo_associations","pvid_hpo_publication_link_status",
        "source_hpo_row","source_hpo_sha256")
LEAD_FIELDS=("gene","hpo_id","publication_id","min_pathogenicity_score",
             "mean_pathogenicity_score","max_pathogenicity_score",
             "n_PVID_with_numeric_score","association_provenance",
             "link_role","source_row")

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):
            h.update(part)
    return h.hexdigest()

def tsv(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        rd=csv.DictReader(f,delimiter="\t")
        if rd.fieldnames is None or len(set(rd.fieldnames))!=len(rd.fieldnames):
            raise ValueError(f"Invalid TSV header: {path}")
        for row in rd:
            if None in row:raise ValueError(f"Malformed TSV row: {path}")
            yield row

def labels_from_obo(path):
    labels={}; term=None; name=None; obsolete=False
    def save():
        if term and name:labels[term]={"name":name,"obsolete":obsolete}
    with path.open(encoding="utf-8") as f:
        for line in f:
            line=line.rstrip("\r\n")
            if line=="[Term]":
                save();term=None;name=None;obsolete=False
            elif line.startswith("id: HP:"):
                term=line[4:]
            elif line.startswith("name: ") and term:
                name=line[6:]
            elif line=="is_obsolete: true" and term:
                obsolete=True
        save()
    return labels

def trace(hpo_path,source_path,membership_path,obo_path,out,targets=TARGETS):
    hpo={}
    for r in tsv(hpo_path):
        key=(r.get("gene_symbol",""),r.get("hpo_id",""))
        if key in targets:
            if key in hpo:raise ValueError(f"Duplicate HPO pair: {key}")
            hpo[key]=r
    matrix={r["gene_symbol"]:r for r in tsv(membership_path)}
    sources=defaultdict(lambda:defaultdict(list))
    for r in tsv(source_path):
        if r.get("gene_symbol") in {g for g,_ in targets}:
            for field in GENE_SOURCE_FIELDS:
                if field not in r:raise ValueError(f"Missing source field {field}")
            sources[r["gene_symbol"]][r["source_type"]].append(r)
    ontology=labels_from_obo(obo_path)
    summary_rows=[];publication_leads=[]
    for gene,term in targets:
        key=(gene,term)
        if key not in hpo or gene not in matrix:
            raise ValueError(f"Missing required target {gene} {term}")
        x=hpo[key];m=matrix[gene]
        if m["griffin_final_2023"]=="1":status="Griffin final"
        elif m["griffin_fully_curated_not_final_2023"]=="1":status="Griffin curated not final"
        elif m["Griffin_2023_Supp_Table_1_All_Candidate_Genes.csv"]=="1":status="Griffin candidate"
        else:status="outside Griffin candidate"
        pubs=sources[gene]["PubMind_publication"]
        mondos=sources[gene]["PubMind_MONDO"]
        record=ontology.get(term)
        if not record: raise ValueError(f"Unknown HPO term in pinned ontology: {term}")
        if record["obsolete"]:raise ValueError(f"Target HPO term is obsolete: {term}")
        summary_rows.append({
            "gene":gene,"hpo_id":term,"hpo_label":record["name"],
            "hpo_unique_publications":x.get("pubmind_publication_count",""),
            "griffin_status":status,"pubmind_status":x.get("integration_status",""),
            "gene_publication_leads":len(pubs),
            "gene_mondo_associations":len(mondos),
            "pvid_hpo_publication_link_status":"not_available_in_aggregated_v2_tables",
            "source_hpo_row":x.get("source_row",""),
            "source_hpo_sha256":x.get("source_sha256","")
        })
        for p in pubs:
            publication_leads.append({
                "gene":gene,"hpo_id":term,
                "publication_id":p["source_identifier"],
                "min_pathogenicity_score":p.get("source_pathogenicity_min",""),
                "mean_pathogenicity_score":p.get("source_pathogenicity_mean",""),
                "max_pathogenicity_score":p.get("source_pathogenicity_max",""),
                "n_PVID_with_numeric_score":p.get("source_numeric_pvid_count",""),
                "association_provenance":p.get("association_provenance",""),
                "link_role":"gene_level_publication_lead_not_hpo_specific_evidence",
                "source_row":p.get("source_row","")
            })
    out.mkdir(parents=True,exist_ok=True)
    def write(name,fields,rows):
        p=out/name
        with p.open("w",encoding="utf-8",newline="") as f:
            w=csv.DictWriter(f,fieldnames=fields,delimiter="\t",lineterminator="\n")
            w.writeheader();w.writerows(rows)
    write("priority_gene_hpo_source_review.tsv",FIELDS,summary_rows)
    write("gene_level_publication_leads_unlinked.tsv",LEAD_FIELDS,publication_leads)
    manifest={
        "targets":[{"gene":g,"hpo_id":h} for g,h in targets],
        "target_hpo_pairs":len(summary_rows),
        "gene_level_publication_leads":len(publication_leads),
        "input_sha256":{
            "hpo_join":sha(hpo_path),"pubmind_source_summaries":sha(source_path),
            "frozen_source_membership_join":sha(membership_path),"hpo_ontology":sha(obo_path)},
        "source_limitation":"Gene-Publication associations in PubMind v2 are not necessarily HPO-specific; no original variant PVID, positional HPO-to-PMID, or patient observation can be reconstructed from these summaries.",
        "next_source":"Original PubMind SNV variant-level export with HPO IDs and positionally matched publication reference identifiers."
    }
    (out/"priority_pubmind_source_review_manifest.json").write_text(
        json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"SHA256SUMS.txt").write_text("".join(
        f"{sha(out/name)}  {name}\n" for name in (
            "priority_gene_hpo_source_review.tsv",
            "gene_level_publication_leads_unlinked.tsv",
            "priority_pubmind_source_review_manifest.json")),encoding="utf-8")
    return summary_rows,manifest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--hpo-join",type=Path,required=True)
    p.add_argument("--source-summaries",type=Path,required=True)
    p.add_argument("--source-membership",type=Path,required=True)
    p.add_argument("--obo",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    rows,manifest=trace(a.hpo_join,a.source_summaries,a.source_membership,a.obo,a.out)
    print(json.dumps({"review_rows":rows,"publication_leads":manifest["gene_level_publication_leads"],
                      "source_limitation":manifest["source_limitation"]},indent=2))
if __name__=="__main__":
    main()
