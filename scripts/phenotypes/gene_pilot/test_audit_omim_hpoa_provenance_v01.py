import csv
import tempfile
import unittest
from pathlib import Path
from audit_omim_hpoa_provenance_v01 import audit

FIELDS=("record_id","candidate_id","original_subject","original_object",
        "source_evidence_code","source_reference","primary_publication_id",
        "source_row_id","source_release","evidence_role")

def fixture(path,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,delimiter="\t",lineterminator="\n")
        w.writeheader();w.writerows(rows)

class OMIMProvenanceTests(unittest.TestCase):
    def test_omim_and_explicit_pmid_are_separated(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=root/"authority.tsv"
            fixture(source,[
                dict(record_id="e1",candidate_id="c1",original_subject="OMIM:111111",
                     original_object="HP:0001631",source_evidence_code="TAS",
                     source_reference="OMIM:123456;PMID:345678",
                     primary_publication_id="PMID:345678",source_row_id="phenotype.hpoa:2",
                     source_release="v2026-09-01",evidence_role="disease_phenotype_annotation"),
                dict(record_id="e2",candidate_id="c2",original_subject="OMIM:111111",
                     original_object="HP:0001961",source_evidence_code="IEA",
                     source_reference="OMIM:123456",primary_publication_id="",
                     source_row_id="phenotype.hpoa:3",source_release="v2026-09-01",
                     evidence_role="disease_phenotype_annotation"),
                dict(record_id="e3",candidate_id="c3",original_subject="OMIM:111111",
                     original_object="HP:0001961",source_evidence_code="TAS",
                     source_reference="ORPHA:2",primary_publication_id="",
                     source_row_id="phenotype.hpoa:4",source_release="v2026-09-01",
                     evidence_role="disease_phenotype_annotation")
            ])
            stats=audit(source,root/"out",strict=False)
            self.assertEqual(stats["hpoa_rows_with_omim_reference"],2)
            self.assertEqual(stats["distinct_omim_records"],1)
            self.assertEqual(stats["unique_omim_disease_phenotype_claims"],2)
            self.assertEqual(stats["hpoa_rows_with_omim_and_explicit_pmid"],1)
            self.assertEqual(stats["bibliography_links_verified"],0)
            with (root/"out"/"omim_hpoa_source_evidence.tsv").open() as f:
                rows=list(csv.DictReader(f,delimiter="\t"))
            self.assertEqual(rows[0]["hpoa_explicit_pmids"],"PMID:345678")
            self.assertEqual(rows[1]["phenotype_specific_verified_pmids"],"")
            self.assertEqual(rows[1]["publication_mapping_status"],
                "omim_bibliography_phenotype_specific_citation_unresolved")

    def test_one_hpoa_row_with_multiple_omim_ids_retains_both(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            source=root/"authority.tsv"
            fixture(source,[dict(record_id="e1",candidate_id="c1",
                original_subject="OMIM:111111",original_object="HP:0001631",
                source_evidence_code="TAS",source_reference="OMIM:123456;OMIM:234567",
                primary_publication_id="",source_row_id="phenotype.hpoa:9",
                source_release="v2026-09-01",evidence_role="disease_phenotype_annotation")])
            stats=audit(source,root/"out",strict=False)
            self.assertEqual(stats["hpoa_rows_with_omim_reference"],1)
            self.assertEqual(stats["omim_evidence_links"],2)
            self.assertEqual(stats["distinct_omim_records"],2)

    def test_duplicate_evidence_mapping_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);source=root/"authority.tsv"
            r=dict(record_id="e1",candidate_id="c1",original_subject="OMIM:111111",
                original_object="HP:0001631",source_evidence_code="TAS",
                source_reference="OMIM:123456",primary_publication_id="",
                source_row_id="phenotype.hpoa:2",source_release="v2026-09-01",
                evidence_role="disease_phenotype_annotation")
            fixture(source,[r,r])
            with self.assertRaisesRegex(ValueError,"Repeated evidence"):
                audit(source,root/"out",strict=False)

if __name__=="__main__":
    unittest.main()
