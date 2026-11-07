# SV-002 | OMIM:314400 short valve chordae | Agent 1 primary-source assessment

**Date:** 2026-11-07
**Status:** Source lead reviewed by Agent 1. Secondary Agent 2 review pending. No direct gene-disruption PAR accepted.
**Source claim scope:** HPOA disease–phenotype annotations from OMIM:314400, original evidence code PCS. This packet establishes citation mapping evidence at disease phenotype level, not new unreviewed variant-to-phenotype assertions.

## Original HPOA records

- OMIM:314400 to HP:0011580, Short chordae tendineae of the mitral valve. Source HPOA v2026-09-01, original clinical study annotation; explicit PMID absent from source reference field.
- OMIM:314400 to HP:0006692, Short chordae tendineae of the tricuspid valve. Same HPOA provenance status.

## Original primary clinical cohort

Le Tourneau T et al. **New insights into mitral valve dystrophy: a Filamin-A genotype-phenotype and outcome study**. *European Heart Journal* 2018;39:1269–1277. PMID **29020406**, PMCID **PMC5905589**, DOI **10.1093/eurheartj/ehx505**.

Source full text: https://pmc.ncbi.nlm.nih.gov/articles/PMC5905589/

**Exact original location:** Results subsection **Sub-valvular mitral valve apparatus** (PMC text around lines 453–455). Authors describe mitral valve chordae shortening (specifically in women), papillary muscle alterations and occasional absent or elongated primary chordae in individual cases. The Discussion subsection **Subvalvular apparatus alteration** (around lines 493–496) describes chordal shortening and congenital subvalvular lesions. Section **Relation of mitral valve parameters to age** reports childhood diagnosis as early as two months and prenatal detection in two patients (around line 458). The abstract describes a four-family cohort, 246 subjects, 72 FLNA variant carriers. Distinct FLNA variants are p.Pro637Gln, p.His743Pro and p.Gly288Arg (please independently check allele mapping).

### Claim SV-002a: OMIM:314400 -> HP:0011580

**Agent 1 finding:** A clinically reported shortened mitral chordae phenotype is present in an FLNA-associated valvular dysplasia cohort. The exact HPO term is anatomically concordant. Link PMID:29020406 as a **proposed direct primary clinical publication** at original disease–phenotype assertion scope, pending Agent 2 verification that the cohort corresponds to the original HPOA annotation and the full text/table locator is accurate.

**Limit:** This article documents a cohort, not an individual PVID/HPO/PMID link. There is no evidence here of a distinct individual event for each referenced genotype. The source also describes progressive adult valve remodeling superimposed on congenital maldevelopment. Do not infer that every carrier has shortened chordae.

### Claim SV-002b: OMIM:314400 -> HP:0006692

**Agent 1 finding:** Same study reports tricuspid valve involvement and multivalve prolapse, but the reviewed text does not report shortened **tricuspid chordae specifically**. Keep source citation unresolved for this exact HPO term until a primary publication provides the tricuspid-specific morphological description. Do not transfer mitral-specific evidence across valves.

### Additional primary and secondary leads

- Kyndt F et al., *Circulation* 2007;115:40–49, PMID **17190868**, DOI **10.1161/CIRCULATIONAHA.106.622621**. Foundational original genetic family study FLNA p.Pro637Gln. The original paper/abstract establishes genetic valvular dystrophy but the exact short chordae phenotype was not verified from the accessible source material during this review.
- Haataja TJK et al., *Biophysical Journal* 2019;117:1467–1475, PMCID **PMC6817519**, DOI **10.1016/j.bpj.2019.08.032**. Introduction states mitral chordae are shorter in FLNA valvular dystrophy; cites previous patient studies, so this text is a secondary clinical description rather than a fresh independent patient.
- NCBI MedGen https://www.ncbi.nlm.nih.gov/medgen/78083 and HPO disease mapping show both HP:0006692 and HP:0011580 under OMIM:314400, which confirms the original phenotype annotation but not a source-specific PMID.

## SCUTER Agent 2 challenge requested

1. Independently read full Le Tourneau 2018 PMC5905589 Results, Table 2 and source supplementary material. Verify shortening direction, sex differences and cohort provenance against original HPOA disease phenotype.
2. Check whether HP:0011580 should be recorded as verified from original source at cohort level and whether its citation genuinely corresponds to HPOA's PCS evidence.
3. Examine the 2007 Kyndt source and 2018 Le Tourneau for any explicit shortened **tricuspid chordae** clinical description, including tables/supplement. Avoid inferring from tricuspid regurgitation or prolapse.
4. Evaluate independent source evidence versus derivative restatements, developmental timing and affected valve specificity.
5. Return `supported`, `supported_with_narrowing`, `unresolved`, or `contradicted` for each separate term with exact textual/table locator.

**Human approval:** User scientific decision reserved for any new or broadened DevMap claim. The expert-curated original HPOA source assertions remain imported at original scope under 2026-11-07 source policy. This packet does not modify registry or evidence data.


## Agent 1 evidence addendum, 2026-11-07: original postmortem report resolves both short-chordae observations

**Newbury-Ecob RA, Zuccollo JM, Rutter N, Young ID.** *Sex linked valvular dysplasia.* Journal of Medical Genetics. 1993;30:873–874. **PMID:8230166**, **PMCID:PMC1016573**, **DOI:10.1136/jmg.30.10.873**.

**Primary text locator:** https://jmg.bmj.com/content/jmedgenet/30/10/873.full.pdf, **page 873, Case reports, Patient 1 (IV:1), postmortem findings**. The infant had prenatal detection of cardiac malformation, neonatal multivalvular dysplasia and died at 24 hours. The original autopsy report describes abnormal **tricuspid and mitral cusps** and then states: **"The chordae were short and irregular."** This is an anatomical, case-specific observation for both valves. In this paragraph the antecedent is the tricuspid and mitral valves; the valve-specific attribution is textually justified. Preserve this exact source passage locator for Agent 2 to check the interpretation.

**Original claim scope:** Both OMIM:314400 -> HP:0006692 (short tricuspid chordae) and OMIM:314400 -> HP:0011580 (short mitral chordae) have an original patient-level clinical anatomy report. Because the paper predates FLNA gene discovery, the original individual IV:1 was **not genetically linked to a verified FLNA sequence variant** in the 1993 report. This paper supports the expert-curated **disease–phenotype** assertions, with subsequent genetic publications supporting the disease–FLNA association separately.

**Further direct source:** Le Tourneau et al. 2018, PMID:29020406, results subsection `Sub-valvular mitral valve apparatus` describes shortened mitral chordae in FLNA variant carriers, with associated developmental valve abnormalities. Its `Aortic, tricuspid, and pulmonary valves` subsection describes tricuspid prolapse and regurgitation but does **not** independently specify shortened tricuspid chordae. Do not attribute the latter to this 2018 cohort.

**Updated Agent 1 proposed source dispositions:**
- SV-002a OMIM:314400 / HP:0011580 mitral chordae: `phenotype_specific_primary_source_identified`, citing 1993 PMID:8230166 and 2018 PMID:29020406 separately with cohort/patient distinctions.
- SV-002b OMIM:314400 / HP:0006692 tricuspid chordae: `phenotype_specific_primary_source_identified`, citing the original 1993 Patient 1 postmortem observation (PMID:8230166), pending Agent 2 independent full-text validation.
- Neither disposition implies that the 1993 patient harbored a sequence-confirmed FLNA variant or that an inferred direct variant-phenotype PAR has been accepted.

**Agent 2 focused review:** Independently verify page 873 source text and anatomical referent of the short and irregular chordae; check neonatal patient IV:1 and distinguish both disease–phenotype claims from FLNA genetic attribution. Separately verify the 2018 mitral evidence and original cohort. The PDF web screenshot endpoint returned 403 during Agent 1's inspection attempt, but primary PDF extracted text and BMJ search excerpt present the same observation. No source PDF is redistributed in GitHub. No user biological decision yet.


## Agent 2 source review addendum, 2026-11-07 (partially reviewed)

[Claude's source review](https://app.notion.com/41129187800881fca046e55f2ff85766) independently inspected Le Tourneau 2018 after exposure to Agent 1's source locators. The **2018 cohort evidence supports shortened mitral chordae in FLNA variant-positive women**, rather than an unqualified effect across all variant carriers. In Table 2, normalized chordal length (mm/m²), FLNA-positive versus FLNA-negative women is 10.2 ± 2.2 versus 12.1 ± 2.0 anteriorly (P=0.02) and 10.6 ± 1.9 versus 12.2 ± 2.2 posteriorly (P=0.009). The corresponding male comparisons are not statistically significant (P=0.55 anteriorly and P=0.10 posteriorly). The study provides no tricuspid chordal-length result. Maintain original cohort, valve, sex, modality and PMID provenance as separate clinical evidence from the 1993 neonatal anatomical report.

Claude **has not inspected Newbury-Ecob 1993** because the scanned PDF and page images were inaccessible in the reviewer environment. Agent 1's previous text extraction remains a source lead pending independent visual inspection of p.873 Patient 1 IV:1. The 1993 infant has no sequence-confirmed FLNA attribution in that paper. The original HPOA OMIM:314400–HP:0011580 and OMIM:314400–HP:0006692 PCS assertions remain disease-subject claims without explicit original HPOA PMID fields.

Status: 2018 mitral evidence **supported with narrowing**; 1993 neonatal mitral/tricuspid evidence **awaits Agent 2 primary image review**; human biological disposition pending. No direct FLNA variant–phenotype PAR accepted.
