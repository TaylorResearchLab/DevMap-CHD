#!/usr/bin/env python3
"""Screen HPO-linked PubMed abstracts for gene disruption and exact HPO phenotype labels.

Produces machine-detected direct-evidence *review* rows, never accepted PARs.
"""
import argparse
import csv
import hashlib
import json
import re
import ssl
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

DISRUPTION_PATTERNS = [
    ("haploinsufficiency",r"\bhaploinsufficien(?:cy|t)\b"),
    ("loss_of_function",r"\bloss[- ]of[- ]function\b|\b(?:null|truncat(?:ing|ion|ed)|frameshift) variant(?:s)?\b"),
    ("gain_of_function",r"\bgain[- ]of[- ]function\b"),
    ("deletion",r"\b(?:gene|genic) deletions?\b|\bdeletion(?:s)?\b"),
    ("pathogenic_variant",r"\bpathogenic variants?\b"),
    ("disruption_unspecified",r"\b(?:mutations?|variants?|disruptions?)\b")
]
DISRUPTION_PATTERNS=[(name,re.compile(pattern,re.I)) for name,pattern in DISRUPTION_PATTERNS]
NEGATION=re.compile(r"\b(?:no|not|without|absence of|lacked|unaffected by)\b",re.I)
COLUMNS=["candidate_id","gene_id","gene_symbol","disease_id","phenotype_id","phenotype_label",
         "publication_id","abstract_sentence","disruption_lexeme","negation_flag",
         "evidence_decision","source_record","source_sha256"]
REVIEW_COLUMNS=["candidate_id","gene_symbol","phenotype_label","publication_id",
                "reason","evidence_decision"]

def checksum(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1048576),b""):
            h.update(chunk)
    return h.hexdigest()
def read_table(path,cols):
    with open(path,encoding="utf-8-sig",newline="") as f:
        r=csv.DictReader(f,delimiter="\t")
        miss=set(cols)-set(r.fieldnames or [])
        if miss: raise ValueError(f"{path}: missing {sorted(miss)}")
        yield from r
def write_table(path,cols,rows):
    with open(path,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=cols,delimiter="\t",lineterminator="\n")
        w.writeheader();w.writerows(rows)
def load_hpo_labels(path):
    terms={}
    current={}
    def keep():
        if current.get("id","").startswith("HP:") and current.get("name") and not current.get("is_obsolete"):
            terms[current["id"]]=current["name"]
    for line in path.read_text(encoding="utf-8").splitlines():
        if line=="[Term]":
            keep();current={}
        elif line.startswith("["):
            keep();current={}
        elif line.startswith("id: "):current["id"]=line[4:].strip()
        elif line.startswith("name: "):current["name"]=line[6:].strip()
        elif line.startswith("is_obsolete: true"):current["is_obsolete"]=True
    keep()
    if not terms:raise ValueError("No active HPO terms")
    return terms

def fetch_pubmed(pmids,xml_file,ca_bundle,batch_size=80):
    """NCBI PubMed EFetch XML; one request/second, max 80 PMIDs/request."""
    if batch_size<1 or batch_size>80:raise ValueError("batch_size must be 1..80")
    ids=sorted(set(pmids),key=int)
    if not ids:raise ValueError("No valid PMIDs to fetch")
    if not all(re.fullmatch(r"[0-9]+",p) for p in ids):raise ValueError("Non-numeric PMID")
    context=ssl.create_default_context(cafile=str(ca_bundle))
    root=ET.Element("PubmedArticleSet")
    for start in range(0,len(ids),batch_size):
        batch=ids[start:start+batch_size]
        query=urllib.parse.urlencode({"db":"pubmed","id":",".join(batch),"rettype":"abstract","retmode":"xml","tool":"DevMapPhenotypePilot"})
        url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?"+query
        req=urllib.request.Request(url,headers={"User-Agent":"DevMap-CHD phenotype evidence retrieval/0.1"})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req,context=context,timeout=90) as response:
                    data=response.read()
                fragment=ET.fromstring(data)
                for article in fragment.findall("PubmedArticle"):
                    root.append(article)
                break
            except (OSError,ET.ParseError):
                if attempt==2:raise
                time.sleep(2*(attempt+1))
        if start+batch_size<len(ids):time.sleep(1.1)
    xml_file.parent.mkdir(parents=True,exist_ok=True)
    ET.ElementTree(root).write(xml_file,encoding="utf-8",xml_declaration=True)
    return len(root)

def abstracts(xml_file):
    root=ET.parse(xml_file).getroot()
    records={}
    for article in root.findall(".//PubmedArticle"):
        node=article.find("./MedlineCitation/PMID")
        if node is None or not node.text:continue
        pmid=node.text.strip()
        title=" ".join("".join(n.itertext()) for n in article.findall("./MedlineCitation/Article/ArticleTitle"))
        parts=[]
        for abstract in article.findall("./MedlineCitation/Article/Abstract/AbstractText"):
            heading=abstract.attrib.get("Label","")
            parts.append((heading+": " if heading else "")+"".join(abstract.itertext()))
        records[pmid]=(title+" "+" ".join(parts)).strip()
    return records
def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])",text) if s.strip()]
def contains_term(sentence,term):
    return bool(re.search(r"(?<![A-Za-z0-9])"+re.escape(term)+r"(?![A-Za-z0-9])",sentence,re.I))
def source_verified(source,names):
    hashes={}
    for ln in (source/"SHA256SUMS.txt").read_text().splitlines():
        parts=ln.split(None,1)
        if len(parts)!=2:raise ValueError("Invalid source SHA256SUMS")
        key=parts[1].strip()
        if Path(key).name!=key:raise ValueError("Unsafe manifest filename")
        hashes[key]=parts[0]
    for name in names:
        if name not in hashes or checksum(source/name)!=hashes[name]:
            raise ValueError("Source output differs from pinned manifest: "+name)
def screen(source_dir,queue_file,obo,xml_file,out,max_pairs=150):
    source_verified(source_dir,("par_candidates.tsv","par_evidence.tsv","manifest.json"))
    manifest=json.loads((source_dir/"manifest.json").read_text())
    if manifest.get("reference_release")!="HPO:v2026-09-01" or manifest.get("registry_gene_count")!=662:
        raise ValueError("Unexpected input source")
    candidates={r["candidate_id"]:r for r in read_table(source_dir/"par_candidates.tsv",
        ("candidate_id","gene_id","gene_symbol","phenotype_id","disease_id","assertion_state"))}
    labels=load_hpo_labels(obo)
    lead_rows=list(read_table(queue_file,("gene_id","gene_symbol","publication_id","phenotype_count")))
    leads=sorted(lead_rows,key=lambda r:(-int(r["phenotype_count"]),r["gene_symbol"],r["publication_id"]))[:max_pairs]
    allowed={(r["gene_id"],r["publication_id"]) for r in leads}
    by_pair=defaultdict(set)
    for row in read_table(source_dir/"par_evidence.tsv",("candidate_id","primary_publication_id")):
        c=candidates.get(row["candidate_id"])
        if c is None:raise ValueError("Evidence references unknown candidate")
        if c["assertion_state"]!="disease_mediated_candidate_asserted_present":
            continue
        for p in row["primary_publication_id"].split(";"):
            if p.startswith("PMID:") and (c["gene_id"],p) in allowed:
                by_pair[(c["gene_id"],p)].add(row["candidate_id"])
    article_text=abstracts(xml_file)
    out.mkdir(parents=True,exist_ok=True)
    digest=checksum(xml_file)
    matches=[];unresolved=[];considered=0
    for (gid,ref),cids in sorted(by_pair.items()):
        pmid=ref.removeprefix("PMID:")
        article=article_text.get(pmid)
        for cid in sorted(cids):
            c=candidates[cid]
            label=labels.get(c["phenotype_id"])
            considered+=1
            if not article or not label:
                unresolved.append({"candidate_id":cid,"gene_symbol":c["gene_symbol"],
                    "phenotype_label":label or "","publication_id":ref,
                    "reason":"missing_pubmed_text_or_hpo_label","evidence_decision":"not_assessed"})
                continue
            found=False
            for sentence in sentences(article):
                if not contains_term(sentence,c["gene_symbol"]) or not contains_term(sentence,label):continue
                disruptions=[name for name,pattern in DISRUPTION_PATTERNS if pattern.search(sentence)]
                if not disruptions:continue
                found=True
                matches.append({"candidate_id":cid,"gene_id":gid,"gene_symbol":c["gene_symbol"],
                    "disease_id":c["disease_id"],"phenotype_id":c["phenotype_id"],"phenotype_label":label,
                    "publication_id":ref,"abstract_sentence":sentence,
                    "disruption_lexeme":";".join(disruptions),
                    "negation_flag":"yes" if NEGATION.search(sentence) else "no",
                    "evidence_decision":"requires_original_article_verification",
                    "source_record":"PubMed efetch abstract","source_sha256":digest})
            if not found:
                unresolved.append({"candidate_id":cid,"gene_symbol":c["gene_symbol"],
                    "phenotype_label":label,"publication_id":ref,
                    "reason":"no_joint_gene_disruption_phenotype_sentence",
                    "evidence_decision":"not_assessed"})
    write_table(out/"abstract_candidate_sentences.tsv",COLUMNS,matches)
    write_table(out/"abstract_unresolved.tsv",REVIEW_COLUMNS,unresolved)
    summary={"source_hpo_release":manifest["reference_release"],
             "pubmed_xml_sha256":digest,"hpo_obo_sha256":checksum(obo),
             "publication_gene_pairs_requested":len(leads),
             "distinct_pmids_requested":len({r["publication_id"] for r in leads}),
             "pmids_retrieved":len(article_text),"candidate_publication_pairs_screened":considered,
             "screened_sentence_matches":len(matches),
             "candidate_publication_pairs_unresolved":len(unresolved),
             "biological_pars_accepted":0,
             "status":"abstract_screening_only_original_article_verification_required"}
    (out/"abstract_screen_manifest.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    with open(out/"SHA256SUMS.txt","w") as f:
        for name in ("abstract_candidate_sentences.tsv","abstract_unresolved.tsv","abstract_screen_manifest.json"):
            f.write(f"{checksum(out/name)}  {name}\n")
    return summary

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--hpo-dir",type=Path,required=True)
    p.add_argument("--publication-queue",type=Path,required=True)
    p.add_argument("--hpo-obo",type=Path,required=True)
    p.add_argument("--pubmed-xml",type=Path,required=True)
    p.add_argument("--ca-bundle",type=Path,default=Path("/etc/pki/tls/certs/ca-bundle.crt"))
    p.add_argument("--max-gene-publication-pairs",type=int,default=150)
    p.add_argument("--fetch",action="store_true")
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    if args.fetch:
        rows=list(read_table(args.publication_queue,("gene_id","publication_id","phenotype_count")))
        rows.sort(key=lambda r:-int(r["phenotype_count"]))
        pmids=[]
        for row in rows[:args.max_gene_publication_pairs]:
            pmid=row["publication_id"].removeprefix("PMID:")
            if re.fullmatch(r"[0-9]+",pmid):pmids.append(pmid)
        fetched=fetch_pubmed(pmids,args.pubmed_xml,args.ca_bundle)
        print("PubMed articles retrieved:",fetched)
    print(json.dumps(screen(args.hpo_dir,args.publication_queue,args.hpo_obo,
                            args.pubmed_xml,args.out,args.max_gene_publication_pairs),indent=2))
if __name__=="__main__":
    main()
