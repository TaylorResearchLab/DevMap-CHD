#!/usr/bin/env python3
"""Audit pinned HPO terms in PubMind v2 and classify cardiac ontology ancestry.

All classifications are based on is_a relationships in the supplied pinned HPO
ontology. Source HPO identifiers remain unchanged in outputs. Does not assign
causal evidence or generate accepted PARs.
"""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path

ROOTS={
    "cardiovascular":"HP:0001626",
    "cardiovascular_morphology":"HP:0030680",
    "heart_morphology":"HP:0001627",
    "cardiovascular_physiology":"HP:0011025",
}
TERM_FIELDS=["source_hpo_id","resolved_hpo_id","name","status","alt_id_mapping",
             "replaced_by","consider","is_cardiovascular","is_cardiovascular_morphology",
             "is_heart_morphology","is_cardiovascular_physiology",
             "severity_descriptor","direct_parent_ids","ontology_depth_to_cardiovascular"]
PAIR_FIELDS=["gene_id","gene_symbol","hpo_id","hpo_name","hpo_status","resolved_hpo_id",
             "cardiovascular","cardiovascular_morphology","heart_morphology",
             "cardiovascular_physiology","severity_descriptor",
             "integration_status","pubmind_publication_count","pubmind_source_row"]

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()

def ontology(path):
    terms={};record=None
    def save():
        if record and "id" in record:
            key=record["id"]
            if key in terms:raise ValueError(f"Duplicate ontology term: {key}")
            terms[key]=record.copy()
    with path.open(encoding="utf-8") as f:
        for raw in f:
            line=raw.strip()
            if line=="[Term]":
                save()
                record={"alt_id":[],"is_a":[],"replaced_by":[],"consider":[],
                        "is_obsolete":False}
            elif line.startswith("["):
                save();record=None
            elif record is not None and ": " in line:
                key,value=line.split(": ",1)
                if key in ("id","name"):record[key]=value
                elif key in ("alt_id","replaced_by","consider"):
                    record[key].append(value.split(" ! ",1)[0])
                elif key=="is_a":
                    record[key].append(value.split(" ! ",1)[0])
                elif key=="is_obsolete":
                    record[key]=value.lower()=="true"
        save()
    alternate={}
    for id_,node in terms.items():
        for alias in node["alt_id"]:
            if alias in alternate or alias in terms:
                raise ValueError(f"Repeated alternate HPO ID {alias}")
            alternate[alias]=id_
    return terms,alternate

def term_classifier(terms,alternate):
    @lru_cache(maxsize=None)
    def ancestors(t):
        if t not in terms:return frozenset()
        collected={t}
        for parent in terms[t]["is_a"]:
            # DAG nodes in HPO: reject cycles on the pinned export via recursion.
            if parent in terms:
                collected.update(ancestors(parent))
        return frozenset(collected)
    def classify(original):
        resolved=original if original in terms else alternate.get(original)
        if not resolved:
            return {"source_hpo_id":original,"resolved_hpo_id":"","name":"",
              "status":"unresolved","alt_id_mapping":"","replaced_by":"","consider":"",
              "is_cardiovascular":0,"is_cardiovascular_morphology":0,
              "is_heart_morphology":0,"is_cardiovascular_physiology":0,
              "severity_descriptor":0,"direct_parent_ids":"","ontology_depth_to_cardiovascular":""}
        node=terms[resolved]
        obsolete=node["is_obsolete"]
        status="obsolete" if obsolete else "alternate_id" if original!=resolved else "active"
        anc=ancestors(resolved) if not obsolete else frozenset()
        flags={f"is_{key}":int(root in anc) for key,root in ROOTS.items()}
        label=node.get("name","")
        # Only explicit, broad severity labels. Other modifiers remain available for review.
        broad=label.casefold().replace("obsolete ","") in {"severity","severe","moderate","mild"}
        dist=""
        root=ROOTS["cardiovascular"]
        if root in anc:
            queue=[(resolved,0)];seen=set()
            while queue:
                term,d=queue.pop(0)
                if term in seen:continue
                seen.add(term)
                if term==root:dist=str(d);break
                queue.extend((p,d+1) for p in terms[term]["is_a"] if p in terms)
        return {"source_hpo_id":original,"resolved_hpo_id":resolved,
                "name":label,"status":status,
                "alt_id_mapping":resolved if resolved!=original else "",
                "replaced_by":";".join(node["replaced_by"]),
                "consider":";".join(node["consider"]),**flags,
                "severity_descriptor":int(broad),
                "direct_parent_ids":";".join(node["is_a"]),
                "ontology_depth_to_cardiovascular":dist}
    return classify

def read_tsv(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f,delimiter="\t")
        if reader.fieldnames is None or len(reader.fieldnames)!=len(set(reader.fieldnames)):
            raise ValueError(f"Malformed input header {path}")
        for row in reader:
            if None in row:raise ValueError(f"Malformed TSV row {path}")
            yield row

def write(path,columns,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=columns,delimiter="\t",lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

def audit(hpo_path,obo_path,out,expected_counts=True):
    pairs=list(read_tsv(hpo_path))
    required={"gene_id","gene_symbol","hpo_id","integration_status",
              "pubmind_publication_count","source_row"}
    if not pairs or not required.issubset(pairs[0]):
        raise ValueError(f"PubMind join lacks columns {sorted(required-set(pairs[0] if pairs else []))}")
    keys=[(x["gene_id"],x["hpo_id"]) for x in pairs]
    if len(keys)!=len(set(keys)):raise ValueError("Repeated Gene-HPO pair")
    if any(not re.fullmatch(r"HP:[0-9]{7}",x["hpo_id"]) for x in pairs):
        raise ValueError("Malformed PubMind HPO IDs")
    terms,alt=ontology(obo_path)
    for name,root in ROOTS.items():
        if root not in terms:raise ValueError(f"Missing HPO root {name}: {root}")
        if terms[root]["is_obsolete"]:raise ValueError(f"Obsolete HPO root {name}: {root}")
    classifier=term_classifier(terms,alt)
    unique=sorted({x["hpo_id"] for x in pairs})
    term_rows=[classifier(x) for x in unique]
    by_term={x["source_hpo_id"]:x for x in term_rows}
    pair_rows=[]
    for x in pairs:
        t=by_term[x["hpo_id"]]
        pair_rows.append({
            "gene_id":x["gene_id"],"gene_symbol":x["gene_symbol"],
            "hpo_id":x["hpo_id"],"hpo_name":t["name"],
            "hpo_status":t["status"],"resolved_hpo_id":t["resolved_hpo_id"],
            "cardiovascular":t["is_cardiovascular"],
            "cardiovascular_morphology":t["is_cardiovascular_morphology"],
            "heart_morphology":t["is_heart_morphology"],
            "cardiovascular_physiology":t["is_cardiovascular_physiology"],
            "severity_descriptor":t["severity_descriptor"],
            "integration_status":x["integration_status"],
            "pubmind_publication_count":x["pubmind_publication_count"],
            "pubmind_source_row":x["source_row"]})
    if expected_counts and (
        len(unique)!=844 or len(pairs)!=1522 or
        sum(x["integration_status"]=="new_pubmind_gene_hpo" for x in pairs)!=947):
        raise ValueError("Input PubMind release does not match frozen v2 comparison")
    def count(rows,field):return sum(int(x[field]) for x in rows)
    stats={
        "input_sha256":{"pubmind_hpo_join":sha(hpo_path),"pinned_hpo_obo":sha(obo_path)},
        "ontology_roots":ROOTS,
        "distinct_hpo_terms":len(unique),"gene_hpo_pairs":len(pairs),
        "new_gene_hpo_pairs":sum(x["integration_status"]=="new_pubmind_gene_hpo" for x in pair_rows),
        "ontology_term_status":dict(Counter(x["status"] for x in term_rows)),
        "cardiovascular_terms":count(term_rows,"is_cardiovascular"),
        "heart_morphology_terms":count(term_rows,"is_heart_morphology"),
        "cardiovascular_physiology_terms":count(term_rows,"is_cardiovascular_physiology"),
        "cardiovascular_pairs":count(pair_rows,"cardiovascular"),
        "new_cardiovascular_pairs":sum(x["cardiovascular"] for x in pair_rows
            if x["integration_status"]=="new_pubmind_gene_hpo"),
        "new_heart_morphology_pairs":sum(x["heart_morphology"] for x in pair_rows
            if x["integration_status"]=="new_pubmind_gene_hpo"),
        "new_cardiovascular_physiology_pairs":sum(x["cardiovascular_physiology"] for x in pair_rows
            if x["integration_status"]=="new_pubmind_gene_hpo"),
        "obsolete_terms":[{"id":x["source_hpo_id"],"label":x["name"],
                            "replaced_by":x["replaced_by"],"consider":x["consider"]}
                          for x in term_rows if x["status"]=="obsolete"],
        "unresolved_terms":[x["source_hpo_id"] for x in term_rows if x["status"]=="unresolved"],
        "caution":"Ontology ancestry is a phenotype category, not evidence of congenital onset or gene causality. Source IDs are retained; obsolete term replacements are not applied automatically."
    }
    out.mkdir(parents=True,exist_ok=True)
    write(out/"pubmind_hpo_terms_ontology_audit.tsv",TERM_FIELDS,term_rows)
    write(out/"pubmind_gene_hpo_cardiovascular_annotations.tsv",PAIR_FIELDS,pair_rows)
    (out/"pubmind_hpo_ontology_manifest.json").write_text(json.dumps(stats,indent=2,sort_keys=True)+"\n")
    names=["pubmind_hpo_terms_ontology_audit.tsv",
           "pubmind_gene_hpo_cardiovascular_annotations.tsv",
           "pubmind_hpo_ontology_manifest.json"]
    (out/"SHA256SUMS.txt").write_text(
        "".join(f"{sha(out/name)}  {name}\n" for name in names))
    return stats

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pubmind-hpo",required=True,type=Path)
    parser.add_argument("--obo",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    print(json.dumps(audit(args.pubmind_hpo,args.obo,args.out),indent=2))
if __name__=="__main__":
    main()
