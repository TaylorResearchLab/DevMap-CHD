import csv
import tempfile
import unittest
from pathlib import Path
from prepare_pubmind_variant_trace_v01 import trace, labels_from_obo

def write(path, fields, rows):
    with path.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t",lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

class PubMindVariantTraceTest(unittest.TestCase):
    def test_priority_targets_do_not_infer_publication_link(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            targets=[("HAND1","HP:0001961"),("GJC1","HP:0001631"),("ID2","HP:0012248")]
            hpo=root/"hpo.tsv"
            write(hpo,["gene_symbol","hpo_id","pubmind_publication_count","integration_status","source_row","source_sha256"],
                [{"gene_symbol":g,"hpo_id":h,"pubmind_publication_count":"1",
                  "integration_status":"new_pubmind_gene_hpo","source_row":str(i+2),
                  "source_sha256":"sourcehash"} for i,(g,h) in enumerate(targets)])
            evidence=root/"source.tsv"
            write(evidence,["gene_symbol","source_type","source_identifier","source_pathogenicity_min","source_pathogenicity_mean","source_pathogenicity_max","source_numeric_pvid_count","association_provenance","source_row"],
                [{"gene_symbol":"HAND1","source_type":"PubMind_publication",
                  "source_identifier":"PMID:1","source_pathogenicity_min":"0.1",
                  "source_pathogenicity_mean":"0.4","source_pathogenicity_max":"0.8",
                  "source_numeric_pvid_count":"2","association_provenance":"SNV","source_row":"5"},
                 {"gene_symbol":"HAND1","source_type":"PubMind_MONDO",
                  "source_identifier":"MONDO:123","association_provenance":"SNV","source_row":"10"}])
            membership=root/"membership.tsv"
            write(membership,["gene_symbol","griffin_final_2023","griffin_fully_curated_not_final_2023",
                "Griffin_2023_Supp_Table_1_All_Candidate_Genes.csv"],
                [{"gene_symbol":g,"griffin_final_2023":str(int(g=="HAND1")),
                  "griffin_fully_curated_not_final_2023":str(int(g=="ID2")),
                  "Griffin_2023_Supp_Table_1_All_Candidate_Genes.csv":"1"} for g,h in targets])
            obo=root/"hp.obo"
            obo.write_text("[Term]\nid: HP:0001961\nname: Hypoplastic ventricle\n\n[Term]\nid: HP:0001631\nname: Atrial septal defect\n\n[Term]\nid: HP:0012248\nname: Prolonged PR interval\n")
            rows,manifest=trace(hpo,evidence,membership,obo,root/"out")
            self.assertEqual(len(rows),3)
            self.assertEqual(rows[0]["gene_publication_leads"],1)
            self.assertEqual(rows[0]["gene_mondo_associations"],1)
            self.assertEqual(rows[0]["griffin_status"],"Griffin final")
            self.assertEqual(rows[2]["griffin_status"],"Griffin curated not final")
            self.assertEqual(manifest["gene_level_publication_leads"],1)
            self.assertEqual(rows[0]["pvid_hpo_publication_link_status"],
                             "not_available_in_aggregated_v2_tables")
            with (root/"out"/"gene_level_publication_leads_unlinked.tsv").open() as f:
                leads=list(csv.DictReader(f,delimiter="\t"))
            self.assertEqual(leads[0]["link_role"],
                             "gene_level_publication_lead_not_hpo_specific_evidence")

    def test_missing_target_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            hpo=root/"hpo.tsv"; hpo.write_text("gene_symbol\thpo_id\n")
            source=root/"sources.tsv";source.write_text("gene_symbol\tsource_type\tsource_identifier\n")
            matrix=root/"membership.tsv";matrix.write_text("gene_symbol\n")
            obo=root/"hp.obo";obo.write_text("")
            with self.assertRaisesRegex(ValueError,"Missing required target"):
                trace(hpo,source,matrix,obo,root/"out")

    def test_ontology_obsolete_detection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"hp.obo"
            path.write_text("[Term]\nid: HP:0033798\nname: obsolete Impaired leukocyte adhesion\nis_obsolete: true\n")
            self.assertTrue(labels_from_obo(path)["HP:0033798"]["obsolete"])

if __name__=="__main__":
    unittest.main()
