#!/usr/bin/env python3
"""Audit all 662 frozen DevMap-CHD genes against a pinned HPO gene summary.

The HPO gene summary is a DISEASE-MEDIATED DISCOVERY INDEX, not independent
primary gene-phenotype evidence. Zero rows mean no annotation in this file.

Optionally --hgnc-complete-set supplies an HGNC TSV with hgnc_id/entrez_id to
check old HPO symbols by stable NCBI Gene identifiers. No guessed alias mapping.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from collections import defaultdict, Counter
from pathlib import Path

EXPECTED_G2P_SHA = '507a17bff9c49e6329fbd88b1f91734fa7e9fdea5c06304044c0892eb6ab248c'
EXPECTED_HPOA_SHA = 'e89aa39c8f97bf5a52c5d160f9250a603681d630ade8ec2679d84ac5aece1f72'
G2P_COLS = {'ncbi_gene_id', 'gene_symbol', 'hpo_id', 'disease_id'}
HPOA_COLS = {'database_id', 'hpo_id', 'aspect', 'frequency', 'qualifier'}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def tsv_rows(path, required):
    with path.open(encoding='utf-8-sig', newline='') as f:
        header = None
        for lineno, text in enumerate(f, 1):
            if not text.strip():
                continue
            if text.startswith('#'):
                cols = text.lstrip('#').strip().split('\t')
                if required <= set(cols):
                    header = cols
                continue
            cols = next(csv.reader([text], delimiter='\t'))
            if header is None:
                if required <= set(cols):
                    header = cols
                    continue
                raise ValueError(f'{path}:{lineno}: unexpected header {cols[:8]}')
            if cols == header:
                continue
            if len(cols) != len(header):
                raise ValueError(f'{path}:{lineno}: wrong column count ({len(cols)} vs {len(header)})')
            yield dict(zip(header, cols))
    if header is None:
        raise ValueError(f'{path}: no header')


def absence(row):
    f = (row.get('frequency') or '').strip()
    if (row.get('qualifier') or '').strip().upper() == 'NOT':
        return True
    if f in ('0%', 'HP:0040285'):
        return True
    if '/' in f:
        parts = f.split('/')
        return len(parts) == 2 and parts[0].strip() == '0' and parts[1].strip().isdigit() and int(parts[1]) > 0
    return False


def write_tsv(path, records, fieldnames):
    with path.open('w', newline='', encoding='utf-8') as f:
        wr = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t', extrasaction='ignore', lineterminator='\n')
        wr.writeheader()
        wr.writerows(records)


def audit(registry, g2p, hpoa, out, hgnc=None, require_hash=True):
    out.mkdir(parents=True, exist_ok=True)
    source_hash = sha256(g2p)
    if require_hash and source_hash != EXPECTED_G2P_SHA:
        raise ValueError('HPO genes_to_phenotype source digest not pinned v2026-09-01')
    hpoa_hash = sha256(hpoa) if hpoa else None
    if require_hash and hpoa and hpoa_hash != EXPECTED_HPOA_SHA:
        raise ValueError('HPO phenotype.hpoa digest not pinned v2026-09-01')

    with registry.open(newline='', encoding='utf-8') as f:
        genes = list(csv.DictReader(f, delimiter='\t'))
    assert len(genes) == 662 and len({r['hgnc_id'] for r in genes}) == 662, 'Frozen 662-gene registry mismatch'
    assert len({r['approved_hgnc_symbol'] for r in genes}) == 662, 'Registry has duplicate approved symbols'

    id_by_hgnc = {}
    if hgnc:
        for r in tsv_rows(hgnc, {'hgnc_id', 'entrez_id'}):
            n = (r.get('entrez_id') or '').strip()
            if n and n.isdigit():
                id_by_hgnc[r['hgnc_id']] = n

    by_symbol, by_ncbi, all_symbols = defaultdict(list), defaultdict(list), set()
    n_source = 0
    for row in tsv_rows(g2p, G2P_COLS):
        n_source += 1
        sym = row['gene_symbol'].strip()
        all_symbols.add(sym)
        by_symbol[sym].append(row)
        by_ncbi[row['ncbi_gene_id'].strip()].append(row)

    aspect_map = defaultdict(set)
    positive_p = set()
    negative_p = set()
    hpoa_total = 0
    if hpoa:
        for r in tsv_rows(hpoa, HPOA_COLS):
            hpoa_total += 1
            key = (r['database_id'].strip(), r['hpo_id'].strip())
            aspect_map[key].add(r['aspect'])
            if r['aspect'] == 'P':
                (negative_p if absence(r) else positive_p).add(key)

    summary = []
    for r in genes:
        sym = r['approved_hgnc_symbol']
        ncbi = id_by_hgnc.get(r['hgnc_id'], '')
        symbol_rows = by_symbol.get(sym, [])
        id_rows = by_ncbi.get(ncbi, []) if ncbi else []
        if id_rows:
            rows, method = id_rows, 'NCBI_GENE_ID'
        elif symbol_rows:
            rows, method = symbol_rows, 'SYMBOL_EXACT'
        else:
            rows, method = [], 'NO_MATCH'
        triples = {(x['disease_id'], x['hpo_id']) for x in rows}
        p_keys = {k for k in triples if 'P' in aspect_map.get(k, set())}
        p_positive = p_keys & positive_p
        p_negative_only = (p_keys & negative_p) - positive_p
        unknown = {k for k in triples if k not in aspect_map} if hpoa else set()
        summary.append({
            'hgnc_id': r['hgnc_id'],
            'approved_hgnc_symbol': sym,
            'ensembl_gene_id': r.get('ensembl_gene_id', ''),
            'matched_hpo_ncbi_gene_id': ncbi if id_rows else '',
            'match_method': method,
            'hpo_gene_summary_rows': len(rows),
            'distinct_hpo_terms_any_aspect': len({x['hpo_id'] for x in rows}),
            'distinct_hpo_disease_ids': len({x['disease_id'] for x in rows}),
            'hpoa_p_source_term_count': len({x[1] for x in p_keys}) if hpoa else 'NOT_ASSESSED',
            'hpoa_p_positive_term_count': len({x[1] for x in p_positive}) if hpoa else 'NOT_ASSESSED',
            'hpoa_p_negative_only_term_count': len({x[1] for x in p_negative_only}) if hpoa else 'NOT_ASSESSED',
            'unmatched_disease_hpo_keys': len(unknown) if hpoa else 'NOT_ASSESSED',
            'hpo_gene_summary_status': 'PRESENT' if rows else 'NO_ROWS_IN_PINNED_HPO_DISCOVERY_INDEX',
            'direct_gene_phenotype_evidence': 'NOT_ASSESSED',
            'chd_specific_phenotype_coverage': 'NOT_ASSESSED',
            'source_symbol_disagreement': ('|'.join(sorted({x['gene_symbol'] for x in rows if x['gene_symbol'] != sym})) if rows else ''),
        })
    missing = [r for r in summary if r['hpo_gene_summary_status'].startswith('NO_ROWS')]
    no_p = [r for r in summary if r['hpo_gene_summary_rows'] and r['hpoa_p_source_term_count'] == 0] if hpoa else []
    fields = list(summary[0].keys())
    write_tsv(out / 'gene_hpo_coverage_662.tsv', summary, fields)
    write_tsv(out / 'genes_without_hpo_gene_summary.tsv', missing, fields)
    if hpoa:
        write_tsv(out / 'genes_with_hpo_but_no_P_annotations.tsv', no_p, fields)
    manifest = {
        'interpretation': 'HPO disease-mediated discovery index; not independent source-issued gene-phenotype evidence',
        'source_release': 'v2026-09-01',
        'frozen_gene_registry_count': len(genes),
        'hpo_total_gene_summary_rows': n_source,
        'hpo_gene_summary_annotated_gene_count': len(genes) - len(missing),
        'hpo_gene_summary_unannotated_gene_count': len(missing),
        'hpo_gene_summary_exact_match_count': sum(r['match_method'] == 'SYMBOL_EXACT' for r in summary),
        'hpo_gene_summary_ncbi_id_match_count': sum(r['match_method'] == 'NCBI_GENE_ID' for r in summary),
        'hpo_ncbi_crosswalk_provided': bool(hgnc),
        'match_scope': 'NCBI_GENE_ID_WITH_EXACT_SYMBOL_FALLBACK' if hgnc else 'APPROVED_SYMBOL_EXACT_ONLY',
        'hpoa_provided': bool(hpoa),
        'hpoa_total_rows_scanned': hpoa_total if hpoa else 'NOT_ASSESSED',
        'genes_with_hpo_gene_rows_but_no_hpoa_P_aspect': len(no_p) if hpoa else 'NOT_ASSESSED',
        'genes_with_hpoa_P_aspect': sum(bool(r['hpoa_p_source_term_count']) for r in summary) if hpoa else 'NOT_ASSESSED',
        'genes_with_hpoa_positive_P_source_annotation': sum(bool(r['hpoa_p_positive_term_count']) for r in summary) if hpoa else 'NOT_ASSESSED',
        'chd_specific_coverage': 'NOT_ASSESSED',
        'meaning_of_zero': 'No gene-summary row matched by the reported match_scope in this HPO release; unresolved name/ID aliases may require review; no implication of no phenotype or CHD relevance',
        'sha256': {'registry': sha256(registry), 'genes_to_phenotype': source_hash, 'phenotype_hpoa': hpoa_hash, 'hgnc_crosswalk': sha256(hgnc) if hgnc else None},
    }
    (out / 'hpo_coverage_662_manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    (out / 'SHA256SUMS.txt').write_text(''.join(
        f'{sha256(p)}  {p.name}\n' for p in sorted(out.glob('*')) if p.is_file() and p.name != 'SHA256SUMS.txt'
    ))
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    base = Path(__file__).resolve().parent
    repo = base.parents[2]
    p.add_argument('--registry', type=Path, default=repo / 'data/releases/2026.09.08/genes.tsv')
    p.add_argument('--gene-summary', type=Path, default=base / 'inputs/genes_to_phenotype.txt')
    p.add_argument('--hpoa', type=Path, default=base / 'inputs/phenotype.hpoa')
    p.add_argument('--hgnc-complete-set', type=Path)
    p.add_argument('--out', type=Path, default=base / 'results/hpo_coverage_662')
    p.add_argument('--allow-unpinned-test-inputs', action='store_true', help='Only for synthetic unit tests, not scientific reports')
    args = p.parse_args()
    audit(args.registry, args.gene_summary, args.hpoa, args.out, args.hgnc_complete_set, not args.allow_unpinned_test_inputs)

if __name__ == '__main__':
    main()