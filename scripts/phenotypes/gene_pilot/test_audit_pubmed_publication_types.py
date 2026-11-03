import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from audit_pubmed_publication_types import audit, classify

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(path,rows):
    with open(path,"w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]),delimiter="\t",lineterminator="\n")
        writer.writeheader();writer.writerows(rows)

def seal(path,names):
    (path/"SHA256SUMS.txt").write_text(
        "".join(f"{sha(path/name)}  {name}\n" for name in names),encoding="utf-8")

class PublicationTypeAuditTest(unittest.TestCase):
    def fixture(self,root):
        queue_dir=root/"queue";queue_dir.mkdir()
        screen=root/"screen";screen.mkdir()
        write(queue_dir/"publication_gene_queue.tsv",[
            {"gene_id":"HGNC:1","gene_symbol":"A","publication_id":"PMID:1","phenotype_count":"5"},
            {"gene_id":"HGNC:2","gene_symbol":"B","publication_id":"PMID:1","phenotype_count":"4"},
            {"gene_id":"HGNC:3","gene_symbol":"C","publication_id":"PMID:2","phenotype_count":"3"},
            {"gene_id":"HGNC:4","gene_symbol":"D","publication_id":"PMID:3","phenotype_count":"2"}])
        seal(queue_dir,["publication_gene_queue.tsv"])
        xml=root/"pubmed.xml"
        xml.write_text(
            "<PubmedArticleSet>"+
            '<PubmedArticle><MedlineCitation><PMID>1</PMID><Article>'
            '<ArticleTitle>Primary cohort</ArticleTitle><PublicationTypeList>'
            '<PublicationType>Journal Article</PublicationType>'
            '<PublicationType>Clinical Study</PublicationType></PublicationTypeList>'
            '</Article></MedlineCitation></PubmedArticle>'+
            '<PubmedArticle><MedlineCitation><PMID>2</PMID><Article>'
            '<ArticleTitle>Review paper</ArticleTitle><PublicationTypeList>'
            '<PublicationType>Review</PublicationType>'
            '<PublicationType>Journal Article</PublicationType></PublicationTypeList>'
            '</Article></MedlineCitation></PubmedArticle>'+
            '<PubmedArticle><MedlineCitation><PMID>3</PMID><Article>'
            '<ArticleTitle>Generic journal</ArticleTitle><PublicationTypeList>'
            '<PublicationType>Journal Article</PublicationType></PublicationTypeList>'
            '</Article></MedlineCitation></PubmedArticle>'+
            "</PubmedArticleSet>",encoding="utf-8")
        write(screen/"abstract_candidate_sentences.tsv",[
            {"candidate_id":"candidate1","gene_id":"HGNC:1","gene_symbol":"A",
             "phenotype_id":"HP:1","publication_id":"PMID:1",
             "abstract_sentence":"A pathogenic variant and phenotype were documented.",
             "evidence_decision":"requires_original_article_verification"},
            {"candidate_id":"candidate2","gene_id":"HGNC:3","gene_symbol":"C",
             "phenotype_id":"HP:2","publication_id":"PMID:2",
             "abstract_sentence":"C mutation and phenotype were discussed.",
             "evidence_decision":"requires_original_article_verification"}])
        (screen/"abstract_screen_manifest.json").write_text(json.dumps({
            "pubmed_xml_sha256":sha(xml),
            "publication_gene_pairs_requested":4,
            "screened_sentence_matches":2}),encoding="utf-8")
        seal(screen,["abstract_candidate_sentences.tsv","abstract_screen_manifest.json"])
        return xml,queue_dir/"publication_gene_queue.tsv",screen

    def test_gene_multiplicity_and_review_vs_clinical_study(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            xml,queue,screen=self.fixture(root)
            stats=audit(xml,queue,screen,root/"output",max_pairs=4)
            self.assertEqual(stats["publication_count"],3)
            self.assertEqual(stats["selected_gene_publication_pairs"],4)
            self.assertEqual(stats["multi_gene_publication_count"],1)
            self.assertEqual(stats["publication_classifications"],{
                "primary_study_type":1,"review_or_meta_analysis":1,
                "journal_article_unresolved":1})
            self.assertEqual(stats["screened_sentence_rows"],2)
            self.assertEqual(stats["direct_disruption_phenotype_pars_accepted"],0)
            with open(root/"output"/"screened_sentences_with_publication_type.tsv") as f:
                rows=list(csv.DictReader(f,delimiter="\t"))
            self.assertEqual({r["publication_classification"] for r in rows},
                             {"review_or_meta_analysis","primary_study_type"})
            self.assertEqual({r["review_disposition"] for r in rows},
                             {"requires_original_article_verification"})

    def test_review_priority_and_unknown(self):
        self.assertEqual(classify(["Journal Article","Review"])[0],"review_or_meta_analysis")
        self.assertEqual(classify(["Journal Article"])[0],"journal_article_unresolved")
        self.assertEqual(classify([])[0],"unclassified")

    def test_source_checksum_integrity(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            xml,queue,screen=self.fixture(root)
            with open(queue,"a",encoding="utf-8") as f:f.write("mutation\n")
            with self.assertRaisesRegex(ValueError,"Unverified input"):
                audit(xml,queue,screen,root/"output",max_pairs=4)

if __name__=="__main__":
    unittest.main()
