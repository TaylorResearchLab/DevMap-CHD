import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from integrate_gencc_evidence import run

def tsv(path,fields,rows):
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t",lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class GenCCIntegrationTest(unittest.TestCase):
    def test_source_identity_and_exact_disease_only(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            src=root/"source"
            src.mkdir()
            coverage=[{"gene_id":f"HGNC:{i}","gene_symbol":f"GENE{i}","candidate_count":"1" if i==1 else "0"}
                      for i in range(1,663)]
            tsv(src/"gene_coverage.tsv",list(coverage[0]),coverage)
            tsv(src/"par_candidates.tsv",["candidate_id","gene_id","gene_symbol","disease_id","phenotype_id"],
                [{"candidate_id":"c1","gene_id":"HGNC:1","gene_symbol":"GENE1",
                  "disease_id":"OMIM:123","phenotype_id":"HP:001"}])
            (src/"manifest.json").write_text(json.dumps({
                "reference_release":"HPO:v2026-09-01",
                "registry_gene_count":662,"candidate_count":1}))
            with open(src/"SHA256SUMS.txt","w") as f:
                for n in ("gene_coverage.tsv","par_candidates.tsv","manifest.json"):
                    f.write(f"{sha(src/n)}  {n}\n")
            gencc=root/"gencc.tsv"
            tsv(gencc,["sgc_id","version_number","gene_curie","disease_curie",
                       "classification_title","moi_title","submitter_title"],
                [{"sgc_id":"SGC-1","version_number":"2","gene_curie":"HGNC:1",
                  "disease_curie":"OMIM:123","classification_title":"Definitive",
                  "moi_title":"Autosomal dominant","submitter_title":"ClinGen"},
                 {"sgc_id":"SGC-2","version_number":"1","gene_curie":"HGNC:2",
                  "disease_curie":"MONDO:888","classification_title":"Limited",
                  "moi_title":"Autosomal recessive","submitter_title":"Other"},
                 {"sgc_id":"SGC-3","version_number":"1","gene_curie":"HGNC:1",
                  "disease_curie":"MONDO:888","classification_title":"Strong",
                  "moi_title":"Autosomal dominant","submitter_title":"Other"}])
            result=run(src,gencc,root/"out")
            self.assertEqual(result["gencc_assertions_for_registry_genes"],3)
            self.assertEqual(result["exact_disease_candidate_matches"],1)
            self.assertEqual(result["genes_without_hpo_candidates_with_gencc_evidence"],1)
            with open(root/"out"/"gencc_hpo_exact_disease_matches.tsv") as f:
                match=list(csv.DictReader(f,delimiter="\t"))
            self.assertEqual(match[0]["gencc_id"],"SGC-1")
            self.assertEqual(match[0]["evidence_role"],"gene_disease_curation_not_direct_phenotype_evidence")

    def test_invalid_hpo_checksum(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            (root/"manifest.json").write_text(json.dumps({
                "reference_release":"HPO:v2026-09-01","registry_gene_count":662}))
            (root/"SHA256SUMS.txt").write_text("0000  gene_coverage.tsv\n")
            (root/"gene_coverage.tsv").write_text("incorrect")
            with self.assertRaises(ValueError):
                run(root,root/"unused.tsv",root/"out")

if __name__=="__main__":
    unittest.main()
