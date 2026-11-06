#!/usr/bin/env python3
"""Build an evidence review ledger for PubMind cardiovascular phenotype candidates.

Read-only to private PubMind sources. Generates a queue, never accepts claims.
The positional HPO/PVID/publication linkage must come from original PubMind data.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

FIELDS=[
    "candidate_review_id","gene_id","gene_symbol","hpo_id","hpo_name",
    "phenotype_category","pubmind_publication_count",
    "pubmind_hpo_source_row","pubmind_hpo_source_sha256",
    "griffin_source_class","griffin_candidate_flag",
    "hpo_source_status","original_hpo_id","source_variant_dataset",
    "source_release","PVID","variant_annotation_original",
    "variant_hgvs_g","disease_id_original","Publication_ID",
    "source_record_id","publication_mapping_method",
    "publication_specific_pathogenicity_score",
    "evidence_location","source_observation_summary",
    "phenotype_polarity","review_status","reviewer","review_date",
    "review_note"
]
STATUS="awaiting_original_variant_hpo_publication_link"

def read(path):
    with path.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f,delimiter="\t")
        if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError(f"Invalid TSV: {path}")
        for row in reader:
            if None in row:raise ValueError(f"Malformed TSV row: {path}")
            yield row

def sha(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()

def ledger(ontology_pairs,membership,hpo_join,out,expected=True):
    phenotype=list(read(ontology_pairs))
    source=list(read(hpo_join))
    source_index={(r["gene_id"],r["hpo_id"]):r for r in source}
    if len(source_index)!=len(source):raise ValueError("Duplicate PubMind Gene-HPO source pair")
    members={r["gene_id"]:r for r in read(membership)}
    if len(members)!=662 and expected:
        raise ValueError("Expected frozen 662-gene membership")
    collected=[]
    for row in phenotype:
        if row["integration_status"]!="new_pubmind_gene_hpo" or row["cardiovascular"]!="1":
            continue
        key=(row["gene_id"],row["hpo_id"])
        if key not in source_index or key[0] not in members:
            raise ValueError(f"Missing source or membership: {key}")
        orig=source_index[key];m=members[key[0]]
        status="final" if m["griffin_final_2023"]=="1" else (
            "fully_curated_not_final" if m["griffin_fully_curated_not_final_2023"]=="1"
            else "candidate_only" if m["Griffin_2023_Supp_Table_1_All_Candidate_Genes.csv"]=="1"
            else "outside_candidate")
        category="heart_morphology" if row["heart_morphology"]=="1" else (
            "cardiovascular_physiology" if row["cardiovascular_physiology"]=="1"
            else "other_cardiovascular")
        identity=f'{row["gene_id"]}|{row["hpo_id"]}|{orig["source_sha256"]}'
        review_id="dmrev:"+hashlib.sha256(identity.encode()).hexdigest()[:24]
        item={field:"" for field in FIELDS}
        item.update({
            "candidate_review_id":review_id,"gene_id":row["gene_id"],
            "gene_symbol":row["gene_symbol"],"hpo_id":row["hpo_id"],
            "hpo_name":row["hpo_name"],"phenotype_category":category,
            "pubmind_publication_count":row["pubmind_publication_count"],
            "pubmind_hpo_source_row":orig["source_row"],
            "pubmind_hpo_source_sha256":orig["source_sha256"],
            "griffin_source_class":status,
            "griffin_candidate_flag":m["Griffin_2023_Supp_Table_1_All_Candidate_Genes.csv"],
            "hpo_source_status":row["hpo_status"],
            "original_hpo_id":row["hpo_id"],
            "review_status":STATUS
        })
        # No original variant or linked PMID can be inferred from aggregate tables.
        collected.append(item)
    collected.sort(key=lambda r:(0 if r["phenotype_category"]=="heart_morphology"
                                 else 1 if r["phenotype_category"]=="cardiovascular_physiology" else 2,
                                 -int(r["pubmind_publication_count"] or 0),
                                 r["gene_symbol"],r["hpo_id"]))
    if expected and len(collected)!=192:
        raise ValueError(f"Expected 192 new cardiovascular pairs, found {len(collected)}")
    if len({r["candidate_review_id"] for r in collected}) != len(collected):
        raise ValueError("Review identifiers collide")
    out.mkdir(parents=True,exist_ok=True)
    path=out/"pubmind_novel_cardiovascular_evidence_review_queue.tsv"
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS,delimiter="\t",lineterminator="\n")
        writer.writeheader();writer.writerows(collected)
    counts=Counter(r["phenotype_category"] for r in collected)
    classes=Counter(r["griffin_source_class"] for r in collected)
    stats={
      "candidate_pairs":len(collected),
      "distinct_genes":len({r["gene_id"] for r in collected}),
      "phenotype_categories":dict(sorted(counts.items())),
      "griffin_source_classes":dict(sorted(classes.items())),
      "source_sha256":{
         "ontology_annotation":sha(ontology_pairs),
         "frozen_membership_join":sha(membership),
         "pubmind_hpo_join":sha(hpo_join)
      },
      "review_status":STATUS,
      "publication_links_recovered":0,
      "accepted_direct_assertions":0,
      "interpretation":"Each row is a provisional Gene-HPO discovery. Source publication count is aggregated; no specific PVID/PMID linkage is inferred."
    }
    manifest=out/"pubmind_novel_cardiovascular_review_manifest.json"
    manifest.write_text(json.dumps(stats,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"SHA256SUMS.txt").write_text(
        f"{sha(path)}  {path.name}\n{sha(manifest)}  {manifest.name}\n")
    return stats

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ontology-pairs",required=True,type=Path)
    p.add_argument("--membership",required=True,type=Path)
    p.add_argument("--pubmind-hpo",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(ledger(a.ontology_pairs,a.membership,a.pubmind_hpo,a.out),indent=2))
if __name__=="__main__":
    main()
