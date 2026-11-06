import csv
import tempfile
import unittest
from pathlib import Path
from audit_pubmind_hpo_ontology_v01 import audit

ROOTS = """format-version: 1.2
[Term]
id: HP:0001626
name: Abnormality of the cardiovascular system

[Term]
id: HP:0030680
name: Abnormal cardiovascular system morphology
is_a: HP:0001626 ! Abnormality of the cardiovascular system

[Term]
id: HP:0001627
name: Abnormal heart morphology
is_a: HP:0030680 ! Abnormal cardiovascular system morphology

[Term]
id: HP:0011025
name: Abnormal cardiovascular system physiology
is_a: HP:0001626 ! Abnormality of the cardiovascular system

[Term]
id: HP:0001961
name: Hypoplastic ventricle
is_a: HP:0001627 ! Abnormal heart morphology
alt_id: HP:9990001

[Term]
id: HP:0012248
name: Prolonged PR interval
is_a: HP:0011025 ! Abnormal cardiovascular system physiology

[Term]
id: HP:0033798
name: obsolete Impaired leukocyte adhesion
is_obsolete: true
consider: HP:0001961

[Term]
id: HP:0012826
name: Moderate

[Term]
id: HP:0020000
name: Metabolic feature
"""
FIELDS=("gene_id","gene_symbol","hpo_id","integration_status",
        "pubmind_publication_count","source_row")

def create(path,rows):
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,delimiter="\t",lineterminator="\n")
        w.writeheader()
        for i,(gene,hpo,status) in enumerate(rows):
            w.writerow({"gene_id":f"HGNC:{i+1}","gene_symbol":gene,
                        "hpo_id":hpo,"integration_status":status,
                        "pubmind_publication_count":"1","source_row":str(i+2)})

class HPOOntologyAuditTest(unittest.TestCase):
    def test_ancestry_obsolete_and_alternate_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            obo=root/"hp.obo";obo.write_text(ROOTS)
            inp=root/"pairs.tsv"
            create(inp,[("HAND1","HP:0001961","new_pubmind_gene_hpo"),
                        ("ID2","HP:0012248","new_pubmind_gene_hpo"),
                        ("VCAM1","HP:0033798","new_pubmind_gene_hpo"),
                        ("BMP7","HP:0012826","overlap_hpo_unspecified"),
                        ("ALIAS","HP:9990001","new_pubmind_gene_hpo")])
            manifest=audit(inp,obo,root/"out",expected_counts=False)
            self.assertEqual(manifest["new_cardiovascular_pairs"],3)
            self.assertEqual(manifest["new_heart_morphology_pairs"],2)
            self.assertEqual(manifest["new_cardiovascular_physiology_pairs"],1)
            self.assertEqual(len(manifest["obsolete_terms"]),1)
            with (root/"out"/"pubmind_hpo_terms_ontology_audit.tsv").open() as f:
                terms={r["source_hpo_id"]:r for r in csv.DictReader(f,delimiter="\t")}
            self.assertEqual(terms["HP:9990001"]["status"],"alternate_id")
            self.assertEqual(terms["HP:0033798"]["status"],"obsolete")
            self.assertEqual(terms["HP:0012826"]["severity_descriptor"],"1")
            self.assertEqual(terms["HP:0033798"]["is_cardiovascular"],"0")

    def test_duplicate_gene_hpo_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            obo=root/"hp.obo";obo.write_text(ROOTS)
            inp=root/"pairs.tsv"
            create(inp,[("HAND1","HP:0001961","new_pubmind_gene_hpo"),
                        ("HAND1","HP:0001961","new_pubmind_gene_hpo")])
            # Input generator uses different HGNC IDs, so force repeated gene identity
            lines=inp.read_text().splitlines()
            lines[2]=lines[2].replace("HGNC:2","HGNC:1")
            inp.write_text("\n".join(lines)+"\n")
            with self.assertRaisesRegex(ValueError,"Repeated Gene-HPO"):
                audit(inp,obo,root/"out",expected_counts=False)

    def test_documented_release_counts_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            obo=root/"hp.obo";obo.write_text(ROOTS)
            inp=root/"pairs.tsv"
            create(inp,[("HAND1","HP:0001961","new_pubmind_gene_hpo")])
            with self.assertRaisesRegex(ValueError,"frozen v2"):
                audit(inp,obo,root/"out")

if __name__=="__main__":
    unittest.main()
