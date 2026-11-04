#!/usr/bin/env python3
"""Join frozen CHD gene source-membership v2 to PubMind phenotype coverage.

Source memberships are provenance indicators, not independent biological votes.
Reads the existing frozen release in place. Never modifies its files.
"""
import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

MEMBERSHIP = [
    "CHDGENE_table_10Aug26.csv",
    "ClinGen_Dosage_GENE-only_10Aug26.csv",
    "Dong observed recessive 23",
    "Dong recessive 108",
    "GenCC_data_Aug10_2026",
    "Griffin_2023_Supp_Table_1_All_Candidate_Genes.csv",
    "Griffin_2023_Supp_Table_2_All_Curated_Genes.csv",
    "Griffin_2023_Supp_Table_3_Curated_De_Novo Variants.csv",
    "Griffin_2023_Supp_Table_4_Curated_LoF_Variants.csv",
    "Griffin_2023_Supp_Table_5_Curated_Recessive_Variants.csv",
    "Griffin_2023_fully_curated_not_final_n196.csv",
    "Griffin_2023_table1_isolated.csv",
    "Griffin_2023_table1_syndromic.csv",
    "Sierant dominant 60",
]
FINAL = ["Griffin_2023_table1_isolated.csv", "Griffin_2023_table1_syndromic.csv"]
NOT_FINAL = "Griffin_2023_fully_curated_not_final_n196.csv"
CANDIDATE = "Griffin_2023_Supp_Table_1_All_Candidate_Genes.csv"
CURATED = "Griffin_2023_Supp_Table_2_All_Curated_Genes.csv"
MATRIX_FILENAME = "CHD_Gene_Source_Membership_Matrix_v2_ids_canonical.tsv"

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for part in iter(lambda: f.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()

def read_table(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        header = f.readline()
        if not header:
            raise ValueError(f"Empty input: {path}")
        sep = "\t" if header.count("\t") >= header.count(",") else ","
        f.seek(0)
        reader = csv.DictReader(f, delimiter=sep)
        if not reader.fieldnames or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError(f"Invalid or duplicate header: {path}")
        for i, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"Malformed row {i}: {path}")
            yield {k: (v or "").strip() for k, v in row.items()}

def binary(value, field, gene):
    if value not in ("0", "1", "0.0", "1.0"):
        raise ValueError(f"Expected 0/1 membership for {gene}, {field}: {value!r}")
    return int(float(value))

def locate_matrix(source):
    if source.is_file():
        return source
    preferred = source / MATRIX_FILENAME
    if preferred.is_file():
        return preferred
    alternate = source / MATRIX_FILENAME.replace(".tsv", ".csv")
    if alternate.is_file():
        return alternate
    hits = sorted(p for p in source.rglob("*") if p.is_file()
                  and p.name.startswith("CHD_Gene_Source_Membership_Matrix_v2_ids_canonical")
                  and p.suffix in (".tsv", ".csv"))
    if len(hits) != 1:
        raise ValueError(f"Expected one frozen v2 membership matrix in {source}, found {len(hits)}: {hits[:8]}")
    return hits[0]

def integrate(matrix_path, coverage_path, hpo_path, output):
    matrix_path = locate_matrix(matrix_path)
    source = list(read_table(matrix_path))
    if len(source) != 662:
        raise ValueError(f"Frozen matrix expected 662 genes, found {len(source)}")
    # Canonical release column labels; never derive membership from original symbols.
    missing = [x for x in ("HGNC ID", "Approved HGNC symbol", *MEMBERSHIP)
               if x not in source[0]]
    if missing:
        raise ValueError(f"Frozen matrix missing fields: {missing}")
    matrix = {}
    for row in source:
        gid = row["HGNC ID"]
        if not gid.startswith("HGNC:") or gid in matrix:
            raise ValueError(f"Missing or repeated canonical HGNC ID: {gid}")
        for field in MEMBERSHIP:
            row[field] = str(binary(row[field], field, gid))
        matrix[gid] = row
    if sum(int(x[NOT_FINAL]) for x in matrix.values()) != 196:
        raise ValueError("Expected Griffin fully curated but not final = 196")
    if sum(int(x[CANDIDATE]) for x in matrix.values()) != 556:
        raise ValueError("Expected Griffin canonical candidate = 556")
    if sum(int(x[FINAL[0]]) or int(x[FINAL[1]]) for x in matrix.values()) != 99:
        raise ValueError("Expected Griffin final union = 99")
    for gid,row in matrix.items():
        final = int(row[FINAL[0]]) or int(row[FINAL[1]])
        if final and int(row[NOT_FINAL]):
            raise ValueError(f"Mutually exclusive Griffin classes overlap: {gid}")

    coverage = list(read_table(coverage_path))
    if len(coverage) != 662:
        raise ValueError(f"PubMind coverage expected 662 genes, found {len(coverage)}")
    joined, seen = [], set()
    for row in coverage:
        gid = row.get("gene_id", "")
        if gid not in matrix or gid in seen:
            raise ValueError(f"Unmatched or repeated PubMind gene ID: {gid}")
        seen.add(gid)
        src = matrix[gid]
        if row.get("gene_symbol") != src["Approved HGNC symbol"]:
            raise ValueError(f"Canonical symbol mismatch for {gid}: {row.get('gene_symbol')} vs {src['Approved HGNC symbol']}")
        out = dict(row)
        for field in MEMBERSHIP:
            out[field] = src[field]
        out["griffin_final_2023"] = str(int(any(int(src[k]) for k in FINAL)))
        out["griffin_fully_curated_not_final_2023"] = src[NOT_FINAL]
        joined.append(out)
    if set(matrix) != seen:
        raise ValueError("Registry sets differ between PubMind and frozen source matrix")

    hpo = list(read_table(hpo_path))
    gene_pair_count = Counter()
    new_pair_count = Counter()
    for row in hpo:
        gid = row.get("gene_id", "")
        if gid not in seen:
            raise ValueError(f"Unmatched PubMind HPO association: {gid}")
        gene_pair_count[gid] += 1
        if row.get("integration_status") == "new_pubmind_gene_hpo":
            new_pair_count[gid] += 1

    for row in joined:
        gid = row["gene_id"]
        if int(row["pubmind_hpo_pairs"]) != gene_pair_count[gid]:
            raise ValueError(f"PubMind HPO count mismatch: {gid}")
        if int(row["pubmind_hpo_new_pairs"]) != new_pair_count[gid]:
            raise ValueError(f"New HPO count mismatch: {gid}")

    fieldnames = list(coverage[0]) + MEMBERSHIP + [
        "griffin_final_2023", "griffin_fully_curated_not_final_2023"]
    output.mkdir(parents=True,exist_ok=True)
    report = output / "pubmind_gene_source_membership_662.tsv"
    with report.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fieldnames,delimiter="\t",lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(joined,key=lambda x:x["gene_symbol"]))

    new_genes = [row for row in joined if row["has_pubmind_hpo"] == "1"
                 and row["has_hpo_discovery"] == "0"]
    if len(new_genes)!=31:
        raise ValueError(f"Expected 31 newly covered genes, found {len(new_genes)}")
    new_gene_report=output/"pubmind_31_new_genes_source_membership.tsv"
    with new_gene_report.open("w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=fieldnames,delimiter="\t",lineterminator="\n")
        writer.writeheader()
        writer.writerows(sorted(new_genes,key=lambda x:x["gene_symbol"]))

    def summarize(rows):
        return {
            "genes":len(rows),
            "pubmind_hpo_pairs":sum(int(x["pubmind_hpo_pairs"]) for x in rows),
            "pubmind_new_hpo_pairs":sum(int(x["pubmind_hpo_new_pairs"]) for x in rows),
            "griffin_final":sum(int(x["griffin_final_2023"]) for x in rows),
            "griffin_fully_curated_not_final":sum(int(x[NOT_FINAL]) for x in rows),
            "griffin_candidate":sum(int(x[CANDIDATE]) for x in rows),
            "griffin_not_candidate":sum(not int(x[CANDIDATE]) for x in rows)
        }

    summary = {
        "source_matrix_path":str(matrix_path),
        "matrix_sha256":sha(matrix_path),
        "pubmind_coverage_sha256":sha(coverage_path),
        "pubmind_hpo_join_sha256":sha(hpo_path),
        "source_membership_columns":MEMBERSHIP,
        "all_genes":summarize(joined),
        "genes_newly_covered_by_pubmind":summarize(new_genes),
        "newly_covered_gene_symbols":sorted(x["gene_symbol"] for x in new_genes),
        "interpretation":"One-hot membership records original source inclusion, not validation or phenotype evidence. Griffin final and curated-not-final are disjoint. No direct phenotype PARs accepted."
    }
    if summary["all_genes"]["pubmind_hpo_pairs"] != 1522 or summary["all_genes"]["pubmind_new_hpo_pairs"] != 947:
        raise ValueError("PubMind integration totals differ from frozen baseline")
    path=output/"pubmind_source_membership_manifest.json"
    path.write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (output/"SHA256SUMS.txt").write_text(
        "".join(f"{sha(output/n)}  {n}\n" for n in [
          report.name,new_gene_report.name,path.name]),encoding="utf-8")
    return summary

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--membership-release",required=True,type=Path)
    p.add_argument("--pubmind-coverage",required=True,type=Path)
    p.add_argument("--pubmind-hpo",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    a=p.parse_args()
    print(json.dumps(integrate(a.membership_release,a.pubmind_coverage,
                               a.pubmind_hpo,a.out),indent=2))
if __name__=="__main__":
    main()
