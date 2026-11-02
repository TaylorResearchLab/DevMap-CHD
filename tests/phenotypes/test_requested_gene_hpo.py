"""Synthetic checks for requested symbols, PCDHG members and HPOA sources."""
import csv
import sys
import tempfile
import unittest
from pathlib import Path

PILOT = Path(__file__).resolve().parents[2] / 'scripts/phenotypes/gene_pilot'
if str(PILOT) not in sys.path:
    sys.path.insert(0, str(PILOT))
from map_requested_gene_hpo import PCDHG_MEMBERS, QUERY, audit


class MappingTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.registry = self.root/'genes.tsv'
        with self.registry.open('w') as f:
            writer=csv.writer(f,delimiter='\t')
            writer.writerow(['hgnc_id','approved_hgnc_symbol'])
            writer.writerows((f'HGNC:{i}', 'LZTR1' if i == 1 else f'SYNTHETIC{i}') for i in range(1, 663))
        self.g2p = self.root/'genes_to_phenotype.txt'
        self.g2p.write_text('ncbi_gene_id\tgene_symbol\thpo_id\tdisease_id\n'
                            '1\tLZTR1\tHP:0100000\tOMIM:1\n'
                            '2\tPOGZ\tHP:0100000\tOMIM:2\n'
                            '2\tPOGZ\tHP:0100001\tOMIM:2\n'
                            '3\tPCDHGA1\tHP:0100000\tOMIM:3\n'
                            '4\tOTHER\tHP:0100000\tOMIM:4\n')
        self.hpoa = self.root/'phenotype.hpoa'
        self.hpoa.write_text('#database_id\thpo_id\taspect\tqualifier\tfrequency\treference\tevidence\tonset\tsex\tmodifier\n'
                             'OMIM:1\tHP:0100000\tP\t\t1/3\tPMID:11\tPCS\t\t\t\n'
                             'OMIM:2\tHP:0100000\tP\t\t0/4\tPMID:22\tPCS\t\t\t\n'
                             'OMIM:2\tHP:0100001\tP\t\t3/4\tPMID:22\tPCS\t\t\t\n'
                             'OMIM:3\tHP:0100000\tP\t\t2/3\tPMID:33\tTAS\t\t\t\n'
                             'OMIM:4\tHP:0100000\tP\t\t2/3\tPMID:44\tTAS\t\t\t\n')
        self.obo=self.root/'hp.obo'
        roots = ['HP:0001626','HP:0001627','HP:0025015','HP:0033353','HP:0030962']
        with self.obo.open('w') as f:
            f.write('format-version: 1.2\n')
            for r in roots:
                f.write(f'\n[Term]\nid: {r}\nname: Synthetic root\n')
            f.write('\n[Term]\nid: HP:0100000\nname: Synthetic heart phenotype\nis_a: HP:0001627 ! heart\nis_a: HP:0001626 ! cardiovascular\n')
            f.write('\n[Term]\nid: HP:0100001\nname: Synthetic vascular phenotype\nis_a: HP:0025015 ! vascular\nis_a: HP:0001626 ! cardiovascular\n')

    def test_cluster_has_22_explicit_members(self):
        self.assertEqual(len(PCDHG_MEMBERS),22)
        self.assertEqual(len(set(PCDHG_MEMBERS)),22)
        self.assertEqual(len(QUERY),6)
        self.assertNotIn('PCDHG@',PCDHG_MEMBERS)

    def test_maps_selected_genes_and_preserves_absence(self):
        o=self.root/'out';m=audit(self.registry,self.g2p,self.hpoa,self.obo,o,False)
        with (o/'selected_genes_hpo_summary.tsv').open() as f:
            rows=list(csv.DictReader(f,delimiter='\t'))
        d={x['gene_symbol']:x for x in rows}
        self.assertEqual(len(rows),28)
        self.assertEqual(m['selected_gene_symbols_with_hpo_g2p'],3)
        self.assertEqual(d['LZTR1']['in_frozen_chd_662'],'1')
        self.assertEqual(d['POGZ']['in_frozen_chd_662'],'0')
        self.assertEqual(d['POGZ']['source_hpoa_P_negative_only_pairs'],'1')
        self.assertEqual(d['POGZ']['heart_morphology_positive_pairs'],'0')
        self.assertEqual(d['POGZ']['vascular_morphology_positive_pairs'],'1')
        self.assertEqual(d['PCDHGA1']['heart_morphology_positive_pairs'],'1')
        self.assertEqual(d['PCDHGA2']['hpo_gene_summary_rows'],'0')
        self.assertEqual(m['selected_gene_hpoa_P_evidence_links'],4)
        with (o/'selected_genes_hpoa_evidence.tsv').open() as f:
            det=list(csv.DictReader(f,delimiter='\t'))
        self.assertEqual(sum(x['hpoa_explicit_absence']=='1' for x in det),1)

    def test_hash_gate_rejects_synthetic_sources(self):
        with self.assertRaisesRegex(ValueError,'source hash mismatch'):
            audit(self.registry,self.g2p,self.hpoa,self.obo,self.root/'out',True)


if __name__=='__main__': unittest.main()