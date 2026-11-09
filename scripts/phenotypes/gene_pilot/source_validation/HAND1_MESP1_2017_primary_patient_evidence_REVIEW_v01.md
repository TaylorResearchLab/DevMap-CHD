# HAND1 and MESP1 | 2017 original patient-level structural CHD sources

**Date:** 2026-11-09  
**Construction:** DevMap-GPT Agent 1, full original publisher HTML inspected directly  
**Independent review:** DevMap-Claude Agent 2 requested; earlier Agent 2 review checked abstracts but not publisher full text  
**Status:** **Source observation candidates ready for independent review**, not yet accepted by scientific authority. **Keep outside the SV-003/SV-004 approved structured clinical ledger until independently reviewed and dispositioned.**

## Clinical and variant observations (two original papers, two reported individuals)

| Field | HAND1 Li et al. 2017 | MESP1 Zhang et al. 2017 |
| --- | --- | --- |
| Original publication | PMID **28112363**, DOI **10.3892/ijmm.2017.2865** | PMID **28677747**, DOI **10.3892/mmr.2017.6875** |
| Source | [Publisher complete original HTML](https://www.spandidos-publications.com/10.3892/ijmm.2017.2865?text=fulltext) | [Publisher complete original HTML](https://www.spandidos-publications.com/10.3892/mmr.2017.6875?text=fulltext) |
| Source location | Results → **Discovery of a de novo HAND1 mutation**, Fig. 1/2 and assay Fig. 4/5 | Results → **Identification of a novel MESP1 mutation in CHD**, Fig. 1/2 and assay Fig. 4 |
| Original nucleotide/protein variant | **c.394A>T, p.K132X** | **c.352C>T, p.Q118X** |
| Original patient | **5-month-old boy** | **3-month-old female** |
| Individual clinical diagnosis | **Congenital double outlet right ventricle (DORV) and ventricular septal defect (VSD)** | **DORV and VSD** |
| Source original phenotype wording (case narrative) | `congenital DORV, as well as VSD` | `DORV and VSD` |
| HPO normalization candidates | DORV **HP:0001719**, VSD **HP:0001629**, independently confirmed in ClinGen curation at broad exact disease term | DORV **HP:0001719**, VSD **HP:0001629** |
| Source inheritance | **De novo** by testing healthy parents, mutation absent from both | **De novo** by parental genotyping, absent in both |
| Reported family history | No CHD family history | No CHD family history; parents reportedly unaffected by CHD |
| Population screened | **158** unrelated Chinese Han CHD cases; **300** unrelated controls, i.e., **600 control chromosomes** | **178** unrelated Chinese Han CHD cases; **200** unrelated controls, i.e., **400 control chromosomes** |
| Study genotype source | Sanger/PCR sequencing of HAND1 coding exons and splice junctions; published chromatograms in Fig. 1 | PCR sequencing of MESP1 coding exons and splice junctions; published chromatograms in Fig. 1 |
| Original source ascertainment | Clinically evaluated and CHD confirmed by echocardiography; syndromic CHD excluded | Cardiac imaging and/or operative confirmation; recognizable syndromic CHD excluded |
| Individual patient source ID | **Not separately assigned in accessible original case narrative** | **Not separately assigned in accessible original case narrative** |

The original studies report one index case per variant. Both publications report joint DORV and VSD as case observations, not a general cohort-wide phenotype assigned to every sampled individual. Their distinct variants and genes are kept in separate records. Case ID is recorded as absent from the source narrative; do not manufacture a clinical subject ID.

## Experimental assay evidence (separate from clinical observations)

**HAND1 p.K132X:** Publisher full-text Results, HeLa ANF reporter Fig. 4: wild-type ~10-fold versus mutant ~1-fold activation. In NIH3T3 with GATA4, wild-type HAND1 ~22-fold versus mutant ~7-fold ANF reporter activation (Fig. 5). This reports impaired transcription and synergy in vitro, not a direct anatomical lesion measurement or independent patient sample.

**MESP1 p.Q118X:** HEK293 E-box/E47 reporter, Fig. 4: wild-type ~14-fold activation versus Q118X mutant ~1-fold; co-expression wild-type plus Q118X ~7-fold. Retain source scale as approximate fold-change and original assay conditions. Published figure legend states means ± standard deviation for three independent experiments performed in triplicate. Do not reinterpret these functional measurements as independent affected individuals.

## Source-specific discrepancy: MESP1 p.Q118X proband sex

**Primary patient report:** [Zhang et al. 2017 original full-text Results](https://www.spandidos-publications.com/10.3892/mmr.2017.6875?text=fulltext) specifies a **3-month-old female** and uses **her** for the index patient's family history. Preserve `source_sex=female` in the original publication observation.

**Secondary curator source:** [ClinGen MESP1–CHD, CCID:008509](https://search.clinicalgenome.org/CCID:008509), individual scored evidence row `Chinese Han Proband Zhang`, variant `NM_018670.4(MESP1):c.352C>T (p.Gln118Ter)`, PMID `28677747`, records **Proband Sex: Male** with HPO DORV `HP:0001719` and VSD `HP:0001629`. This refers to the **same underlying article, gene, and variant**. It is a documented **source-versus-curation disagreement**, not two probands. Record the original patient sex and ClinGen's distinct curator annotation with explicit conflict status. Pending a source correction, the primary publication takes precedence for transcription of its own patient record. Preserve ClinGen's scored case row as separate curation evidence; consider a ClinGen issue/report later after independent agent review.

## Cohort identity and interpretation

The two studies have common senior authors and overlapping clinical recruitment institutions. **Cohort overlap cannot be excluded from the available descriptions**, so do not sum the sample denominators to infer independent population coverage or derive independent replication. However, the papers report **different variants in different genes**; neither source claims its index patient is identical to the other's. Current case documentation assigns one source-specific case per published paper, with no inferred shared person identifier.

The earlier HAND1 p.R118C TOF source [Wang et al. 2017, PMID 27942761](https://pubmed.ncbi.nlm.nih.gov/27942761/) describes a third source-reported variant in **165** unrelated CHD patients and **600** control chromosomes, with reduced HAND1 reporter activity. Its **abstract confirms an index TOF case**, but the full original Springer case Results text, subject age and inheritance remain to be independently verified. The source paper uses shared senior-author networks, so preserve potential ascertainment overlap. This case is **not** included in the full-text-verified two-case packet.

## Relation to existing DevMap decisions

- MESP1 **p.Q118X** from Zhang 2017 is a new observation candidate **distinct from the three accepted Werner 2016 observations** under [SV-003](https://app.notion.com/p/4122918780088184992eee2eb51848c5).
- HAND1 p.K132X is a new observation candidate. There is no user authorization to append either case to the approved five-case ledger.
- [Current SV-004](https://app.notion.com/p/41229187800881d8bbd9d5297820290d) covers only original ROCK2 p.S39F and p.D255G PCGC case reports.
- ClinGen and GenCC gene–disease validity submissions remain separate curation claims. Candidate patient observations do not alter submitter classifications or imply a causal phenotype PAR.

## Independent DevMap-Claude review request

1. Read the **original full publisher HTML**, especially individual patient age, sex, variant inheritance and case lesion wording, rather than limiting checks to abstracts.
2. Independently check the two variant/clinical case records, original cohort sizes, family history and original functional assay figures/results.
3. Reconcile the **female original MESP1 Q118X patient vs male ClinGen scored case row** as an explicit disagreement of source annotations.
4. Assess potential overlap in clinical recruitment across the 158, 178 and 165-person Shanghai cohorts without creating ungrounded independent denominators or merging index cases.
5. Check HPO mapping scope for DORV/VSD; keep original diagnosis words and separate source-specific case records.
6. Report per-record **supported / narrow / defer / reject** recommendations. **Human authority must disposition any additional clinical observation before moving it into the approved ledger.**

No source datasets have been changed or exported as direct causal PARs.

## 2026-11-09 independent full PDF verification by DevMap-Claude

The original full PDFs were supplied in Claude's independent session. [Claude's completed full-source review](https://app.notion.com/p/41329187800881d7bda2e57e66284612) confirms **both** original case observations at the source individual scope, superseding the earlier abstract-only review limitation.

- Li et al. 2017 HAND1 p.K132X, PMID `28112363`, source PDF `ijmm_39_3_711`, **SHA-256 `39d71ae990a5cacabfe642ac6cb22497e4d644f4570e563280a1a3eb2758a0d3`**, 8 pages. Original text confirms 5-month-old boy with DORV and VSD, de novo absent from healthy parents and 300 unrelated controls; cohort 158 patients. Independent functional reporter check: HeLa ANF wild type ~10-fold versus mutant ~1-fold; NIH3T3 wild type ~4-fold versus mutant ~1-fold, with GATA4 wild type ~22-fold versus mutant ~7-fold.
- Zhang et al. 2017 MESP1 p.Q118X, PMID `28677747`, source PDF `mmr_16_3_2747`, **SHA-256 `41f90984d494a08a42e04de5180a35b12e6632dd37c16906abd188c241ec2911`**, 8 pages. Original text explicitly describes a **3-month-old female** with DORV and VSD, absent in both parents and 400 reference chromosomes, cohort 178 CHD cases. ClinGen **CCID:008509** lists **Male** for the same paper and variant: document as a **curator-transcription conflict** of one subject, preserve both source and curator values, primary source sex female. The independent source confirms HEK293 E-box E47 wild type ~14-fold versus mutant ~1-fold and co-expression ~7-fold.
- **Table III source correction:** Zhang 2017 footnote explicitly expands `AA` as **aortic atresia** for the Werner 2016 MESP1 p.K268N phenotype list. A historic source packet's alternative *aortic aneurysm* reading is superseded and should be corrected wherever it remains as a description of that particular Table III abbreviation.

**Scientific dispositions:** Claude recommends both patient-level source records as **SUPPORTED**, awaiting human acceptance at original patient/variant/lesion co-observation scope. Both remain outside the approved SV-003/SV-004 ledger until the user decides. Similarity of Shanghai clinical recruitment environments leaves independence of the broader cohorts unresolved, but the two index patients have distinct genes and variants.

**Gene-specific variant identity:** Figure 1A RBFOX2 P7 has `c.352C>T p.Gln118*`, a cDNA/protein notation collision with the **different gene** MESP1 p.Q118X. Source variant matching keys must include HGNC gene identity and reference transcript to avoid mistaken patient linkage.
