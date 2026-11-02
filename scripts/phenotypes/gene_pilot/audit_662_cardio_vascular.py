#!/usr/bin/env python3
"""Audit HPO cardiovascular morphology coverage in all 662 DevMap-CHD genes.

This is a disease-mediated HPO discovery-index census, not direct gene-to-phenotype
proof or pediatric/congenital clinical evidence. No PAR candidates are emitted.
Ontology descendant traversal is based only on OBO is_a relationships at the
pinned HPO v2026-09-01 release. Explicit negative source annotations are kept
separate from positive observations; negative evidence never creates coverage.
"""
from __future__ import annotations
import argparse, csv, hashlib, json
from collections import defaultdict, Counter
from functools import lru_cache
from pathlib import Path

from audit_662_hpo_coverage import tsv_rows, absence, sha256, write_tsv, EXPECTED_G2P_SHA, EXPECTED_HPOA_SHA

OBO_SHA = '93dace952fcb3ec4728818857f6ba76bc2d5312f4d83266519b8694b8e798f22'
ROOTS = {
    'cardiovascular_any': 'HP:0001626',
    'heart_morphology': 'HP:0001627',
    'vascular_morphology': 'HP:0025015',
    'blood_vessel_morphology': 'HP:0033353',
    'great_vessel_morphology': 'HP:0030962',
}


def read_obo(path):
    terms, alt = {}, {}
    data, in_term = {}, False
    def save():
        if not in_term or not data.get('id'):
            return
        terms[data['id']] = dict(data)
        for aid in data.get('alt_id', []):
            if aid in alt and alt[aid] != data['id']:
                raise ValueError(f'Conflicting alt_id {aid}')
            alt[aid] = data['id']
    with path.open(encoding='utf-8') as f:
        for s in f:
            s=s.rstrip('\n\r')
            if s == '[Term]':
                save(); data={'parents':[], 'alt_id': []}; in_term=True
            elif s.startswith('['):
                save(); data={}; in_term=False
            elif in_term and ': ' in s:
                k, v = s.split(': ', 1)
                if k == 'id': data['id'] = v.strip()
                elif k == 'name': data['name'] = v.strip()
                elif k == 'is_a': data['parents'].append(v.split(' ! ', 1)[0].strip())
                elif k == 'alt_id': data['alt_id'].append(v.strip())
                elif k == 'is_obsolete': data['obsolete'] = v.strip() == 'true'
    save()
    for label, root in ROOTS.items():
        if root not in terms or terms[root].get('obsolete'):
            raise ValueError(f'Missing current HPO root {label}: {root}')
    return terms, alt


def descendant_index(terms, alt):
    @lru_cache(None)
    def ancestors(term_id):
        term_id=alt.get(term_id, term_id)
        if term_id not in terms or terms[term_id].get('obsolete'):
            return frozenset()
        seen={term_id}
        for p in terms[term_id]['parents']:
            p = alt.get(p,p)
            if p == term_id: raise ValueError(f'Cycle in HPO at {p}')
            seen.update(ancestors(p))
        return frozenset(seen)
    def categories(hpo_id):
        anc=ancestors(hpo_id)
        return tuple(label for label,root in ROOTS.items() if root in anc)
    return categories


def audit(registry, g2p, hpoa, obo, out, hgnc=None, require_hash=True):
    paths={'genes_to_phenotype':g2p,'phenotype_hpoa':hpoa,'hp_obo':obo,'registry':registry}
    digests={k:sha256(v) for k,v in paths.items()}
    if hgnc:digests['hgnc_crosswalk']=sha256(hgnc)
    if require_hash:
        for k,expected in [('genes_to_phenotype',EXPECTED_G2P_SHA),('phenotype_hpoa',EXPECTED_HPOA_SHA),('hp_obo',OBO_SHA)]:
            if digests[k]!=expected: raise ValueError(f'{k}: input hash differs from pinned HPO v2026-09-01')
    terms,alt=read_obo(obo)
    cats=descendant_index(terms,alt)
    rows=list(tsv_rows(registry, {'hgnc_id','approved_hgnc_symbol'}))
    if len(rows)!=662 or len({r['hgnc_id'] for r in rows})!=662 or len({r['approved_hgnc_symbol'] for r in rows})!=662:
        raise ValueError('Frozen 662-gene registry failed denominator or uniqueness checks')

    # A deterministic optional stable-ID matching path; never guess synonyms.
    ncbi_by_hgnc={}
    if hgnc:
        for r in tsv_rows(hgnc, {'hgnc_id','entrez_id'}):
            n=r['entrez_id'].strip()
            if n.isdecimal():ncbi_by_hgnc[r['hgnc_id']]=n

    by_symbol=defaultdict(list);by_ncbi=defaultdict(list);g2p_count=0
    for r in tsv_rows(g2p, {'ncbi_gene_id','gene_symbol','hpo_id','disease_id'}):
        g2p_count+=1
        by_symbol[r['gene_symbol'].strip()].append(r)
        by_ncbi[r['ncbi_gene_id'].strip()].append(r)

    # One disease/HPO key can have several source evidence rows with independent
    # positive and negative frequency encodings. Preserve both states.
    evidence=defaultdict(lambda:{'positive':set(),'negative':set(),'source_rows':0})
    scanned=Counter()
    for r in tsv_rows(hpoa, {'database_id','hpo_id','aspect','frequency','qualifier','reference','evidence'}):
        scanned['all']+=1
        if r['aspect']!='P': continue
        scanned['P']+=1
        key=r['database_id'].strip(), alt.get(r['hpo_id'].strip(),r['hpo_id'].strip())
        e=evidence[key]
        e['source_rows']+=1
        state='negative' if absence(r) else 'positive'
        # Fingerprint exact original HPOA information; do not count duplicate
        # reference strings as independent cohorts.
        e[state].add((r.get('reference',''),r.get('frequency',''),r.get('evidence',''),r.get('qualifier','')))

    summary=[]; detail=[]; missing_obo_terms=set()
    for gene in rows:
        symbol=gene['approved_hgnc_symbol']
        ncbi=ncbi_by_hgnc.get(gene['hgnc_id'],'')
        matched_ncbi=by_ncbi.get(ncbi,[]) if ncbi else []
        source_rows=matched_ncbi if matched_ncbi else by_symbol.get(symbol,[])
        match='NCBI_GENE_ID' if matched_ncbi else 'SYMBOL_EXACT' if source_rows else 'NO_MATCH'
        pairs={(r['disease_id'].strip(),alt.get(r['hpo_id'].strip(),r['hpo_id'].strip())) for r in source_rows}
        groups={label:{'any':set(),'positive':set(),'negative_only':set(),'mixed':set()} for label in ROOTS}
        for disease,hpo in pairs:
            labels=cats(hpo)
            if not labels and hpo not in terms: missing_obo_terms.add(hpo)
            if not labels: continue
            e=evidence.get((disease,hpo))
            if not e: continue
            has_pos=bool(e['positive']);has_neg=bool(e['negative'])
            for label in labels:
                groups[label]['any'].add((disease,hpo))
                if has_pos: groups[label]['positive'].add((disease,hpo))
                if has_neg and not has_pos: groups[label]['negative_only'].add((disease,hpo))
                if has_neg and has_pos: groups[label]['mixed'].add((disease,hpo))
            detail.append({'hgnc_id':gene['hgnc_id'],'gene_symbol':symbol,'match_method':match,
                'disease_id':disease,'hpo_id':hpo,'hpo_name':terms.get(hpo,{}).get('name',''),
                'categories':'|'.join(labels),'positive_evidence':int(has_pos),'negative_evidence':int(has_neg),
                'source_hpoa_rows':e['source_rows']})
        line={'hgnc_id':gene['hgnc_id'],'gene_symbol':symbol,'match_method':match,
              'hpo_gene_summary_rows':len(source_rows),'hpo_disease_hpo_keys':len(pairs)}
        for label in ROOTS:
            for state in ['any','positive','negative_only','mixed']:
                line[f'{label}_{state}_keys']=len(groups[label][state])
        # Counts mean disease-mediated HPO index coverage. Not clinical causality.
        line['heart_morphology_positive']=int(bool(groups['heart_morphology']['positive']))
        line['vascular_morphology_positive']=int(bool(groups['vascular_morphology']['positive']))
        line['heart_only_positive']=int(bool(groups['heart_morphology']['positive']) and not groups['vascular_morphology']['positive'])
        line['vascular_only_positive']=int(bool(groups['vascular_morphology']['positive']) and not groups['heart_morphology']['positive'])
        line['heart_and_vascular_positive']=int(bool(groups['heart_morphology']['positive']) and bool(groups['vascular_morphology']['positive']))
        line['structural_heart_or_vascular_positive']=int(bool(groups['heart_morphology']['positive'] or groups['vascular_morphology']['positive']))
        line['cardiovascular_any_positive']=int(bool(groups['cardiovascular_any']['positive']))
        line['no_hpo_gene_summary']=int(not source_rows)
        summary.append(line)
    out.mkdir(parents=True,exist_ok=True)
    fields=list(summary[0]);write_tsv(out/'gene_cardio_vascular_662.tsv',summary,fields)
    write_tsv(out/'cardio_vascular_disease_hpo_links.tsv',detail,list(detail[0]) if detail else ['hgnc_id','gene_symbol','match_method','disease_id','hpo_id','hpo_name','categories','positive_evidence','negative_evidence','source_hpoa_rows'])
    write_tsv(out/'genes_without_structural_heart_or_vascular_hpo.tsv',[r for r in summary if not r['structural_heart_or_vascular_positive']],fields)
    write_tsv(out/'genes_with_general_hpo_but_no_structural_cardiovascular_hpo.tsv',[r for r in summary if r['hpo_gene_summary_rows'] and not r['structural_heart_or_vascular_positive']],fields)
    manifest={
      'source_release':'v2026-09-01', 'registry_genes':len(summary),
      'match_scope':'NCBI_GENE_ID_WITH_SYMBOL_FALLBACK' if hgnc else 'APPROVED_SYMBOL_EXACT_ONLY',
      'hpo_gene_summary_rows_scanned':g2p_count, 'hpoa_rows_scanned':scanned['all'],
      'hpoa_P_rows_scanned':scanned['P'],
      'general_hpo_annotated_genes':sum(bool(r['hpo_gene_summary_rows']) for r in summary),
      'general_hpo_unmatched_genes':sum(r['no_hpo_gene_summary'] for r in summary),
      'structural_heart_or_vascular_any_positive_genes':sum(r['structural_heart_or_vascular_positive'] for r in summary),
      'general_hpo_but_no_structural_heart_or_vascular_positive_genes':sum(bool(r['hpo_gene_summary_rows']) and not r['structural_heart_or_vascular_positive'] for r in summary),
      'no_structural_heart_or_vascular_positive_genes':sum(not r['structural_heart_or_vascular_positive'] for r in summary),
      'heart_only_positive_genes':sum(r['heart_only_positive'] for r in summary),
      'vascular_only_positive_genes':sum(r['vascular_only_positive'] for r in summary),
      'heart_and_vascular_positive_genes':sum(r['heart_and_vascular_positive'] for r in summary),
      'broad_cardiovascular_positive_genes':sum(r['cardiovascular_any_positive'] for r in summary),
      'category_counts':{label:{state+'_genes':sum(bool(r[f'{label}_{state}_keys']) for r in summary) for state in ['any','positive','negative_only','mixed']} for label in ROOTS},
      'roots':ROOTS, 'unresolved_hpo_ids':sorted(missing_obo_terms),
      'sha256':digests,
      'interpretation':'Disease-mediated HPO discovery annotation coverage, not direct gene evidence, congenital etiology or pediatric age specificity',
      'clinical_congenital_scope':'NOT_ASSESSED', 'pediatric_age_specificity':'NOT_ASSESSED',
      'ready_for_public_release':False}
    (out/'cardio_vascular_662_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    (out/'SHA256SUMS.txt').write_text(''.join(f'{sha256(p)}  {p.name}\n' for p in sorted(out.iterdir()) if p.is_file() and p.name!='SHA256SUMS.txt'))
    print(json.dumps(manifest,indent=2,sort_keys=True))
    return manifest


def main():
    p=argparse.ArgumentParser(description=__doc__)
    base=Path(__file__).resolve().parent;repo=base.parents[2]
    p.add_argument('--registry',type=Path,default=repo/'data/releases/2026.09.08/genes.tsv')
    p.add_argument('--gene-summary',type=Path,default=base/'inputs/genes_to_phenotype.txt')
    p.add_argument('--hpoa',type=Path,default=base/'inputs/phenotype.hpoa')
    p.add_argument('--obo',type=Path,default=base/'inputs/hp.obo')
    p.add_argument('--out',type=Path,default=base/'results/cardio_vascular_662')
    p.add_argument('--hgnc-complete-set',type=Path)
    p.add_argument('--allow-unpinned-test-inputs',action='store_true',help='Only use with synthetic unit tests')
    a=p.parse_args()
    audit(a.registry,a.gene_summary,a.hpoa,a.obo,a.out,a.hgnc_complete_set,not a.allow_unpinned_test_inputs)

if __name__=='__main__':main()