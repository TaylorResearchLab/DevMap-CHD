import csv
import json
import tempfile
import unittest
from pathlib import Path
import importlib.util

MOD_PATH = Path(__file__).resolve().parents[2] / 'scripts' / 'phenotypes' / 'gene_pilot' / 'audit_hpo_primary_sources.py'
spec = importlib.util.spec_from_file_location('audit_hpo_primary_sources', MOD_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TestSourceAudit(unittest.TestCase):
    def test_classifications(self):
        self.assertEqual(mod.ref_kind('PMID:123'), 'PUBMED_PUBLICATION_LEAD')
        self.assertEqual(mod.ref_kind('OMIM:147690'), 'OMIM_CURATED_RECORD')
        self.assertEqual(mod.ref_kind('DOI:10.1234/example'), 'DOI_PUBLICATION_LEAD')
        self.assertEqual(mod.ref_kind(''), 'MISSING_REFERENCE')
        self.assertEqual(mod.ref_kind('ABC:123'), 'UNRESOLVED_REFERENCE_TYPE')

    def test_retains_multiple_diseases_and_negative_aspects(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)
            summary=[
                {'hgnc_id':'HGNC:1','gene_symbol':'TEST1','disease_id':'OMIM:111','hpo_id':'HP:0000001','hpo_name':'Fictional trait','annotation_class':'HPO_DISEASE_MEDIATED_GENE_VIEW','source_line':'3'},
                {'hgnc_id':'HGNC:1','gene_symbol':'TEST1','disease_id':'OMIM:222','hpo_id':'HP:0000001','hpo_name':'Fictional trait','annotation_class':'HPO_DISEASE_MEDIATED_GENE_VIEW','source_line':'4'},
                {'hgnc_id':'HGNC:1','gene_symbol':'TEST1','disease_id':'OMIM:111','hpo_id':'HP:0000007','hpo_name':'Fictional inheritance','annotation_class':'HPO_DISEASE_MEDIATED_GENE_VIEW','source_line':'5'}
            ]
            hpoa=[
                {'hgnc_id':'HGNC:1','gene_symbol':'TEST1','disease_id':'OMIM:111','hpo_id':'HP:0000001','hpoa_source_line':'12','reference':'PMID:123456','evidence':'PCS','aspect':'P','qualifier':'','frequency':'3/5','biocuration':'HPO:tester[2026-01-01]'},
                {'hgnc_id':'HGNC:1','gene_symbol':'TEST1','disease_id':'OMIM:111','hpo_id':'HP:0000001','hpoa_source_line':'13','reference':'PMID:123456','evidence':'PCS','aspect':'P','qualifier':'','frequency':'3/5','biocuration':''},
                {'hgnc_id':'HGNC:1','gene_symbol':'TEST1','disease_id':'OMIM:222','hpo_id':'HP:0000001','hpoa_source_line':'14','reference':'OMIM:222','evidence':'IEA','aspect':'P','qualifier':'','frequency':'','biocuration':''},
                {'hgnc_id':'HGNC:1','gene_symbol':'TEST1','disease_id':'OMIM:111','hpo_id':'HP:0000007','hpoa_source_line':'15','reference':'PMID:77777','evidence':'TAS','aspect':'I','qualifier':'NOT','frequency':'','biocuration':''},
            ]
            for fname, rows in [('summary.tsv',summary),('hpoa.tsv',hpoa)]:
                with (d/fname).open('w',newline='') as f:
                    w=csv.DictWriter(f,fieldnames=rows[0].keys(),delimiter='\t');w.writeheader();w.writerows(rows)
            mod.run(d/'summary.tsv',d/'hpoa.tsv',d/'out')
            x=json.loads((d/'out'/'primary_source_audit_manifest.json').read_text())
            self.assertEqual(x['unique_positive_P_gene_hpo_pairs'],1)
            self.assertEqual(x['positive_P_publication_candidate_rows'],2)
            self.assertEqual(x['positive_P_curated_source_rows'],1)
            self.assertEqual(x['unique_publication_identifiers'],1)
            with (d/'out'/'gene_hpo_provenance_index.tsv').open() as f:
                r=list(csv.DictReader(f,delimiter='\t'))
            self.assertEqual(r[0]['n_diseases'],'2')
            self.assertEqual(r[0]['publication_leads'],'PMID:123456')
            self.assertIn('OMIM:222',r[0]['curated_records'])
            with (d/'out'/'all_hpoa_reference_leads.tsv').open() as f:
                r=list(csv.DictReader(f,delimiter='\t'))
            neg=[x for x in r if x['hpo_aspect']=='I']
            self.assertEqual(len(neg),1)
            self.assertEqual(neg[0]['phenotype_positive_P'],'false')

    def test_rejects_missing_key(self):
        with tempfile.TemporaryDirectory() as t:
            d=Path(t)
            (d/'summary.tsv').write_text('hgnc_id\tgene_symbol\tdisease_id\thpo_id\thpo_name\tannotation_class\tsource_line\n')
            (d/'hpoa.tsv').write_text('hgnc_id\tgene_symbol\tdisease_id\thpo_id\thpoa_source_line\treference\tevidence\taspect\tqualifier\nHGNC:1\tTEST\tOMIM:1\tHP:0000001\t1\tPMID:123\tPCS\tP\t\n')
            with self.assertRaises(ValueError):mod.run(d/'summary.tsv',d/'hpoa.tsv',d/'out')

if __name__=='__main__':unittest.main()
