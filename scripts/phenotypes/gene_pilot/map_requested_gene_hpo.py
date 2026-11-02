#!/usr/bin/env python3
"""Map user-selected gene symbols and all 22 PCDHG members to pinned HPO references.

Source: HPO genes_to_phenotype is a disease-mediated discovery index, not proof
of direct gene-to-phenotype causality. Results preserve original HPOA references.
No PARs or clinical assertions are emitted by this diagnostic.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

from audit_662_hpo_coverage import (
    EXPECTED_G2P_SHA, EXPECTED_HPOA_SHA, absence, sha256, tsv_rows, write_tsv,
)
from audit_662_cardio_vascular import OBO_SHA, ROOTS, read_obo, descendant_index

# Cluster includes all 22 protein-coding members, even if HPO has zero rows.
PCDHG_MEMBERS = (
    [f'PCDHGA{i}' for i in range(1, 13)]
    + [f'PCDHGB{i}' for i in range(1, 8)]
    + [f'PCDHGC{i}' for i in range(3, 6)]
)
QUERY = ('LZTR1', 'POGZ', 'FAM76A', 'PELO', 'CIC', 'IREB2')


def audit(registry: Path, g2p: Path, hpoa: Path, obo: Path, out: Path,
          require_hash: bool = True):
    paths = {'registry': registry, 'genes_to_phenotype': g2p,
             'phenotype_hpoa': hpoa, 'hp_obo': obo}
    digests = {key: sha256(path) for key, path in paths.items()}
    for key, expected in [('genes_to_phenotype', EXPECTED_G2P_SHA),
                          ('phenotype_hpoa', EXPECTED_HPOA_SHA), ('hp_obo', OBO_SHA)]:
        if require_hash and digests[key] != expected:
            raise ValueError(f'{key}: source hash mismatch for HPO v2026-09-01')

    registry_rows = list(tsv_rows(registry, {'hgnc_id', 'approved_hgnc_symbol'}))
    if len(registry_rows) != 662 or len({r['hgnc_id'] for r in registry_rows}) != 662:
        raise ValueError('Frozen DevMap-CHD gene registry must contain 662 unique HGNC IDs')
    registry_symbols = {r['approved_hgnc_symbol']: r['hgnc_id'] for r in registry_rows}
    terms, alt_ids = read_obo(obo)
    classify = descendant_index(terms, alt_ids)
    selected = set(QUERY) | set(PCDHG_MEMBERS)

    g2p_rows = defaultdict(list)
    g2p_count = 0
    for r in tsv_rows(g2p, {'gene_symbol', 'ncbi_gene_id', 'disease_id', 'hpo_id'}):
        g2p_count += 1
        sym = r['gene_symbol'].strip()
        if sym in selected:
            g2p_rows[sym].append(r)

    desired = set()
    for rows in g2p_rows.values():
        for r in rows:
            desired.add((r['disease_id'].strip(), alt_ids.get(r['hpo_id'], r['hpo_id'])))

    hpoa_rows = defaultdict(list)
    hpoa_count = 0
    for r in tsv_rows(hpoa, {'database_id', 'hpo_id', 'aspect', 'qualifier',
                             'frequency', 'reference', 'evidence'}):
        hpoa_count += 1
        key = (r['database_id'].strip(), alt_ids.get(r['hpo_id'], r['hpo_id']))
        if key in desired and r['aspect'] == 'P':
            hpoa_rows[key].append(r)

    summary = []
    detail = []
    for symbol in list(QUERY) + PCDHG_MEMBERS:
        pairs = {(r['disease_id'].strip(), alt_ids.get(r['hpo_id'], r['hpo_id']))
                 for r in g2p_rows[symbol]}
        nonnegative_pairs = set()
        negative_only_pairs = set()
        category_pairs = {k: set() for k in ROOTS}
        for disease, hp in sorted(pairs):
            rows = hpoa_rows.get((disease, hp), [])
            if not rows:
                continue
            flags = classify(hp)
            pos = any(not absence(r) for r in rows)
            neg = any(absence(r) for r in rows)
            if pos:
                nonnegative_pairs.add((disease, hp))
                for cat in flags:
                    category_pairs[cat].add((disease, hp))
            elif neg:
                negative_only_pairs.add((disease, hp))
            for source in rows:
                detail.append({
                    'gene_symbol': symbol,
                    'query_group': 'PCDHG_CLUSTER' if symbol in PCDHG_MEMBERS else 'INDIVIDUAL',
                    'ncbi_gene_id_hpo': '|'.join(sorted({r['ncbi_gene_id'] for r in g2p_rows[symbol]})),
                    'disease_id': disease,
                    'hpo_id': hp,
                    'hpo_term': terms.get(hp, {}).get('name', ''),
                    'categories': '|'.join(flags),
                    'hpoa_reference': source['reference'],
                    'hpoa_evidence_code': source['evidence'],
                    'hpoa_frequency': source['frequency'],
                    'hpoa_explicit_absence': int(absence(source)),
                    'hpoa_qualifier': source.get('qualifier', ''),
                    'hpoa_onset': source.get('onset', ''),
                    'hpoa_sex': source.get('sex', ''),
                    'hpoa_modifier': source.get('modifier', ''),
                })
        summary.append({
            'gene_symbol': symbol,
            'query_group': 'PCDHG_CLUSTER' if symbol in PCDHG_MEMBERS else 'INDIVIDUAL',
            'in_frozen_chd_662': int(symbol in registry_symbols),
            'hgnc_id_in_frozen_chd': registry_symbols.get(symbol, ''),
            'hpo_gene_summary_rows': len(g2p_rows[symbol]),
            'hpo_diseases': len({r['disease_id'] for r in g2p_rows[symbol]}),
            'hpo_terms': len({r['hpo_id'] for r in g2p_rows[symbol]}),
            'source_hpoa_P_nonnegative_pairs': len(nonnegative_pairs),
            'source_hpoa_P_negative_only_pairs': len(negative_only_pairs),
            **{f'{cat}_positive_pairs': len(category_pairs[cat]) for cat in ROOTS},
            'status': 'HPO_G2P_MATCH' if g2p_rows[symbol] else 'NO_EXACT_HPO_G2P_MATCH',
        })

    out.mkdir(parents=True, exist_ok=True)
    write_tsv(out/'selected_genes_hpo_summary.tsv', summary, list(summary[0]))
    detail_fields = ['gene_symbol', 'query_group', 'ncbi_gene_id_hpo', 'disease_id',
                     'hpo_id', 'hpo_term', 'categories', 'hpoa_reference',
                     'hpoa_evidence_code', 'hpoa_frequency', 'hpoa_explicit_absence',
                     'hpoa_qualifier', 'hpoa_onset', 'hpoa_sex', 'hpoa_modifier']
    write_tsv(out/'selected_genes_hpoa_evidence.tsv', detail, detail_fields)
    manifest = {
        'source_release': 'v2026-09-01',
        'query_genes': list(QUERY), 'pcdhg_cluster_members': PCDHG_MEMBERS,
        'pcdhg_member_count': len(PCDHG_MEMBERS),
        'frozen_registry_genes': len(registry_rows),
        'requested_individual_genes_in_registry': [s for s in QUERY if s in registry_symbols],
        'hpo_gene_summary_rows_scanned': g2p_count,
        'hpoa_source_rows_scanned': hpoa_count,
        'selected_gene_symbols_with_hpo_g2p': sum(bool(g2p_rows[s]) for s in selected),
        'selected_gene_symbols_without_hpo_g2p': sorted(s for s in selected if not g2p_rows[s]),
        'selected_gene_hpoa_P_evidence_links': len(detail),
        'roots': ROOTS,
        'sha256': digests,
        'match_method': 'HPO_EXACT_GENE_SYMBOL',
        'interpretation': 'HPO disease-mediated discovery index and original disease-phenotype annotation references; no direct gene-phenotype validation',
        'ready_for_public_release': False,
    }
    (out/'selected_gene_hpo_manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
    (out/'SHA256SUMS.txt').write_text(''.join(
        f'{sha256(path)}  {path.name}\n' for path in sorted(out.iterdir())
        if path.is_file() and path.name != 'SHA256SUMS.txt'))
    return manifest


def main():
    p = argparse.ArgumentParser(description=__doc__)
    base = Path(__file__).resolve().parent
    root = base.parents[2]
    p.add_argument('--registry', type=Path, default=root/'data/releases/2026.09.08/genes.tsv')
    p.add_argument('--gene-summary', type=Path, default=base/'inputs/genes_to_phenotype.txt')
    p.add_argument('--hpoa', type=Path, default=base/'inputs/phenotype.hpoa')
    p.add_argument('--obo', type=Path, default=base/'inputs/hp.obo')
    p.add_argument('--out', type=Path, default=base/'results/requested_gene_hpo_map')
    p.add_argument('--allow-unpinned-test-inputs', action='store_true',
                   help='Synthetic tests only; report must not be interpreted as a pinned result')
    args = p.parse_args()
    manifest = audit(args.registry, args.gene_summary, args.hpoa,
                     args.obo, args.out, require_hash=not args.allow_unpinned_test_inputs)
    print(json.dumps(manifest, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()