"""Synthetic audit tests; these do not measure real HPO coverage."""
import csv
import importlib.util
import tempfile
import unittest
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / 'scripts/phenotypes/gene_pilot/audit_662_hpo_coverage.py'
spec = importlib.util.spec_from_file_location('audit_662_hpo_coverage', PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class Coverage662Test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        d = self.d = Path(self.tmp.name)
        with (d / 'registry.tsv').open('w') as f:
            w = csv.writer(f, delimiter='\t')
            w.writerow(['hgnc_id', 'approved_hgnc_symbol', 'ensembl_gene_id'])
            w.writerows((f'HGNC:{i}', f'GENE{i:04}', f'ENSG{i:011}') for i in range(1, 663))
        (d / 'gene.tsv').write_text('ncbi_gene_id\tgene_symbol\thpo_id\thpo_name\tfrequency\tdisease_id\n'
                                     '100\tGENE0001\tHP:0000001\tTest\t0/4\tOMIM:1\n'
                                     '100\tGENE0001\tHP:0000002\tTest2\t2/4\tOMIM:1\n'
                                     '300\tOLDGENE3\tHP:0000001\tTest\t1/1\tOMIM:2\n')
        (d / 'hpoa.tsv').write_text('#database_id\tdisease_name\tqualifier\thpo_id\treference\tevidence\tonset\tfrequency\tsex\tmodifier\taspect\tbiocuration\n'
                                     'OMIM:1\tDisease A\t\tHP:0000001\tPMID:1\tPCS\t\t0/4\t\t\tP\tx\n'
                                     'OMIM:1\tDisease A\t\tHP:0000002\tPMID:2\tPCS\t\t2/4\t\t\tP\tx\n'
                                     'OMIM:2\tDisease B\t\tHP:0000001\tPMID:3\tPCS\t\t1/1\t\t\tP\tx\n')
        (d / 'hgnc.tsv').write_text('hgnc_id\tentrez_id\nHGNC:3\t300\n')

    def test_exact_symbols_are_bounded_to_662(self):
        m = mod.audit(self.d/'registry.tsv', self.d/'gene.tsv', self.d/'hpoa.tsv', self.d/'out', require_hash=False)
        self.assertEqual(m['hpo_gene_summary_annotated_gene_count'], 1)
        self.assertEqual(m['hpo_gene_summary_unannotated_gene_count'], 661)
        self.assertEqual(m['genes_with_hpoa_P_aspect'], 1)
        self.assertEqual(m['match_scope'], 'APPROVED_SYMBOL_EXACT_ONLY')

    def test_hgnc_ncbi_rescue(self):
        m = mod.audit(self.d/'registry.tsv', self.d/'gene.tsv', self.d/'hpoa.tsv', self.d/'out2', self.d/'hgnc.tsv', False)
        self.assertEqual(m['hpo_gene_summary_annotated_gene_count'], 2)
        self.assertEqual(m['hpo_gene_summary_ncbi_id_match_count'], 1)
        self.assertEqual(m['hpo_gene_summary_unannotated_gene_count'], 660)

    def test_absence_modes(self):
        for f in ['0/4', '0%', 'HP:0040285']:
            self.assertTrue(mod.absence({'frequency':f}))
        for f in ['1/4', 'HP:0040283', '']:
            self.assertFalse(mod.absence({'frequency':f}))
        self.assertTrue(mod.absence({'qualifier':'NOT'}))

    def test_pinned_sha_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'digest not pinned'):
            mod.audit(self.d/'registry.tsv', self.d/'gene.tsv', self.d/'hpoa.tsv', self.d/'out3')


if __name__ == '__main__':
    unittest.main()