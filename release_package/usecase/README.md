# 3gpp-tracer Usecase Evaluation — 4 Cross-WG 질문에 대한 3-way RAG 답변 비교

## 목적

사내 모뎀 표준 엔지니어가 실무에서 던질 법한 **4개의 cross-WG 통합 질문**에 대해, **3개 시스템의 답변을 5축 rubric으로 비교 평가**한다:

1. **3gpp-tracer** — spec-trace 프로젝트의 Neo4j(7687-7691) + Qdrant(6333) RAG. 외부 툴/학습지식 절대 금지.
2. **GPT** — OpenAI GPT 답변 (사용자 입력)
3. **Claude** — Anthropic Claude 답변 (사용자 입력)

## 폴더 구조

```
docs/usecase/
├─ README.md                                 ← 본 문서
├─ answers/                                  ← 1차 답변 (모든 모델, 원본 보존)
│   ├─ tracer/                               ← 3gpp-tracer 답변 4개
│   ├─ gpt/                                  ← GPT 답변 4개
│   └─ claude/                               ← Claude 답변 4개
└─ evaluations/                              ← 평가
    ├─ tracer/                               ← 3gpp-tracer 답변 단일 모델 평가 (웹 권위 대조)
    │   └─ q[1-4]_quality_eval.md            ← D/O/R 분류 포함
    └─ 3way/                                 ← tracer vs GPT vs Claude 3-way 비교
        ├─ q[1-4]_3way_comparison.md         ← 질문별 3-way 비교
        └─ summary.md                        ← 4Q 종합 + tracer 개선 우선순위 + 실무 활용 가이드
```

## 평가 대상 4개 질문

| # | 질문 | 관련 spec | 답변 | 단일 평가 | 3-way 비교 |
|---|---|---|---|---|---|
| Q1 | Rel-16 enhanced Type-II codebook | 38.211/212/214/306/331/521-4 | [tracer](answers/tracer/q1_rel16_typeii_codebook.md) / [gpt](answers/gpt/q1_rel16_typeii_codebook.md) / [claude](answers/claude/q1_rel16_typeii_codebook.md) | [tracer_eval](evaluations/tracer/q1_quality_eval.md) | [3way](evaluations/3way/q1_3way_comparison.md) |
| Q2 | TCI-state Rel-15~Rel-20 | 38.214/321/331/306 | [tracer](answers/tracer/q2_tci_state_rel15_to_rel20.md) / [gpt](answers/gpt/q2_tci_state_rel15_to_rel20.md) / [claude](answers/claude/q2_tci_state_rel15_to_rel20.md) | [tracer_eval](evaluations/tracer/q2_quality_eval.md) | [3way](evaluations/3way/q2_3way_comparison.md) |
| Q3 | Beam Failure Detection / Recovery | 38.213/321/331/133/533 | [tracer](answers/tracer/q3_beam_failure_recovery.md) / [gpt](answers/gpt/q3_beam_failure_recovery.md) / [claude](answers/claude/q3_beam_failure_recovery.md) | [tracer_eval](evaluations/tracer/q3_quality_eval.md) | [3way](evaluations/3way/q3_3way_comparison.md) |
| Q4 | Rel-18 LTM (L1/L2 Triggered Mobility) + Rel-19/20 | 38.300/214/321/331/133/306 | [tracer](answers/tracer/q4_ltm_rel18.md) / [gpt](answers/gpt/q4_ltm_rel18.md) / [claude](answers/claude/q4_ltm_rel18.md) | [tracer_eval](evaluations/tracer/q4_quality_eval.md) | [3way](evaluations/3way/q4_3way_comparison.md) |

**시작점 권장**: [evaluations/3way/summary.md](evaluations/3way/summary.md) — 4Q 종합 + 모델별 일관 패턴 + tracer 개선 우선순위 + 실무 활용 가이드.

## 평가 워크플로우 (3 단계)

### 1차: 답변 생성 (각 모델 독립)
- **3gpp-tracer**: 멀티 에이전트 4개 병렬, OpenRouter 임베딩 + Qdrant top_k=10 + Neo4j Cypher. 외부 툴 금지, 학습지식 첨가 금지. retrieval log JSON으로 모든 인용 검증 가능.
- **GPT/Claude**: 사용자가 외부에서 동일 질문 입력 후 답변 수집.

### 2차: tracer 단일 평가 (`evaluations/tracer/`)
- 1차 답변을 권위 출처(IEEE Xplore, ETSI TS, 3gpp.org, sharetechnote, Ofinno, Ericsson)와 대조.
- 5축 점수 + Hallucination 검출 + Coverage 누락 + **D/O/R 약점 원인 분류**.

### 3차: 3-way 비교 (`evaluations/3way/`)
- tracer vs GPT vs Claude 3개 답변을 동일 5축 rubric으로 비교.
- 모델별 강점/약점 + Hallucination 검출 패턴 + tracer 개선 시사점 + 실무 활용 결론.

## 5축 평가 rubric

| 축 | 정의 | 핵심 분기 |
|---|---|---|
| **A1 Accuracy** | 권위 출처와 사실 일치 | 정량값 / RP-WID 번호 / spec section 번호 |
| **A2 Coverage** | 질문 항목 충족도 | IE 본문 / capability 행 / cross-doc 항목 |
| **A3 Citation Integrity** | 인용한 사실의 검증 가능성 | tracer chunkId / GPT-Claude spec section 번호 / ASN.1 코드 출처 |
| **A4 Hallucination Control** | 학습지식 첨가 없음 | 미발견 영역 정직 표기, Rel-20 추측 채움 회피 |
| **A5 Cross-Doc Linkage** | 문서간 매핑 정확성 | RRC IE → MAC-CE → PHY → RRM → capability 흐름 |

## 인프라 상태 / 데이터 신선도 (평가 시점 2026-04-29)

질문이 다루는 모든 spec이 적재되어 있음 사전 검증.

| Spec | 컬렉션 | chunks | 비고 |
|---|---|---:|---|
| 38.211 | `ran1_ts_sections` | 196 | |
| 38.212 | `ran1_ts_sections` | 219 | |
| 38.213 | `ran1_ts_sections` | 164 | |
| 38.214 | `ran1_ts_sections` | 214 | |
| 38.300 | `ran2_ts_sections` | 466 | |
| 38.306 | `ran2_ts_sections` | 99 | (capability 표 헤더만 노출 — R 약점) |
| 38.321 | `ran2_ts_sections` | 288 | |
| 38.331 | `ran2_ts_sections` | 562 | (절 단위 chunk, IE block 단위 미분리 — R 약점) |
| 38.133 | `ran4_ts_sections` | 7,301 | (표 행 단위 chunking 약함 — R 약점) |
| 38.521-4 | `ran5_ts_sections` | 617 | (사용자 표기 "38.512-4"는 0건, 38.521-4가 실제 spec) |
| 38.533 | `ran5_ts_sections` | 2,221 | (일부 절 FFS 마커 — D 약점) |

| WG | Neo4j 노드 | 최신 미팅 |
|---|---:|---:|
| RAN1 | 160,601 | RAN1 #123 |
| RAN2 | 141,126 | RAN2 #132 |
| RAN3 | 71,155 | RAN3 #130 |
| RAN4 | 234,022 | RAN4 #117 |
| RAN5 | 134,196 | RAN5 #110 |

전체 Qdrant ~3.7M points (20 컬렉션). 데이터 lag ≈ 6개월 (마지막 미팅 2025-Q4) — 3GPP 미팅 주기상 정상. **Rel-20 spec 본문은 timeline상 2026-09(Stage-2 freeze)~2027-03(Stage-3 freeze) 이후 적재 가능.**

## 3-way 비교 핵심 결과

### 4Q 종합 점수 매트릭스

| Q | tracer | GPT | Claude | 1위 |
|---|---:|---:|---:|---|
| Q1 Rel-16 Type-II codebook | **4.5** | 3.1 | 3.9 | tracer |
| Q2 TCI-state Rel-15~20 | **4.6** | 3.2 | 3.4 | tracer |
| Q3 BFD/BFR | **4.6** | 3.3 | 3.7 | tracer |
| Q4 Rel-18 LTM + Rel-19/20 | **4.5** | 3.5 | 3.6 | tracer |
| **평균** | **4.55** | **3.28** | **3.65** | **tracer** |

### 축별 평균 (4Q 통합)

| 축 | tracer | GPT | Claude | tracer 우위/열위 |
|---|---:|---:|---:|---|
| **A1 Accuracy** | **4.55** | 3.65 | 3.75 | +0.80 |
| **A2 Coverage** | 3.95 | 3.78 | **4.58** | -0.63 (Claude 우위) |
| **A3 Citation Integrity** | **4.83** | 1.28 | 2.38 | +2.45 |
| **A4 Hallucination Control** | **4.85** | 3.63 | 3.08 | +1.22 |
| **A5 Cross-Doc Linkage** | **4.58** | 3.95 | 4.53 | +0.05 |

**결론**: Coverage 1축에서만 Claude 우위(+0.63), 나머지 4축은 tracer 1위. **Citation Integrity 차이가 가장 큼** — closed-domain RAG의 본질적 강점.

### Hallucination 검출 (4Q 통합)

| 모델 | 명백 단정 | 분류 오류 | 위장 단정 | 합계 |
|---|---:|---:|---:|---:|
| **tracer** | 0 | 0 | 0 | **0건** |
| **GPT** | 0 | 1 | 0 | **1건** |
| **Claude** | 1 | 0 | 약 9건 | **약 11건** |

**Claude 위장 패턴**: "TBD" / "draft" / "(현재 시점 기준)" / "typical" / "default" 가드 표기를 단정 인용에 첨부 (RP-234037, Rel-20 ASN.1, Multi-RAT LTM 등). 표준 회의 인용 시 위험.

### 모델별 일관 패턴

- **tracer**: ★ Honesty 4.85 (Hallucination 0건) + ★ Citation Integrity 100% / 약점 = IE 본문·capability 행·정량값 미회수 (시스템 R/O 한계)
- **GPT**: ★ Rel-20 정직성 우수, 안전한 일반론 / 약점 = Citation 거의 없음 + 정량값/세부 IE 회피
- **Claude**: ★ Coverage 4.58 가장 풍부 (ASN.1 IE/MAC-CE 본문) / 약점 = 위장 hallucination 11건 패턴 (RP-WID 가짜 인용, Rel-20 ASN.1 추정, "typical" 정량값 단정)

## tracer 시스템 개선 우선순위 (D/O/R 분류 기반)

> **D**: 3GPP 데이터 자체 시점 한계 (시간 해결) / **O**: KG 모델링 부재 / **R**: VDB 빌드 한계

### P1 (즉시 / 4Q 모두 영향, 종합 4.55 → 4.85 추정)

| # | 액션 | 분류 | 영향 |
|---|---|:---:|---|
| **P1.1** | 38.331 ASN.1 IE 단위 chunking + KG IE 노드 풀세트 | R + O | Q1/Q2/Q3/Q4 — IE 본문 직접 인용 → Claude 수준 + tracer Citation 유지 |
| **P1.2** | 38.306 capability 표 행 단위 chunking + KG `Capability` 라벨 | R + O | Q1/Q2/Q4 — feature group 인용 가능 |
| **P1.3** | chunk text preview 600 → 2000자 확장 (또는 컷오프 제거) | R | Q3/Q4 — BLER 임계값/timer/ms 값 인용 가능 |
| **P1.4** | chunk payload `specVersion` 메타 + Spec↔Version graph edge | R + O | Q2 — release attribution 직인용 |

### P2 (중기, 일부 Q 영향)

- P2.1: RP-WID(`ranX_rp_tdocs`) 별도 컬렉션 + WID 본문 적재 (R) — 4Q 공통
- P2.2: 38.133 RRM 표 행 단위 chunking (R) — Q3
- P2.3: 38.101-4 RAN4 컬렉션 적재 (R) — Q1
- P2.4: KG `IE`/`Capability`/`Procedure` 풀세트 + IE→Procedure `REFERENCES_CLAUSE` edge (O) — 4Q 공통
- P2.5: FFS / Editor's note 마커 chunk 자동 필터 (R) — Q3

### P3 (장기, 임베딩·검색 튜닝)

- P3.1: sparse(BM25) + dense hybrid retrieval — ASN.1 IE 이름 매칭 (R)
- P3.2: 동일 절 다른 chunkIndex 보강 검색 후처리 (R)
- P3.3: type 필터(`type=WID`) 활용 강화 (R)

### P4 (시간 해결, D 한계)

- Rel-20 spec 본문 적재 — 2026-09 (Stage-2 freeze) ~ 2027-03 (Stage-3 freeze) 이후 (D)

## 실무 활용 가이드 (상황별 권장)

| 상황 | 권장 모델 | 사유 | 주의사항 |
|---|---|---|---|
| **표준 회의 contribution 작성** | **tracer (1순위)** | citation traceability + hallucination 0 | 38.331 IE 본문은 chunk 부재 영역 — Claude 답변을 권위 출처로 cross-check 후 사용 |
| **사내 표준 학습 자료 / overview** | **GPT (1순위)** | 안전한 일반론, Rel-20 정직 | 세부 IE/정량값은 다른 모델로 보강 |
| **Rel-X 기능 비교 / 구현 영향 평가** | **Claude (1순위)** | Coverage 가장 풍부 | RP-WID, Rel-20 항목, 정량값, ASN.1 코드는 권위 출처 cross-check 필수 |
| **Rel-19/20 미래 변경 예측** | **tracer 또는 GPT** | timeline 부합, 정직성 | Claude의 Rel-20 ASN.1/Multi-RAT LTM 단정 인용 금지 |
| **신입 onboarding** | GPT → Claude (학습용) | 단계적 학습 | 실무 인용 시 권위 출처 검증 필수 |
| **정량값 / RRM ms 인용** | **권위 출처 직접 (3gpp.org)** | 3개 LLM 모두 정량값 약점 | tracer P1.3 보강 후 tracer 사용 가능 |

## 결론

### tracer 우위의 본질

1. **Citation Integrity** (4.83/5) — chunkId로 모든 사실 1:1 검증 가능
2. **Honesty** (Hallucination 0건) — Claude의 위장 단정 11건과 결정적 차이
3. **Rel-20 timeline 부합** — 데이터 lag을 정직 미답으로 처리

### tracer 보강 필요 (Claude만 풍부한 영역)

1. 38.331 ASN.1 IE 본문 chunking (P1.1, R+O)
2. 38.306 capability 행 chunking (P1.2, R+O)
3. Chunk preview 컷오프 확장 (P1.3, R)

### 핵심 권고

**현 시점에서 표준 작업에는 tracer 우선**. 38.331 IE / 38.306 capability / 정량값 영역은 Claude 답변을 권위 출처로 cross-check 후 보조 사용. **P1 4건 보강 시 tracer가 Claude 풍부함 + tracer 고유 honesty + citation traceability를 동시 확보** — 종합 4.55 → 4.85 도달 예상. Rel-20 spec 본문은 timeline 자연 해결.

## 산출물 요약

```
docs/usecase/
├─ README.md                              ← 본 문서
├─ answers/  (12 files)
│   ├─ tracer/    q[1-4]_*.md
│   ├─ gpt/       q[1-4]_*.md
│   └─ claude/    q[1-4]_*.md
└─ evaluations/
    ├─ tracer/    q[1-4]_quality_eval.md  (D/O/R 포함, 4 files)
    └─ 3way/      q[1-4]_3way_comparison.md + summary.md  (5 files)

scripts/cross-phase/usecase/
├─ q[1-4]_search_*.py                     ← tracer 검색 스크립트 (재현용)

logs/cross-phase/usecase/
├─ q[1-4]_retrieval_log.json              ← tracer retrieval log (감사용)
```
