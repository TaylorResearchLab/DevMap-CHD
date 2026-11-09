# SV-005 | Scientific acceptance of HAND1 and MESP1 individual clinical observations

**Decision date:** 2026-11-09. **Scientific authority:** Deanne M. Taylor.  
**Disposition:** **ACCEPT** the two independently verified original **patient–variant–clinical diagnosis co-observations** at individual scope. Both are distinct from the previously accepted MESP1 Werner (SV-003) and ROCK2 PCGC (SV-004) cases.

**User authorization:** The user answered **“Yes. How do I inform ClinGen of the correction?”** to the explicit proposal to accept both HAND1 p.K132X and MESP1 p.Q118X individual observations, preserve the original diagnoses, and authorize notification of ClinGen about the MESP1 Q118X proband sex discrepancy.

## Accepted original clinical observations

| Decision | Gene and source variant | Original patient and structural diagnoses | Original source |
| --- | --- | --- | --- |
| **SV-005a** | **HAND1** `c.394A>T, p.K132X` | **5-month-old male** with **double outlet right ventricle (DORV) and ventricular septal defect (VSD)** | Li et al. 2017, *International Journal of Molecular Medicine*, PMID **28112363**, DOI **10.3892/ijmm.2017.2865**, Results “Discovery of a de novo HAND1 mutation” |
| **SV-005b** | **MESP1** `c.352C>T, p.Q118X` | **3-month-old female** with **DORV and VSD** | Zhang et al. 2017, *Molecular Medicine Reports*, PMID **28677747**, DOI **10.3892/mmr.2017.6875**, Results “Identification of a novel MESP1 mutation in CHD” |

Both publications describe **de novo** variant status through direct examination of the unaffected parents and report no CHD family history. HAND1 was identified in one of 158 unrelated Chinese Han CHD patients, with 300 unrelated controls (600 chromosomes). MESP1 was identified in one of 178 unrelated Chinese Han CHD patients and was absent in 400 control chromosomes. Preserve these publication-specific denominators. Shared senior authors and clinical recruitment settings leave overall cohort overlap unresolved.

### Ontology candidates, separate from the reported clinical wording

- DORV → `HP:0001719`.
- VSD → `HP:0001629`.

The underlying published diagnosis is **DORV and VSD observed together in the same subject** for both cases. The HPO mappings constitute representations of those original source terms, not independent patients or original HPO annotations.

### Separate experimental evidence

Li et al. report mutant HAND1 impairment in ANF reporter assays, including approximate HeLa wild-type 10-fold versus mutant 1-fold and NIH3T3 GATA4 coexpression wild-type 22-fold versus mutant 7-fold. Zhang et al. report wild-type MESP1 E-box/E47 reporter approximately 14-fold versus mutant 1-fold, with coexpression approximately 7-fold. These remain **experimental observations from the cited papers**, distinct from clinical subject records.

## Independent SCUTER source verification

[DevMap-Claude full source review, November 9](https://app.notion.com/p/41329187800881d7bda2e57e66284612) examined complete user-attached primary PDF text, including patient descriptions and parental testing. Independently verified both reports and recommended **SUPPORTED at single-patient scope**.

- Li PDF `ijmm_39_3_711`, SHA-256 `39d71ae990a5cacabfe642ac6cb22497e4d644f4570e563280a1a3eb2758a0d3`.
- Zhang PDF `mmr_16_3_2747`, SHA-256 `41f90984d494a08a42e04de5180a35b12e6632dd37c16906abd188c241ec2911`.

See the earlier [Agent A source packet](HAND1_MESP1_2017_primary_patient_evidence_REVIEW_v01.md). Each original report has **one** reported carrier of the specific variant and the corresponding DORV/VSD diagnosis. No original subject ID was supplied in the reviewed case narratives; an eventual internal indexing key is not a published subject identifier.

## Approved ClinGen correction notification

**Explicit user authorization:** report the sex discrepancy in [ClinGen MESP1–CHD gene validity curation CCID:008509](https://search.clinicalgenome.org/CCID:008509).

- The ClinGen `Chinese Han Proband Zhang` entry for `NM_018670.4(MESP1):c.352C>T (p.Gln118Ter)`, PMID **28677747**, lists **Proband Sex: Male**.
- **Original Zhang et al. 2017 Results** identify a **3-month-old female** and refer to **her** parents. This is **one** patient with a conflicting *curator transcription*, not a second proband.
- Request correction of the curation record's sex from Male to **Female**, retaining the same gene, variant, DORV/VSD diagnosis and original paper.
- The request can be filed through ClinGen's [Evidence Feedback for CCID:008509](https://search.clinicalgenome.org/CCID:008509), or the [ClinGen website feedback form](https://clinicalgenome.org/contact/share-feedback/) under Gene-Disease Validity Curation Activity. Do not attach protected patient health information. A published paper citation and exact curation ID suffice.

**Authorization to notify is recorded; no external ClinGen feedback submission or email is claimed to have occurred.** The proposed correction does not change the ClinGen Moderate disease-validity classification or alter the primary publication.

## Data representation and governance

Both newly accepted observations can be appended to the **approved clinical observations ledger** only as **original human clinical co-observations**, with variants keyed by **gene plus source transcript/variant and primary publication**. RBFOX2 P7 has the same cDNA notation `c.352C>T` as MESP1 p.Q118X, so neither the variant string nor protein shorthand alone identifies the gene.

Existing SV-003 three MESP1 Werner observations and SV-004 two ROCK2 PCGC observations remain accepted and unchanged. Accepted original human observations now total **7** across these decisions. Additional experimental work, pathogenicity classification, penetrance, direct causal gene disruption–phenotype PAR issuance and broader disease validity are separate evidence dimensions.

The original DevMap-CHD 662-gene registry, approved HPOA disease-scope records, GenCC source classifications and frozen releases remain unchanged.
