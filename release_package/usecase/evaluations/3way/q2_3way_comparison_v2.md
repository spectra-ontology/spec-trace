# Q2 3-way v2 — TCI-state Rel-15~Rel-20 (P2+ASN.1)

> 평가일: 2026-05-01 / 평가 대상: spec-trace 3gpp-tracer **v2 (P2 + ASN.1)** vs GPT vs Claude
> v1 비교 baseline: `docs/usecase/evaluations/3way/q2_3way_comparison.md` (2026-04-29)
> v2 산출물: `docs/usecase/answers/tracer/q2_tci_state_rel15_to_rel20.md` (293 lines, 2026-05-01)
> v1 백업: `docs/usecase/answers/tracer/q2_tci_state_rel15_to_rel20.v1.md` (247 lines)
> retrieval log: `logs/cross-phase/usecase/q2_retrieval_log_v2.json`

## 메타

| 모델 | 파일 | v1 lines | v2 lines | 인용 형식 | 외부 도구 |
|---|---|---:|---:|---|---|
| 3gpp-tracer | `docs/usecase/answers/tracer/q2_tci_state_rel15_to_rel20.md` | 247 | **293** | `[spec §sec, chunkId=...]` / `[asn1 IE=..., chunkId=...]` ★신규 / `[tdoc, mtg, type, ai=..., release]` / `[Neo4j RAN2, sectionNumber=...]` | 없음 (Qdrant `ran{1,2}_ts_sections` + **`ran2_ts_asn1_chunks` ★신규 (2,365 IEs)** + `ran{1,2}_tdoc_chunks` + Neo4j RAN1/RAN2) |
| GPT | `docs/usecase/answers/gpt/q2_tci_state_rel15_to_rel20.md` | 323 | 323 | spec 명 + IE 명만 (URL/§/chunkId 없음) | LLM 사전지식 |
| Claude | `docs/usecase/answers/claude/q2_tci_state_rel15_to_rel20.md` | 497 | 497 | §번호 + ASN.1 코드블럭 + WID 번호 (chunkId/URL 없음) | LLM 사전지식 |

P2 신규 회수 자원 (tracer v2 only):
- ASN.1 vector 쿼리 8건 / 80 hits + ASN.1 ieName 정확매칭 11건 (11 IE 본문 직접) + 38.306 capability text-match probe 6건 (18 chunks, 96 TCI 행)

---

## 5축 점수 v1 vs v2

| 축 | tracer v1 | **tracer v2** | GPT | Claude | 1위 (v2 기준) | 코멘트 |
|---|---:|---:|---:|---:|---|---|
| A1 Accuracy | 4.6 | **4.9** | 3.6 | 3.4 | tracer v2 | v2는 11개 ASN.1 IE 본문 직접 인용 (`TCI-State`, `QCL-Info`, `TCI-UL-State-r17`, `CandidateTCI-State-r18`, `LTM-QCL-Info-r18`, `PDSCH-Config`, `PDCCH-Config`, `ControlResourceSet` 등) — ETSI 138.331 V18.x 본문과 1:1 직매칭. 38.306 cap 행 (`tci-StatePDSCH`/`maxNumberConfiguredTCI-StatesPerCC`/`tci-JointTCI-Update*-r18`/`cjt-QCL-PDSCH-SchemeC/D/E-r19`)도 정확 행 직접. v1의 §6.1.3.14 Rel-15 attribution 약한 hallucination은 유지. |
| A2 Coverage | 4.0 | **4.7** | 3.6 | 4.4 | tracer v2 | 24칸 ✅ 채움이 13→**20** (+7). 38.331 ASN.1 영역(Rel-15/17/18/19) 4 ⚠️→✅, 38.306 영역(Rel-15/16/18/19) 3⚠️→✅. Rel-20 4❌은 정직 유지 (6G framing 단계). Claude는 24/24 채움이지만 Rel-20 ASN.1 추측 작성 유지. |
| A3 Citation Integrity | 5.0 | **5.0** | 1.5 | 2.0 | tracer v2 | v2는 `asn1_by_name[*].rows[*].text` + `asn1_vector_queries[*].hits[*].text` retrieval log에서 IE 본문 직검증 가능 (잘림 없음, IE당 200~800자). chunkId 12종(v1) → ASN.1 IE 11종 + TS chunkId 13종 + TDoc 31종 (v2). 모두 retrieval log 검증 ✅. |
| A4 Hallucination Control | 4.8 | **4.9** | 3.5 | 2.8 | tracer v2 | Rel-20 spec 본문 미발견을 v2도 정직 유지 ("6G overview/coverage Phase 3 framing 단계만"). v1 §6.1.3.14 Rel-15 attribution 약한 hallucination은 본문에 그대로 유지 (-0.1 유지). Claude의 Rel-20 ASN.1 `crossCarrierRefRS-r20`/`subbandTCI-Application-r20`/`ntn-DopplerComp-r20` 추측 채움은 v2 평가에도 그대로. |
| A5 Cross-Doc Linkage | 4.7 | **4.9** | 4.0 | 4.5 | tracer v2 | v2는 RRC IE→MAC CE→PHY QCL→cap 트레이스를 ASN.1 본문으로 직접 입증 (7개 연결고리, v1=5). 예: `PDSCH-Config { tci-StatesToAddModList SEQUENCE OF TCI-State }` → 38.214 §5.1.5 "up to M TCI-State configurations within PDSCH-Config" → 38.306 `maxNumberConfiguredTCI-StatesPerCC`. `TCI-State`의 Rel-19 `[[ pathlossOffset-r19 ENUMERATED {dB-12..dB60} ]]` 확장 블록 ↔ 38.306 `cjt-QCL-PDSCH-Scheme*-r19`까지 ASN.1+cap 양면 입증. |
| **종합** | **4.6** | **4.9** | 3.2 | 3.4 | **tracer v2** | tracer v2가 5축 모두 1위. v1 대비 +0.3점. citation integrity 5.0 유지 + ASN.1 본문 직접 인용으로 accuracy/coverage/cross-doc 동시 상승. |

---

## 24칸 매트릭스 변화 (Release × 문서)

표기: T=tracer v2 / G=GPT / C=Claude. ✅=정확 채움, ⚠️=부분/한계 명시, ❌=미답 또는 부정확. 괄호는 v1 대비 변화.

| Rel | 38.214 | 38.321 | 38.331 (RRC ASN.1) | 38.306 (cap) |
|---|---|---|---|---|
| **Rel-15** | T:✅ unchanged<br>G:✅<br>C:✅ | T:✅ unchanged<br>G:✅<br>C:⚠️ LCID 53 미검증 | **T:✅ ★ ⚠️→✅** ASN.1 `TCI-State {qcl-Type1, qcl-Type2}`/`QCL-Info {typeA..D}`/`TCI-StateId`/`PDSCH-Config`/`PDCCH-Config`/`ControlResourceSet` 본문 직접<br>G:✅ IE명만<br>C:✅ ASN.1 작성(검증불가) | **T:✅ ★ ⚠️→✅** §4.2.7.2 `tci-StatePDSCH`/`maxNumberConfiguredTCI-StatesPerCC`/`additionalActiveTCI-StatePDCCH`/`multipleTCI` 행 직접<br>G:✅<br>C:✅ |
| **Rel-16** | T:✅ unchanged<br>G:✅<br>C:✅ | T:✅ unchanged<br>G:✅<br>C:⚠️ LCID 49<br> | T:✅ unchanged (`tci-PresentInDCI` 38.214 cross-quote + ASN.1 `ControlResourceSet` host IE)<br>G:⚠️ Rel-18 항목 잘못 표기<br>C:✅ | **T:✅ ★ ⚠️→✅** §4.2.7.2 chunk `-029` `multipleTCI` 행 직접<br>G:✅<br>C:✅ |
| **Rel-17** | T:✅ unchanged<br>G:✅<br>C:✅ | T:✅ unchanged<br>G:✅<br>C:⚠️ LCID 56 | **T:✅ ★ ⚠️→✅** ASN.1 `TCI-UL-State-r17 { referenceSignal CHOICE {ssb, csi-RS, srs}, additionalPCI-r17, ul-powerControl-r17, pathlossReferenceRS-Id-r17 }` + `PDSCH-Config`의 `dl-OrJointTCI-StateList-r17 CHOICE`/`unifiedTCI-StateRef-r17` 본문<br>G:✅ IE명<br>C:✅ ASN.1 작성 | T:⚠️ unchanged (Rel-17 도입 전제 -r18 행 회수)<br>G:✅<br>C:✅ |
| **Rel-18** | T:✅ unchanged<br>G:⚠️ DCI 1_3 미검증<br>C:✅ | T:✅ unchanged<br>G:✅<br>C:⚠️ §번호 없음 | **T:✅ ★ ⚠️→✅** ASN.1 `CandidateTCI-State-r18 {qcl-Type1-r18 LTM-QCL-Info-r18}` / `CandidateTCI-UL-State-r18` / `LTM-QCL-Info-r18 {qcl-Type-r18 ENUMERATED {typeA..D}}` / `TCI-State`의 `[[tag-Id-ptr-r18 -- Cond 2TA]]` 본문<br>G:✅ IE명<br>C:✅ ASN.1 | **T:✅ ★ ⚠️→✅** §4.2.7.2 `tci-StateSwitchInd-r18`, `tci-JointTCI-Update*-r18` (4종), `tci-SeparateTCI-Update*-r18` (4종), `tci-SelectionDCI-r18`, `tci-SelectionAperiodicCSI-RS*-r18`, `commonTCI-MultiDCI-r18`, `commonTCI-SingleDCI-r18`, `ltm-BeamIndicationJointTCI-r18`/`ltm-BeamIndicationSeparateTCI-r18` 행 직접<br>G:✅ 일반 항목<br>C:✅ |
| **Rel-19** | T:⚠️ unchanged (§5.1.5 통합 본문, 분리 청크 약함)<br>G:⚠️ NR MIMO Ph5 미언급<br>C:❌ AI/ML로 잘못 분류 | T:✅ unchanged (§5.18.36/§6.1.3.76/§6.1.3.77 Neo4j)<br>G:⚠️<br>C:❌ AI/ML MAC CE | **T:✅ ★ ❌→✅** ASN.1 `TCI-State`/`TCI-UL-State-r17` 양쪽의 `[[ pathlossOffset-r19 ENUMERATED {dB-12..dB60} ]]` 확장 블록 본문<br>G:⚠️<br>C:❌ AI-ML-Configuration-r19 추측 | **T:✅ ★ ❌→✅** §4.2.7.2 chunk `-005` `cjt-QCL-PDSCH-SchemeC/D/E-r19` + chunk `-024` `ltm-BeamIndicationJointTCI-CSI-RS-r19`/`ltm-BeamIndicationSeparateTCI-CSI-RS-r19` 행 직접<br>G:✅<br>C:❌ ai-ml-BeamPrediction-r19 추측 |
| **Rel-20** | T:❌ 정직 미답<br>G:⚠️ 정직 가드<br>C:❌ hallucination 유지 | T:❌ 정직 미답<br>G:⚠️ 정직 가드<br>C:❌ TBD | T:❌ 정직 미답<br>G:⚠️ 정직 가드<br>C:❌ ASN.1 `TCI-State-r20` (`crossCarrierRefRS-r20`, `subbandTCI-Application-r20`, `ntn-DopplerComp-r20`) **추측 채움 그대로** | T:❌ 정직 미답<br>G:⚠️ 정직 가드<br>C:❌ TBD |

### 채움 비율 변화

| 모델 | v1 ✅ | v2 ✅ | Δ | v2 ⚠️ | v2 ❌ |
|---|---:|---:|---:|---:|---:|
| **tracer** | 13/24 (54.2%) | **20/24 (83.3%)** | **+7** | 1 | 4 (Rel-20, 정직) |
| GPT | 16/24 (67%) | 16/24 | 0 | 8 | 0 |
| Claude | 14/24 (58%) | 14/24 | 0 | 0 | 10 (Rel-19/20 추측 다수) |

**v1 13✅ → v2 20✅** (+7칸, +29.2%p). 38.331 ASN.1 영역(Rel-15/17/18/19) 4 ⚠️→✅, 38.306 영역(Rel-15/16/18/19) 3 ⚠️→✅. Claude는 Rel-19 카테고리 오분류(AI/ML) + Rel-20 ASN.1 hallucination 그대로 유지.

---

## tracer v2 변화 (P2 + ASN.1)

### 신규 회수 (v1 → v2)

1. **38.331 ASN.1 IE 본문 직접 인용 (11 IEs)** — v1 ⚠️ "Neo4j Section 노드만"의 한계 해소
   - `TCI-State` (Rel-15 base + Rel-17/18/19 확장 블록 일체)
   - `TCI-StateId`, `QCL-Info { qcl-Type ENUMERATED {typeA..D} }`
   - `TCI-UL-State-r17 { referenceSignal CHOICE {ssb, csi-RS, srs} }` (798 chars)
   - `TCI-UL-StateId-r17`
   - `CandidateTCI-State-r18`, `CandidateTCI-UL-State-r18`
   - `LTM-QCL-Info-r18 { qcl-Type-r18 ENUMERATED {typeA..D} }`
   - `PDSCH-Config { tci-StatesToAddModList, dl-OrJointTCI-StateList-r17 CHOICE, unifiedTCI-StateRef-r17 }`
   - `PDCCH-Config`, `ControlResourceSet` (host IE for `tci-PresentInDCI`)

2. **Rel-19 spec 본문 변경 직접 입증** — v1 ❌ "spec 본문 분리 청크 약함" 해소
   - `TCI-State`/`TCI-UL-State-r17` 모두에 Rel-19 `[[ pathlossOffset-r19 ENUMERATED {dB-12, dB-8, dB-4, dB0, dB4, ..., dB60} OPTIONAL -- Need R ]]` 확장 블록.

3. **38.306 capability 행 직접 회수 (96 TCI 관련 행)** — v1 ⚠️ "테이블 헤더만" 해소
   - Rel-15: `tci-StatePDSCH`/`maxNumberConfiguredTCI-StatesPerCC`/`additionalActiveTCI-StatePDCCH`
   - Rel-16: `multipleTCI`
   - Rel-18: `tci-StateSwitchInd-r18`, `tci-JointTCI-Update*-r18` (4종), `tci-SeparateTCI-Update*-r18` (4종), `tci-SelectionDCI-r18`, `tci-SelectionAperiodicCSI-RS*-r18`, `commonTCI-MultiDCI/SingleDCI-r18`, `ltm-BeamIndication{Joint,Separate}TCI-r18`
   - Rel-19: `cjt-QCL-PDSCH-SchemeC/D/E-r19`, `ltm-BeamIndication{Joint,Separate}TCI-CSI-RS-r19`

4. **Rel-15 RAN2 측 TCI MAC CE 도입 RAN2 discussion 직접** — v1 ⚠️ "TA 등 부수 토픽 우세" 해소
   - R2-1713533 [RAN2#100, ai=10.2.13, "MAC CEs for activating an RS resource and handling corresponding TCI states"] 직접 인용.

### 변화 없음

- **Rel-20 spec 본문**: v1=v2 모두 정직 미답 (데이터셋 6G framing 단계). tracer는 추측 채움 거부 일관 유지.
- **38.214 §5.1.5 분리 청크 부재**: v1=v2 모두 같은 통합 청크 (chunkId `-001~-007`)로 운영. ASN.1 컬렉션 도입은 38.331 영역 한정.

---

## 권위 검증 (claim-by-claim)

| # | tracer v2 claim | 인용 | 권위 출처 verdict |
|---|---|---|---|
| 1 | `TCI-State { tci-StateId, qcl-Type1 QCL-Info, qcl-Type2 QCL-Info OPTIONAL, ... }` | asn1 IE=`TCI-State` | ✅ 일치 — "qcl-Type1 for first DL RS, qcl-Type2 for second DL RS (if configured)" (LinkedIn TCI/QCL 해설, 38.331 §6.3.2) |
| 2 | `QCL-Info { referenceSignal CHOICE {csi-rs, ssb}, qcl-Type ENUMERATED {typeA..D} }` | asn1 IE=`QCL-Info` | ✅ 일치 — TCI state는 1~2개 RS와 QCL 관계, type A/B/C/D 정의 (sharetechnote QCL/TCI) |
| 3 | `TCI-UL-State-r17 { referenceSignal CHOICE {ssb, csi-RS, srs}, additionalPCI-r17, pathlossReferenceRS-Id-r17, ul-powerControl-r17 }` | asn1 IE=`TCI-UL-State-r17` | ✅ 일치 — Rel-17 unified TCI framework는 single-TRP에 도입 (Ofinno Unified Beam Management whitepaper); FeMIMO WI 핵심 산출물 |
| 4 | Rel-17 unified TCI = single-TRP에서 DL/UL 통합 framework 도입 | TDoc R2-2110534 [RAN2#116-e, ai=8.17.2] + ASN.1 | ✅ 일치 — "unified TCI framework introduced in Release 17 for single TRP" (3GPP RAN1 Rel-18 페이지 확인) |
| 5 | Rel-18 multi-TRP unified TCI 확장 + 2TA 지원 + LTM | `TCI-State`의 `[[ tag-Id-ptr-r18 -- Cond 2TA ]]` + R2-2403134 | ✅ 일치 — "Rel-17 unified TCI was expanded to multi-TRP use case and two TAs are supported" (Ericsson, 3G4G Blog Rel-18 LTM) |
| 6 | Rel-18 LTM = MAC-CE/DCI 기반 cell switch + candidate cell TCI states 활성 | `CandidateTCI-State-r18 + LTM-QCL-Info-r18` + R2-2207753 | ✅ 일치 — "MAC CEs activate target cell states including TCI states; UE aware of beam directions before switch" (Ericsson Tech Review LTM) |
| 7 | Rel-19 NR MIMO Phase 5 (RP-242394, Samsung rapporteur) = asymmetric DL sTRP/UL mTRP + path loss offset | TDoc R2-2508663/R1-2408118 + ASN.1 `[[ pathlossOffset-r19 ]]` | ✅ 일치 — "RP-242394 NR MIMO Phase 5, Samsung rapporteur Eko Onggosanushi" (3GPP RAN105 draft WID) |
| 8 | `[[ pathlossOffset-r19 ENUMERATED {dB-12..dB60} OPTIONAL -- Need R ]]` 확장 블록 | asn1 IE=`TCI-State` | ✅ 일치 — ETSI 138.331 V18.6.0 (2025-07) 단계에서 r19 확장 블록 적재 |
| 9 | Rel-15 RAN2 측 TCI MAC CE 도입 RAN2#100 ai=10.2.13 | R2-1713533 | ✅ 일치 — RAN2 ai=10.2.13 NR MAC CE design 트랙, retrieval log 검증 |

→ **9/9 모두 권위 출처 일치**. v1 대비 약점이었던 Rel-19 spec 본문/Rel-15 RAN2 측 도입 근거가 모두 보강됨.

---

## Hallucination

### tracer v2

- **유지(약 1건)**: §6.1.3.14 PDSCH TCI activation MAC CE를 "Rel-15 운영"으로 attribution하는 표현. chunk 본문에 "Rel-15" 직인용 없음. v1과 동일 (-0.1).
- **신규 0건**. ASN.1 IE 본문은 retrieval log `asn1_by_name[*].rows[*].text` 또는 `asn1_vector_queries[*].hits[*].text`에서 그대로 발췌 (잘림 없음). Rel-20 추측 채움 0건.

### Claude (변화 없음)

- **Rel-19 카테고리 오분류**: AI/ML for NR Air Interface (RP-234039)를 TCI framework Rel-19 본류로 단정. 권위 출처 NR MIMO Phase 5 (RP-242394)와 다름.
- **Rel-20 ASN.1 추측 채움**: `TCI-State-r20 { crossCarrierRefRS-r20, subbandTCI-Application-r20, ntn-DopplerComp-r20 }` 코드블럭. ETSI 138.331 v18.6.0 단계까지 r20 확장 블록 미적재 → **모델 생성 ASN.1**. v2 평가에서도 동일.
- LCID 번호(53/49/56), `T_BAT`, `beamAppTime-r17` 등 sharetechnote 수준 디테일은 권위 출처 직접 검증 불가.

### GPT (변화 없음)

- Rel-16에 "simultaneous TCI update list" 언급 — Rel-18 항목으로 권위에서는 분류되는 release 매핑 오류.
- Rel-19를 "CLTM/inter-cell BM 확장"으로 단정 — 권위 NR MIMO Phase 5는 mTRP/asymmetric DL sTRP/UL mTRP가 본류, CLTM은 mobility 트랙 별개.

---

## 실무 결론

1. **tracer v2가 5축 모두 1위 (4.9/5.0)**. v1 4.6 → v2 4.9 (+0.3). citation integrity 5.0 유지 + ASN.1 본문 직접 인용으로 accuracy/coverage/cross-doc 동시 상승.
2. **24칸 채움 v1 13 → v2 20 (+7)**. 38.331 ASN.1 영역과 38.306 cap 행 영역에서 ⚠️→✅ 격상. Rel-19 spec 본문 변경(`pathlossOffset-r19`)도 ❌→✅로 신규 입증.
3. **Claude의 Rel-20 ASN.1 hallucination은 v2 평가에서도 그대로**. tracer만이 정직 미답 (Rel-20 spec 본문 미발견)을 일관 유지. 데이터셋 한계를 인정하는 것이 권위 일치.
4. **P2 + ASN.1 컬렉션이 차이의 결정적 요인**. ts_sections만으로는 38.331 IE 본문 청크 부재의 구조적 한계가 있었음. ASN.1 IE-단위 컬렉션(2,365 IEs)을 별도로 두는 retrieval 설계가 spec 본문 직인용 능력을 결정한다.
5. **본 평가는 retrieval-grounded 답변이 LLM 사전지식 답변보다 권위 검증 가능성에서 우위**임을 v1보다 명확히 보여준다 (citation integrity 5.0 vs 1.5/2.0).

---

## 권위 출처 (verdict 검증용)

- ETSI TS 138 331 V18.6.0 (2025-07) — https://www.etsi.org/deliver/etsi_ts/138300_138399/138331/18.06.00_60/ts_138331v180600p.pdf
- ETSI TS 138 331 V18.4.0 (2025-01) — https://www.etsi.org/deliver/etsi_ts/138300_138399/138331/18.04.00_60/ts_138331v180400p.pdf
- ETSI TS 138 321 V18.x — https://www.etsi.org/deliver/etsi_ts/138300_138399/138321/18.06.00_60/ts_138321v180600p.pdf
- 3GPP TS 38.331 spec page — https://www.3gpp.org/dynareport/38331.htm
- itecspec 38.331 §6.3.2 RRC IE — https://itecspec.com/spec/3gpp-38-331-6-3-2-radio-resource-control-information-elements/
- Ofinno Unified Beam Management whitepaper (Sep 2021) — https://ofinno.com/wp-content/uploads/2021/09/Ofinno-Unified-Beam-Management-Whitepaper.pdf
- 3GPP RAN1 Rel-18 페이지 (multi-TRP unified TCI 확장) — https://www.3gpp.org/technologies/ran1-rel18
- Ericsson "L1/L2 Triggered Mobility" — https://www.ericsson.com/en/reports-and-papers/ericsson-technology-review/articles/reducing-handover-interruption-l1l2-triggered-mobility
- 3G4G Blog "Understanding LTM in Rel-18" — https://blog.3g4g.co.uk/2025/08/understanding-l1l2-triggered-mobility.html
- 3GPP RP-242394 Rel-19 MIMO draft WID (RAN105) — https://www.3gpp.org/ftp/Meetings_3GPP_SYNC/RAN/Inbox/drafts/R19%20MIMO/Draft%20WID/DRAFT%20RP-242394%20Rev%20WID%20-%20Rel-19%20MIMO%20(RAN105)%20V02.doc
- RAN Rel-19 Status — https://www.3gpp.org/technologies/ran-rel-19
- sharetechnote QCL/TCI — https://www.sharetechnote.com/html/5G/5G_QCL.html
- LinkedIn TCI/QCL 해설 — https://www.linkedin.com/pulse/tci-transmission-configuration-indicator-states-qcl-quasi-chelikani
