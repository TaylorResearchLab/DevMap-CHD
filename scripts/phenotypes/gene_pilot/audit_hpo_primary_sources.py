#!/usr/bin/env python3
"""Audit leads to original primary studies behind HPO disease-mediated gene annotations.

This reports provenance leads, not proven direct gene-to-phenotype assertions.
Inputs are produced by DevMap-CHD scripts/phenotypes/gene_pilot/run_gene_phenotype_pilot.py.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

KEYS = ('gene_symbol', 'disease_id', 'hpo_id')
PMID_RE = re.compile(r'^(?:PMID|PubMed):\s*([0-9]+)$', re.I)
DOI_RE = re.compile(r'^(?:DOI:)?10\.\d{4,9}/\S+$', re.I)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def read_tsv(path, required):
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f, delimiter='\t')
        cols = reader.fieldnames or []
        if len(cols) != len(set(cols)):
            raise ValueError(f'{path}: duplicate column names')
        missing = set(required) - set(cols)
        if missing:
            raise ValueError(f'{path}: missing columns {sorted(missing)}')
        return list(reader)


def ref_kind(ref):
    r = ref.strip()
    if not r:
        return 'MISSING_REFERENCE'
    if PMID_RE.fullmatch(r):
        return 'PUBMED_PUBLICATION_LEAD'
    if DOI_RE.fullmatch(r):
        return 'DOI_PUBLICATION_LEAD'
    prefix = r.partition(':')[0].upper()
    if prefix in {'OMIM', 'MIM'}:
        return 'OMIM_CURATED_RECORD'
    if prefix in {'ORPHA', 'ORPHANET', 'ORDO'}:
        return 'ORPHANET_CURATED_RECORD'
    if prefix == 'DECIPHER':
        return 'DECIPHER_DATABASE_RECORD'
    if prefix == 'HPO':
        return 'HPO_CURATOR_RECORD'
    if r.lower().startswith(('https://', 'http://')):
        return 'WEB_REFERENCE_REVIEW'
    return 'UNRESOLVED_REFERENCE_TYPE'


def reference_tokens(s):
    # HPOA normally has one reference per row. Retain the original string and
    # record a flag if multiple semicolon-delimited citations are encountered.
    parts = [p.strip() for p in s.split(';') if p.strip()]
    return parts if parts else ['']


def write_tsv(path, fields, rows):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        out = csv.DictWriter(f, delimiter='\t', fieldnames=fields, extrasaction='ignore', lineterminator='\n')
        out.writeheader()
        out.writerows(rows)


def run(gene_file: Path, hpoa_file: Path, out: Path):
    out.mkdir(parents=True, exist_ok=True)
    gene = read_tsv(gene_file, [*KEYS, 'hgnc_id', 'hpo_name', 'annotation_class', 'source_line'])
    hpoa = read_tsv(hpoa_file, [*KEYS, 'hgnc_id', 'hpoa_source_line', 'reference', 'evidence', 'aspect', 'qualifier'])
    lookup = defaultdict(list)
    for row in gene:
        lookup[tuple(row[k] for k in KEYS)].append(row)
    if any(len(rows) > 1 for rows in lookup.values()):
        # A duplicated gene-summary input can generate repeated joined HPOA entries.
        raise ValueError('gene summary has repeated gene/disease/HPO keys; inspect before auditing citations')

    leads = []
    candidates = []
    indirect = []
    unresolved = []
    by_pair = defaultdict(list)
    overall = Counter()
    for r in hpoa:
        key = tuple(r[k] for k in KEYS)
        original = lookup.get(key)
        if not original:
            raise ValueError(f'HPOA join row lacks gene-summary key: {key}')
        if r.get('hgnc_id') != original[0]['hgnc_id']:
            raise ValueError(f'HGNC ID mismatch for {key}')
        overall[(r.get('aspect', ''), r.get('qualifier', ''))] += 1
        for token in reference_tokens(r.get('reference', '')):
            typ = ref_kind(token)
            positive = r['aspect'] == 'P' and r['qualifier'].strip().upper() != 'NOT'
            item = {
                'hgnc_id': r['hgnc_id'], 'gene_symbol': r['gene_symbol'],
                'disease_id': r['disease_id'], 'hpo_id': r['hpo_id'],
                'hpo_name': original[0]['hpo_name'],
                'gene_summary_line': original[0]['source_line'],
                'hpoa_source_line': r['hpoa_source_line'],
                'hpo_aspect': r['aspect'], 'qualifier': r['qualifier'],
                'source_reference': r['reference'], 'reference_token': token,
                'reference_type': typ, 'evidence_code': r['evidence'],
                'frequency': r.get('frequency', ''), 'biocuration': r.get('biocuration', ''),
                'phenotype_positive_P': str(positive).lower(),
                'primary_publication_status': 'CANDIDATE_REQUIRES_FULL_TEXT_CHECK' if typ in {'PUBMED_PUBLICATION_LEAD', 'DOI_PUBLICATION_LEAD'} else 'ORIGINATING_PUBLICATION_NOT_IDENTIFIED',
                'gene_disease_origin_status': 'NOT_CAPTURED_BY_HPO_GENE_SUMMARY',
                'gene_phenotype_direct_source_status': 'NOT_ESTABLISHED'
            }
            leads.append(item)
            if positive:
                by_pair[(r['hgnc_id'], r['hpo_id'])].append(item)
                if typ in {'PUBMED_PUBLICATION_LEAD', 'DOI_PUBLICATION_LEAD'}:
                    candidates.append(item)
                elif typ in {'OMIM_CURATED_RECORD', 'ORPHANET_CURATED_RECORD', 'DECIPHER_DATABASE_RECORD'}:
                    indirect.append(item)
                else:
                    unresolved.append(item)

    fields = ['hgnc_id', 'gene_symbol', 'disease_id', 'hpo_id', 'hpo_name',
              'gene_summary_line', 'hpoa_source_line', 'hpo_aspect', 'qualifier',
              'source_reference', 'reference_token', 'reference_type', 'evidence_code',
              'frequency', 'biocuration', 'phenotype_positive_P',
              'primary_publication_status', 'gene_disease_origin_status',
              'gene_phenotype_direct_source_status']
    leads.sort(key=lambda x: (x['gene_symbol'], x['disease_id'], x['hpo_id'], int(x['hpoa_source_line']), x['reference_token']))
    for path, rows in [
        ('all_hpoa_reference_leads.tsv', leads),
        ('publication_candidates_for_review.tsv', candidates),
        ('curated_database_records_for_followup.tsv', indirect),
        ('unresolved_positive_P_references.tsv', unresolved),
    ]:
        write_tsv(out / path, fields, rows)

    idx = []
    for (hgnc, hpo), rows in sorted(by_pair.items()):
        idx.append({
            'hgnc_id': hgnc,
            'gene_symbol': rows[0]['gene_symbol'],
            'hpo_id': hpo,
            'hpo_name': rows[0]['hpo_name'],
            'diseases': '|'.join(sorted({r['disease_id'] for r in rows})),
            'n_diseases': len({r['disease_id'] for r in rows}),
            'publication_leads': '|'.join(sorted({r['reference_token'] for r in rows if r['reference_type'] in {'PUBMED_PUBLICATION_LEAD', 'DOI_PUBLICATION_LEAD'}})),
            'curated_records': '|'.join(sorted({r['reference_token'] for r in rows if r['reference_type'] in {'OMIM_CURATED_RECORD', 'ORPHANET_CURATED_RECORD', 'DECIPHER_DATABASE_RECORD'}})),
            'evidence_codes': '|'.join(sorted({r['evidence_code'] for r in rows})),
            'n_hpoa_reference_tokens': len(rows),
            'gene_phenotype_direct_source_status': 'NOT_ESTABLISHED'
        })
    write_tsv(out / 'gene_hpo_provenance_index.tsv', [
        'hgnc_id', 'gene_symbol', 'hpo_id', 'hpo_name', 'diseases',
        'n_diseases', 'publication_leads', 'curated_records', 'evidence_codes',
        'n_hpoa_reference_tokens', 'gene_phenotype_direct_source_status'], idx)

    by_gene = defaultdict(list)
    for r in leads:
        by_gene[(r['hgnc_id'], r['gene_symbol'])].append(r)
    gene_summary = []
    for (hgnc, symbol), rows in sorted(by_gene.items(), key=lambda x: x[0][1]):
        pos = [r for r in rows if r['phenotype_positive_P'] == 'true']
        pub = [r for r in pos if r['reference_type'] in {'PUBMED_PUBLICATION_LEAD', 'DOI_PUBLICATION_LEAD'}]
        curated = [r for r in pos if r['reference_type'] in {'OMIM_CURATED_RECORD', 'ORPHANET_CURATED_RECORD', 'DECIPHER_DATABASE_RECORD'}]
        gene_summary.append({
            'hgnc_id': hgnc, 'gene_symbol': symbol,
            'positive_P_source_annotation_rows': len({r['gene_summary_line'] for r in pos}),
            'positive_P_reference_token_rows': len(pos),
            'distinct_P_hpo_terms': len({r['hpo_id'] for r in pos}),
            'distinct_P_disease_ids': len({r['disease_id'] for r in pos}),
            'publication_candidate_reference_rows': len(pub),
            'unique_publication_identifiers': len({r['reference_token'] for r in pub}),
            'PCS_publication_reference_rows': sum(r['evidence_code'] == 'PCS' for r in pub),
            'curated_database_reference_rows': len(curated),
            'unresolved_P_reference_rows': len(pos)-len(pub)-len(curated),
            'other_aspect_or_NOT_source_rows': len(rows)-len(pos),
            'direct_gene_phenotype_evidence_status': 'NOT_ESTABLISHED'
        })
    gene_summary_fields = ['hgnc_id','gene_symbol','positive_P_source_annotation_rows',
        'positive_P_reference_token_rows','distinct_P_hpo_terms','distinct_P_disease_ids',
        'publication_candidate_reference_rows','unique_publication_identifiers',
        'PCS_publication_reference_rows','curated_database_reference_rows',
        'unresolved_P_reference_rows','other_aspect_or_NOT_source_rows',
        'direct_gene_phenotype_evidence_status']
    write_tsv(out / 'gene_source_reference_summary.tsv', gene_summary_fields, gene_summary)

    counts = Counter((r['reference_type'], r['evidence_code'], r['hpo_aspect'], r['qualifier']) for r in leads)
    dist = [{'reference_type': k[0], 'evidence_code': k[1], 'aspect': k[2], 'qualifier': k[3], 'rows': n} for k, n in sorted(counts.items())]
    write_tsv(out / 'reference_evidence_distribution.tsv', ['reference_type', 'evidence_code', 'aspect', 'qualifier', 'rows'], dist)

    manifest = {
        'source_type': 'HPOA_secondary_annotation_provenance_audit',
        'inputs': {'gene_summary': {'path': str(gene_file), 'sha256': sha256(gene_file), 'rows': len(gene)},
                   'matched_hpoa': {'path': str(hpoa_file), 'sha256': sha256(hpoa_file), 'rows': len(hpoa)}},
        'gene_summary_key_count': len(lookup),
        'hpoa_reference_token_rows': len(leads),
        'positive_P_reference_token_rows': len(candidates) + len(indirect) + len(unresolved),
        'positive_P_publication_candidate_rows': len(candidates),
        'positive_P_curated_source_rows': len(indirect),
        'positive_P_unresolved_reference_rows': len(unresolved),
        'unique_positive_P_gene_hpo_pairs': len(idx),
        'genes_present_in_join': len(gene_summary),
        'unique_publication_identifiers': len({r['reference_token'] for r in candidates}),
        'source_annotation_aspect_qualifier_counts': {f'{k[0]}|{k[1]}': n for k,n in sorted(overall.items())},
        'verified_primary_gene_phenotype_claim_count': 'NOT_ASSESSED',
        'gene_disease_origin': 'NOT_CAPTURED_IN_HPO_GENE_SUMMARY',
        'interpretation': 'PMID/DOI are literature retrieval leads, not verified direct gene-phenotype evidence; curated references require citation tracing',
    }
    (out / 'primary_source_audit_manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    sums = sorted((p.name, sha256(p)) for p in out.iterdir() if p.is_file() and p.name != 'SHA256SUMS.txt')
    (out / 'SHA256SUMS.txt').write_text(''.join(f'{digest}  {name}\n' for name,digest in sums))
    print(json.dumps(manifest, indent=2, sort_keys=True))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--gene-summary', type=Path, default=Path('results/hpo_disease_mediated_gene_view.tsv'))
    p.add_argument('--matched-hpoa', type=Path, default=Path('results/matched_hpoa_disease_phenotype.tsv'))
    p.add_argument('--out', type=Path, default=Path('results/primary_source_audit'))
    a = p.parse_args()
    run(a.gene_summary, a.matched_hpoa, a.out)

if __name__ == '__main__':
    main()
