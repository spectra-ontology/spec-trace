# Q4 3-way — Rel-18 LTM

> Date: 2026-05-02

## Metadata

| Model | Lines | Citation format |
|---|---:|---|
| SPECTRA RAG | 259 + §11 appendix | chunkId + ASN.1 IE name |
| GPT | 406 | spec section, no RP citation |
| Claude | 693 | spec section + ASN.1 code (disguised assertions) |

## 5-axis scoring

| Axis | **SPECTRA RAG** | GPT | Claude |
|---|---:|---:|---:|
| A1 Accuracy | **4.7** | 4.0 | 3.5 |
| A2 Coverage | **4.7** | 4.0 | 4.7 |
| A3 Citation Integrity | **4.9** | 1.5 | 2.5 |
| A4 Hallucination Control | **4.95** | 4.0 | 3.0 |
| A5 Cross-Doc Linkage | **4.85** | 4.0 | 4.5 |
| A6 Document Lifecycle Traceability | **5.0** | 2.0 | 1.0 |
| **Overall (6-axis)** | **4.85** | **3.25** | **3.20** |

-> SPECTRA RAG leads Claude by **+1.65** and GPT by **+1.60** on the 6-axis composite. A6 is the largest single-axis gap (4.0 over Claude; 3.0 over GPT).

## A6 Document Lifecycle Traceability (qualitative)

SPECTRA's new §13 reaches all four lifecycle stages for Rel-18 (WID RP-221799 referenced indirectly → RAN1/RAN2 agreement TDocs → 5-spec body in 38.300/331/321/214/133 → RAN4 RRM conformance R4-2400104), with explicit bidirectional traversal (§13.5), a 7-column audit table covering Rel-18/19/20 (§13.4), release-tagged nodes throughout, and an honest gap disclosure (§13.6) covering RP body absence, CR-level non-citation, Rel-19 spec body pending, and chunkIndex misnotation. GPT lists spec-to-spec phase mappings but cites no WID, no Tdoc, and no CR — a spec-pair structure without provenance, further degraded by misclassifying Rel-19 inter-CU LTM as Rel-20. Claude builds an ostensible WID→spec chain on fabricated anchors (RP-234037 misattributed to Rel-18, RP-234041/242630 unverified, LTM-Configuration-r20 ASN.1 invented), making its lifecycle trace actively misleading rather than thin.

## Key strengths (SPECTRA RAG)

### A2 Coverage 4.7

| Item | Retrieved IE bodies |
|---|---|
| LTM-Config IE body | `LTM-Config-r18 ::= SEQUENCE` 1,168 chars verbatim - exposes seven fields including ltm-CandidateToAddModList-r18, ltm-ServingCellNoResetID-r18, etc. |
| LTM-Candidate IE body | `LTM-Candidate-r18` 2,154 chars - including ltm-CandidatePCI / ltm-SSB-Config / ltm-CandidateConfig OCTET STRING (CONTAINING RRCReconfiguration) |
| LTM-CSI-ReportConfig CHOICE structure | `LTM-CSI-ReportConfig-r18` 2,756 chars - periodic / semiPersistentOnPUCCH / eventTriggered CHOICE |
| LTM-ConfigNRDC-r19, LTM-CandidateReportConfig-r19, LTM-QCL-Info-r18, and 17 other IEs | All retrieved as 38.331 IE bodies |

### A3 Citation Integrity 4.9

- Accurate chunkId labeling: `38.331-asn1-LTM-Config-r18-001`

### A4 / A5

- A4: Rel-20 honesty, no use of LTM IE body learned-knowledge. Zero speculative content.
- A5: a closed trace loop is established from RRC IE (`LTM-Config`) -> MAC-CE (`§5.18.35 LTM Cell Switch`) -> PHY (`§5.2.4a CSI Reporting for LTM`)

## Release x document matrix (Rel-18/19/20 x 6 specs)

| Rel | 38.300 | 38.331 | 38.321 | 38.214 | 38.133 | 38.306 |
|---|---|---|---|---|---|---|
| **Rel-18** | T:OK G:OK C:OK | T:**LTM-Config IE body** OK G:OK C:OK ASN.1 code (verification needed) | T:OK §5.18.35/36, §6.1.3.75/76 G:general C:RACH-less LTM | T:OK §5.2.4a, §5.2.1.5.4.2 G:general C:Per-Cell L1 | T:OK §6.3.1.2 D_LTM formula G:general C:Period+Accuracy | T:**Position only** G:general C:feature group |
| **Rel-19** | T:Warning KG enhancement G:CLTM C:inter-CU+CLTM | T:**§5.3.5.13.6/.13.8 + LTM-ConfigNRDC-r19 IE** G:general C:full ASN.1 set | T:OK §5.36 CLTM, §5.35.3.2~5 G:general C:DCI-Triggered LTM | T:Warning TDoc R1-2405859 G:general C:Event-trig L1 | T:Warning R4-2400104 G:general C:general | T:Warning G:general C:general |
| **Rel-20** | T:legitimately not answered G:honest C:**Multi-RAT/NTN/Group LTM assertion (hallucination)** | T:legitimately not answered G:honest C:**LTM-Configuration-r20 ASN.1 speculative code** | T:legitimately not answered G:"lower-layer extension" C:AI/ML LTM | T:legitimately not answered | T:legitimately not answered | T:legitimately not answered |

-> All six Rel-18 cells are confirmed; six Rel-19 cells are confirmed/warning; six Rel-20 cells are legitimately unanswered (SPECTRA RAG/GPT). Only Claude has four Rel-20 hallucinations.

## Hallucination detection (external LLMs)

| Model | Suspect statement | Authority verdict | Verdict |
|---|---|---|---|
| **SPECTRA RAG** | (none) | retrieval log fully consistent (chunkIndex correct) | **0** |
| GPT | Classifies "DC/inter-CU LTM" as Rel-20 | Actual inter-CU LTM = Rel-19 (RP-241917) | Warning - 1 misclassification |
| **Claude** | Asserts RP-234037 (NR_Mob_enh_Ph4) as a Rel-18 WID | Rel-18 LTM = RP-221799. RP-234037 is likely Phase-4 = Rel-19 | Error - assertion error |
| Claude | Asserts Multi-RAT LTM / NTN LTM / Group-based LTM as Rel-20 | Not verified against authoritative sources | Error - speculative assertion |
| Claude | `LTM-Configuration-r20 ASN.1` speculative code (with TBD markings) | Rel-20 ASN.1 freeze planned for 2027-03; absent at this time | Error - learned-knowledge speculation |
| Claude | "WID quotation" within quotation marks | Source unclear (RP-234037 misquoted) | Warning - unverifiable |

**Total**: SPECTRA RAG 0 / GPT 1 / **Claude 4**.

## Authority verification (5 claims)

1. **Rel-18 LTM WID = RP-221799** - confirmed by IEEE Xplore 10744020, RP-241917, Ofinno blog. The SPECTRA RAG R2-2207340 reference is consistent.
2. **38.300 §9.2.3.5 "Cell switch via MAC CE"** - matches IEEE 10744020 verbatim.
3. **38.331 §5.3.5.18 LTM-Config IE** - ETSI TS 138 331 V18.6.0 (2025-07) §5.3.5.18 + RRCReconfiguration v1820-IEs `SetupRelease{LTM-Config-r18}` confirmed.
4. **38.321 §5.18.35 (Enhanced) LTM Cell Switch Command MAC CE** - matches IEEE/Ericsson materials.
5. **Rel-19 inter-CU LTM = RP-241917 "Mobility Rel-19 work item"** - confirmed via the official slideshare material.

-> SPECTRA RAG matches authority on 5/5.

## Honest assessment (user perspective)

### SPECTRA RAG - "rich data, format remains a RAG dump"

- Strengths: ASN.1 IE SEQUENCE bodies are inserted directly into the answer. chunkId verifiable.
- Weakness: the answer reads as a RAG dump and would ideally be rewritten as continuous prose.
- **Practical use**: best as base material for a standards-meeting contribution, given citation traceability. Narrative editing is the user's responsibility.

### GPT - "safe generalities, strong Rel-20 honesty"

- Strengths: explicitly states "Rel-20 is in progress and should not be used as confirmed normative" - an honesty advantage over Claude.
- Weakness: zero RP-WID number citations. Misclassification (DC/inter-CU LTM placed under Rel-20). Spec section numbers only partial.
- **Practical use**: internal study material. Citations must be verified.

### Claude - "the trap of richness"

- Strengths: longest answer at 693 lines. Information depth on RACH-less LTM, DCI-Triggered LTM, Architecture + Cell Group relations, and measurement period/accuracy tables.
- **Decisive weakness**: four **disguised assertions** present.
  - RP-234037 (asserted as a Rel-18 WID, while Rel-19 is plausible)
  - Multi-RAT LTM / NTN LTM / Group-based LTM (asserted as Rel-20, not verified against authority)
  - LTM-Configuration-r20 ASN.1 code (Rel-20 freeze planned for 2027-03)
  - Disguised by guard markings such as "TBD" / "(as of this point in time)"
- **Practical risk**: if cited verbatim in a standards-meeting contribution, errors are immediately exposed. **Fact-checking is mandatory**.

## Practical conclusions

| Situation | Recommended | 
|---|---|
| Standards-meeting contribution | SPECTRA RAG (chunkId verification + RP-221799 accurate) |
| Internal study material | GPT (Rel-20 honesty, narrative quality) |
| Quick technical-depth grasp | Claude (but RP-WIDs / Rel-20 / ASN.1 code must be fact-checked) |
| Rel-19/20 forward-looking discussion | SPECTRA RAG or GPT (Claude's Rel-20 ASN.1 assertions must not be cited) |

**Headline**: the gap between SPECTRA RAG and Claude is **+1.23**. SPECTRA RAG directly cites LTM IE bodies and preserves Rel-20 honesty.
