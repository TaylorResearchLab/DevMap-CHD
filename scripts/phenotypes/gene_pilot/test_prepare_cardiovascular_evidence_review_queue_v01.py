import csv
import tempfile
import unittest
from pathlib import Path
from prepare_cardiovascular_evidence_review_queue_v01 import ledger

def table(path,fields,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t",lineterminator="\n")
        w.writeheader();w.writerows(rows)

class CardiovascularEvidenceReviewTest(unittest.TestCase):
    def test_source_only_review_record_and_category(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            ontology=root/"ontology.tsv"
            table(ontology,["gene_id","gene_symbol","hpo_id","hpo_name",
                 "integration_status","cardiovascular","heart_morphology",
                 "cardiovascular_physiology","pubmind_publication_count","hpo_status"],[
                {"gene_id":"HGNC:1","gene_symbol":"HAND1","hpo_id":"HP:0001961",
                 "hpo_name":"Hypoplastic ventricle","integration_status":"new_pubmind_gene_hpo",
                 "cardiovascular":"1","heart_morphology":"1","cardiovascular_physiology":"0",
                 "pubmind_publication_count":"1","hpo_status":"active"},
                {"gene_id":"HGNC:2","gene_symbol":"FTO","hpo_id":"HP:0031418",
                 "hpo_name":"Increased BMI","integration_status":"new_pubmind_gene_hpo",
                 "cardiovascular":"0","heart_morphology":"0","cardiovascular_physiology":"0",
                 "pubmind_publication_count":"50","hpo_status":"active"}])
            membership=root/"membership.tsv"
            table(membership,["gene_id","griffin_final_2023",
                 "griffin_fully_curated_not_final_2023",
                 "Griffin_2023_Supp_Table_1_All_Candidate_Genes.csv"],[
                {"gene_id":"HGNC:1","griffin_final_2023":"1",
                 "griffin_fully_curated_not_final_2023":"0",
                 "Griffin_2023_Supp_Table_1_All_Candidate_Genes.csv":"1"},
                {"gene_id":"HGNC:2","griffin_final_2023":"0",
                 "griffin_fully_curated_not_final_2023":"0",
                 "Griffin_2023_Supp_Table_1_All_Candidate_Genes.csv":"1"}])
            source=root/"source.tsv"
            table(source,["gene_id","hpo_id","source_row","source_sha256"],[
                {"gene_id":"HGNC:1","hpo_id":"HP:0001961",
                 "source_row":"805","source_sha256":"fixture-sha"}])
            summary=ledger(ontology,membership,source,root/"out",expected=False)
            self.assertEqual(summary["candidate_pairs"],1)
            self.assertEqual(summary["phenotype_categories"]["heart_morphology"],1)
            self.assertEqual(summary["publication_links_recovered"],0)
            with (root/"out"/"pubmind_novel_cardiovascular_evidence_review_queue.tsv").open() as f:
                row=next(csv.DictReader(f,delimiter="\t"))
            self.assertEqual(row["griffin_source_class"],"final")
            self.assertEqual(row["pubmind_hpo_source_row"],"805")
            self.assertEqual(row["Publication_ID"],"")
            self.assertEqual(row["PVID"],"")
            self.assertEqual(row["review_status"],
                             "awaiting_original_variant_hpo_publication_link")
    def test_unlinked_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            ontology=root/"ontology.tsv"
            table(ontology,["gene_id","gene_symbol","hpo_id","hpo_name",
                 "integration_status","cardiovascular","heart_morphology",
                 "cardiovascular_physiology","pubmind_publication_count","hpo_status"],[
                {"gene_id":"HGNC:1","gene_symbol":"HAND1","hpo_id":"HP:0001961",
                 "hpo_name":"Hypoplastic ventricle","integration_status":"new_pubmind_gene_hpo",
                 "cardiovascular":"1","heart_morphology":"1","cardiovascular_physiology":"0",
                 "pubmind_publication_count":"1","hpo_status":"active"}])
            membership=root/"membership.tsv"
            table(membership,["gene_id","griffin_final_2023",
                 "griffin_fully_curated_not_final_2023",
                 "Griffin_2023_Supp_Table_1_All_Candidate_Genes.csv"],[
                {"gene_id":"HGNC:1","griffin_final_2023":"1",
                 "griffin_fully_curated_not_final_2023":"0",
                 "Griffin_2023_Supp_Table_1_All_Candidate_Genes.csv":"1"}])
            source=root/"source.tsv"
            table(source,["gene_id","hpo_id","source_row","source_sha256"],[])
            with self.assertRaisesRegex(ValueError,"Missing source"):
                ledger(ontology,membership,source,root/"out",expected=False)

if __name__=="__main__":
    unittest.main()
