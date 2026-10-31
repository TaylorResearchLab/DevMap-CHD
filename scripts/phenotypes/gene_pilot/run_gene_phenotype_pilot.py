#!/usr/bin/env python3
"""DevMap-CHD pilot HPO gene associations; source fidelity before phenotype inference.

Two evidence classes remain separate:
  1. HPO genes_to_phenotype gene–phenotype view derived through a disease.
  2. Original HPOA disease–phenotype annotations, if supplied.
Neither constitutes independent directly-observed gene–phenotype evidence.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, re, sys
from collections import defaultdict
from pathlib import Path

GENE_COLUMNS=['ncbi_gene_id','gene_symbol','hpo_id','hpo_name','frequency','disease_id']
HPOA_COLUMNS=['database_id','disease_name','qualifier','hpo_id','reference','evidence','onset','frequency','sex','modifier','aspect','biocuration']
HPO_RE = re.compile(r'^HP:\d{7}$')

def sha256(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()

def records(p,required):
    """Process public HPO TSV with hash-comments and optional header conventions."""
    with p.open(encoding='utf-8-sig',newline='') as fh:
        header=None
        for line_number,line in enumerate(fh,1):
            if not line.strip():continue
            if line.startswith('#'):
                maybe=line.lstrip('#').strip().split('\t')
                if set(required).issubset(set(maybe)):
                    header=maybe
                continue
            vals=next(csv.reader([line],delimiter='\t'))
            if header is None:
                if set(required).issubset(set(vals)):
                    header=vals;continue
                raise ValueError(f'{p.name}:{line_number}: missing recognizable column header; found {vals[:8]}')
            if vals==header:continue
            if len(vals)!=len(header):
                yield line_number,dict(zip(header,vals)),f'COLUMN_COUNT_{len(vals)}_EXPECTED_{len(header)}'
            else:yield line_number,dict(zip(header,vals)),None


def write_tsv(p,fields,rows):
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter='\t',extrasaction='ignore',lineterminator='\n')
        w.writeheader();w.writerows(rows)

def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--genes',type=Path,required=True)
    a.add_argument('--gene-phenotype',type=Path,required=True)
    a.add_argument('--phenotype-hpoa',type=Path,help='Optional disease-phenotype HPOA, same release as gene summary')
    a.add_argument('--out',type=Path,required=True)
    a.add_argument('--source-release',default='unspecified')
    a.add_argument('--expected-gene-sha256',default='')
    a.add_argument('--expected-hpoa-sha256',default='')
    a.add_argument('--gene-registry-github-blob','--registry-blob',default='92143728ae7b5d1105bbdd59c6f08892ec031c0b')
    args=a.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    if args.expected_gene_sha256 and sha256(args.gene_phenotype).lower()!=args.expected_gene_sha256.lower():
        raise SystemExit('ERROR: genes_to_phenotype checksum mismatch: source is NOT pinned release')
    if args.phenotype_hpoa and args.expected_hpoa_sha256 and sha256(args.phenotype_hpoa).lower()!=args.expected_hpoa_sha256.lower():
        raise SystemExit('ERROR: phenotype.hpoa checksum mismatch')
    with args.genes.open(newline='',encoding='utf-8') as f:
        gene_rows=list(csv.DictReader(f,delimiter='\t'))
    assert len(gene_rows)==16 and len(set(r['hgnc_id'] for r in gene_rows))==16 and len(set(r['gene_symbol'] for r in gene_rows))==16
    genes={r['gene_symbol']:r for r in gene_rows}
    direct=[]; anomalies=[]; all_n=0; match_n=0; symbol_seen=set()
    for line,raw,issue in records(args.gene_phenotype,GENE_COLUMNS):
        all_n+=1;symbol=raw.get('gene_symbol','')
        if symbol not in genes:continue
        match_n+=1;symbol_seen.add(symbol)
        if issue or not HPO_RE.match(raw.get('hpo_id','')) or not raw.get('disease_id'):
            anomalies.append({'source':'genes_to_phenotype','source_line':line,'gene_symbol':symbol,'reason':issue or 'MISSING_DISEASE_OR_INVALID_HPO','raw':json.dumps(raw,sort_keys=True)});continue
        rec={'hgnc_id':genes[symbol]['hgnc_id'],'gene_symbol':symbol,'ensembl_gene_id':genes[symbol]['ensembl_gene_id'],
             **{k:raw.get(k,'') for k in GENE_COLUMNS},'source_line':line,
             'annotation_class':'HPO_DISEASE_MEDIATED_GENE_VIEW',
             'direct_gene_phenotype_evidence':'NO_DIRECT_EVIDENCE_FROM_THIS_SOURCE',
             'phenotype_aspect':'UNASSESSED_WITHOUT_HPOA','hpoa_match_count':0,
             'source_release':args.source_release}
        direct.append(rec)
    hpoa=[]; by_key=defaultdict(list); hpoa_n=0
    if args.phenotype_hpoa:
        for line,raw,issue in records(args.phenotype_hpoa,HPOA_COLUMNS):
            hpoa_n+=1
            if issue or not HPO_RE.match(raw.get('hpo_id','')):
                anomalies.append({'source':'phenotype.hpoa','source_line':line,'gene_symbol':'','reason':issue or 'INVALID_HPO','raw':json.dumps(raw,sort_keys=True)});continue
            by_key[(raw['database_id'],raw['hpo_id'])].append((line,raw))
        for r in direct:
            matches=by_key.get((r['disease_id'],r['hpo_id']),[])
            r['hpoa_match_count']=len(matches)
            aspects={v.get('aspect','') for _,v in matches}
            r['phenotype_aspect']='|'.join(sorted(aspects)) if aspects else 'UNMATCHED_HPOA'
            for line,v in matches:
                hpoa.append({'hgnc_id':r['hgnc_id'],'gene_symbol':r['gene_symbol'],
                    'disease_id':r['disease_id'],'hpo_id':r['hpo_id'],'hpoa_source_line':line,
                    **{k:v.get(k,'') for k in HPOA_COLUMNS},'source_release':args.source_release})
    direct.sort(key=lambda r:(r['gene_symbol'],r['disease_id'],r['hpo_id'],r['source_line']))
    hpoa.sort(key=lambda r:(r['gene_symbol'],r['disease_id'],r['hpo_id'],r['hpoa_source_line']))
    counters=[]
    for gene in gene_rows:
        gene_rs=[r for r in direct if r['gene_symbol']==gene['gene_symbol']]
        arows=[r for r in hpoa if r['gene_symbol']==gene['gene_symbol']]
        p_valid=[r for r in gene_rs if 'P' in r['phenotype_aspect'].split('|') and any(x['qualifier']!='NOT' and x['hgnc_id']==r['hgnc_id'] and x['disease_id']==r['disease_id'] and x['hpo_id']==r['hpo_id'] for x in arows)]
        counters.append({**gene,'gene_summary_rows':len(gene_rs),
          'distinct_hpo_terms':len({r['hpo_id'] for r in gene_rs}),
          'distinct_diseases':len({r['disease_id'] for r in gene_rs}),
          'hpoa_matched_rows':sum(int(r['hpoa_match_count']>0) for r in gene_rs),
          'hpoa_confirmed_P_positive_rows':len(p_valid),
          'explicit_not_hpoa_rows':sum(r['qualifier']=='NOT' for r in arows),
          'gene_summary_status':'OBSERVED_IN_SOURCE' if gene_rs else 'NO_ROWS_IN_SEARCHED_HPO_SUMMARY',
          'direct_gene_association_status':'NOT_ASSESSED_FROM_INDEPENDENT_SOURCES'})
    dfields=['hgnc_id','gene_symbol','ensembl_gene_id',*[k for k in GENE_COLUMNS if k!='gene_symbol'],'source_line','annotation_class','direct_gene_phenotype_evidence','phenotype_aspect','hpoa_match_count','source_release']
    write_tsv(args.out/'hpo_disease_mediated_gene_view.tsv',dfields,direct)
    if args.phenotype_hpoa:
        write_tsv(args.out/'matched_hpoa_disease_phenotype.tsv', ['hgnc_id','gene_symbol','disease_id','hpo_id','hpoa_source_line',*[k for k in HPOA_COLUMNS if k!='hpo_id'],'source_release'],hpoa)
    write_tsv(args.out/'gene_coverage.tsv',list(counters[0].keys()),counters)
    write_tsv(args.out/'parse_findings.tsv',['source','source_line','gene_symbol','reason','raw'],anomalies)
    report={'pipeline':'DevMap-CHD human gene phenotype pilot v0.1','source_release':args.source_release,
      'registry_gene_count':len(genes),'registry_github_blob':args.gene_registry_github_blob,
      'input_files':{'gene_phenotype':{'path':str(args.gene_phenotype),'sha256':sha256(args.gene_phenotype)},
                    'phenotype_hpoa':{'path':str(args.phenotype_hpoa),'sha256':sha256(args.phenotype_hpoa)} if args.phenotype_hpoa else None},
      'source_gene_phenotype_rows_total':all_n,'source_gene_phenotype_rows_matched_16':match_n,
      'pilot_gene_summary_rows_valid':len(direct),'pilot_gene_symbols_present_in_source':len(symbol_seen),
      'pilot_gene_symbols_without_source_rows':[r['gene_symbol'] for r in counters if not r['gene_summary_rows']],
      'distinct_disease_ids':len({r['disease_id'] for r in direct}),'distinct_hpo_terms':len({r['hpo_id'] for r in direct}),
      'hpoa_rows_parsed':hpoa_n,'matched_hpoa_rows':len(hpoa),'parse_findings':len(anomalies),
      'direct_gene_phenotype_associations':'NOT_ASSESSED','variant_phenotype_associations':'OUT_OF_SCOPE',
      'hpoa_status':'PROVIDED' if args.phenotype_hpoa else 'NOT_PROVIDED',
      'source_semantics':'gene-level HPO summary derives from gene-to-disease plus disease-to-phenotype, not independent gene observation',
      'source_fidelity':'UNREVIEWED_BY_AGENT_2'}
    (args.out/'run_manifest.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    sums={p.name:sha256(p) for p in args.out.iterdir() if p.is_file()}
    (args.out/'SHA256SUMS.txt').write_text(''.join(f'{h}  {name}\n' for name,h in sorted(sums.items())))
    print(json.dumps(report,indent=2,sort_keys=True))

if __name__=='__main__':main()
