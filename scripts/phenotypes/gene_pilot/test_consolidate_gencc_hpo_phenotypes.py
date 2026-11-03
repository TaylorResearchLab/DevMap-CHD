import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from consolidate_gencc_hpo_phenotypes import summarize

def write_tsv(path,rows):
    with open(path,"w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter="\t",lineterminator="\n")
        w.writeheader()
        w.writerows(rows)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def seal(directory,names):
    (directory/"SHA256SUMS.txt").write_text(
        "".join(f"{sha(directory/name)}  {name}\n" for name in names),encoding="utf-8")

class ConsolidationTest(unittest.TestCase):
    def make_inputs(self,root):
        hpo=root/"hpo";hpo.mkdir()
        gencc=root/"gencc";gencc.mkdir()
        candidates=[
            {"candidate_id":"c1","gene_id":"HGNC:1","gene_symbol":"GENE1",
             "disruption_type":"unspecified_disruption","phenotype_id":"HP:1",
             "disease_id":"OMIM:1","assertion_state":"disease_mediated_candidate_asserted_present",
             "evidence_count":"2"},
            {"candidate_id":"c2","gene_id":"HGNC:1","gene_symbol":"GENE1",
             "disruption_type":"unspecified_disruption","phenotype_id":"HP:2",
             "disease_id":"OMIM:2","assertion_state":"disease_mediated_candidate_asserted_absent",
             "evidence_count":"1"},
            {"candidate_id":"c3","gene_id":"HGNC:2","gene_symbol":"GENE2",
             "disruption_type":"unspecified_disruption","phenotype_id":"HP:3",
             "disease_id":"MONDO:7","assertion_state":"disease_mediated_candidate_unspecified",
             "evidence_count":"1"}]
        write_tsv(hpo/"par_candidates.tsv",candidates)
        write_tsv(hpo/"gene_coverage.tsv",[
            {"gene_id":f"HGNC:{i}","gene_symbol":f"GENE{i}",
             "candidate_count":2 if i==1 else (1 if i==2 else 0)}
            for i in range(1,663)])
        (hpo/"par_evidence.tsv").write_text("candidate_id\n",encoding="utf-8")
        (hpo/"manifest.json").write_text(json.dumps({
            "reference_release":"HPO:v2026-09-01",
            "registry_gene_count":662,"candidate_count":3}),encoding="utf-8")
        seal(hpo,["manifest.json","par_candidates.tsv","par_evidence.tsv","gene_coverage.tsv"])
        genetics=[
            {"gene_id":"HGNC:1","gencc_id":"SGC-A","gencc_version":"1",
             "source_disease_id":"OMIM:1","source_classification":"Definitive",
             "source_inheritance":"Autosomal dominant","source_submitter":"Submitter A"},
            {"gene_id":"HGNC:1","gencc_id":"SGC-B","gencc_version":"2",
             "source_disease_id":"OMIM:1","source_classification":"Strong",
             "source_inheritance":"Autosomal dominant","source_submitter":"Submitter B"},
            {"gene_id":"HGNC:3","gencc_id":"SGC-C","gencc_version":"1",
             "source_disease_id":"MONDO:3","source_classification":"Limited",
             "source_inheritance":"Autosomal recessive","source_submitter":"Submitter C"}]
        write_tsv(gencc/"gencc_gene_disease_evidence.tsv",genetics)
        matches=[{"candidate_id":"c1","gene_id":"HGNC:1","phenotype_id":"HP:1",
                  "disease_id":"OMIM:1","gencc_id":x["gencc_id"],
                  "gencc_version":x["gencc_version"],
                  "source_classification":x["source_classification"],
                  "source_inheritance":x["source_inheritance"],
                  "source_submitter":x["source_submitter"],
                  "match_type":"identical_native_disease_curie"}
                 for x in genetics[:2]]
        write_tsv(gencc/"gencc_hpo_exact_disease_matches.tsv",matches)
        (gencc/"gencc_integration_manifest.json").write_text(json.dumps({
            "hpo_candidate_count":3,
            "gencc_assertions_for_registry_genes":3,
            "exact_disease_candidate_matches":2}),encoding="utf-8")
        seal(gencc,["gencc_integration_manifest.json",
                    "gencc_gene_disease_evidence.tsv",
                    "gencc_hpo_exact_disease_matches.tsv"])
        return hpo,gencc

    def test_unique_candidate_and_multi_source_provenance(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            hpo,gencc=self.make_inputs(root)
            result=summarize(hpo,gencc,root/"out")
            self.assertEqual(result["unique_hpo_candidates"],3)
            self.assertEqual(result["gencc_source_links"],2)
            self.assertEqual(result["unique_candidates_with_gencc_support"],1)
            self.assertEqual(result["unique_candidates_hpo_only"],2)
            self.assertEqual(result["coverage_categories"],
                {"both_sources":1,"gencc_only":1,"hpo_only":1,"neither_source":659})
            with open(root/"out"/"consolidated_phenotype_candidates.tsv") as f:
                rows=list(csv.DictReader(f,delimiter="\t"))
            by_id={r["candidate_id"]:r for r in rows}
            self.assertEqual(by_id["c1"]["gencc_submission_count"],"2")
            self.assertEqual(by_id["c1"]["gencc_assertion_ids"],"SGC-A@1;SGC-B@2")
            self.assertEqual(by_id["c2"]["gencc_submission_count"],"0")
            self.assertEqual(result["direct_disruption_phenotype_records_accepted"],0)
            with open(root/"out"/"direct_phenotype_evidence_template.tsv") as f:
                self.assertEqual(len(f.readlines()),1)

    def test_modified_gencc_source_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            hpo,gencc=self.make_inputs(root)
            with open(gencc/"gencc_gene_disease_evidence.tsv","a") as f:
                f.write("changed\n")
            with self.assertRaisesRegex(ValueError,"Unverified or modified"):
                summarize(hpo,gencc,root/"out")

if __name__=="__main__":
    unittest.main()
