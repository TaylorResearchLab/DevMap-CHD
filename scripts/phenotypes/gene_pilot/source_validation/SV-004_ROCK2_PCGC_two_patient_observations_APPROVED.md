# SV-004 | User approval of two ROCK2 original PCGC patient observations

**Scientific decision date:** 2026-11-08  
**Authority:** Deanne M. Taylor  
**Disposition:** **ACCEPT at original patient / variant / reported cardiac diagnosis scope**, with the original published diagnosis strings retained verbatim.  
**Independent source verification:** DevMap-Claude review [ROCK2 PCGC join complete](https://app.notion.com/p/4122918780088142a658e15bb37de4d2), second-reader checked both published original supplementary datasets against source files after exposure to Agent 1's construction packet.

## Evidence unit and original patient records

The evidence unit is a **single reported patient** with an observed ROCK2 de novo variant and the **actual PCGC cardiac diagnostic strings**. Two distinct probands are documented. Each has a single record in Jin et al. 2017 Supplementary Data Set 1 and a single corresponding ROCK2 row in Sevim Bayrak et al. 2020 Table S2.

| Attribute | SV-004a | SV-004b |
| --- | --- | --- |
| Original PCGC blinded ID | **1-11926** | **1-13760** |
| ROCK2 protein variant | **p.S39F** | **p.D255G** |
| S2 source chr:pos ref>alt | chr2:11484147 G>A | chr2:11367484 T>C |
| S2 source allele class | missense; reported filtered de novo variant | missense; reported filtered de novo variant |
| Primary PCGC record | Jin 2017 S1 **line 2687**, PCGC Trio | Jin 2017 S1 **line 2740**, PCGC Trio |
| Sevim Bayrak 2020 Table S2 | **line 245**, category CTD | **line 246**, category other |
| **Original `Cardiac Diagnoses` field, including its source pipe delimiters** | `AORTIC STENOSIS \| BICOMMISSURAL (BICUSPID, BILEAFLET, BIFOLIATE) AORTIC VALVE \| TETRALOGY OF FALLOT ` | `PATENT DUCTUS ARTERIOSUS ` |
| Original source `EM` / `NDD` | Yes / No | Yes / No |
| S2 Family history of CHD | Negative | Negative |

The diagnostic field for SV-004a contains **three separate diagnosis strings joined by literal pipe characters in the source**. The trailing space inside each source string is retained here. The original 2017 cohort records contain **2,871 unique blinded IDs** (2,645 trios, 226 singletons), each appearing once. The original 2020 S2 source contains **320 variant rows**, exactly **two ROCK2 rows**. The same individual is represented across the 2017 and 2020 publications; the 2020 report is a reanalysis and not an independent new proband.

### Source locator and custody

- Jin et al. 2017, *Nature Genetics*, PMID **28991257**, DOI **10.1038/ng.3970**. Supplementary Data Set 1 `Phenotypes for each CHD proband`, original published workbook `NIHMS906719-supplement-supp_datasets.xlsx`. User-provided original sheet export `NIHMS906719-supplement-supp_datasets_TABLE_S1.tsv.txt` (TSV text, 515,316 bytes, ChatGPT conversation file `file_00000000785481f5bcae6ac78df7ada5`). Independently checked SHA-256 **8089f313183d025f0ad9d5e58d554c5740a15dfb53172492cd03a8c6d3fe03ee**.
- Sevim Bayrak et al. 2020, *Genome Medicine*, DOI **10.1186/s13073-019-0709-8**, [Springer original Supplementary XLSX](https://media.springernature.com/original/springer-static/esm/art%3A10.1186%2Fs13073-019-0709-8/MediaObjects/13073_2019_709_MOESM1_ESM.xlsx), Table S2 `Filtered de novo mutations in cases`. User sheet export `13073_2019_709_MOESM1_ESM_TABLE_S2.tsv` (36,362 bytes; ChatGPT conversation file `file_00000000445881f592c11bb3e3a88732`). Independently checked original publisher workbook SHA-256 **1ee89cc19b7e88182e5c039e5a5621f6e488a3efaf9342d5cba63381362d9ab9**.
- Source review [Jin S1 to Sevim Bayrak S2 join](https://github.com/TaylorResearchLab/DevMap-CHD/blob/feature/gene-phenotypes/scripts/phenotypes/gene_pilot/source_validation/ROCK2_Jin2017_S1_to_SevimBayrak2020_S2_CASE_JOIN_v01.md); [independent review](https://app.notion.com/p/4122918780088142a658e15bb37de4d2); [DevMap CHD4 communications](https://app.notion.com/p/4122918780088122a501d23809e7e124).

## Normalization retained separately from the original observations

The accepted payload consists of the **original diagnosis strings**, not substituted HPO labels. The independent reviewer checked candidate HPO representations against the pinned ontology:

- `TETRALOGY OF FALLOT` → `HP:0001636`.
- `BICOMMISSURAL (BICUSPID, BILEAFLET, BIFOLIATE) AORTIC VALVE` → `HP:0001647` (bicuspid aortic valve general term, without assigning a raphe subtype).
- `AORTIC STENOSIS` retains its original unspecific anatomical level. `HP:0001650` denotes **aortic valve stenosis**, with `Aortic stenosis` as an ontology synonym, adding a *valvar level* absent from the original PCGC source. Store `HP:0001650` only as an optional **flagged candidate mapping** retaining the distinction, not as an accepted replacement or an assertion of original source specificity. This term is in the **physiology branch**, outside the strict structural heart-morphology subset.
- `PATENT DUCTUS ARTERIOSUS` → `HP:0001643` (great-artery vascular morphology). The 2017 S1 record does not report gestational age or age at diagnosis. Preserve PDA as a clinical observation with that source context.

**Additional context retained:** EM=Yes denotes extracardiac manifestations **without identified specific extracardiac phenotypes** in these source tables. NDD=No denotes the source's cohort label. Family history of CHD is Negative in S2. S2 genomic coordinates are recorded exactly as published; the assembly is **unstated in the source** and must be independently established before genomic normalization.

The original combination TOF + bicuspid aortic valve + aortic stenosis in subject 1-11926 is **clinically unusual**. An optional expert review (e.g., Dr. Goldmuntz) may refine or confirm diagnosis context as a separate, later source evaluation. The **user's approval of faithful documentation already stands**.

## Scientific scope of decision

User statement recorded verbatim: **“I accept the documentation of both patient observations while retaining the original dx strings.”**

This accepts two original, patient-associated clinical co-observation records. The ROCK2 gene–disease validity assessment remains **ClinGen Limited**; PanelApp Australia's separate Moderate classification cites overlapping literature. The observed variant and diagnoses can be retained as linked evidence without assigning causal sufficiency to ROCK2 for each lesion. **Canonical direct causal gene-disruption–phenotype PAR generation is a separate later decision**. Approval does not alter the pinned HPOA source claim/discovery representation (`dmpdsrc1`, `dmpview1`), the frozen 662-gene registry, or the three MESP1 observations approved under SV-003.

**Disposition:** SV-004a **Accepted, original observations**; SV-004b **Accepted, original observation**. Documentation complete and biological authority recorded. Retain verbatim original text and lineage. Pending technical implementation: optional source-level structured observation ledger and flagged HPO candidate map; no silent source rewriting.
