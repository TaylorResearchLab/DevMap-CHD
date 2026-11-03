#!/usr/bin/env python3
"""Inventory existing PubMind OWLNETS node/edge files without modifying source data."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path

EXTENSIONS={".csv",".tsv",".txt",".gz",".parquet",".jsonl"}
SIGNALS=("pvid","hpo","mondo","publication","pubmed","pmid","pmcid",
         "variant","mutation","phenotype","gene","subject","object",
         "predicate","source","target","score","pathogenic","evidence")
def open_text(path):
    return gzip.open(path,"rt",encoding="utf-8-sig",errors="replace",newline="") if path.suffix.lower()==".gz" else open(path,"r",encoding="utf-8-sig",errors="replace",newline="")
def describe(path,root):
    record={"path":str(path.relative_to(root)),"size_bytes":path.stat().st_size}
    suffixes=[x.lower() for x in path.suffixes]
    if ".parquet" in suffixes:
        record["format"]="parquet"
        try:
            import pyarrow.parquet as pq
            schema=pq.read_schema(path)
            record["columns"]=list(schema.names)
            record["row_count_metadata"]=pq.ParquetFile(path).metadata.num_rows
        except ImportError:
            record["error"]="Install pyarrow on HPC or provide parquet schema with a local tool"
        except Exception as exc:
            record["error"]=type(exc).__name__+": "+str(exc)[:180]
    elif ".jsonl" in suffixes:
        record["format"]="jsonl"
        try:
            with open_text(path) as f:
                for line in f:
                    if line.strip():
                        obj=json.loads(line)
                        record["columns"]=sorted(obj) if isinstance(obj,dict) else []
                        break
        except Exception as exc:
            record["error"]=type(exc).__name__+": "+str(exc)[:180]
    else:
        record["format"]="delimited_text"
        try:
            with open_text(path) as f:
                head=f.readline().rstrip("\r\n")
            if not head:
                record["error"]="Empty source"
            else:
                sep="\t" if head.count("\t")>=head.count(",") else ","
                record["delimiter"]="TAB" if sep=="\t" else "COMMA"
                record["columns"]=[x.strip().strip('"').lstrip("#") for x in next(csv.reader([head],delimiter=sep))]
                if len(record["columns"])==1:
                    record["note"]="Single-field line: verify file is a table and not metadata"
        except Exception as exc:
            record["error"]=type(exc).__name__+": "+str(exc)[:180]
    cols=record.get("columns",[])
    record["suggested_roles"]=[s for s in SIGNALS if any(s in col.lower() for col in cols)]
    record["probable_edge_table"]=any(c.lower() in ("subject","source","node1","subject_id") for c in cols) and any(c.lower() in ("object","target","node2","object_id") for c in cols)
    return record
def inspect(root,registry,out,max_files=1000):
    if not root.is_dir():raise ValueError(f"Missing PubMind directory: {root}")
    if not registry.is_file():raise ValueError(f"Missing registry file: {registry}")
    with registry.open(encoding="utf-8-sig",newline="") as f:
        genes=list(csv.DictReader(f,delimiter="\t"))
    if len(genes)!=662 or len({g["hgnc_id"] for g in genes})!=662:
        raise ValueError("Frozen DevMap registry must have 662 unique HGNC IDs")
    paths=sorted(p for p in root.rglob("*") if p.is_file() and
                 (p.suffix.lower() in EXTENSIONS or any(x.lower() in EXTENSIONS for x in p.suffixes)))
    if len(paths)>max_files:raise ValueError(f"{len(paths)} files exceed max-files={max_files}")
    records=[describe(p,root) for p in paths]
    summary={"root":str(root),"registry":str(registry),"registry_genes":662,
             "file_count":len(records),"file_formats":{},
             "files_with_hpo_columns":[],"files_with_pubmind_variant_columns":[],
             "files_with_publication_columns":[],"files_with_mondo_columns":[],
             "files":records}
    for r in records:
        fmt=r["format"]
        summary["file_formats"][fmt]=summary["file_formats"].get(fmt,0)+1
        signals=r["suggested_roles"]
        for label,terms in (("files_with_hpo_columns",("hpo","phenotype")),
                            ("files_with_pubmind_variant_columns",("pvid","variant","mutation")),
                            ("files_with_publication_columns",("pmid","pmcid","publication","pubmed")),
                            ("files_with_mondo_columns",("mondo",))):
            if any(t in signals for t in terms):summary[label].append(r["path"])
    out.mkdir(parents=True,exist_ok=True)
    target=out/"pubmind_source_inventory.json"
    target.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    h=hashlib.sha256(target.read_bytes()).hexdigest()
    (out/"SHA256SUMS.txt").write_text(f"{h}  {target.name}\n",encoding="utf-8")
    return {k:v for k,v in summary.items() if k!="files"}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--root",type=Path,default=Path("/mnt/isilon/opentargets/U24KG/data/owlnets_nodes_and_edges/pubmind"))
    p.add_argument("--registry",type=Path,default=Path("data/releases/2026.09.08/genes.tsv"))
    p.add_argument("--out",type=Path,default=Path("results/phenotypes/pubmind_raw_inventory_v01"))
    p.add_argument("--max-files",type=int,default=1000)
    args=p.parse_args()
    print(json.dumps(inspect(args.root,args.registry,args.out,args.max_files),indent=2))
if __name__=="__main__":
    main()
