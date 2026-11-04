#!/usr/bin/env python3
"""Integrate Aditya Lahiri's PubMind v2 summaries with 662-gene HPO/GenCC evidence.

Preserves source rows and positional-publication support counts. Does not infer
that a gene-level PubMind publication supports a particular HPO term.
"""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

HPO_FIELDS = ["gene_id", "gene_symbol", "hpo_id", "pubmind_publication_count",
              "pubmind_gene_provenance", "pubmind_association_provenance",
              "hpo_candidate_ids", "hpo_candidate_count",
              "gencc_supported_candidate_count", "integration_status",
              "source_row", "source_sha256"]
GENE_FIELDS = ["gene_id", "gene_symbol", "pubmind_hpo_pairs",
               "pubmind_mondo_pairs", "pubmind_publication_pairs",
               "hpo_candidate_count", "gencc_assertions",
               "has_pubmind_hpo", "has_hpo_discovery", "has_gencc",
               "pubmind_hpo_new_pairs", "source_coverage"]
SOURCE_FIELDS = ["source_type", "gene_id", "gene_symbol", "source_identifier",
                 "source_publication_count", "source_pathogenicity_min",
                 "source_pathogenicity_mean", "source_pathogenicity_max",
                 "source_numeric_pvid_count", "gene_provenance",
                 "association_provenance", "source_row", "source_sha256"]

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1 << 20),b""):
            h.update(block)
    return h.hexdigest()

def records(path, required):
    with path.open(encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f,delimiter="\t")
        if reader.fieldnames is None:raise ValueError(f"No header in {path}")
        names={x.strip().casefold():x for x in reader.fieldnames}
        missing=set(required)-set(names)
        if missing:raise ValueError(f"Missing columns {sorted(missing)} in {path}")
        for rownum,row in enumerate(reader,2):
            values={k.strip().casefold():(v or "").strip() for k,v in row.items() if k is not None}
            yield rownum,values

def checked_source(directory,names):
    checks={}
    with (directory/"SHA256SUMS.txt").open(encoding="utf-8") as f:
        for line in f:
            parts=line.strip().split(None,1)
            if len(parts)!=2:raise ValueError("Invalid checksum line")
            name=parts[1].strip()
            if Path(name).name!=name or name.startswith("."):
                raise ValueError("Unsafe checksum entry")
            checks[name]=parts[0]
    for name in names:
        if name not in checks or digest(directory/name)!=checks[name]:
            raise ValueError(f"Failed SHA256 input validation: {directory/name}")

def output(path,fields,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fields,delimiter="\t",
                              lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

def value(r,*keys):
    for key in keys:
        found=r.get(key,"")
        if found:return found
    return ""

def nonempty(v):
    return bool(v and v.upper() not in ("NA","N/A","NULL","NONE"))

def integer_count(v):
    if not nonempty(v):return ""
    if not re.fullmatch(r"[0-9]+",v):raise ValueError(f"Invalid publication count {v!r}")
    return str(int(v))

def integrate(registry,hpo_v2,mondo_v2,publications_v2,
              hpo_dir,gencc_dir,out,strict_expected=True):
    paths=[hpo_v2,mondo_v2,publications_v2]
    hashes={p.name:digest(p) for p in paths}
    if len(hashes)!=3:raise ValueError("Three input files need distinct names")
    genes=list(records(registry,("hgnc_id","approved_hgnc_symbol")))
    if len(genes)!=662:raise ValueError("Registry must contain 662 genes")
    gene_map={r["approved_hgnc_symbol"]:r["hgnc_id"] for _,r in genes}
    if len(gene_map)!=662 or len(set(gene_map.values()))!=662:
        raise ValueError("Gene registry contains duplicate symbols or HGNC IDs")
    gene_by_id={v:k for k,v in gene_map.items()}

    checked_source(hpo_dir,("manifest.json","par_candidates.tsv"))
    checked_source(gencc_dir,("gencc_integration_manifest.json",
                              "gencc_gene_disease_evidence.tsv",
                              "gencc_hpo_exact_disease_matches.tsv"))
    hm=json.loads((hpo_dir/"manifest.json").read_text())
    gm=json.loads((gencc_dir/"gencc_integration_manifest.json").read_text())
    if hm.get("registry_gene_count")!=662 or hm.get("reference_release")!="HPO:v2026-09-01":
        raise ValueError("Incorrect HPO source release")
    if gm.get("hpo_candidate_count")!=hm.get("candidate_count"):
        raise ValueError("Incompatible GenCC integration")

    hpo_pairs=defaultdict(set)
    original_candidates={}
    for _,r in records(hpo_dir/"par_candidates.tsv",
                       ("candidate_id","gene_id","phenotype_id")):
        cid=r["candidate_id"]
        if cid in original_candidates:raise ValueError("Duplicate HPO candidate ID")
        original_candidates[cid]=r
        hpo_pairs[(r["gene_id"],r["phenotype_id"])].add(cid)
    if len(original_candidates)!=hm["candidate_count"]:
        raise ValueError("HPO candidate count mismatch")

    g_counts=Counter()
    gencc_ids=set()
    for _,r in records(gencc_dir/"gencc_gene_disease_evidence.tsv",
                       ("gene_id","gencc_id","gencc_version")):
        if r["gene_id"] not in gene_by_id:raise ValueError("GenCC gene outside frozen registry")
        key=(r["gencc_id"],r["gencc_version"])
        if key in gencc_ids:raise ValueError("Duplicate GenCC assertion version")
        gencc_ids.add(key)
        g_counts[r["gene_id"]]+=1
    if len(gencc_ids)!=gm["gencc_assertions_for_registry_genes"]:
        raise ValueError("GenCC source assertion count mismatch")
    supported=set()
    for _,r in records(gencc_dir/"gencc_hpo_exact_disease_matches.tsv",
                       ("candidate_id","gencc_id","gencc_version")):
        if r["candidate_id"] not in original_candidates:
            raise ValueError("Unknown HPO candidate referenced by GenCC")
        if (r["gencc_id"],r["gencc_version"]) not in gencc_ids:
            raise ValueError("Unknown GenCC assertion")
        supported.add(r["candidate_id"])

    per_gene=defaultdict(lambda:Counter())
    hpo_rows=[]
    unique_hpo=set()
    placeholder_hpo=set()
    for lineno,r in records(hpo_v2,
            ("gene","hpo_id","n_unique_publications","gene_provenance","association_provenance")):
        sym=r["gene"]
        if sym not in gene_map:raise ValueError(f"Nonregistry gene in PubMind HPO table: {sym}")
        gid=gene_map[sym]
        hpo=value(r,"hpo_id")
        if not nonempty(hpo):
            placeholder_hpo.add(gid)
            continue
        if not re.fullmatch(r"HP:[0-9]{7}",hpo):
            raise ValueError(f"Invalid PubMind HPO ID at row {lineno}: {hpo}")
        key=(gid,hpo)
        if key in unique_hpo:raise ValueError(f"Duplicate PubMind gene-HPO pair: {key}")
        unique_hpo.add(key)
        per_gene[gid]["hpo"]+=1
        cids=sorted(hpo_pairs.get(key,()))
        supported_count=sum(cid in supported for cid in cids)
        if not cids:per_gene[gid]["new_hpo"]+=1
        hpo_rows.append({
            "gene_id":gid,"gene_symbol":sym,"hpo_id":hpo,
            "pubmind_publication_count":integer_count(r["n_unique_publications"]),
            "pubmind_gene_provenance":r["gene_provenance"],
            "pubmind_association_provenance":r["association_provenance"],
            "hpo_candidate_ids":";".join(cids),"hpo_candidate_count":len(cids),
            "gencc_supported_candidate_count":supported_count,
            "integration_status":"overlap_existing_hpo" if cids else "new_pubmind_gene_hpo",
            "source_row":lineno,"source_sha256":hashes[hpo_v2.name]
        })
    if strict_expected and (len(unique_hpo)!=1522 or
                            len({x[0] for x in unique_hpo})!=347 or
                            len({x[1] for x in unique_hpo})!=844):
        raise ValueError("PubMind v2 HPO counts differ from Aditya's documented release")

    evidence=[]
    for source_type,path,id_field in (
        ("PubMind_MONDO",mondo_v2,"mondo_id"),
        ("PubMind_publication",publications_v2,"publication_id")
    ):
        used=set()
        for lineno,r in records(path,("gene","gene_provenance","association_provenance")):
            sym=r["gene"]
            if sym not in gene_map:raise ValueError(f"Nonregistry gene in {path.name}: {sym}")
            gid=gene_map[sym]
            source_id=value(r,id_field)
            if not nonempty(source_id):continue
            key=(gid,source_id)
            if key in used:raise ValueError(f"Duplicate {source_type} pair: {key}")
            used.add(key)
            per_gene[gid]["mondo" if source_type=="PubMind_MONDO" else "publication"]+=1
            evidence.append({
                "source_type":source_type,"gene_id":gid,"gene_symbol":sym,
                "source_identifier":source_id,
                "source_publication_count":integer_count(value(r,"n_unique_publications")),
                "source_pathogenicity_min":value(r,"min_pathogenicity_score"),
                "source_pathogenicity_mean":value(r,"mean_pathogenicity_score"),
                "source_pathogenicity_max":value(r,"max_pathogenicity_score"),
                "source_numeric_pvid_count":integer_count(value(r,"n_pvid_with_numeric_score")),
                "gene_provenance":value(r,"gene_provenance"),
                "association_provenance":value(r,"association_provenance"),
                "source_row":lineno,"source_sha256":hashes[path.name]
            })
    gene_rows=[]
    hpo_genes={gid for gid,hpo in unique_hpo}
    old_hpo_genes={gid for gid,_ in hpo_pairs}
    for gid,sym in sorted(gene_by_id.items()):
        stats=per_gene[gid]
        hp=stats["hpo"]; hc=sum(len(ids) for (g,_),ids in hpo_pairs.items() if g==gid)
        gc=g_counts[gid]
        gene_rows.append({
            "gene_id":gid,"gene_symbol":sym,
            "pubmind_hpo_pairs":hp,"pubmind_mondo_pairs":stats["mondo"],
            "pubmind_publication_pairs":stats["publication"],
            "hpo_candidate_count":hc,"gencc_assertions":gc,
            "has_pubmind_hpo":int(hp>0),"has_hpo_discovery":int(hc>0),
            "has_gencc":int(gc>0),"pubmind_hpo_new_pairs":stats["new_hpo"],
            "source_coverage":";".join(x for x,b in [
                ("PubMind_HPO",hp>0),("HPO",hc>0),("GenCC",gc>0)] if b) or "none"
        })
    hpo_rows.sort(key=lambda r:(r["gene_symbol"],r["hpo_id"]))
    evidence.sort(key=lambda r:(r["source_type"],r["gene_symbol"],r["source_identifier"]))
    gene_rows.sort(key=lambda r:r["gene_symbol"])
    out.mkdir(parents=True,exist_ok=True)
    tables={
      "pubmind_hpo_to_devmap.tsv":(HPO_FIELDS,hpo_rows),
      "pubmind_mondo_publication_sources.tsv":(SOURCE_FIELDS,evidence),
      "pubmind_gene_coverage_662.tsv":(GENE_FIELDS,gene_rows)}
    for name,(fields,rows) in tables.items():output(out/name,fields,rows)
    overview={
      "registry_genes":662,"pubmind_hpo_pairs":len(unique_hpo),
      "pubmind_hpo_genes":len(hpo_genes),"pubmind_unique_hpo_terms":len({x[1] for x in unique_hpo}),
      "pubmind_no_hpo_genes":662-len(hpo_genes),
      "pubmind_hpo_placeholder_genes":len(placeholder_hpo),
      "pubmind_hpo_pairs_overlapping_hpo":sum(x["hpo_candidate_count"]>0 for x in hpo_rows),
      "pubmind_hpo_pairs_new_to_hpo":sum(x["hpo_candidate_count"]==0 for x in hpo_rows),
      "pubmind_genes_not_in_hpo_discovery":len(hpo_genes-old_hpo_genes),
      "pubmind_mondo_pairs":sum(x["source_type"]=="PubMind_MONDO" for x in evidence),
      "pubmind_gene_publication_pairs":sum(x["source_type"]=="PubMind_publication" for x in evidence),
      "original_hpo_candidates":len(original_candidates),
      "original_gencc_assertions":len(gencc_ids),
      "input_sha256":hashes,
      "status":"provisional_source_summary_no_direct_gene_disruption_pars_accepted",
      "interpretation":"PubMind v2 Gene-HPO publication counts are aggregated. Gene-publication and Gene-MONDO tables cannot be interpreted as PVID-specific HPO source links without the original PubMind positional mappings."
    }
    (out/"pubmind_v2_integration_manifest.json").write_text(json.dumps(overview,indent=2,sort_keys=True)+"\n")
    with (out/"SHA256SUMS.txt").open("w",encoding="utf-8") as f:
        for name in (*tables,"pubmind_v2_integration_manifest.json"):
            f.write(f"{digest(out/name)}  {name}\n")
    return overview

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--registry",type=Path,required=True)
    p.add_argument("--pubmind-hpo",type=Path,required=True)
    p.add_argument("--pubmind-mondo",type=Path,required=True)
    p.add_argument("--pubmind-publications",type=Path,required=True)
    p.add_argument("--hpo-dir",type=Path,required=True)
    p.add_argument("--gencc-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--allow-synthetic-counts",action="store_true",help="Unit tests only")
    a=p.parse_args()
    result=integrate(a.registry,a.pubmind_hpo,a.pubmind_mondo,a.pubmind_publications,
                     a.hpo_dir,a.gencc_dir,a.out,not a.allow_synthetic_counts)
    print(json.dumps(result,indent=2))
if __name__=="__main__":
    main()
