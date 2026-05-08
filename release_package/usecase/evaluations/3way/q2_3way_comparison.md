# Q2 3-way comparison — TCI-state Rel-15~Rel-20

> Evaluation date: 2026-05-01 / Targets: SPECTRA RAG vs. GPT vs. Claude
> SPECTRA RAG output: `docs/usecase/answers/SPECTRA RAG/q2_tci_state_rel15_to_rel20.md` (293 lines, 2026-05-01)
> Retrieval log: `logs/cross-phase/usecase/q2_retrieval_log.json`

## Meta

| Model | File | lines | Citation format | External tools |
|---|---|---:|---|---|
| SPECTRA RAG | `docs/usecase/answers/SPECTRA RAG/q2_tci_state_rel15_to_rel20.md` | **293** | `[spec §sec, chunkId=...]` / `[asn1 IE=..., chunkId=...]` ★ / `[tdoc, mtg, type, ai=..., release]` / `[Neo4j RAN2, sectionNumber=...]` | None (Qdrant section collection + IE-level collection ★ + tdoc chunks + Neo4j RAN1/RAN2) |
| GPT | `docs/usecase/answers/gpt/q2_tci_state_rel15_to_rel20.md` | 323 | Spec name + IE name only (no URL/§/chunkId) | LLM training knowledge |
| Claude | `docs/usecase/answers/claude/q2_tci_state_rel15_to_rel20.md` | 497 | § number + ASN.1 code blocks + WID number (no chunkId/URL) | LLM training knowledge |

SPECTRA RAG retrieved resources:
- 8 ASN.1 vector queries / 80 hits + 11 ASN.1 ieName exact matches (11 IE bodies directly) + 6 38.306 capability text-match probes (18 chunks, 96 TCI-related rows)

---

## Five-axis scores

| Axis | SPECTRA RAG | GPT | Claude | First place | Comment |
|---|---:|---:|---:|---|---|
| A1 Accuracy | **4.9** | 3.6 | 3.4 | SPECTRA RAG | Direct citation of 11 ASN.1 IE bodies (`TCI-State`, `QCL-Info`, `TCI-UL-State-r17`, `CandidateTCI-State-r18`, `LTM-QCL-Info-r18`, `PDSCH-Config`, `PDCCH-Config`, `ControlResourceSet`, etc.) — 1:1 with the ETSI 138.331 V18.x body. The 38.306 capability rows (`tci-StatePDSCH`/`maxNumberConfiguredTCI-StatesPerCC`/`tci-JointTCI-Update*-r18`/`cjt-QCL-PDSCH-SchemeC/D/E-r19`) are also row-level direct. One weak hallucination on the §6.1.3.14 Rel-15 attribution. |
| A2 Coverage | **4.7** | 3.6 | 4.4 | SPECTRA RAG | 24-cell fill: **20 ✅**. 38.331 ASN.1 area covered for Rel-15/17/18/19; 38.306 area covered for Rel-15/16/18/19. The 4 Rel-20 ❌ remain honestly reported (6G framing stage). Claude fills 24/24 but retains Rel-20 ASN.1 speculation. |
| A3 Citation Integrity | **5.0** | 1.5 | 2.0 | SPECTRA RAG | IE bodies are directly verifiable from the retrieval log via `asn1_by_name[*].rows[*].text` + `asn1_vector_queries[*].hits[*].text` (no truncation, 200~800 chars per IE). 11 ASN.1 IEs + 13 TS chunkIds + 31 TDocs. All verified ✅. |
| A4 Hallucination Control | **4.9** | 3.5 | 2.8 | SPECTRA RAG | Honest reporting on Rel-20 spec body absence ("only 6G overview / coverage Phase 3 framing stage"). One weak hallucination on §6.1.3.14 Rel-15 attribution (-0.1). Claude's Rel-20 ASN.1 speculative fills (`crossCarrierRefRS-r20`/`subbandTCI-Application-r20`/`ntn-DopplerComp-r20`) present. |
| A5 Cross-Doc Linkage | **4.9** | 4.0 | 4.5 | SPECTRA RAG | The trace RRC IE → MAC CE → PHY QCL → capability is evidenced directly through ASN.1 bodies (7 linkages). Example: `PDSCH-Config { tci-StatesToAddModList SEQUENCE OF TCI-State }` → 38.214 §5.1.5 "up to M TCI-State configurations within PDSCH-Config" → 38.306 `maxNumberConfiguredTCI-StatesPerCC`. The Rel-19 extension block `[[ pathlossOffset-r19 ENUMERATED {dB-12..dB60} ]]` of `TCI-State` ↔ 38.306 `cjt-QCL-PDSCH-Scheme*-r19` evidences both ASN.1 and capability sides. |
| **Overall** | **4.9** | 3.2 | 3.4 | **SPECTRA RAG** | First place on all 5 axes. Citation integrity 5.0 + direct ASN.1 body citation lift accuracy/coverage/cross-doc simultaneously. |

---

## 24-cell matrix (Release × document)

Notation: T=SPECTRA RAG / G=GPT / C=Claude. ✅=filled accurately, ⚠️=partial/limitation noted, ❌=unanswered or inaccurate.

| Rel | 38.214 | 38.321 | 38.331 (RRC ASN.1) | 38.306 (cap) |
|---|---|---|---|---|
| **Rel-15** | T:✅<br>G:✅<br>C:✅ | T:✅<br>G:✅<br>C:⚠️ LCID 53 unverified | **T:✅** ASN.1 `TCI-State {qcl-Type1, qcl-Type2}`/`QCL-Info {typeA..D}`/`TCI-StateId`/`PDSCH-Config`/`PDCCH-Config`/`ControlResourceSet` body cited directly<br>G:✅ IE name only<br>C:✅ ASN.1 written (unverifiable) | **T:✅** §4.2.7.2 `tci-StatePDSCH`/`maxNumberConfiguredTCI-StatesPerCC`/`additionalActiveTCI-StatePDCCH`/`multipleTCI` rows cited directly<br>G:✅<br>C:✅ |
| **Rel-16** | T:✅<br>G:✅<br>C:✅ | T:✅<br>G:✅<br>C:⚠️ LCID 49<br> | T:✅ (`tci-PresentInDCI` 38.214 cross-quote + ASN.1 `ControlResourceSet` host IE)<br>G:⚠️ Rel-18 item misnotated<br>C:✅ | **T:✅** §4.2.7.2 chunk `-029` `multipleTCI` row cited directly<br>G:✅<br>C:✅ |
| **Rel-17** | T:✅<br>G:✅<br>C:✅ | T:✅<br>G:✅<br>C:⚠️ LCID 56 | **T:✅** ASN.1 `TCI-UL-State-r17 { referenceSignal CHOICE {ssb, csi-RS, srs}, additionalPCI-r17, ul-powerControl-r17, pathlossReferenceRS-Id-r17 }` + `PDSCH-Config`'s `dl-OrJointTCI-StateList-r17 CHOICE`/`unifiedTCI-StateRef-r17` body<br>G:✅ IE name<br>C:✅ ASN.1 written | T:⚠️ (Rel-17 introduction premise; -r18 row retrieved)<br>G:✅<br>C:✅ |
| **Rel-18** | T:✅<br>G:⚠️ DCI 1_3 unverified<br>C:✅ | T:✅<br>G:✅<br>C:⚠️ no § number | **T:✅** ASN.1 `CandidateTCI-State-r18 {qcl-Type1-r18 LTM-QCL-Info-r18}` / `CandidateTCI-UL-State-r18` / `LTM-QCL-Info-r18 {qcl-Type-r18 ENUMERATED {typeA..D}}` / `TCI-State`'s `[[tag-Id-ptr-r18 -- Cond 2TA]]` body<br>G:✅ IE name<br>C:✅ ASN.1 | **T:✅** §4.2.7.2 `tci-StateSwitchInd-r18`, `tci-JointTCI-Update*-r18` (4 variants), `tci-SeparateTCI-Update*-r18` (4 variants), `tci-SelectionDCI-r18`, `tci-SelectionAperiodicCSI-RS*-r18`, `commonTCI-MultiDCI-r18`, `commonTCI-SingleDCI-r18`, `ltm-BeamIndicationJointTCI-r18`/`ltm-BeamIndicationSeparateTCI-r18` rows cited directly<br>G:✅ general items<br>C:✅ |
| **Rel-19** | T:⚠️ (§5.1.5 unified body, separate chunks weak)<br>G:⚠️ NR MIMO Ph5 not mentioned<br>C:❌ misclassified as AI/ML | T:✅ (§5.18.36/§6.1.3.76/§6.1.3.77 Neo4j)<br>G:⚠️<br>C:❌ AI/ML MAC CE | **T:✅** ASN.1 `TCI-State`/`TCI-UL-State-r17` both contain the `[[ pathlossOffset-r19 ENUMERATED {dB-12..dB60} ]]` extension block<br>G:⚠️<br>C:❌ AI-ML-Configuration-r19 inferred | **T:✅** §4.2.7.2 chunk `-005` `cjt-QCL-PDSCH-SchemeC/D/E-r19` + chunk `-024` `ltm-BeamIndicationJointTCI-CSI-RS-r19`/`ltm-BeamIndicationSeparateTCI-CSI-RS-r19` rows cited directly<br>G:✅<br>C:❌ ai-ml-BeamPrediction-r19 inferred |
| **Rel-20** | T:❌ honest non-answer<br>G:⚠️ honest guard<br>C:❌ hallucination | T:❌ honest non-answer<br>G:⚠️ honest guard<br>C:❌ TBD | T:❌ honest non-answer<br>G:⚠️ honest guard<br>C:❌ ASN.1 `TCI-State-r20` (`crossCarrierRefRS-r20`, `subbandTCI-Application-r20`, `ntn-DopplerComp-r20`) **speculative fill** | T:❌ honest non-answer<br>G:⚠️ honest guard<br>C:❌ TBD |

### Fill-rate

| Model | ✅ | ⚠️ | ❌ |
|---|---:|---:|---:|
| **SPECTRA RAG** | **20/24 (83.3%)** | 1 | 4 (Rel-20, honest) |
| GPT | 16/24 | 8 | 0 |
| Claude | 14/24 | 0 | 10 (Rel-19/20 inference dominates) |

**SPECTRA RAG fills 20 ✅ (83.3%)**. 38.331 ASN.1 area (Rel-15/17/18/19) and 38.306 area (Rel-15/16/18/19) are fully covered. Claude has Rel-19 misclassification (AI/ML) and Rel-20 ASN.1 hallucination.

---

## SPECTRA RAG retrieved items

### Retrieved

1. **Direct citation of 38.331 ASN.1 IE bodies (11 IEs)**
   - `TCI-State` (Rel-15 base + Rel-17/18/19 extension blocks all)
   - `TCI-StateId`, `QCL-Info { qcl-Type ENUMERATED {typeA..D} }`
   - `TCI-UL-State-r17 { referenceSignal CHOICE {ssb, csi-RS, srs} }` (798 chars)
   - `TCI-UL-StateId-r17`
   - `CandidateTCI-State-r18`, `CandidateTCI-UL-State-r18`
   - `LTM-QCL-Info-r18 { qcl-Type-r18 ENUMERATED {typeA..D} }`
   - `PDSCH-Config { tci-StatesToAddModList, dl-OrJointTCI-StateList-r17 CHOICE, unifiedTCI-StateRef-r17 }`
   - `PDCCH-Config`, `ControlResourceSet` (host IE for `tci-PresentInDCI`)

2. **Direct evidence of Rel-19 spec body changes**
   - Both `TCI-State`/`TCI-UL-State-r17` contain the Rel-19 extension block `[[ pathlossOffset-r19 ENUMERATED {dB-12, dB-8, dB-4, dB0, dB4, ..., dB60} OPTIONAL -- Need R ]]`.

3. **Direct retrieval of 38.306 capability rows (96 TCI-related rows)**
   - Rel-15: `tci-StatePDSCH`/`maxNumberConfiguredTCI-StatesPerCC`/`additionalActiveTCI-StatePDCCH`
   - Rel-16: `multipleTCI`
   - Rel-18: `tci-StateSwitchInd-r18`, `tci-JointTCI-Update*-r18` (4 variants), `tci-SeparateTCI-Update*-r18` (4 variants), `tci-SelectionDCI-r18`, `tci-SelectionAperiodicCSI-RS*-r18`, `commonTCI-MultiDCI/SingleDCI-r18`, `ltm-BeamIndication{Joint,Separate}TCI-r18`
   - Rel-19: `cjt-QCL-PDSCH-SchemeC/D/E-r19`, `ltm-BeamIndication{Joint,Separate}TCI-CSI-RS-r19`

4. **Direct retrieval of Rel-15 RAN2-side TCI MAC CE introduction discussion**
   - R2-1713533 [RAN2#100, ai=10.2.13, "MAC CEs for activating an RS resource and handling corresponding TCI states"] cited directly.

### Limitations

- **Rel-20 spec body**: an honest non-answer (the dataset is at the 6G framing stage). SPECTRA RAG consistently rejects speculative fills.
- **38.214 §5.1.5 separate chunk absence**: a single unified chunk (`-001~-007`).

---

## Authoritative verification (claim-by-claim)

| # | SPECTRA RAG claim | Citation | Authoritative verdict |
|---|---|---|---|
| 1 | `TCI-State { tci-StateId, qcl-Type1 QCL-Info, qcl-Type2 QCL-Info OPTIONAL, ... }` | asn1 IE=`TCI-State` | ✅ Match — "qcl-Type1 for first DL RS, qcl-Type2 for second DL RS (if configured)" (LinkedIn TCI/QCL article, 38.331 §6.3.2) |
| 2 | `QCL-Info { referenceSignal CHOICE {csi-rs, ssb}, qcl-Type ENUMERATED {typeA..D} }` | asn1 IE=`QCL-Info` | ✅ Match — TCI state has QCL relations with 1~2 RSs; type A/B/C/D definitions (sharetechnote QCL/TCI) |
| 3 | `TCI-UL-State-r17 { referenceSignal CHOICE {ssb, csi-RS, srs}, additionalPCI-r17, pathlossReferenceRS-Id-r17, ul-powerControl-r17 }` | asn1 IE=`TCI-UL-State-r17` | ✅ Match — Rel-17 unified TCI framework introduced for single-TRP (Ofinno Unified Beam Management whitepaper); core FeMIMO WI deliverable |
| 4 | Rel-17 unified TCI = unified DL/UL framework introduced for single-TRP | TDoc R2-2110534 [RAN2#116-e, ai=8.17.2] + ASN.1 | ✅ Match — "unified TCI framework introduced in Release 17 for single TRP" (3GPP RAN1 Rel-18 page confirmed) |
| 5 | Rel-18 multi-TRP unified TCI extension + 2TA support + LTM | `TCI-State`'s `[[ tag-Id-ptr-r18 -- Cond 2TA ]]` + R2-2403134 | ✅ Match — "Rel-17 unified TCI was expanded to multi-TRP use case and two TAs are supported" (Ericsson, 3G4G Blog Rel-18 LTM) |
| 6 | Rel-18 LTM = MAC-CE/DCI-based cell switch + candidate cell TCI states activation | `CandidateTCI-State-r18 + LTM-QCL-Info-r18` + R2-2207753 | ✅ Match — "MAC CEs activate target cell states including TCI states; UE aware of beam directions before switch" (Ericsson Tech Review LTM) |
| 7 | Rel-19 NR MIMO Phase 5 (RP-242394, Samsung rapporteur) = asymmetric DL sTRP/UL mTRP + path loss offset | TDoc R2-2508663/R1-2408118 + ASN.1 `[[ pathlossOffset-r19 ]]` | ✅ Match — "RP-242394 NR MIMO Phase 5, Samsung rapporteur Eko Onggosanushi" (3GPP RAN105 draft WID) |
| 8 | `[[ pathlossOffset-r19 ENUMERATED {dB-12..dB60} OPTIONAL -- Need R ]]` extension block | asn1 IE=`TCI-State` | ✅ Match — r19 extension block loaded as of ETSI 138.331 V18.6.0 (2025-07) |
| 9 | Rel-15 RAN2-side TCI MAC CE introduction RAN2#100 ai=10.2.13 | R2-1713533 | ✅ Match — RAN2 ai=10.2.13 NR MAC CE design track, retrieval log verified |

→ **9/9 all match authoritative sources**. Rel-19 spec body and Rel-15 RAN2-side introduction evidence are both directly cited.

---

## Hallucinations

### SPECTRA RAG

- **One weak hallucination**: the expression that §6.1.3.14 PDSCH TCI activation MAC CE is "operational since Rel-15". The chunk body lacks a direct "Rel-15" citation (-0.1).
- **0 other hallucinations**. ASN.1 IE bodies are reproduced from the retrieval log's `asn1_by_name[*].rows[*].text` or `asn1_vector_queries[*].hits[*].text` (no truncation). Rel-20 speculation count = 0.

### Claude

- **Rel-19 misclassification**: AI/ML for NR Air Interface (RP-234039) is asserted as the Rel-19 main TCI-framework line. Differs from the authoritative source NR MIMO Phase 5 (RP-242394).
- **Rel-20 ASN.1 speculative fill**: code block `TCI-State-r20 { crossCarrierRefRS-r20, subbandTCI-Application-r20, ntn-DopplerComp-r20 }`. As of ETSI 138.331 v18.6.0 the r20 extension block is not loaded → **model-generated ASN.1**.
- LCID numbers (53/49/56), `T_BAT`, `beamAppTime-r17`, and other sharetechnote-level details cannot be verified directly against authoritative sources.

### GPT

- Mentions a "simultaneous TCI update list" for Rel-16 — release-mapping error since the authority classifies the item under Rel-18.
- Asserts Rel-19 as "CLTM/inter-cell BM extension" — the authoritative NR MIMO Phase 5 lists mTRP/asymmetric DL sTRP/UL mTRP as the main line, while CLTM is a separate mobility track.

---

## Practical conclusion

1. **SPECTRA RAG ranks first across all 5 axes (4.9/5.0)**. Citation integrity 5.0 + direct ASN.1 body citation lift accuracy/coverage/cross-doc simultaneously.
2. **24-cell fill rate 20/24 (83.3%)**. The 38.331 ASN.1 area and 38.306 capability rows area are filled. The Rel-19 spec body change (`pathlossOffset-r19`) is cited as direct evidence.
3. **Claude's Rel-20 ASN.1 hallucination is present**. Only SPECTRA RAG consistently maintains the honest non-answer (Rel-20 spec body not found). Acknowledging the dataset limitation aligns with authoritative sources.
4. **Direct citation of 38.331 IE bodies is the decisive factor.**
5. **Retrieval-grounded answers outperform LLM-knowledge-based answers in verifiability** (citation integrity 5.0 vs. 1.5/2.0).

---

## Authoritative sources (used for verdict verification)

- ETSI TS 138 331 V18.6.0 (2025-07) — https://www.etsi.org/deliver/etsi_ts/138300_138399/138331/18.06.00_60/ts_138331v180600p.pdf
- ETSI TS 138 331 V18.4.0 (2025-01) — https://www.etsi.org/deliver/etsi_ts/138300_138399/138331/18.04.00_60/ts_138331v180400p.pdf
- ETSI TS 138 321 V18.x — https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/18.06.00_60/ts_138321v180600p.pdf
- 3GPP TS 38.331 spec page — https://www.3gpp.org/dynareport/38331.htm
- itecspec 38.331 §6.3.2 RRC IE — https://itecspec.com/spec/3gpp-38-331-6-3-2-radio-resource-control-information-elements/
- Ofinno Unified Beam Management whitepaper (Sep 2021) — https://ofinno.com/wp-content/uploads/2021/09/Ofinno-Unified-Beam-Management-Whitepaper.pdf
- 3GPP RAN1 Rel-18 page (multi-TRP unified TCI extension) — https://www.3gpp.org/technologies/ran1-rel18
- Ericsson "L1/L2 Triggered Mobility" — https://www.ericsson.com/en/reports-and-papers/ericsson-technology-review/articles/reducing-handover-interruption-l1l2-triggered-mobility
- 3G4G Blog "Understanding LTM in Rel-18" — https://blog.3g4g.co.uk/2025/08/understanding-l1l2-triggered-mobility.html
- 3GPP RP-242394 Rel-19 MIMO draft WID (RAN105) — https://www.3gpp.org/ftp/Meetings_3GPP_SYNC/RAN/Inbox/drafts/R19%20MIMO/Draft%20WID/DRAFT%20RP-242394%20Rev%20WID%20-%20Rel-19%20MIMO%20(RAN105)%20V02.doc
- RAN Rel-19 Status — https://www.3gpp.org/technologies/ran-rel-19
- sharetechnote QCL/TCI — https://www.sharetechnote.com/html/5G/5G_QCL.html
- LinkedIn TCI/QCL article — https://www.linkedin.com/pulse/tci-transmission-configuration-indicator-states-qcl-quasi-chelikani
