"""Synthetic tests of disease-mediated cardiovascular morphology coverage.

These tests do not measure real HPO or source claim validity.
"""
import csv, importlib.util, sys, tempfile, unittest
from pathlib import Path

SCRIPTS=Path(__file__).resolve().parents[2]/'scripts/phenotypes/gene_pilot'
sys.path.insert(0,str(SCRIPTS))
spec=importlib.util.spec_from_file_location('cardio_audit',SCRIPTS/'audit_662_cardio_vascular.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class CoverageCardioTest(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.d=Path(tmp.name)
        with (self.d/'registry.tsv').open('w') as f:
            w=csv.writer(f,delimiter='\t');w.writerow(['hgnc_id','approved_hgnc_symbol'])
            w.writerows((f'HGNC:{i}',f'GENE{i:04}') for i in range(1,663))
        (self.d/'g2p.tsv').write_text(
            'ncbi_gene_id\tgene_symbol\thpo_id\thpo_name\tfrequency\tdisease_id\n'
            '100\tGENE0001\tHP:0000001\tTest heart\t2/4\tOMIM:1\n'
            '100\tGENE0001\tHP:0000003\tTest negative artery\t0/4\tOMIM:1\n'
            '200\tGENE0002\tHP:0000002\tTest vessel\t4/4\tOMIM:2\n'
            '300\tOLDGENE3\tHP:0000002\tTest vessel\t4/4\tOMIM:3\n')
        (self.d/'hpoa.tsv').write_text(
            '#database_id\tdisease_name\tqualifier\thpo_id\treference\tevidence\tonset\tfrequency\tsex\tmodifier\taspect\tbiocuration\n'
            'OMIM:1\tD1\t\tHP:0000001\tPMID:1\tPCS\t\t2/4\t\t\tP\ta\n'
            'OMIM:1\tD1\t\tHP:0000003\tPMID:2\tPCS\t\t0/4\t\t\tP\ta\n'
            'OMIM:2\tD2\t\tHP:0000002\tPMID:3\tPCS\t\t4/4\t\t\tP\ta\n'
            'OMIM:3\tD3\t\tHP:0000002\tPMID:4\tPCS\t\t4/4\t\t\tP\ta\n')
        (self.d/'hgnc.tsv').write_text('hgnc_id\tentrez_id\nHGNC:3\t300\n')
        def term(id,name,parent=None,alt=None):
            x=f'[Term]\nid: {id}\nname: {name}\n'
            if parent:x+=f'is_a: {parent} ! parent\n'
            if alt:x+=f'alt_id: {alt}\n'
            return x+'\n'
        (self.d/'hp.obo').write_text('format-version: 1.2\n\n'+''.join([
            term('HP:0001626','Cardiovascular'),
            term('HP:0030680','Cardiovascular morphology','HP:0001626'),
            term('HP:0001627','Heart morphology','HP:0030680'),
            term('HP:0025015','Vascular morphology','HP:0030680'),
            term('HP:0033353','Blood vessel','HP:0025015'),
            term('HP:0030962','Great vessels','HP:0033353'),
            term('HP:0000001','Heart defect','HP:0001627'),
            term('HP:0000002','Great vessel defect','HP:0030962',alt='HP:0001002'),
            term('HP:0000003','Arterial defect','HP:0033353'),
        ]))
    def run_audit(self,hgnc=None):
        return module.audit(self.d/'registry.tsv',self.d/'g2p.tsv',self.d/'hpoa.tsv',self.d/'hp.obo',self.d/'out',hgnc,False)
    def test_heart_and_vessel_separate_and_negative_evidence_excluded(self):
        x=self.run_audit()
        self.assertEqual(x['registry_genes'],662)
        self.assertEqual(x['general_hpo_annotated_genes'],2)
        self.assertEqual(x['structural_heart_or_vascular_any_positive_genes'],2)
        self.assertEqual(x['category_counts']['heart_morphology']['positive_genes'],1)
        self.assertEqual(x['category_counts']['vascular_morphology']['positive_genes'],1)
        self.assertEqual(x['category_counts']['blood_vessel_morphology']['negative_only_genes'],1)
        self.assertEqual(x['heart_only_positive_genes'],1)
        self.assertEqual(x['vascular_only_positive_genes'],1)
        self.assertEqual(x['heart_and_vascular_positive_genes'],0)
        self.assertEqual(x['heart_only_positive_genes']+x['vascular_only_positive_genes']+x['heart_and_vascular_positive_genes'],x['structural_heart_or_vascular_any_positive_genes'])
    def test_crosswalk_recovers_renamed_gene(self):
        x=self.run_audit(self.d/'hgnc.tsv')
        self.assertEqual(x['general_hpo_annotated_genes'],3)
        self.assertEqual(x['category_counts']['great_vessel_morphology']['positive_genes'],2)
    def test_sha_rejected_when_unpinned(self):
        with self.assertRaisesRegex(ValueError,'input hash differs'):
            module.audit(self.d/'registry.tsv',self.d/'g2p.tsv',self.d/'hpoa.tsv',self.d/'hp.obo',self.d/'out',require_hash=True)
    def test_alt_id_and_ontology_descendants(self):
        terms,alt=module.read_obo(self.d/'hp.obo')
        cats=module.descendant_index(terms,alt)
        self.assertIn('vascular_morphology', cats('HP:0001002'))
        self.assertNotIn('heart_morphology',cats('HP:0001002'))

if __name__=='__main__':unittest.main()