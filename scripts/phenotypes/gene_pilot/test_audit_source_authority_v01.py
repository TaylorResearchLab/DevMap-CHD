import csv
import tempfile
import unittest
from pathlib import Path
from audit_source_authority_v01 import audit

def write(path,fields,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,delimiter="\t",lineterminator="\n")
        w.writeheader();w.writerows(rows)

class SourceAuthorityTests(unittest.TestCase):
    def test_source_scopes_and_review_policy(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            hpo=root/"par_evidence.tsv"
            write(hpo,["candidate_id","evidence_id","original_subject","original_object",
                       "source_resource","source_release","source_evidence_code",
                       "primary_publication_id","original_reference",
                       "source_row_id","evidence_role"],[
                {"candidate_id":"c1","evidence_id":"e1","original_subject":"OMIM:1",
                 "original_object":"HP:0001631","source_resource":"HPOA",
                 "source_release":"v2026-09-01","source_evidence_code":"PCS",
                 "primary_publication_id":"PMID:123;PMID:456",
                 "original_reference":"PMID:123;PMID:456","source_row_id":"phenotype.hpoa:2",
                 "evidence_role":"disease_phenotype_annotation"},
                {"candidate_id":"c2","evidence_id":"e2","original_subject":"OMIM:2",
                 "original_object":"HP:0001961","source_resource":"HPOA",
                 "source_release":"v2026-09-01","source_evidence_code":"TAS",
                 "primary_publication_id":"","original_reference":"OMIM:2",
                 "source_row_id":"phenotype.hpoa:3",
                 "evidence_role":"disease_phenotype_annotation"}])
            gencc=root/"gencc.tsv"
            write(gencc,["gencc_id","gencc_version","gene_id",
                         "source_disease_id","source_classification","source_submitter"],[
                {"gencc_id":"SGC:1","gencc_version":"1","gene_id":"HGNC:1",
                 "source_disease_id":"MONDO:1","source_classification":"Definitive",
                 "source_submitter":"ClinGen"},
                {"gencc_id":"SGC:2","gencc_version":"1","gene_id":"HGNC:2",
                 "source_disease_id":"MONDO:2","source_classification":"Limited",
                 "source_submitter":"External Submitter"}])
            pub=root/"pubmind.tsv"
            write(pub,["gene_id","gene_symbol","hpo_id",
                       "pubmind_publication_count","source_row"],[
                {"gene_id":"HGNC:1","gene_symbol":"HAND1","hpo_id":"HP:0001961",
                 "pubmind_publication_count":"1","source_row":"805"}])
            result=audit(hpo,gencc,pub,root/"out",strict=False)
            self.assertEqual(result["hpoa_rows_with_traceable_pmid"],1)
            self.assertEqual(result["gencc_rows_with_pmid_in_this_export"],0)
            self.assertEqual(result["pubmind_rows_with_hpo_specific_pmid_in_this_export"],0)
            with (root/"out"/"hpoa_source_authority.tsv").open() as f:
                h=list(csv.DictReader(f,delimiter="\t"))
            self.assertEqual(h[0]["source_curation_status"],"expert_curated_with_pmid")
            self.assertEqual(h[0]["original_subject"],"OMIM:1")
            self.assertEqual(h[1]["devmap_disposition"],"provenance_review")
            with (root/"out"/"gencc_source_authority.tsv").open() as f:
                g=list(csv.DictReader(f,delimiter="\t"))
            self.assertEqual(g[0]["source_curation_status"],"expert_curated_provenance_incomplete")
            self.assertEqual(g[1]["source_curation_status"],"unresolved_source_type")
            with (root/"out"/"pubmind_source_authority.tsv").open() as f:
                p=next(csv.DictReader(f,delimiter="\t"))
            self.assertEqual(p["devmap_disposition"],"pending_secondary_review")
    def test_duplicate_original_evidence_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            fields=["candidate_id","evidence_id","original_subject","original_object",
                    "source_resource","source_release","source_evidence_code",
                    "primary_publication_id","original_reference","source_row_id","evidence_role"]
            r={k:"x" for k in fields}
            hpo=root/"hpo.tsv";write(hpo,fields,[r,r])
            gencc=root/"gencc.tsv"
            write(gencc,["gencc_id","gencc_version","gene_id",
                         "source_disease_id","source_classification","source_submitter"],[])
            pub=root/"pub.tsv"
            write(pub,["gene_id","gene_symbol","hpo_id",
                       "pubmind_publication_count","source_row"],[])
            with self.assertRaisesRegex(ValueError,"Duplicate HPO"):
                audit(hpo,gencc,pub,root/"out",strict=False)

if __name__=="__main__":
    unittest.main()
