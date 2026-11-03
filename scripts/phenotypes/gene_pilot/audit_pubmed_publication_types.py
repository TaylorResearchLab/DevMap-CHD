#!/usr/bin/env python3
"""Classify PubMed source types for the frozen DevMap HPO-linked abstract screen."""
import argparse
import csv
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

REVIEW_TYPES = {"review", "systematic review", "meta-analysis"}
PRIMARY_TYPES = {
    "journal article", "case reports", "clinical study", "clinical trial",
    "clinical trial, phase i", "clinical trial, phase ii", "clinical trial, phase iii",
    "clinical trial, phase iv", "observational study", "comparative study",
    "randomized controlled trial", "multicenter study", "evaluation study",
    "validation study"
}
OTHER_TYPES = {
    "editorial", "letter", "comment", "news", "published erratum",
    "guideline", "practice guideline", "consensus development conference",
    "database", "historical article"
}
ARTICLE_COLUMNS = [
    "pmid","title","publication_type","classification","classification_basis",
    "gene_count","genes","gene_publication_pairs","screened_sentence_rows",
    "screened_candidate_publication_pairs","source_xml_sha256"
]
GENE_COLUMNS = [
    "pmid","gene_id","gene_symbol","publication_classification",
    "gene_count_for_publication","phenotype_count_in_queue","screened_sentences",
    "source_role"
]
SENTENCE_COLUMNS = [
    "candidate_id","gene_symbol","phenotype_id","publication_id",
    "publication_classification","publication_types","gene_count_for_publication",
    "original_evidence_decision","review_disposition","abstract_sentence"
]

def sha(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for block in iter(lambda:f.read(1048576),b""):
            h.update(block)
    return h.hexdigest()

def verified(directory,filenames):
    checks={}
    for line in (directory/"SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        parts=line.split(None,1)
        if len(parts)!=2:raise ValueError("Invalid checksum line")
        name=parts[1].strip()
        if Path(name).name!=name or name.startswith("."):
            raise ValueError("Invalid checksum filename")
        checks[name]=parts[0]
    for name in filenames:
        if name not in checks or checks[name]!=sha(directory/name):
            raise ValueError("Unverified input "+str(directory/name))

def tsv(path,columns):
    with open(path,encoding="utf-8-sig",newline="") as f:
        reader=csv.DictReader(f,delimiter="\t")
        missing=set(columns)-set(reader.fieldnames or ())
        if missing:raise ValueError(f"{path}: missing {sorted(missing)}")
        yield from reader

def output(path,columns,rows):
    with open(path,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=columns,delimiter="\t",
                         extrasaction="ignore",lineterminator="\n")
        w.writeheader();w.writerows(rows)

def classify(types):
    lower={x.casefold() for x in types}
    if lower & REVIEW_TYPES:
        return "review_or_meta_analysis","pubmed_publication_type"
    if lower & (PRIMARY_TYPES-{"journal article"}):
        return "primary_study_type","pubmed_publication_type"
    if lower & OTHER_TYPES:
        return "other_nonprimary_or_context","pubmed_publication_type"
    if lower=={"journal article"} or ("journal article" in lower and len(lower)==1):
        return "journal_article_unresolved","generic_pubmed_type"
    return "unclassified","missing_or_noninformative_pubmed_type"

def audit(xml_file,queue_file,screen_dir,out,max_pairs=150):
    if max_pairs<1:raise ValueError("max_pairs must be positive")
    verified(queue_file.parent,(queue_file.name,))
    verified(screen_dir,("abstract_screen_manifest.json","abstract_candidate_sentences.tsv"))
    manifest=json.loads((screen_dir/"abstract_screen_manifest.json").read_text())
    if manifest.get("pubmed_xml_sha256")!=sha(xml_file):
        raise ValueError("PubMed XML checksum differs from original screen")
    if manifest.get("publication_gene_pairs_requested")!=max_pairs:
        raise ValueError("Selection size differs from original PubMed screen")
    queue=sorted(tsv(queue_file,("gene_id","gene_symbol","publication_id","phenotype_count")),
                 key=lambda r:(-int(r["phenotype_count"]),r["gene_symbol"],r["publication_id"]))[:max_pairs]
    pairs=defaultdict(dict)
    for r in queue:
        if not r["publication_id"].startswith("PMID:"):
            raise ValueError("Non-PMID source in publication queue")
        pmid=r["publication_id"][5:]
        if not pmid.isdigit():raise ValueError("Invalid PMID")
        pairs[pmid][r["gene_id"]]=r

    root=ET.parse(xml_file).getroot()
    articles={}
    for node in root.findall("./PubmedArticle"):
        id_node=node.find("./MedlineCitation/PMID")
        if id_node is None or not id_node.text:continue
        pmid=id_node.text.strip()
        if pmid in articles:raise ValueError("Duplicate PubMed record "+pmid)
        title_node=node.find("./MedlineCitation/Article/ArticleTitle")
        title="".join(title_node.itertext()).strip() if title_node is not None else ""
        types=sorted(set("".join(x.itertext()).strip() for x in
                    node.findall("./MedlineCitation/Article/PublicationTypeList/PublicationType")
                    if "".join(x.itertext()).strip()))
        category,basis=classify(types)
        articles[pmid]={"title":title,"types":types,"category":category,"basis":basis}
    missing=sorted(set(pairs)-set(articles))
    if missing:raise ValueError("PMIDs from selected queue missing in PubMed XML: "+",".join(missing[:10]))
    sentences=list(tsv(screen_dir/"abstract_candidate_sentences.tsv",
                       ("candidate_id","gene_id","gene_symbol","phenotype_id",
                        "publication_id","abstract_sentence","evidence_decision")))
    matched=defaultdict(list)
    for row in sentences:
        pmid=row["publication_id"].removeprefix("PMID:")
        if pmid not in pairs or row["gene_id"] not in pairs[pmid]:
            raise ValueError("Screen hit outside original gene-PMID selection")
        matched[pmid].append(row)
    if len(sentences)!=manifest["screened_sentence_matches"]:
        raise ValueError("Screened sentence count differs from original manifest")

    arows=[];grows=[];srows=[]
    for pmid in sorted(pairs,key=int):
        a=articles[pmid]
        assoc=pairs[pmid]
        hits=matched.get(pmid,[])
        distinct={(r["candidate_id"],r["gene_id"]) for r in hits}
        arows.append({"pmid":"PMID:"+pmid,"title":a["title"],
                      "publication_type":";".join(a["types"]),
                      "classification":a["category"],"classification_basis":a["basis"],
                      "gene_count":len(assoc),
                      "genes":";".join(sorted(x["gene_symbol"] for x in assoc.values())),
                      "gene_publication_pairs":len(assoc),
                      "screened_sentence_rows":len(hits),
                      "screened_candidate_publication_pairs":len(distinct),
                      "source_xml_sha256":sha(xml_file)})
        for gid,g in sorted(assoc.items()):
            grows.append({"pmid":"PMID:"+pmid,"gene_id":gid,
                "gene_symbol":g["gene_symbol"],"publication_classification":a["category"],
                "gene_count_for_publication":len(assoc),
                "phenotype_count_in_queue":g["phenotype_count"],
                "screened_sentences":sum(x["gene_id"]==gid for x in hits),
                "source_role":"hpo_citation_lead_not_direct_gene_disruption_evidence"})
        for hit in hits:
            srows.append({"candidate_id":hit["candidate_id"],
                          "gene_symbol":hit["gene_symbol"],"phenotype_id":hit["phenotype_id"],
                          "publication_id":hit["publication_id"],
                          "publication_classification":a["category"],
                          "publication_types":";".join(a["types"]),
                          "gene_count_for_publication":len(assoc),
                          "original_evidence_decision":hit["evidence_decision"],
                          "review_disposition":"requires_original_article_verification",
                          "abstract_sentence":hit["abstract_sentence"]})
    counts=Counter(x["classification"] for x in arows)
    out.mkdir(parents=True,exist_ok=True)
    tables={
        "publication_types.tsv":(ARTICLE_COLUMNS,arows),
        "publication_gene_membership.tsv":(GENE_COLUMNS,grows),
        "screened_sentences_with_publication_type.tsv":(SENTENCE_COLUMNS,srows)
    }
    for name,(fields,rows) in tables.items():output(out/name,fields,rows)
    stats={
        "source_pubmed_xml_sha256":sha(xml_file),
        "source_publication_queue_sha256":sha(queue_file),
        "publication_count":len(arows),
        "selected_gene_publication_pairs":len(queue),
        "multi_gene_publication_count":sum(x["gene_count"]>1 for x in arows),
        "publication_classifications":dict(sorted(counts.items())),
        "screened_sentence_rows":len(srows),
        "screened_sentences_by_publication_classification":dict(sorted(
            Counter(x["publication_classification"] for x in srows).items())),
        "direct_disruption_phenotype_pars_accepted":0,
        "interpretation":"PubMed publication types indicate reviews and study designs; generic Journal Article remains unclassified by study design. All direct evidence requires source-specific biological verification."
    }
    (out/"publication_type_manifest.json").write_text(json.dumps(stats,indent=2,sort_keys=True)+"\n")
    with open(out/"SHA256SUMS.txt","w",encoding="utf-8") as f:
        for filename in (*tables,"publication_type_manifest.json"):
            f.write(f"{sha(out/filename)}  {filename}\n")
    return stats

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--pubmed-xml",type=Path,required=True)
    p.add_argument("--publication-queue",type=Path,required=True)
    p.add_argument("--screen-dir",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--max-gene-publication-pairs",type=int,default=150)
    args=p.parse_args()
    print(json.dumps(audit(args.pubmed_xml,args.publication_queue,args.screen_dir,args.out,
                           args.max_gene_publication_pairs),indent=2))
if __name__=="__main__":
    main()
