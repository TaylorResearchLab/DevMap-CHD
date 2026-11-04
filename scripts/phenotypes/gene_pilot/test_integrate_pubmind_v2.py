import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from integrate_pubmind_v2 import integrate

def write(path,fields,rows):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t",lineterminator="\n")
        w.writeheader();w.writerows(rows)
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def seal(path,names):
    (path/"SHA256SUMS.txt").write_text("".join(f"{digest(path/n)}  {n}\n" for n in names))

class PubMindV2Test(unittest.TestCase):
    def test_overlap_novel_and_source_integrity(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            registry=root/"registry.tsv"
            write(registry,["hgnc_id","approved_hgnc_symbol"],
                  [{"hgnc_id":f"HGNC:{i}","approved_hgnc_symbol":f"GENE{i}"} for i in range(662)])
            hpo=root/"hpo";hpo.mkdir()
            write(hpo/"par_candidates.tsv",
                  ["candidate_id","gene_id","phenotype_id"],
                  [{"candidate_id":"c1","gene_id":"HGNC:0","phenotype_id":"HP:0000001"},
                   {"candidate_id":"c2","gene_id":"HGNC:0","phenotype_id":"HP:0000001"}])
            (hpo/"manifest.json").write_text(json.dumps({"reference_release":"HPO:v2026-09-01",
                "registry_gene_count":662,"candidate_count":2}))
            seal(hpo,["par_candidates.tsv","manifest.json"])
            gencc=root/"gencc";gencc.mkdir()
            write(gencc/"gencc_gene_disease_evidence.tsv",
                  ["gene_id","gencc_id","gencc_version"],
                  [{"gene_id":"HGNC:0","gencc_id":"SGC:1","gencc_version":"1"}])
            write(gencc/"gencc_hpo_exact_disease_matches.tsv",
                  ["candidate_id","gencc_id","gencc_version"],
                  [{"candidate_id":"c1","gencc_id":"SGC:1","gencc_version":"1"}])
            (gencc/"gencc_integration_manifest.json").write_text(json.dumps({
                "hpo_candidate_count":2,"gencc_assertions_for_registry_genes":1}))
            seal(gencc,["gencc_gene_disease_evidence.tsv",
                        "gencc_hpo_exact_disease_matches.tsv",
                        "gencc_integration_manifest.json"])
            pmh=root/"CHD_gene_HPO_associations_ranked_v2.tsv"
            write(pmh,["gene","HPO_ID","n_unique_publications","gene_provenance","association_provenance"],[
                {"gene":"GENE0","HPO_ID":"HP:0000001","n_unique_publications":"2","gene_provenance":"SNV","association_provenance":"SNV"},
                {"gene":"GENE1","HPO_ID":"HP:0000002","n_unique_publications":"1","gene_provenance":"SNV","association_provenance":"SNV"},
                {"gene":"GENE2","HPO_ID":"NA","n_unique_publications":"NA","gene_provenance":"CNV","association_provenance":"NA"}])
            pmm=root/"CHD_gene_MONDO_associations_ranked_v2.tsv"
            write(pmm,["gene","MONDO_ID","n_unique_publications","gene_provenance","association_provenance"],[
                {"gene":"GENE0","MONDO_ID":"MONDO:1","n_unique_publications":"5","gene_provenance":"SNV","association_provenance":"SNV"}])
            pmp=root/"CHD_gene_publication_associations_ranked_v2.tsv"
            write(pmp,["gene","Publication_ID","min_pathogenicity_score","mean_pathogenicity_score",
                       "max_pathogenicity_score","n_PVID_with_numeric_score","gene_provenance","association_provenance"],[
                {"gene":"GENE0","Publication_ID":"PMID:1","min_pathogenicity_score":"0.2",
                 "mean_pathogenicity_score":"0.5","max_pathogenicity_score":"0.8",
                 "n_PVID_with_numeric_score":"2","gene_provenance":"SNV","association_provenance":"SNV"}])
            result=integrate(registry,pmh,pmm,pmp,hpo,gencc,root/"out",strict_expected=False)
            self.assertEqual(result["pubmind_hpo_pairs"],2)
            self.assertEqual(result["pubmind_hpo_pairs_overlapping_hpo"],1)
            self.assertEqual(result["pubmind_hpo_pairs_new_to_hpo"],1)
            self.assertEqual(result["pubmind_genes_not_in_hpo_discovery"],1)
            with (root/"out"/"pubmind_hpo_to_devmap.tsv").open() as f:
                rows=list(csv.DictReader(f,delimiter="\t"))
            self.assertEqual(rows[0]["hpo_candidate_count"],"2")
            self.assertEqual(rows[0]["gencc_supported_candidate_count"],"1")
            self.assertEqual(rows[1]["integration_status"],"new_pubmind_gene_hpo")
            self.assertEqual(result["pubmind_gene_publication_pairs"],1)
            self.assertEqual(result["registry_genes"],662)

    def test_missing_column_rejected(self):
        from integrate_pubmind_v2 import records
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"bad.tsv"
            p.write_text("gene\tMONDO_ID\nA\tMONDO:1\n")
            with self.assertRaisesRegex(ValueError,"Missing columns"):
                list(records(p,("gene","hpo_id")))

if __name__=="__main__":
    unittest.main()
