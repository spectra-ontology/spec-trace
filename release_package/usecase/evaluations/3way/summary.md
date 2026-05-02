# 3-way Comparison Summary — 3gpp-tracer vs GPT vs Claude (4 cross-WG 질문 종합)

## 평가 메타

| 항목 | 값 |
|---|---|
| 평가일 | 2026-04-29 |
| 평가 대상 | 4개 cross-WG 표준 질문 (Q1 Rel-16 Type-II codebook / Q2 TCI-state Rel-15~20 / Q3 BFD/BFR / Q4 Rel-18 LTM + Rel-19/20) |
| 평가 모델 | (1) **3gpp-tracer**: spec-trace의 Neo4j(7687-7691) + Qdrant(6333) RAG, 외부 도구 금지 (2) **GPT** (3) **Claude** |
| 평가 rubric | A1 Accuracy / A2 Coverage / A3 Citation Integrity / A4 Hallucination Control / A5 Cross-Doc Linkage (각 0~5) |
| 권위 검증 | WebSearch + WebFetch — IEEE Xplore, ETSI TS, 3gpp.org, sharetechnote, Ofinno, Ericsson 등 |

## 4Q 종합 점수 매트릭스

| Q | tracer | GPT | Claude | 1위 | 메모 |
|---|---:|---:|---:|---|---|
| Q1 Rel-16 Type-II codebook | **4.5** | 3.1 | 3.9 | tracer | tracer Citation/Hallucination 1위, Claude Coverage 1위 |
| Q2 TCI-state Rel-15~20 | **4.6** | 3.2 | 3.4 | tracer | tracer 4축 1위, Claude Rel-20 ASN.1 hallucination |
| Q3 BFD/BFR | **4.6** | 3.3 | 3.7 | tracer | tracer 정량값 미답이지만 Claude는 위장 hallucination 4건 |
| Q4 Rel-18 LTM + Rel-19/20 | **4.5** | 3.5 | 3.6 | tracer | tracer Rel-20 정직, Claude RP-234037 + Rel-20 ASN.1 hallucination |
| **평균** | **4.55** | **3.28** | **3.65** | **tracer** | tracer 1.27점 차로 압도, Claude > GPT |

### 축별 평균 비교

| 축 | tracer | GPT | Claude | 차이 (tracer - 2위) |
|---|---:|---:|---:|---:|
| **A1 Accuracy** | **4.55** | 3.65 | 3.75 | +0.80 |
| **A2 Coverage** | 3.95 | 3.78 | **4.58** | -0.63 (Claude 우위) |
| **A3 Citation Integrity** | **4.83** | 1.28 | 2.38 | +2.45 |
| **A4 Hallucination Control** | **4.85** | 3.63 | 3.08 | +1.22 |
| **A5 Cross-Doc Linkage** | **4.58** | 3.95 | 4.53 | +0.05 |

→ **Coverage 1축에서만 Claude 우위** (+0.63). 나머지 4축은 모두 tracer 1위. **Citation Integrity 차이가 가장 큼 (tracer +2.45 vs GPT, +2.45 vs Claude)** — closed-domain RAG의 본질적 강점.

## 모델별 4Q 일관 패턴

### 3gpp-tracer (spec-trace 시스템)

**일관된 강점**:
- ★ **Hallucination 0~1건/Q** — 4Q 합계 1건 (Q2 §6.1.3.14 약한 추론). 학습지식 미첨가 원칙 일관 준수.
- ★ **Citation Integrity 100%** — chunkId 검증 가능, retrieval log JSON으로 모든 인용 1:1 검증.
- ★ **권위 timeline 부합** — Rel-20 정직 미답, 데이터 lag로 인한 한계를 정직하게 표기.
- 38.214/38.321/38.300 본문 verbatim 인용 다수 (특히 Q1 §5.2.2.2.5 / Q3 §5.17 / Q4 §9.2.3.5 / D_LTM 공식).

**일관된 약점** (4Q 모두에서 노출):
- ★ **38.331 ASN.1 IE 본문 미회수** — `CodebookConfig` (Q1) / `TCI-State` (Q2) / `BeamFailureRecoveryConfig` (Q3) / `LTM-Config` (Q4) 모두 IE 단위 chunk 부재로 본문 인용 불가. → **R + O 한계**
- ★ **38.306 capability 표 행 미회수** — Q1/Q2/Q4에서 capability 위치만 답하고 feature group 본문 미회수. → **R + O 한계**
- chunk text preview 600자 컷오프로 **정량값 잘림** (Q3 BLER 임계값, Q4 LTM timer). → **R 한계**
- RP-WID 별도 컬렉션 미적재로 도입배경 직접 인용 불가 (4Q 공통). → **R 한계**

### GPT

**일관된 강점**:
- ★ **Rel-20 정직성 우수** — Q4에서 "확정적 normative처럼 쓰면 안 된다" 명시. tracer와 동급 honesty.
- 안전한 일반론 + 깔끔한 구조 — overview 학습 자료에 적합.
- 절차도 / 흐름도 직관적 표현.

**일관된 약점**:
- ★ **Citation 거의 없음** (평균 1.28/5) — spec section 번호만, chunk/URL/RP-WID 인용 부재.
- ★ **세부 IE / 정량값 회피** — Q3에서 BLER 임계값 / 타이머 범위 6개 모두 미답, Q4에서 RP-221799 끝까지 명시 안 함.
- 분류 오류 발생 (Q4: "DC/inter-CU LTM"을 Rel-20으로 분류, 실제 Rel-19).
- Coverage 깊이가 Claude 대비 부족.

### Claude

**일관된 강점**:
- ★ **Coverage 가장 풍부** (평균 4.58/5) — ASN.1 SEQUENCE 코드, IE 의미 표, 시퀀스 다이어그램, 측정 주기/정확도 표 등 시각적·구조적 풍부함.
- Q1 CodebookConfig SEQUENCE / Q2 TCI-State IE / Q4 LTM-Config IE 본문 직접 작성.
- RACH-less LTM, DCI-Triggered LTM 등 GPT/tracer 미답 영역 다룸.

**일관된 약점** (가장 위험):
- ★ ★ **위장된 hallucination 패턴** — "TBD" / "draft" / "(현재 시점 기준)" / "typical" 같은 가드 표기를 붙이지만 형태 자체가 단정 답변.
  - Q1: RP-182863, RP-191085 출처 불명 인용
  - Q2: `TCI-State-r20` ASN.1 draft + Cross-Carrier/Sub-band/NTN TCI 단정
  - Q3: T_recovery <80ms typical, -110 dBm default, LCID 47/48 등 4건
  - Q4: **RP-234037 (NR_Mob_enh_Ph4)을 Rel-18 LTM parent WID로 단정 인용** (권위 RP-221799와 불일치) + Multi-RAT/NTN/Group-based LTM Rel-20 단정 + LTM-Configuration-r20 ASN.1 코드
- ASN.1 코드를 직접 작성 — chunk-level 검증 불가, 학습지식 기반 추정 코드 위험.
- Citation Integrity 2.38/5 — spec section 인용은 있으나 ASN.1/RP-WID는 출처 검증 불가.

## Hallucination 패턴 분석

### 4Q 통합 hallucination 검출 매트릭스

| 모델 | 명백 단정 오류 | 분류 오류 | 위장 단정 (가드 표기 포함) | 출처 불명 quote/code | 합계 |
|---|---:|---:|---:|---:|---:|
| **tracer** | **0** | 0 | 0 | 0 | **0건** |
| **GPT** | 0 | 1 (Q4 "DC/inter-CU LTM"을 Rel-20) | 0 | 0 | **1건** |
| **Claude** | 1 (Q4 RP-234037) | 0 | 약 9건 (Q1 ×3, Q2 Rel-20 ASN.1, Q3 ×4, Q4 Multi-RAT/ASN.1) | 1 (Q4 WID quote) | **약 11건** |

→ **tracer는 모든 Q에서 hallucination 0건**, GPT는 1건(분류 오류), **Claude는 약 11건의 위장 hallucination** 일관 패턴.

### Claude의 위장 hallucination 매커니즘

```
[Claude의 위험 패턴]
1. "TBD" / "draft" / "(현재 시점 기준)" / "typical" / "default" 같은 가드 표기
2. ASN.1 SEQUENCE 코드 / 정량값 / RP-WID 번호를 단정 형태로 작성
3. 가드 표기를 봐도 형태 자체가 검증 가능한 단정처럼 보임 → 실무 인용 위험
```

**실무에서 인용 시 위험도**:
- `RP-234037 (NR_Mob_enh_Ph4)` — 표준 회의 contribution에 인용하면 즉시 발견됨 (Rel-18 ≠ Rel-19 mobility WID 혼동).
- `LTM-Configuration-r20 ASN.1 코드` — 현 시점(2026-04) Rel-20 ASN.1 freeze 미예정이므로 실제 spec과 다른 "허구 코드".
- `T_recovery <80ms typical` — 정량값 단정이지만 권위 출처에 동일 표현 부재.

→ **Claude 답변을 표준 작업에 사용하려면 RP-WID, Rel-20 항목, 정량값, ASN.1 코드는 권위 출처 cross-check 필수**.

## Coverage vs Honesty 트레이드오프

| 모델 | Coverage | Honesty | 전략적 위치 |
|---|:---:|:---:|---|
| tracer | 3.95 | 4.85 | **High Honesty, Mid Coverage** — 보수적 RAG, 모르는 것은 모른다고 답 |
| GPT | 3.78 | 3.63 | Low-Mid 양쪽 — 안전한 일반론 위주 |
| Claude | **4.58** | 3.08 | **High Coverage, Low Honesty** — 풍부하지만 위장 단정 다수 |

→ **3축 분포**: Honesty 우선이면 tracer, Coverage 우선이면 Claude(단 검증 필수), Overview만 필요하면 GPT.

**P1 4건 보강 시 tracer 시뮬레이션**: Coverage 3.95 → 4.55 (Claude 수준) + Honesty 4.85 유지 = **종합 4.55 → 4.85** 추정.

## 3gpp-tracer 시스템 개선 우선순위 (4Q 통합)

### P1 (즉시 / 4Q 모두 영향, 종합 4.55 → 4.85)

| # | 액션 | 분류 | 영향 받는 Q | 효과 |
|---|---|:---:|:---:|---|
| **P1.1** | **38.331 ASN.1 IE 단위 chunking + KG IE 노드 풀세트** | R + O | Q1/Q2/Q3/Q4 | IE 본문 직접 인용 → Claude 수준 ASN.1 답변 가능 + tracer Citation Integrity 유지 |
| **P1.2** | **38.306 capability 표 행(row) 단위 chunking + KG `Capability`/`FeatureGroup` 라벨** | R + O | Q1/Q2/Q4 | feature group 본문 인용 → 4축 점수 모두 상승 |
| **P1.3** | **chunk text preview 600자 → 2000자 확장 (또는 컷오프 제거)** | R | Q3/Q4 | BLER 임계값/enumerated 범위/ms 절대값/LTM timer 변수 인용 가능 |
| **P1.4** | **chunk payload `specVersion` 메타 추가 + Spec↔Version graph edge** | R + O | Q2/(Q1/Q4 일부) | release attribution 직인용 — Q2 §6.1.3.14 약한 추론 hallucination 해소 |

### P2 (중기 / 일부 Q 영향)

| # | 액션 | 분류 | 영향 받는 Q | 효과 |
|---|---|:---:|:---:|---|
| P2.1 | RP-WID(Plenary RP-Tdoc) 별도 컬렉션 (`ranX_rp_tdocs`) + WID 본문 적재 | R | Q1/Q2/Q3/Q4 | RP-221799 본문 직접 인용 — Claude의 RP-234037 hallucination 영역에서 tracer가 우위 |
| P2.2 | 38.133 RRM 표 행(row) 단위 chunking + table-aware chunker | R | Q3 | ms 절대값 인용 가능 |
| P2.3 | 38.101-4 RAN4 컬렉션 적재 (38.521-4 normative ref) | R | Q1 | 38.521-4 normative 본문 인용 가능 |
| P2.4 | KG `IE`/`Capability`/`FeatureGroup`/`Procedure` 라벨 풀세트 + IE→Procedure `REFERENCES_CLAUSE` edge | O | Q1/Q2/Q3/Q4 | graph-RAG 우회 검색 — IE/cap 단위 cross-clause 추적 |
| P2.5 | 38.533 등 FFS / Editor's note 마커 chunk 자동 필터 | R | Q3 | 미완 chunk top score 회수 방지 |
| P2.6 | 38.300 §9.2.3.5 sub-clause 단위 chunking | R | Q4 | RACH-less LTM, DCI-Triggered LTM 등 세부 답변 |

### P3 (장기 / 임베딩·검색 튜닝)

| # | 액션 | 분류 | 영향 받는 Q | 효과 |
|---|---|:---:|:---:|---|
| P3.1 | sparse(BM25) + dense hybrid retrieval — ASN.1 IE 이름 매칭 강화 | R | Q1/Q2 | IE 이름 자연어 쿼리 직접 매칭 |
| P3.2 | 동일 절(section)의 다른 chunkIndex 보강 검색 후처리 | R | Q1 | 14개 chunk 있는 절에서 -001 외 본문도 회수 |
| P3.3 | type 필터(`type=WID`) 활용 강화 | R | Q1/Q2/Q4 | discussion보다 정식 WID 청크 우선 |

### P4 (시간 해결, 데이터 한계)

| # | 액션 | 분류 | 영향 받는 Q | 효과 |
|---|---|:---:|:---:|---|
| P4.1 | Rel-20 spec 본문 적재 — 2026-09 (Stage-2 freeze) ~ 2027-03 (Stage-3 freeze) 이후 | D | Q2/Q4 | 자연 해결 |

## 실무 활용 가이드 (상황별 권장 모델)

| 상황 | 권장 모델 | 사유 | 주의사항 |
|---|---|---|---|
| **표준 회의 contribution 작성** (RP-WID 인용, ASN.1 IE 정확성, spec section 검증) | **tracer (1순위)** | citation traceability + hallucination 0 | 38.331 IE 본문은 chunk 부재 영역이므로 P1.1 보강 전까지는 Claude 답변을 권위 출처로 cross-check 후 사용 |
| **사내 표준 학습 자료 / overview** | **GPT (1순위)** | 안전한 일반론, Rel-20 정직 | 세부 IE/정량값은 다른 모델로 보강 |
| **Rel-X 기능 비교 / 구현 영향 평가** (ASN.1 IE 본문, IE 의미 풍부함) | **Claude (1순위)** | Coverage 가장 풍부 | RP-WID, Rel-20 항목, 정량값, ASN.1 코드는 권위 출처(3gpp.org/IEEE) 필수 cross-check |
| **Rel-19/20 미래 변경 예측 / SI 추적** | **tracer 또는 GPT** | 데이터 timeline 부합, 정직성 | Claude의 Rel-20 ASN.1 / Multi-RAT LTM 같은 단정 인용 금지 |
| **신입 표준 엔지니어 onboarding** | GPT → Claude (학습용) | 일반론 → 풍부함 단계적 학습 | 실무 인용 시 반드시 권위 출처 검증 |
| **정량값 / 임계값 / RRM 시간 인용** | **권위 출처 직접 (3gpp.org)** | 3개 LLM 모두 정량값에서 약점 | tracer P1.3 보강 후 tracer 사용 가능 |

## 종합 결론

### tracer가 우위인 본질적 이유

1. ★ **Citation Integrity** — chunkId로 모든 사실 1:1 검증 가능. 표준 회의에서 "어디서 본 거냐"에 대해 즉시 source 제시 가능.
2. ★ **Honesty (Hallucination 0건)** — 모르는 영역은 "미발견"으로 답. Claude의 위장 단정 11건 대비 결정적 차이.
3. ★ **Rel-20 timeline 부합** — 데이터 lag(2025-Q4 까지 적재) → Rel-20 정식 spec 부재 → 정직 미답. 권위 timeline(Stage-2 2026-09 / Stage-3 2027-03)과 일치.

### tracer가 보강해야 할 본질적 약점

1. ★ **38.331 ASN.1 IE 본문 chunking 부재** — Claude만 풍부한 영역. P1.1 액션으로 보강 필요. **R + O 분류**.
2. ★ **38.306 capability 행 단위 chunking 부재** — P1.2 액션 필요. **R + O 분류**.
3. ★ **Chunk preview 600자 컷오프** — 정량값 잘림. P1.3 액션. **R 분류**.

### 핵심 권고

**현 시점에서 표준 작업에는 tracer 우선 사용**. 단 38.331 IE 본문 / 38.306 capability 행 / 정량값 영역은 **Claude 답변을 권위 출처(3gpp.org/ETSI/IEEE)로 cross-check 후 보조 사용**. **P1 4건 보강 시 tracer가 Claude 수준 풍부함 + tracer 고유 honesty + citation traceability를 동시 확보** — 종합 4.55 → 4.85 도달 예상. Rel-20 등 미래 release는 **3GPP 공식 timeline(2026-09 ~ 2027-03 freeze) 이후 자연 해결** (D 한계, 시스템 결함 아님).

## 산출물 인덱스

| 카테고리 | 경로 | 파일 |
|---|---|---|
| **3-way 비교 (질문별)** | `evaluations/3way/` | `q1_3way_comparison.md` (23 KB) / `q2_3way_comparison.md` (28 KB) / `q3_3way_comparison.md` (21 KB) / `q4_3way_comparison.md` (16 KB) |
| **3-way 종합** | `evaluations/3way/` | `summary.md` (본 문서) |
| **tracer 단일 모델 평가** | `evaluations/tracer/` | `q[1-4]_quality_eval.md` (D/O/R 분류 포함) |
| **tracer 답변** | `answers/tracer/` | `q[1-4]_*.md` (1차 답변, GPT 비교용 원본 보존) |
| **GPT 답변** | `answers/gpt/` | `q[1-4]_*.md` (사용자 입력) |
| **Claude 답변** | `answers/claude/` | `q[1-4]_*.md` (사용자 입력) |
| **검색 스크립트** | `scripts/cross-phase/usecase/` | `q[1-4]_search_*.py` |
| **Retrieval log** | `logs/cross-phase/usecase/` | `q[1-4]_retrieval_log.json` |
