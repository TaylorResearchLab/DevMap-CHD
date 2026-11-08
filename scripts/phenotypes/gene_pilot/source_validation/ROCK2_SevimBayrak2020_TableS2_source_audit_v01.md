# ROCK2 | Primary supplementary source audit of Table S2 (2026-11-08)

**Status:** Real user-supplied original supplementary TSV examined via ChatGPT Files structured reading. Source provenance and source-level genotype/cardiac-category observations independently checkable; clinical lesion-level records beyond the published cardiac category remain unverified. This is a versioned audit, not a biological acceptance or a direct PAR release.

## Original publication and file custody

- Paper: Sevim Bayrak et al. 2020, *Genome Medicine*, [DOI 10.1186/s13073-019-0709-8](https://doi.org/10.1186/s13073-019-0709-8), [PMC6961332](https://pmc.ncbi.nlm.nih.gov/articles/PMC6961332/).
- Original publisher additional file 1: [13073_2019_709_MOESM1_ESM.xlsx](https://media.springernature.com/original/springer-static/esm/art%3A10.1186%2Fs13073-019-0709-8/MediaObjects/13073_2019_709_MOESM1_ESM.xlsx). The original workbook is preserved as a Notion attachment in [DevMap CHD4 Communications Log](https://app.notion.com/p/4122918780088122a501d23809e7e124).
- User directly exported and attached `13073_2019_709_MOESM1_ESM_TABLE_S2.tsv` from workbook Table S2, with **36,362 bytes**, conversation attachment ID `file_00000000445881f592c11bb3e3a88732`. The declared conversation sandbox path is `/mnt/data/13073_2019_709_MOESM1_ESM_TABLE_S2.tsv`, but the container and Python execution environments did not mount it in this session. **ChatGPT Files read and find parsed the actual TSV source and returned the original text rows**, including header and source line locations. There is no evidence of a damaged source file. File-level SHA-256 is pending filesystem access.
- Table S2 title: **Filtered de novo mutations in cases**; the source contains **320 variant records** beneath a title row and 19-column header (322 text lines including header/title). Its original gene column has **two ROCK2 rows**, lines **245 and 246** of the TSV. Other genes' rows are conserved in the original uploaded source; this audit does not rewrite the source.

## Full two ROCK2 source rows transcribed as source records

| Original source field | ROCK2 p.S39F | ROCK2 p.D255G |
| --- | --- | --- |
| `CHROM` | 2 | 2 |
| `POS` | 11484147 | 11367484 |
| `REF` / `ALT` | G / A | T / C |
| `Ensemble_GENEID` (source column spelling) | ENSG00000134318 | ENSG00000134318 |
| `Variant_Class` | mis | mis |
| `AA change` | p.S39F | p.D255G |
| `Blinded ID` | **1-11926** | **1-13760** |
| `Cardiac Category` | **CTD** | **other** |
| `EM` | Yes | Yes |
| `NDD` | No | No |
| `Family history of CHD` | Negative | Negative |
| `CADD_Score` | 27.6 | 28.4 |
| `MSC (CADD)` | 8.931 | 8.931 |
| `GDI_Phred` | 9.60708 | 9.60708 |
| `GDI_Prediction` | Medium | Medium |
| `#_mutations_cases` | 2 | 2 |
| `#_mutations_controls` | 0 | 0 |
| Source line | 245 | 246 |

These are **two distinct blinded patient IDs**, each with a ROCK2 missense de novo variant in the source filtered table. The `#_mutations_cases=2` is the **gene-level case count repeated per ROCK2 variant row**, not two mutations in each of the two patients; it must not be double-counted as four observations.

The category **CTD** is the article's *conotruncal defect* category. Original PCGC cardiac groupings include TOF, DORV, truncus, membranous VSD and aortic arch abnormalities under CTD; **a CTD category does not identify which exact lesion this patient carried**. The category **other** includes several possible cardiac lesions (such as pulmonary valve anomalies, ASD, atrioventricular canal defects and more); it is not evidence of one selected lesion. The `EM` field denotes extracardiac malformation/manifestation and `NDD` neurodevelopmental deficiency in the published study's source conventions. The two ROCK2 patients have **EM=Yes, NDD=No**, which indicates syndromic/extra-cardiac context despite absent neurodevelopmental deficiency in the source table. `Family history of CHD=Negative` is recorded separately from de novo variant classification. The source reference assembly is likely consistent with the original PCGC hg19 alignment, but this table itself does not declare an assembly. Keep raw coordinates until verified.

## Reconciliation with ClinGen CHD gene–disease validity

- [ClinGen ROCK2, CCID:008432](https://search.clinicalgenome.org/CCID:008432) retains a **Limited** gene–disease validity classification for broad congenital heart disease. It maps `p.S39F` to `HP:0001710` **Conotruncal defect** and `p.D255G` to broad `HP:0001627` **Abnormal heart morphology** in its clinical case evidence.
- **p.S39F:** original S2 **CTD** category and ClinGen **Conotruncal defect** map at compatible broad scope. This is a **category-level concordance**, not independent confirmation of an exact lesion or proof of a causal gene disruption–phenotype relationship.
- **p.D255G:** original S2 category **other** and ClinGen broad heart morphology remain compatible as *nonspecific structural CHD classifications*. Neither states a specific cardiac anatomical lesion in this source. Do not map `other` directly onto `HP:0001627` as an ontology assertion without the original clinical case information.
- Sevim Bayrak 2020 is a reanalysis of a PCGC cohort whose primary published source is [Jin et al. 2017, PMID 28991257](https://doi.org/10.1038/ng.3970), 2,871 probands including 2,645 trios. The source `Blinded ID` values `1-11926` and `1-13760` are the patient linkage keys to inspect in Jin's [Supplementary Data Sets 1–12](https://www.nature.com/articles/ng.3970).
- The original publication's source table and ClinGen's later curator descriptions are **separate records with shared underlying patients**. Repeated citing or study reanalysis does not add independent patient evidence.

## Scientific disposition and next source check

**Directly supported by the user's actual Table S2:** two ROCK2 variants, distinct blinded case identifiers, broad cardiac categories, presence of extracardiac manifestations, absence of reported NDD, and negative recorded CHD family histories. **Still required:** original individual structural diagnosis from PCGC primary case records and an exact case-matching table to the ClinGen curator's probands. A CTD category should be preserved as a categorical annotation and not substituted for a specific patient lesion.

Recommended to DevMap-Claude Agent 2 for independent review of the two source rows, source classification/ontology mapping, and original Jin 2017 linkage. **No direct gene–phenotype PAR minted, no user biological acceptance requested yet, and no frozen source or registry changed.**

## Follow-up: original PCGC clinical diagnoses recovered from Jin 2017 S1

The user subsequently uploaded Jin et al. 2017 **Supplementary Data Set 1** as `NIHMS906719-supplement-supp_datasets_TABLE_S1.tsv.txt`, original conversation Files record `file_00000000785481f5bcae6ac78df7ada5`. Exact blinded ID joins were verified using direct file text reading: **ROCK2 p.S39F** subject `1-11926` (S1 source line 2687) has **AORTIC STENOSIS**, **BICOMMISSURAL (BICUSPID, BILEAFLET, BIFOLIATE) AORTIC VALVE** and **TETRALOGY OF FALLOT**. **ROCK2 p.D255G** subject `1-13760` (S1 source line 2740) has **PATENT DUCTUS ARTERIOSUS**. Both are PCGC trios with EM Yes/NDD No. These are the two same individuals as S2 lines 245–246; joining two publications does not create replication. The exact observed lesion sources and proposed review are captured in the [dedicated S1–S2 case join v01](https://github.com/TaylorResearchLab/DevMap-CHD/blob/feature/gene-phenotypes/scripts/phenotypes/gene_pilot/source_validation/ROCK2_Jin2017_S1_to_SevimBayrak2020_S2_CASE_JOIN_v01.md), commit `c84001d4400b2e990774d841a260d57dece716e6`. **This supersedes the earlier “Still required: original individual structural diagnosis” statement.** HPO normalization, independent review and user acceptance are the remaining requirements. No causal PAR.
