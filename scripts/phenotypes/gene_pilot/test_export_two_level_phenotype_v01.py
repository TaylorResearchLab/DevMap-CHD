import csv
import json
import tempfile
import unittest
from pathlib import Path

from export_two_level_phenotype_v01 import (
    EVIDENCE_SOURCE_FIELDS, DISCOVERY_SOURCE_FIELDS, checked_sources,
    export, interpret, sha256, write_rows,
)


def fixture(root):
    old = root / 'old'
    old.mkdir()
    audit = root / 'audit'
    audit.mkdir()
    types = ('0/19', '12/19', 'HP:0040284', '')
    candidates = []
    evidence = []
    discovery = []
    for i, freq in enumerate(types):
        cid = f'dmpcand:{i:024d}'
        disease = 'OMIM:101' if i < 3 else 'ORPHA:2'
        hpo = 'HP:0000001' if i < 3 else 'HP:0000002'
        state = ['asserted_absent', 'asserted_present', 'unspecified', 'unspecified'][i]
        candidates.append({'candidate_id': cid, 'gene_id': 'HGNC:1', 'gene_symbol': 'GENE1',
                           'disruption_type': 'unspecified_disruption', 'disease_id': disease,
                           'phenotype_id': hpo,
                           'assertion_state': 'disease_mediated_candidate_' + state,
                           'evidence_count': '1'})
        ev = dict.fromkeys(EVIDENCE_SOURCE_FIELDS, '')
        ev.update(candidate_id=cid, evidence_id=f'dmpev:{i}', source_resource='HPOA',
                  source_release='v2026-09-01', source_row_id=f'phenotype.hpoa:{i+10}',
                  original_subject=disease, original_predicate='has_phenotype',
                  original_object=hpo, source_evidence_code='PCS', original_reference=f'PMID:{i+1234}',
                  primary_publication_id=f'PMID:{i+1234}',
                  evidence_role='disease_phenotype_annotation', aspect='P', frequency=freq,
                  source_lineage_key=f'origin:{i}', sex='F' if i == 0 else 'M')
        if i == 3:
            ev['qualifier'] = 'NOT'
        evidence.append(ev)
        d = dict.fromkeys(DISCOVERY_SOURCE_FIELDS, '')
        d.update(candidate_id=cid, gene_id='HGNC:1', gene_symbol='GENE1', disease_id=disease,
                 phenotype_id=hpo, source_resource='HPO-G2P', source_release='v2026-09-01',
                 source_row_id=f'genes_to_phenotype.txt:{i+4}', original_subject='HGNC:1',
                 original_object=hpo, evidence_role='disease_mediated_discovery_only')
        discovery.append(d)
    write_rows(old / 'par_candidates.tsv', tuple(candidates[0].keys()), candidates)
    write_rows(old / 'par_evidence.tsv', EVIDENCE_SOURCE_FIELDS, evidence)
    write_rows(old / 'source_discovery_links.tsv', DISCOVERY_SOURCE_FIELDS, discovery)
    for name in ('gene_coverage.tsv', 'disease_context.tsv'):
        (old / name).write_text('source\n', encoding='utf-8')
    manifest = {
        'status':'provisional_internal_candidates', 'reference_release':'HPO:v2026-09-01',
        'candidate_count': len(candidates), 'hpoa_evidence_records': len(evidence),
        'g2p_discovery_records':len(discovery), 'hpo_source_sha256': {'genes_to_phenotype.txt':'synthetic'}
    }
    (old / 'manifest.json').write_text(json.dumps(manifest))
    with (old / 'SHA256SUMS.txt').open('w') as f:
        for name in ('manifest.json', 'par_candidates.tsv', 'par_evidence.tsv',
                     'source_discovery_links.tsv', 'gene_coverage.tsv', 'disease_context.tsv'):
            f.write(f'{sha256(old / name)}  {name}\n')
    a = {'gate_passed':True, 'source_record_conservation_passed':True,
         'original_candidate_count':len(candidates),
         'producer_manifest_sha256':sha256(old / 'manifest.json'),
         'four_fate_conservation': {'g2p':{'emitted':4}, 'hpoa':{'emitted':4}}}
    (audit / 'audit_manifest.json').write_text(json.dumps(a))
    (audit / 'SHA256SUMS.txt').write_text(f'{sha256(audit / "audit_manifest.json")}  audit_manifest.json\n')
    return old, audit


def read_rows(p):
    with p.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f, delimiter='\t'))


class TestTwoLevelHPOView(unittest.TestCase):
    def test_two_level_frequency_and_source_conservation(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            old, audit=fixture(root)
            result=export(old,audit,root / 'new')
            self.assertEqual(result['legacy_candidate_count'],4)
            self.assertEqual(result['provisional_projection_count'],2)
            self.assertEqual(result['legacy_identity_splits_collapsed'],2)
            self.assertEqual(result['original_evidence_link_count'],4)
            self.assertEqual(result['original_discovery_link_count'],4)
            self.assertEqual(result['direct_gene_phenotype_assertions_promoted'],0)
            self.assertEqual(result['evidence_outcome_counts']['observed_zero'],1)
            self.assertEqual(result['evidence_outcome_counts']['observed_positive'],1)
            self.assertEqual(result['evidence_outcome_counts']['categorical_positive'],1)
            self.assertEqual(result['evidence_outcome_counts']['frequency_unreported'],1)
            self.assertEqual(result['by_namespace']['ORPHA']['negated_projections'],1)
            self.assertEqual(result['by_namespace']['OMIM']['not_negated_projections'],1)
            self.assertEqual(len(read_rows(root/'new'/'legacy_candidate_projection_map.tsv')),4)
            disease=read_rows(root/'new'/'original_disease_phenotype_claims.tsv')
            self.assertEqual({r['disease_id'] for r in disease}, {'ORPHA:2','OMIM:101'})
            observations=read_rows(root/'new'/'original_hpoa_observations.tsv')
            self.assertEqual([r['frequency'] for r in observations], ['0/19','12/19','HP:0040284',''])
            self.assertEqual(observations[0]['frequency_denominator'],'19')
            self.assertEqual(observations[0]['frequency_numerator'],'0')
            self.assertEqual(observations[1]['frequency_numerator'],'12')
            self.assertEqual(observations[2]['categorical_frequency_term'],'HP:0040284')
            self.assertEqual(observations[0]['sex'],'F')
            self.assertEqual(observations[0]['claim_polarity'],'not_negated')
            self.assertEqual(observations[3]['claim_polarity'],'negated')
            checked_sources(root/'new', (
                'original_disease_phenotype_claims.tsv','original_hpoa_observations.tsv',
                'namespace_summary.tsv', 'manifest.json'))

    def test_bad_checksum_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            old,audit=fixture(root)
            with (old/'par_evidence.tsv').open('a') as f:
                f.write('tampered\n')
            with self.assertRaisesRegex(ValueError,'altered input'):
                export(old,audit,root/'new')

    def test_prevent_overwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            old,audit=fixture(root)
            (root/'new').mkdir()
            with self.assertRaisesRegex(ValueError,'Output path exists'):
                export(old,audit,root/'new')

    def test_cohort_zero_not_curator_negation(self):
        pol,basis,obs=interpret({'frequency':'0/19', 'qualifier':''})
        self.assertEqual((pol,basis,obs['evidence_outcome']),
                         ('not_negated','no_source_negation','observed_zero'))
        pol,basis,obs=interpret({'frequency':'HP:0040281', 'qualifier':''})
        self.assertEqual((pol,obs['evidence_outcome']), ('not_negated','categorical_positive'))
        pol,basis,obs=interpret({'frequency':'', 'qualifier':'NOT'})
        self.assertEqual((pol,basis), ('negated','NOT_qualifier'))
        pol,basis,obs=interpret({'frequency':'HP:0040285', 'qualifier':''})
        self.assertEqual((pol,obs['evidence_outcome']), ('negated','categorical_excluded'))
        pol,basis,obs=interpret({'frequency':'2/1', 'qualifier':''})
        self.assertEqual(obs['evidence_outcome'],'unclassified_frequency')
        pol,basis,obs=interpret({'frequency':'30%', 'qualifier':''})
        self.assertEqual((pol,obs['evidence_outcome']), ('not_negated','observed_positive'))


if __name__=='__main__':
    unittest.main()
