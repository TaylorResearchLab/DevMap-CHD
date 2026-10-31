from pathlib import Path
import subprocess, sys, csv, json, tempfile, unittest
ROOT=Path(__file__).resolve().parents[2]/'scripts'/'phenotypes'/'gene_pilot'
class Test(unittest.TestCase):
 def test_synthetic(self):
  with tempfile.TemporaryDirectory() as d:
   cmd=[sys.executable,str(ROOT/'run_gene_phenotype_pilot.py'),'--genes',str(ROOT/'pilot_genes.tsv'),'--gene-phenotype',str(ROOT/'fixtures/genes_to_phenotype.synthetic.txt'),'--phenotype-hpoa',str(ROOT/'fixtures/phenotype.synthetic.hpoa'),'--out',d,'--source-release','SYNTHETIC']
   p=subprocess.run(cmd,capture_output=True,text=True,check=True)
   m=json.loads((Path(d)/'run_manifest.json').read_text())
   self.assertEqual(m['pilot_gene_summary_rows_valid'],3)
   self.assertEqual(m['matched_hpoa_rows'],3)
   self.assertEqual(m['registry_gene_count'],16)
   self.assertEqual(m['variant_phenotype_associations'],'OUT_OF_SCOPE')
   with (Path(d)/'gene_coverage.tsv').open() as f: by_gene={r['gene_symbol']:r for r in csv.DictReader(f,delimiter='\t')}
   self.assertEqual(by_gene['TBX5']['hpoa_confirmed_P_positive_rows'],'1')
   self.assertEqual(by_gene['NKX2-5']['direct_gene_association_status'],'NOT_ASSESSED_FROM_INDEPENDENT_SOURCES')
   self.assertEqual(by_gene['CHD7']['gene_summary_status'],'NO_ROWS_IN_SEARCHED_HPO_SUMMARY')
   with (Path(d)/'hpo_disease_mediated_gene_view.tsv').open() as f: rows=list(csv.DictReader(f,delimiter='\t'))
   self.assertEqual(next(x for x in rows if x['hpo_id']=='HP:0000007')['phenotype_aspect'],'I')
   for name in ['hpo_disease_mediated_gene_view.tsv','matched_hpoa_disease_phenotype.tsv']:
    with (Path(d)/name).open() as f:
     header=next(csv.reader(f,delimiter='\t'))
    self.assertEqual(len(header),len(set(header)),f'duplicate output columns in {name}')
   self.assertTrue(all(x['annotation_class']=='HPO_DISEASE_MEDIATED_GENE_VIEW' for x in rows))
 def test_checksum_fail_closed(self):
  with tempfile.TemporaryDirectory() as d:
   p=subprocess.run([sys.executable,str(ROOT/'run_gene_phenotype_pilot.py'),'--genes',str(ROOT/'pilot_genes.tsv'),'--gene-phenotype',str(ROOT/'fixtures/genes_to_phenotype.synthetic.txt'),'--out',d,'--expected-gene-sha256','0'*64],capture_output=True,text=True)
   self.assertNotEqual(p.returncode,0)
   self.assertIn('checksum mismatch',p.stderr+p.stdout)
if __name__=='__main__':unittest.main()
