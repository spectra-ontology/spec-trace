# Q3 3-way 비교 — Beam Failure Detection/Recovery

> 평가일: 2026-04-29 · 평가자: spec-trace 평가팀
> 본 보고서는 Q3 (BFD/BFR) 답변에 대해 3개 모델(spec-trace 3gpp-tracer / GPT / Claude)을 5축 점수 + 정량값 매트릭스로 비교한다.
> 권위 출처는 `docs/usecase/evaluations/tracer/q3_quality_eval.md`(이미 검증 완료)를 1차 사용하고, 필요 시 그 안의 외부 권위 링크(TS 38.213 mirror, ShareTechnote, Award Solutions, TechSpec, Justia patent 등)를 인용한다.

---

## 메타

| 모델 | 파일 | 라인 수 | 인용 형식 | 외부 도구 사용 |
|---|---|---:|---|---|
| 3gpp-tracer | `docs/usecase/answers/tracer/q3_beam_failure_recovery.md` | 323 | `[<TS> §<sec>, chunkId=...]` / `[TDoc <num>, chunkId=...]` (16건 모두 retrieval log 실재) | WebFetch/WebSearch 0회. Qdrant 39쿼리(TS 27 + TDoc 12) + Neo4j Cypher 4건 |
| GPT | `docs/usecase/answers/gpt/q3_beam_failure_recovery.md` | 319 | spec/section 언급(예: "38.331", "Clause 5.17")만, chunkId/문장 인용 없음. 마지막에 5개 spec 일반 참조만 | 외부 도구 사용 명시 없음. 학습지식 기반 구성 추정 |
| Claude | `docs/usecase/answers/claude/q3_beam_failure_recovery.md` | 568 | spec/section 언급("38.213 §6", "38.321 §5.17") + ASN.1 IE 직접 인용 + Release/WID 번호(RP-201305 등). chunkId/문장 출처 없음 | 외부 도구 사용 명시 없음. 학습지식 기반 추정 |

---

## 5축 점수 비교 (0~5)

| 축 | tracer | GPT | Claude | 1위 | 코멘트 |
|---|:---:|:---:|:---:|:---:|---|
| A1 Accuracy | 4.5 | 3.5 | 4.0 | tracer | tracer는 인용한 사실 16/16 권위 일치(가짜 0). Claude는 ASN.1 enumerated 범위(`{n1,n2,n3,n4,n5,n6,n8,n10}`, `{pbfd1..pbfd10}`)·BLER 10%·SCell BFR LCID 47/48 등 정량값을 정확히 제시. GPT는 절차/파라미터 이름은 정확하나 정량값 자체를 제시하지 않거나 모호 처리. |
| A2 Coverage | 4.0 | 3.5 | 4.5 | Claude | tracer: 6항목+연결고리 모두 다룸, 정량값은 의도적 미인용. GPT: 6항목 균형 있게 다루나 Release 진화·SCell MAC-CE 포맷·정량값 얕음. Claude: BFR MAC-CE 포맷 octet 구조, Release15→18 진화, FR2 80ms latency budget까지 가장 폭넓음. |
| A3 Citation Integrity | 5.0 | 1.5 | 2.5 | tracer | tracer는 chunkId·TDoc#·Cypher 결과 모두 retrieval log 실재 검증 완료. GPT는 spec명만 표기·문장 인용 0건·검증 불가. Claude는 ASN.1 인용·WID 번호(RP-201305/211583/234037) 등 검증 가능한 단서 제공하나 chunk-level traceability 없음. |
| A4 Hallucination Control | 5.0 | 4.0 | 3.0 | tracer | tracer: 학습지식 누출 0건(권위 검증). GPT: 정량값 제시 자체를 회피해 hallucination 위험 낮음. Claude: 일부 수치(`L1-RSRP threshold -110 dBm (default)`, `T_recovery < 80ms typical FR2`, `최대 BFD-RS Rel.16+ 64`)가 표준 본문에 없는 typical/예시값이거나 부정확 — §아래 hallucination 표 참조. |
| A5 Cross-Doc Linkage | 4.5 | 4.0 | 4.5 | tie | tracer: 5개 명시적 연결을 spec 본문 인용("See also TS 38.321 [3], clause 5.17") + 8단계 시퀀스 다이어그램. GPT: 3중 도식(38.331→38.213→38.321→38.133/38.533) 명료하나 spec 본문 출처 없음. Claude: 4-checkpoint(BFD-RS 일관성/카운터·타이머/Recovery 응답/Latency budget) + FR2 80ms timeline 시나리오 등 가장 구조화. |
| **종합** | **4.6** | **3.3** | **3.7** | tracer | citation integrity와 hallucination control이 결정적. 단 정량값 답변 자체는 Claude가 가장 풍부(정확도 검증 필요). |

---

## ★ 정량값 검증 매트릭스 (BFR 핵심 분기)

> 권위 값은 `q3_quality_eval.md` 정량값 표 + 외부 권위 출처(TS 38.213 mirror, ShareTechnote, Award Solutions) 기준.

| 파라미터 | 권위 값 | tracer | GPT | Claude | tracer 한계 원인 |
|---|---|---|---|---|---|
| Q_out,LR BLER | **10%** (가상 PDCCH BLER, DCI 1_0 + CCE AL 8, 2-symbol CORESET) | **미답** — §5/§6 chunk top score 0.33으로 직접 매칭 약함 명시 | **미답** — "Qout_LR/Qin_LR" 변수명만, % 값 없음 | **10%** 명시 (§3.1.3 "BLER_hypothetical > Q_out_LR (e.g., 10%)") + §6.3 표 "Q_out_LR (BLER threshold) 10%" | preview 600자 컷오프로 정량 본문 잘림 (R) |
| Q_in,LR BLER | **2%** (가상 PDCCH BLER, DCI 1_0 + CCE AL 4) | **미답** | **미답** | **미답** (Q_in 별도 정의 없이 "Qin_LR: candidate/in-sync threshold"로만 표기) | preview 600자 컷오프 (R) |
| beamFailureInstanceMaxCount | enumerated `{n1, n2, n3, n4, n5, n6, n8, n10}` | **미답** — 변수명·동작만, 범위 미공개 | **미답** — "몇 번 누적되면 BFR trigger"만, enumerated 없음 | **`1, 2, 3, 4, 5, 6, 8, 10`** (§4.1.1 표 + §6.3 "1~10 (RRC), 통상 3") — 권위와 일치 | 38.331 IE block sectionTitle과 분리 안 됨 (R+O) |
| beamFailureDetectionTimer | enumerated `{pbfd1, pbfd2, pbfd3, pbfd4, pbfd5, pbfd6, pbfd8, pbfd10}` | **미답** — chunk score 낮아 "미발견" 목록 명시 | **미답** — "BFI counter reset timer"만 | **`pbfd1, pbfd2, ... pbfd10` (slot 단위)** (§4.1.1 표) — 권위와 일치(slot 단위 정확) | 38.331 IE block dense retrieval 약함 (R+O) |
| ra-ResponseWindow | enumerated `{sl1, sl2, sl4, sl8, sl10, sl20, sl40, sl80}` | **부분** — 변수명·연결("BeamFailureRecoveryConfig 내 ra-ResponseWindow")만, 범위 미인용 | **미답** — 변수 자체 미언급 | **부분** — `beamFailureRecoveryTimer ENUMERATED {ms10, ms20, ms40, ms60, ms80, ms100, ms150, ms200}`은 인용했으나 이는 ra-ResponseWindow가 아닌 다른 IE | 38.331 §6.3 IE chunk 임베딩 약함 (R+O) |
| 38.133 측정 시간 ms | TS 38.133 §8.18.2.2 표 8.18.2.2-1/-2의 FR1/FR2 row(ms 절대값). FR2-1 N=2/4/6 스케일링 | **부분** — 변수명(`TEvaluate_BFD_SSB`, `Qout_LR_SSB`) + N 값(2,4,6) 정확 인용. 표 row의 ms 절대값은 preview 컷오프로 미인용 | **미답** — "수십 ms ~ 100 ms 이내", "몇 ms 안에" 같은 일반화 표현만 | **부분 + 추정값** — `T_Evaluate_BFD_SSB = max(T_DRX, M·T_SSB)` 수식 + "T_recovery < 80 ms (typical FR2)" — 80ms는 표준 본문이 아닌 typical 가정값 | preview 600자 컷오프 + 표 행 단위 chunking 부재 (R) |

**모델별 정량값 정답 집계**:

| 항목 | tracer | GPT | Claude |
|---|:---:|:---:|:---:|
| 정확 답변 (권위 일치) | 0 | 0 | 3 (`beamFailureInstanceMaxCount` 범위, `beamFailureDetectionTimer` 범위, Q_out 10%) |
| 부분 답변 (변수명·구조 정확) | 3 (ra-Response, 38.133 변수, FR2 N) | 0 | 1 (T_evaluate 수식) |
| 미답 (정직 보고) | 3 (Q_out, Q_in, IE 범위) | 6 (전부 미답) | 1 (Q_in 2%) |
| 추정/typical/일반화로 답변 | 0 | 0 (대신 변수명 자체 회피) | 1 (T_recovery < 80ms typical) |

→ **정량값 답변 풍부도**: Claude > tracer > GPT
→ **정량값 hallucination 위험도**: Claude (typical 값 1건 위험) > tracer (0건) ≈ GPT (회피로 0건)

---

## 항목별 차분 (6개 항목 + 연결고리)

| 항목 | tracer | GPT | Claude | 비고 |
|---|---|---|---|---|
| 도입 배경/필요성 | R1-1707606/R1-1713597/R2-1803196 등 4개 TDoc 본문 verbatim 인용 (Rel-15→16→18 진화) | 일반화 설명(FR2/blockage/RLF 회피)만, TDoc 인용 0 | FR2 path loss 20dB·blockage·dynamic 환경 + Rel.15→17 진화표. 학술 톤 우수 | tracer = TDoc evidence, Claude = 정량/구조 설명, GPT = 평이한 개론 |
| 38.213 PHY | §6 q0/q1 자원 정의 chunk verbatim 인용. BLER 정량값 미답 | q0/q1·Qout_LR/Qin_LR 개념 설명 + 6단계 절차. 정량값 0 | §6 BFI 검출(BLER 10%) + §9 candidate beam(L1-RSRP) + §10 response window. 가상 BLER 수식 + RS 최대 개수(Rel.15=2, Rel.16+=64*) | * Claude의 "Rel.16+ 최대 64 RS"는 정확성 재확인 필요. RadioLinkMonitoringRS 최대치는 IE 정의로 검증 필요 |
| 38.321 MAC | §5.17 chunk verbatim + §5.1.4 BFR PRACH ra-ResponseWindow chunk verbatim. SCell BFR은 KG 노드명만 | §5.17 절차 6단계 + SpCell PRACH vs SCell MAC CE/SR 도식. BFI_COUNTER 동작 정확 | §5.17 + §5.17.2 SCell BFR. BFR MAC CE octet 포맷(C0~C7 bitmap, AC bit, Candidate RS ID 6 bits, LCID 47/48). 가장 깊음 | tracer는 인용 강함, Claude는 포맷 깊이 우수 |
| 38.331 RRC | CR R2-2407883 본문에서 `BeamFailureRecoveryRSConfig` ASN.1 단편 + `rsrp-ThresholdBFR-r16 RSRP-Range` 인용. enumerated 범위 미답 | 두 표(BFD용/recovery용)에 13개 파라미터명 정리. ASN.1 0건 | `BeamFailureRecoveryConfig`/`BeamFailureRecoverySCellConfig-r16`/`RadioLinkMonitoringConfig` 3개 IE의 ASN.1 인용 + enumerated 범위 정확 | Claude = ASN.1 인용 가장 풍부. 단 `BeamFailureRecoveryConfig`의 `rootSequenceIndex-BFR INTEGER (0..137)` 등 일부 필드는 권위 검증 필요 |
| 38.133 RRM | §8.18.2.2 / §8.5B.2.2 / §8.5D.3.2 chunk verbatim. SSB/CSI-RS × 일반/RedCap × FR1/FR2 분기 정확. ms 절대값 미답 | 7개 requirement 범주 표(BFD evaluation/candidate/FR1/FR2/SSB/CSI-RS/DRX/restriction) | T_Evaluate_BFD_SSB 수식 + Test Configuration 예시(SS-RSRP -100/-130 dBm, threshold -110 dBm, T_recovery < 80ms) | tracer = 변수명·N값 정확, Claude = 수식·typical 값 풍부(검증 필요), GPT = 카테고리 정리만 |
| 38.533 시험 | §17.5.2.1 chunk verbatim(PC3, f≤40.8GHz) + §10.3.4/11.4.4 KG 노드 + R5-204985 normative ref 인용. test tolerance는 FFS 표기로 인용 회피 | 7개 test 범주 표 | §7.6 BFD test case + SCell BFR test case + False Alarm test. 시험 시나리오 구체값(SS-RSRP -100/-130 dBm) | tracer = 시험 케이스 KG 구조 강함, Claude = 시험 시나리오 구체화 |
| 문서간 연결고리 | 5개 명시적 연결(spec 본문 인용 기반) + 8단계 시퀀스 다이어그램. R2-2407883 "See also TS 38.321 [3], clause 5.17" 직접 인용으로 38.331↔38.321 강함 | 3중 도식(38.331→38.213→38.321→38.133/38.533) 명료. 출처 없음 | 4-Phase 절차도 + 4-Checkpoint 정합성 검증 + RRC/MAC/PHY/RRM 매트릭스 + FR2 60ms timeline | tracer = 출처 강함, Claude = 구조화 가장 정교, GPT = 명료성 |

---

## 강점 / 약점 (모델별)

### 3gpp-tracer

**강점**:
- Citation Integrity 만점 (16/16 chunk 권위 일치)
- Hallucination 0건 — 정량값 의도적 미인용으로 학습지식 누출 0
- 8단계 BFR 시퀀스 다이어그램이 모두 chunkId 인용 기반
- Release 진화(Rel-15→16→18) TDoc 인용으로 evidence-based
- 자가 검증 표가 한계를 정직하게 노출(FFS 마커, preview 컷오프, IE chunking)

**약점**:
- 사용자 질문이 명시한 정량값(BLER 10%/2%, n1~n10, pbfd1~pbfd10, sl1~sl80, ms row) **0건 직접 답변**
- 38.331 §6.3 IE ASN.1 enumerated 범위는 시스템적 한계로 인용 불가 (RAN1 Phase-7 IE-vs-절차 임베딩 한계와 동일 양상)
- 38.213 Q_out/Q_in BLER 정의가 chunk score 0.33 → retrieve는 됐으나 인용 못함 (preview 컷오프)

### GPT

**강점**:
- 가장 명료한 도식과 구조 (3중 흐름 + SpCell vs SCell 구분)
- 평이하고 한국어 가독성 우수 — 비전문가도 이해 가능
- 변수명/파라미터명 정확 (학습지식 기반이지만 권위 출처와 일치)
- Hallucination 위험 낮음 (정량값 제시 자체를 회피하는 보수적 전략)

**약점**:
- 정량값 **6/6 모두 미답** — 사용자 질문이 명시한 수치 핵심 분기에서 가장 약함
- Citation 0건 — 검증 불가, traceability 없음
- BFR MAC-CE 포맷·LCID·ASN.1 enumerated 범위 등 spec 깊이 부족
- Release별 진화 부재 (Rel-15→17 단계 안 다룸)

### Claude

**강점**:
- 정량값 답변 가장 풍부 — `n1~n10`, `pbfd1~pbfd10`, BLER 10%, BFR MAC CE LCID 47/48, ASN.1 IE 3개
- 학술 보고서 구조 (8장 + 결론 + 참조 WID 번호)
- BFR MAC CE octet 포맷 + LCID 분기 + 4-checkpoint 정합성 매트릭스
- FR2 60ms timeline 시나리오로 latency budget 시각화
- Multi-TRP/Multi-panel BFR (Rel-17/18) 진화 가장 깊음

**약점**:
- chunk-level citation 0 — traceability 없음
- 일부 수치가 typical/예시값(`T_recovery < 80ms typical FR2`, `L1-RSRP threshold -110 dBm default`)으로 표준 본문 출처 불명
- "최대 BFD-RS Rel.16+ 64" 같은 수치는 RadioLinkMonitoringRS 정의에서 검증 필요(권위 미확인)
- WID 번호(RP-201305 / RP-211583 / RP-234037)·LCID 47/48 등은 외부 검증 필요(공식 spec 본문 vs 학습지식 매칭 불완전)
- spec 본문 verbatim 인용 0건 → 사용자가 답변을 표준 회의에서 직접 인용하기 어려움

---

## Hallucination 검출 (외부 LLM 모델별)

> tracer는 권위 검증 결과 hallucination 0건이므로 GPT/Claude만 별도 분석.

| 모델 | 의심 정량값/사실 | 권위 검증 | verdict |
|---|---|---|---|
| GPT | "rlmInSyncOutOfSyncThreshold (Qout/Qin 판단에 사용)" — 38.331 BFR 절에서 직접 사용 여부 불분명 | RLM(Radio Link Monitoring)용 IE이고 BFR과는 별개의 RLM 임계값. GPT 표가 "BFD detection 쪽" 카테고리에 포함시킨 것은 부정확 매핑 | ⚠️ **부정확 매핑** (낮은 위험) |
| GPT | "ssb-perRACH-Occasion / ra-ssb-OccasionMaskIndex"가 BFR 전용 파라미터인 듯 표기 | 이들은 일반 RACH config 파라미터로 BFR에서도 재사용되는 것이지 BFR 전용 아님 | ⚠️ **모호한 분류** |
| GPT | "rsrp-ThresholdSSB" SSB 후보 beam threshold | 권위 출처와 일치 | ✅ 정확 |
| Claude | `T_recovery < 80 ms (typical FR2)` (§6.1.4 Test Configuration 예) | 38.133 RAN4 표에서 FR2 PCell BFR T_recovery는 condition별 60~80ms 범위 — typical 표기로는 위험 낮음 | ⚠️ **typical 표기** — 표준 본문 절대값 아님, 주의 |
| Claude | `L1-RSRP threshold -110 dBm (default)` | -110 dBm은 RSRP-Range 타입의 한 enumerated 값일 뿐 default 값은 spec에 명시 없음. RRC가 설정하는 값 | ⚠️ **default 표기 부정확** — RRC 설정값이지 default 아님 |
| Claude | "Rel.16+ 최대 64 RS (BFD-RS list)" | 38.331 RadioLinkMonitoringConfig는 일반적으로 maxNrofFailureDetectionResources 8 (Rel-15) 정도로 알려져 있음. 64는 candidate beam RS list 한계와 혼동 가능 | ⚠️ **혼동 가능** — BFD-RS와 candidate RS 한계 혼합 의심 |
| Claude | "BFR MAC CE LCID 47 (Truncated), LCID 48 (Full)" | 38.321 LCID 표에서 BFR MAC CE LCID는 release별로 다름. Rel-16 SCell BFR MAC CE는 확인 필요 (정확/부정확 단정 어려움) | ⚠️ **검증 필요** — 공식 LCID 표 대조 필요 |
| Claude | "WID: RP-201305 (NR_eMIMO_2 / Mobility enhancements)" | RP-201305는 실제 WID 번호이지만 정확한 매핑은 RAN plenary 의사록 확인 필요 | ⚠️ **검증 필요** — WID 번호 외부 검증 권장 |
| Claude | `BeamFailureRecoveryConfig`의 `rootSequenceIndex-BFR INTEGER (0..137)` | 38.331 §6.3 ASN.1 본문 직접 대조 필요. 일부 필드는 정확하나 구체 INTEGER 범위는 검증 필요 | ⚠️ **부분 검증 필요** |

**Claude의 hallucination 위험도**: 단정적 hallucination(완전 가짜) 0건이지만 typical/default 표기로 위장된 표준 외 값 다수. 사용자가 표준 회의에서 직접 인용 시 검증 필수.

**GPT의 hallucination 위험도**: 정량값 회피 전략으로 위험 낮음. 단 파라미터 카테고리 매핑 부정확이 있어 BFR 전용 파라미터 식별 시 혼동 가능.

---

## 3gpp-tracer 개선 시사점

> tracer가 GPT/Claude 수준의 정량값 답변을 제공하려면 어떤 시스템 보강이 필요한가? D/O/R 분류 기준.

### 1. Chunk preview 컷오프 확장 (P1, R)
- **현황**: `text_preview` / `content_preview` 600자 → 38.213 §6 BFD 정의 chunk가 retrieve되어도 BLER 10%/2% 본문이 컷오프 뒤에 위치 → 답변 불가
- **개선**: preview 600 → 2000자 확장. 또는 답변 단계에서 chunk full text 별도 호출 fallback
- **영향**: Q_out/Q_in BLER, 38.133 표 ms 절대값, 38.321 BFI_COUNTER 만기 분기 등 **3가지 정량값 카테고리 동시 해소**

### 2. 38.331 IE 단위 chunking + KG IE 노드 (P1, R+O)
- **현황**: 38.331 §6.3 IE block이 sectionTitle과 분리되지 않아 IE 본문 dense retrieval 약함. KG도 절(clause) 단위만, IE 단위 노드 부족
- **개선**:
  - (R) IE chunk를 `chunk_type=asn1_ie`로 표기 + IE-name을 임베딩 텍스트 prefix에 명시
  - (O) phase-3에서 `RRCParameter` 노드 추출 + `BeamFailureRecoveryConfig → 38.321 §5.17 [:REFERENCES_CLAUSE]` edge
- **영향**: `n1~n10`, `pbfd1~pbfd10`, `sl1~sl80` enumerated 범위 인용 가능

### 3. 38.133 RRM 표 행(row) 단위 chunking (P1, R)
- **현황**: 표 8.18.2.2-1 / 8.5B.2.2-1 / 8.5D.3.2-1이 표 단위로 한 chunk → preview 컷오프로 첫 행만 노출
- **개선**: table-row chunking + row 메타데이터(FR1/FR2/N=2/4/6/8 + ms 값)
- **영향**: ms 절대값 인용 가능 → 38.133 latency budget 답변 가능

### 4. FFS 마커 chunk 필터링 또는 우선순위 강하 (P2, R)
- **현황**: 38.533 §7.5.6.1.2 같은 *Editor's note: incomplete, FFS* 마커 포함 chunk가 top-1 hit
- **개선**: chunk metadata `is_ffs_placeholder=true` 또는 retrieval ranker에서 -score
- **영향**: 38.533 시험 정량값 답변 가능 (단 spec 자체 미완성 부분은 해소 불가)

### 5. RP-WID 별도 컬렉션 신설 (P2, R)
- **현황**: RP-* TDoc(plenary 단계 WID)가 별도 컬렉션 미적재 → BFR 도입 결정 본문 직접 인용 불가
- **개선**: `ranX_rp_tdocs` 컬렉션 신설
- **영향**: Release 도입 동기 evidence 강화

### 6. 38.213 §6 BLER 정의 임베딩 보강 (P2, R)
- **현황**: "hypothetical PDCCH BLER 10%" 본문이 spec-trace에서 top score 0.33으로 매우 낮음
- **개선**: chunk 메타데이터에 "hypothetical BLER", "Q_out_LR", "Q_in_LR" 키워드 명시 prefix
- **영향**: 정확한 BLER 정의 chunk가 top-1로 회수

### ★ tracer가 GPT/Claude처럼 정량값을 답하려면? (구체 행동)
1. **즉시(P1)**: preview 600 → 2000자 확장 — 1줄 config 수정, 즉시 효과
2. **단기(P1)**: 38.331 IE 단위 chunking + IE 메타데이터 prefix — phase-3 chunking 스크립트 개선 1주
3. **중기(P1)**: 38.133 표 행 단위 chunking — phase-7 table 처리 로직 추가 1~2주
4. **중기(P2)**: KG IE→Procedure REFERENCES_CLAUSE edge — phase-3/4 cross-spec 추출 추가
5. **장기(P2)**: FFS 마커 필터 + RP-WID 별도 컬렉션 — 데이터 큐레이션

→ 위 1~3만 적용해도 Q3 정량값 6개 중 4~5개 답변 가능 (Q_out/Q_in BLER, n1~n10, pbfd1~pbfd10, ms row).

---

## 실무 활용 결론

| 사용 시나리오 | 추천 모델 | 근거 |
|---|---|---|
| **표준 회의에서 직접 인용 (3GPP CR 작성, RAN1/2 contribution)** | **3gpp-tracer** | chunkId·TDoc#·spec section verbatim 인용 → traceable. hallucination 0. 단, 정량값 직접 답변 부족 시 별도 chunk full text 호출 필요 |
| **정량값(BLER %, enumerated 범위, ms)이 핵심인 빠른 조회** | **Claude** | 정량값 가장 풍부. 단 `T_recovery < 80ms typical`, `-110 dBm default` 같은 typical/default 표기는 권위 출처 재검증 필수. 표준 인용 시 spec 본문 확인 필요 |
| **비전문가 onboarding / 절차 개요 학습** | **GPT** | 도식 명료, 한국어 가독성 우수. 정량값 답변 부족하지만 절차 구조 파악에는 적절. Hallucination 위험 낮음 |
| **Spec 깊이 있는 분석 (BFR MAC CE 포맷, ASN.1, Multi-TRP 진화)** | **Claude** | BFR MAC CE octet 포맷·LCID 분기·ASN.1 IE 3개·Rel-15→18 진화 가장 깊음. 검증 필요 항목은 표시 |
| **Cross-doc linkage 분석 (38.331↔38.321↔38.213↔38.133↔38.533)** | **tracer 또는 Claude** | tracer는 spec 본문 "See also TS 38.321 [3], clause 5.17" 직접 인용으로 강함. Claude는 4-Checkpoint 매트릭스로 구조화 강함. 두 답변 결합이 이상적 |

**결론**:
- **인용 traceability + 권위 보장이 우선 → tracer**.
- **정량값 + 절차 깊이가 모두 필요 → Claude (단 typical 값은 권위 재검증)**.
- **빠른 explanation (개론) → GPT (단 정량값은 별도 출처 확인)**.
- **이상적 워크플로**: tracer로 권위 인용 확보 → Claude로 정량값/구조 보강 → GPT로 명료성 점검.

---

## 부록: 정량값 답변 풍부도 vs Citation Integrity 트레이드오프

| 모델 | 정량값 답변 (6항목 중 정확/부분/미답) | Citation Integrity | 종합 강점 |
|---|---|---|---|
| tracer | 0 정확 / 3 부분 / 3 미답 | 16/16 권위 검증 | **Trust** — 표준 회의 인용 가능 |
| GPT | 0 정확 / 0 부분 / 6 미답 | 0건 | **Clarity** — 개론 가독성 |
| Claude | 3 정확 / 1 부분 / 1 미답 / 1 추정 | ASN.1 인용은 풍부하나 chunk-level 0 | **Depth** — 정량값 + 학술 구조 |

→ tracer는 trade-off에서 **trust 우선** 전략을 모범적으로 실천. Claude는 **depth 우선**, GPT는 **clarity 우선**. 실무에서는 사용자 의도(인용 vs 학습 vs 깊이)에 따라 선택.
