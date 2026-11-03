import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from screen_pubmed_disruption_phenotypes import screen,load_hpo_labels

def write_tsv(path,rows):
    with open(path,"w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter="\t",lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

class PubMedScreenTest(unittest.TestCase):
    def test_abstract_match_and_original_source_identity(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);source=root/"src";source.mkdir()
            write_tsv(source/"par_candidates.tsv",[
                {"candidate_id":"c1","gene_id":"HGNC:11604","gene_symbol":"TBX5",
                 "phenotype_id":"HP:0001631","disease_id":"OMIM:142900",
                 "assertion_state":"disease_mediated_candidate_asserted_present"},
                {"candidate_id":"c2","gene_id":"HGNC:11604","gene_symbol":"TBX5",
                 "phenotype_id":"HP:0001631","disease_id":"OMIM:142900",
                 "assertion_state":"disease_mediated_candidate_asserted_absent"}])
            write_tsv(source/"par_evidence.tsv",[
                {"candidate_id":"c1","primary_publication_id":"PMID:123"},
                {"candidate_id":"c2","primary_publication_id":"PMID:123"}])
            (source/"manifest.json").write_text(json.dumps({"reference_release":"HPO:v2026-09-01","registry_gene_count":662}))
            with open(source/"SHA256SUMS.txt","w") as f:
                for name in ("par_candidates.tsv","par_evidence.tsv","manifest.json"):
                    f.write(f"{sha(source/name)}  {name}\n")
            queue=root/"publication_gene_queue.tsv"
            write_tsv(queue,[{"gene_id":"HGNC:11604","gene_symbol":"TBX5",
                              "publication_id":"PMID:123","phenotype_count":"1"}])
            obo=root/"hp.obo";obo.write_text(
                "format-version: 1.2\n[Term]\nid: HP:0001631\nname: Atrial septal defect\n",encoding="utf-8")
            xml=root/"pubmed.xml";xml.write_text(
                "<PubmedArticleSet><PubmedArticle><MedlineCitation><PMID>123</PMID>"
                "<Article><ArticleTitle>Test</ArticleTitle><Abstract><AbstractText>"
                "TBX5 haploinsufficiency was associated with atrial septal defect in affected individuals."
                "</AbstractText></Abstract></Article></MedlineCitation></PubmedArticle></PubmedArticleSet>")
            result=screen(source,queue,obo,xml,root/"out",max_pairs=10,
                          allow_unpinned_test_inputs=True)
            self.assertEqual(result["screened_sentence_matches"],1)
            self.assertEqual(result["biological_pars_accepted"],0)
            with open(root/"out"/"abstract_candidate_sentences.tsv") as f:
                row=next(csv.DictReader(f,delimiter="\t"))
                self.assertEqual(row["candidate_id"],"c1")
                self.assertIn("haploinsufficiency",row["disruption_lexeme"])
                self.assertEqual(row["evidence_decision"],"requires_original_article_verification")
            self.assertEqual(load_hpo_labels(obo)["HP:0001631"],"Atrial septal defect")

if __name__=="__main__":
    unittest.main()
