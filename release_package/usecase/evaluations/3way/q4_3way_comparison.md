# Q4 3-way 비교 — Rel-18 LTM (L1/L2 Triggered Mobility) + Rel-19/20

> **작성 경위**: Q4 비교 작업이 sub-agent에서 두 차례 API 에러로 중단되어 메인 컨텍스트에서 직접 작성됨. 답변 라인 수 합계 1,358줄(tracer 259 + GPT 406 + Claude 693)이 sub-agent 컨텍스트 한계 초과.

## 메타

| 모델 | 파일 | 라인 | 인용 형식 | 외부 도구 |
|---|---|---:|---|---|
| 3gpp-tracer | `answers/tracer/q4_ltm_rel18.md` | 259 | `[chunkId, tdoc 메타]` + Neo4j Cypher 카탈로그 | RAG only (Qdrant + Neo4j) |
| GPT | `answers/gpt/q4_ltm_rel18.md` | 406 | spec section 번호 (chunkId/URL 없음) | 학습 지식 |
| Claude | `answers/claude/q4_ltm_rel18.md` | 693 | spec clause + ASN.1 코드 블록 + 표 | 학습 지식 |

## 5축 점수 비교 (각 0~5)

| 축 | tracer | GPT | Claude | 1위 | 코멘트 |
|---|---:|---:|---:|---|---|
| **A1 Accuracy** | **4.5** | 4.0 | 3.5 | tracer | tracer는 retrieved chunk verbatim. GPT는 일반론 합리적이나 RP-WID 누락. Claude는 RP-234037 인용으로 정확성 의심 (권위 RP-221799와 불일치) |
| **A2 Coverage** | 4.0 | 4.0 | **4.7** | Claude | Claude가 가장 풍부 — IE/MAC-CE/RACH-less LTM/DCI-Triggered LTM 등 폭넓게 다룸. tracer는 38.306 capability 위치만, GPT는 깊이 일반론. |
| **A3 Citation Integrity** | **4.3** | 1.5 | 2.5 | tracer | tracer는 retrieval log로 30/30 사실 실재(chunkIndex 4건 표기 오기 외 100%). GPT는 spec section 번호만 일부 인용. Claude는 ASN.1 코드 블록을 직접 작성하여 검증 불가 + RP-234037 의심 인용. |
| **A4 Hallucination Control** | **4.9** | 4.0 | 3.0 | tracer | tracer는 Rel-20 "discussion 단계만, spec 반영 미발견" 정직 표기. GPT도 "Rel-20은 진행 중이므로 확정적 normative처럼 쓰면 안 된다"고 명시(우수). Claude는 RP-234037 + Rel-20 LTM-Configuration-r20 ASN.1 코드까지 작성 — 위장된 hallucination 다수. |
| **A5 Cross-Doc Linkage** | **4.6** | 4.0 | 4.5 | tracer | tracer는 6 spec 흐름을 다이어그램 + retrieved chunk로 입증. Claude는 시퀀스 다이어그램 + 표로 풍부하게 매핑. GPT는 §3 "문서 간 연결 구조"로 깔끔하지만 깊이 약함. |
| **종합** | **4.5** | **3.5** | **3.6** | **tracer** | tracer 우위, Claude 풍부함 + 위장 hallucination, GPT 안전한 일반론. |

## Release × 문서 매트릭스 (Rel-18/19/20 × 6 spec)

| Rel | 38.300 | 38.331 | 38.321 | 38.214 | 38.133 | 38.306 |
|---|---|---|---|---|---|---|
| **Rel-18** | T:✅ §9.2.3.5/.7 chunk verbatim<br>G:✅ 일반 절차도<br>C:✅ Architecture + Cell Group 관계 | T:✅ §5.3.5.18.1/.3/.8 + IE 18개 KG<br>G:✅ §5.3.5.X 명시<br>C:✅ ASN.1 코드 풍부 (검증 필요) | T:✅ §5.18.35/36, §6.1.3.75/76 chunk<br>G:✅ MAC CE 동작 일반<br>C:✅ Field 의미 + RACH-less LTM | T:✅ §5.2.4a, §5.2.1.5.4.2<br>G:✅ Candidate cell L1<br>C:✅ Per-Cell L1 Report | T:✅ §6.3.1.2 D_LTM 공식 verbatim<br>G:⚠️ 일반 RRM 요구<br>C:✅ Measurement Period + Accuracy | T:⚠️ §5.4/§5.6 위치만<br>G:⚠️ 일반 capability<br>C:✅ feature group + IE name |
| **Rel-19** | T:⚠️ KG 동일 트리에 enhancement<br>G:✅ CLTM 명시<br>C:✅ inter-CU + CLTM | T:⚠️ §5.3.5.13.6/.13.8 노드<br>G:⚠️ 일반<br>C:✅ ASN.1 IE name 풀세트 | T:✅ §5.36 CLTM, §5.35.3.2~5 Event LTM2~5, §6.1.3.75a Enhanced<br>G:⚠️ 일반<br>C:✅ DCI-Triggered LTM | T:⚠️ TDoc R1-2405859 인용<br>G:⚠️ 일반<br>C:✅ Event-trig L1 | T:⚠️ R4-2400104 인용<br>G:⚠️ 일반<br>C:⚠️ 일반 | T:⚠️ §5.4 위치만<br>G:⚠️ 일반<br>C:⚠️ 일반 |
| **Rel-20** | T:❌ "spec 반영 미발견 (정당한 미답)"<br>G:❌ "진행 중, 확정 description 금지" 정직<br>**C:⚠️ Multi-RAT/NTN/Group LTM (검증 필요)** | T:❌<br>G:❌<br>**C:⚠️ LTM-Configuration-r20 ASN.1 코드 (TBD 표기 있으나 위험)** | T:❌<br>G:⚠️ "lower-layer mobility 확장"<br>**C:⚠️ AI/ML LTM** | T:❌<br>G:⚠️<br>C:⚠️ | T:❌<br>G:⚠️<br>C:⚠️ | T:❌<br>G:⚠️<br>C:⚠️ |

**해석**: Rel-18 6칸은 3개 모델 모두 ✅ 답변. Rel-19도 대체로 충실. **Rel-20은 분기점** — tracer/GPT는 정직하게 미답 또는 study 단계 명시, Claude는 추정으로 채움.

## ★ Rel-20 처리 비교 (가장 중요한 hallucination 분기점)

| 모델 | Rel-20 답변 방식 | 정직성 | 권위 verdict |
|---|---|---|---|
| **tracer** | "RAN2#132 discussion 단계만 적재, spec 반영 미발견" — RAN2 토론 chunk(R2-2508706/-2508384/-2508657) 직접 인용으로 6G mobility framing까지만 답 | ★ 매우 정직 | ✅ 권위 timeline (Stage-2 freeze 2026-09 / Stage-3 freeze 2027-03)과 부합 |
| **GPT** | "Rel.20은 진행 중인 영역이므로 확정적인 normative description처럼 쓰면 안 된다. 다만 공개 scope와 draft CR을 기준으로 하면..." 명시 후 방향만 6개 항목으로 제시 | ★ 매우 정직 | ✅ 정직성 우수, "DC/inter-CU LTM"이 Rel-19에 이미 도입된 점은 약간 혼선 |
| **Claude** | "9.1 Rel.20 SI/WI 진행 (현재 시점 기준)" 항목으로 4개 작업(Multi-RAT LTM / NTN LTM / Group-based LTM / AI/ML LTM) 단정 + "9.2 잠재적 RRC 확장 (TBD)" 항목으로 ASN.1 코드 작성 | ⚠️ 위장된 단정 | ❌ 4개 항목 권위 출처에서 검증 안 됨, ASN.1 코드는 학습지식 기반 추정 |

**핵심**: Rel-20 처리에서 **tracer/GPT는 모범적 honesty**, Claude는 "진행 중", "TBD" 표기로 위장한 단정 답변. 실무에서 Claude의 RP-234037, Multi-RAT LTM, LTM-Configuration-r20 ASN.1을 그대로 인용하면 표준 회의 제출 시점에 문제 발생.

## 항목별 차분 (Rel-18 핵심 + Rel-19/20)

| 항목 | tracer | GPT | Claude | 비고 |
|---|---|---|---|---|
| **Rel-18 도입배경 RP** | RP-221799를 R2-2207340의 reference 형태로 인용 ✅ | RP 번호 없이 latency 동기만 ⚠️ | **RP-234037 (NR_Mob_enh_Ph4)** 단정 인용 ❌ | tracer가 권위 일치 |
| **38.300 §9.2.3.5 LTM 절차** | chunk verbatim "MAC CE로 cell switch + Subsequent LTM" ✅ | "candidate cell pre-config + MAC CE 빠른 switch" 일반 ✅ | Architecture + Cell Group + RACH-less ✅ | 3개 모두 핵심 일치, Claude가 가장 풍부 |
| **38.331 LTM-Config IE** | §5.3.5.18.1 chunk + IE 18개 카탈로그 ✅ | LTM-Config 명시 + IE 일부 ⚠️ | ASN.1 SEQUENCE 코드 + IE 의미 표 ✅ | Claude 풍부, 단 ASN.1 일부 검증 어려움 |
| **38.321 MAC CE** | §5.18.35 LTM Cell Switch + §5.18.36 Candidate TCI 본문 verbatim ✅ | MAC CE 동작 일반 + 절차 그림 ⚠️ | Field 의미 + RACH-less LTM + DCI-Triggered LTM ✅ | tracer가 chunkId 검증 가능, Claude는 풍부하지만 일부 가설 |
| **38.214 L1 measurement** | §5.2.4a + §5.2.1.5.4.2 chunk verbatim ✅ | candidate cell L1 일반 ⚠️ | Per-Cell L1 Report + L3 Filtering 우회 ✅ | Claude가 가장 자세 |
| **38.133 D_LTM** | §6.3.1.2 D_LTM = T_cmd + T_LTM-interrupt 공식 verbatim, §8.20.2 PSCell 분해 ✅ | 일반 RRM 요구 ⚠️ | Measurement Period + Accuracy 표 ✅ | tracer가 공식 정확 |
| **38.306 capability** | §5.4/5.6 위치만, 본문 미회수 (정직 표기) ⚠️ | 일반 capability ⚠️ | feature group + IE name ✅ | Claude가 가장 자세 (단 검증 필요) |
| **Rel-19 inter-CU LTM** | R2-2404271 + KG §5.36 CLTM ✅ | "DC/inter-CU LTM" Rel-20으로 잘못 분류 ⚠️ | inter-CU 명시 ✅ | tracer/Claude 정확, GPT 분류 오류 |
| **Rel-19 CLTM** | R2-2408088 + KG §5.36 ✅ | CLTM 별도 항목 + condition-based 정확 ✅ | CLTM 명시 + RP-241917 (?) | 3개 모두 답변 |
| **Rel-19 event-trig L1** | R2-2505117 + KG §5.35.3.2~5 Event LTM2~5 ✅ | 언급 없음 ❌ | Event-trig L1 + DCI-Triggered ✅ | GPT 누락 |
| **Rel-20 spec 본문** | "discussion 단계만, spec 반영 미발견" 정직 ⚠️ | "진행 중, normative처럼 쓰면 안 됨" 정직 + 방향 6항목 ⚠️ | Multi-RAT/NTN/Group LTM 단정 + ASN.1 코드 ❌ | **Claude만 hallucination** |

## 강점 / 약점 (모델별)

### 3gpp-tracer
**강점**:
- ★ Citation Integrity 100% 검증 가능 (chunkId 30건 retrieval log 실재)
- ★ Hallucination 0건 — Rel-20 정직 표기로 권위 timeline과 부합
- 38.214 §5.2.4a / §5.2.1.5.4.2 / 38.133 §6.3.1.2 D_LTM 공식 / 38.321 §5.18.35-36 / 38.300 §9.2.3.5 모든 핵심 chunk verbatim
- Neo4j KG 카탈로그로 IE 18개 + MAC CE 6개 + RRM 시험 56개 위치 정확 확보

**약점**:
- 38.306 LTM 세부 feature group 본문 미회수 (위치만) → R+O 한계
- LTM 전용 timer (T-LTM) 본문 미발췌 → R 한계 (preview 컷오프)
- RP-WID 본문 직접 인용 불가, discussion reference로 우회 → R 한계
- chunkIndex 표기 4건 오기 (R2-2503785-001 → 실제 -017 등) → 작성 워크플로우

### GPT
**강점**:
- ★ **Rel-20 처리에서 모범적 정직성** — "확정적 normative처럼 쓰면 안 된다" 명시
- 도입 배경 일반론 + 깔끔한 코드블록 흐름도 → 빠른 이해 도움
- 절차 일반론 / 핵심 개념 매우 합리적

**약점**:
- ★ Citation 거의 없음 — spec section 번호 일부만, chunk/URL 없음
- ★ Rel-18 WID 번호 인용 누락 (RP-221799를 끝까지 명시 안 함)
- "DC/inter-CU LTM"을 Rel-20으로 분류 (실제 Rel-19에 도입)
- Rel-19 event-trig L1 measurement (Event LTM2~5) 누락
- 정량값/세부 IE 거의 없음 — 일반론 위주

### Claude
**강점**:
- ★ **Coverage 가장 풍부** — RACH-less LTM, DCI-Triggered LTM, Resource Mapping, L3 Filtering 우회 등 GPT/tracer가 안 다룬 영역
- ★ 38.331 IE를 ASN.1 SEQUENCE 코드 형태로 풍부하게 작성
- Architecture + Cell Group 관계 + 측정 주기/정확도 표 등 시각적 풍부함
- 6 spec 모두 비교적 깊이 다룸

**약점**:
- ★ ★ **WID hallucination**: "RP-234037 (NR_Mob_enh_Ph4)"을 Rel-18 LTM parent WID로 단정 인용 — 권위(IEEE Xplore 10744020 / 3GPP RP-241917) 모두 RP-221799를 Rel-18 LTM parent로 확인. RP-234037은 Phase-4 = Rel-19 가능성.
- ★ ★ **Rel-20 위장된 단정**: Multi-RAT LTM / NTN LTM / Group-based LTM / AI/ML LTM을 "(현재 시점 기준)" 표기로 단정. LTM-Configuration-r20 ASN.1 코드 작성 ("TBD" 라벨 있으나 형태 자체가 위험).
- WID 인용문도 ASN.1 코드 등 직접 인용 형태이지만 출처 불명 — 검증 불가
- chunk-level 출처 없음

## Hallucination 검출

| 모델 | 의심 사실 | 권위 검증 | verdict |
|---|---|---|---|
| **tracer** | (없음) | 30/30 retrieval log 실재 | **0건** ✅ |
| **GPT** | "DC/inter-CU LTM"을 Rel-20 항목으로 분류 | inter-CU LTM은 Rel-19 work item (RP-241917 검증) | ⚠️ 분류 오류 1건 |
| **GPT** | RP-WID 번호 누락 | (생략은 hallucination 아님) | OK (정직한 회피) |
| **Claude** | "RP-234037 (NR_Mob_enh_Ph4)"가 Rel-18 LTM parent WID | 권위(IEEE Xplore 10744020 + Ofinno + Ericsson)는 RP-221799 → Phase-4는 Rel-19 mobility WI 가능성 | ❌ **단정 인용 오류** |
| **Claude** | Rel-18 WID 인용문 *"Specify L1/L2-based inter-cell mobility..."* | RP-221799의 실제 objective와 의미는 비슷하지만 출처가 RP-234037이라고 단 점에서 verbatim quote 신뢰 불가 | ⚠️ 출처 불명 quote |
| **Claude** | Rel-20 Multi-RAT LTM / NTN LTM / Group-based LTM | 권위 출처(3gpp.org Rel-20 page, ATIS 자료)는 "lower-layer mobility 추가 최적화" 정도. Multi-RAT/NTN/Group은 검증 안 됨 | ❌ **추정 단정** |
| **Claude** | LTM-Configuration-r20 ASN.1 코드 | Rel-20 ASN.1 freeze는 2027-03 예정 (3gpp.org timeline), 현 시점 ASN.1 부재 | ❌ **학습지식 기반 추정 코드** |

**합계**: tracer 0건 / GPT 1건(분류 오류) / **Claude 4건 (RP 번호 + WID quote + Rel-20 항목 + ASN.1)**.

## 3gpp-tracer 개선 시사점

### Claude/GPT가 더 잘 답한 영역에서 tracer가 보강할 점

1. **38.331 ASN.1 IE 본문** — Claude는 SEQUENCE 코드 풍부하게 답. tracer는 "Neo4j IE 카탈로그"만 있고 본문 chunk 미회수.
   - **개선책 (P1, R+O)**: 38.331 IE block을 별도 chunk로 분리 (sectionTitle="LTM-Config IE" / "CandidateCellInfoListLTM-r18 IE" 등). KG에 `IE` 라벨 풀세트 추가.
   - 효과: Claude 수준의 IE 본문 인용 + tracer의 chunkId traceability 결합 가능.

2. **38.306 capability feature group** — Claude는 feature group + IE name까지 답. tracer는 §5.4/§5.6 위치만.
   - **개선책 (P1, R+O)**: 38.306 capability 표 행(row) 단위 chunking. KG에 `Capability` / `FeatureGroup` 라벨 추가.

3. **Rel-19 RAN1 spec 본문 chunk** — Claude는 Rel-19 measurement enhancement 깊이 답. tracer는 RAN1 TDoc만.
   - **개선책 (P2, R)**: 2025-Q4 ~ 2026-Q1 RAN1 Rel-19 IE의 IE 단위 chunking 적용.

4. **RACH-less LTM / DCI-Triggered LTM** — Claude만 다룸. tracer/GPT 미답.
   - **개선책 (P2, R)**: 38.300 §9.2.3.5의 모든 sub-clause를 더 잘게 chunking + Rel-19 enhancement 별도 청크.

### tracer가 우위인 영역 (보존해야 할 것)

1. ★ **chunkId Citation Traceability** — Claude의 RP-234037, Rel-20 ASN.1, Multi-RAT LTM 같은 "출처 불명 단정"이 불가능한 구조. 이 강점은 P1 작업으로 보강될 때도 유지되어야 함.
2. ★ **Rel-20 정직 표기** — "discussion 단계만 적재, spec 반영 미발견"으로 추측 회피. Claude가 위장된 단정을 한 영역에서 tracer만 유일하게 honesty 유지.
3. ★ **권위 timeline과 일치** — Stage-2 freeze 2026-09, Stage-3 freeze 2027-03 — 이 timeline에 부합하게 답변. Claude는 timeline을 무시하고 ASN.1 작성.

### tracer가 Claude처럼 풍부하게 답하면서도 정직성을 유지하려면?

| 액션 | 분류 | 효과 |
|---|---|---|
| **P1.1**: 38.331 IE 단위 chunking + KG IE 노드 풀세트 | R+O | IE 본문 직접 인용 가능 → A2 Coverage 4.0 → 4.7 (Claude 수준) |
| **P1.2**: 38.306 capability 표 row chunking | R+O | feature group 인용 가능 → 4축 모두 1점 상승 |
| **P1.3**: chunk preview 600 → 2000자 | R | LTM timer 본문 + 정량값 인용 가능 |
| **P1.4**: payload `specVersion` 메타 + Spec↔Version graph edge | R+O | Rel-X별 attribution 직인용 — Claude의 "RP-234037" 같은 가짜 인용 대신 실제 RP-221799 본문 인용 |
| **P2.1**: RP-* WID 별도 컬렉션 (`ranX_rp_tdocs`) | R | 도입 배경 RP-221799 직접 인용 → Claude의 hallucination 영역에서 tracer가 우위 확보 |
| **P2.2**: 38.300 §9.2.3.5 sub-clause 단위 chunking | R | RACH-less LTM, DCI-Triggered LTM 같은 세부 답변 가능 |

**모두 적용 시**: tracer 종합 4.5 → **4.85 추정**, hallucination 0건 유지하면서 Claude의 풍부함 확보.

## 실무 활용 결론

| 상황 | 권장 모델 | 사유 |
|---|---|---|
| **표준 회의 contribution 작성** (RP-WID 인용, ASN.1 IE 정확성, spec section 번호 검증 필요) | **tracer** | citation traceability + hallucination 0 |
| **사내 표준 학습 자료 / overview** (개념 이해, 배경 latency 동기, 구조 그림) | GPT | 안전한 일반론, Rel-20 정직 |
| **Rel-X 기능 비교 / 구현 영향 평가** (ASN.1 IE 본문, IE 의미 풍부함) | Claude (단, RP-WID + Rel-20 검증 필수) | Coverage 가장 풍부하지만 hallucination 위험 |
| **Rel-20 미래 변경 예측** | **tracer 또는 GPT** | tracer는 timeline 부합, GPT는 정직한 방향 제시. Claude는 위장된 단정 위험. |

**핵심 권고**: tracer P1 4건(IE chunking + cap row chunking + preview 확장 + specVersion 메타) 보강 시, **종합 점수 4.5 → 4.85** + Claude 수준의 풍부함 + Claude가 못 가진 honesty 동시 확보. **현 시점에서 표준 작업에는 tracer 우선, 단 IE 본문 부재 영역은 Claude 답변을 권위 출처로 cross-check 후 사용 권장.**
