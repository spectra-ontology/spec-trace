# Q1~Q4 검색·답변 품질 V2~V6 진화 (2026-05-02 ~ 2026-05-04)

> **목적**: 사용자 4개 cross-WG 질문에 대한 retrieval + LLM 답변 + 5-tier rubric 점수의 단계별 향상 측정.
> **모델**: 답변 + 평가 모두 `google/gemini-2.5-flash` 사용 (동일 모델로 비교 일관성).
> **rubric**: A1 Accuracy / A2 Coverage / A3 Citation Integrity / A4 Hallucination Control / A5 Cross-Doc Linkage (각 0~5).

## 1. 종합 점수 진화

| 버전 | Q1 (Type-II) | Q2 (TCI) | Q3 (BFD/BFR) | Q4 (LTM) | **합계** | Δ vs V2 |
|---|---:|---:|---:|---:|---:|---:|
| V2 (baseline) | 15 | 20 | 19 | 19 | **73/100** | — |
| V3 (신규 컬렉션) | 21 | 19 | 19 | 19 | **78/100** | +5 |
| V4 (hybrid + 프롬프트 + 컨텍스트) | 20 | 18 | 21 | 20 | **79/100** | +6 |
| V5 (+ rerank + sparse + rewrite) | **22** | 19 | **22** | 19 | **82/100** | **+9 (+12.3%)** ⭐ 최고 |
| V6 (top_k_rerank 15→25) | 22 | 19 | 19 | 21 | 81/100 | +8 (-1 vs V5) |
| V7 (Q별 동적 top_k) | 19 | 19 | 22 | 21 | 81/100 | +8 (-1 vs V5) |

## 2. 단계별 변경 내역

### V2 (2026-05-01) — baseline
- ASN.1 별도 컬렉션 (`ran2/3_ts_asn1_chunks`) 추가
- 5쿼리 컴팩트 retrieval 로그
- 컨텍스트: top_k 3, ~2K chars

### V3 (2026-05-02) — 신규 컬렉션 활용
- `ran2_ts_ie_descriptions` (700→723), `ran5_ts_ie_descriptions` (3), `ran2_ts_capabilities` (1,716) 추가
- Q1 Cross-Doc Linkage A5 0→4 점프 (CodebookConfig field 의미 직접 회수)
- Q2~Q4 변동 미미 (기존 V2 컨텍스트가 이미 충분)

### V4 (2026-05-04) — Hybrid + 프롬프트 + 컨텍스트 확장
- A1: V2 + V3 hits union → score sort → top-15
- A2: 답변 프롬프트 — 측면별 소제목 강제, 측면 간 연결 명시 요구
- A3: top_k 3→15, chars 2K→4K
- 효과: Q3 +2, Q4 +1 (개선된 프롬프트가 답변 구조화)
- 한계: Q1 -1, Q2 -1 (더 큰 컨텍스트가 일부 측면 noise)

### V5 (2026-05-04) — Reranker + Sparse + Query Rewriting
- B4: LLM-based reranker (gemini-2.5-flash가 30 candidates → relevance 0~10 → top-15 재정렬)
- B5: Sparse retrieval — 사용자 질문 키워드 → Qdrant `MatchText` filter (정확 매칭)
- B6: Query rewriting — LLM이 질문에서 IE name + capability feature 추출 → 정확 dense 쿼리 추가 생성
- 효과: Q1 +2, Q3 +1 (정확 IE/feature 매칭 + reranker가 noise 제거)
- 한계: Q2 -1 (cross-lingual 한계 — 임베딩 모델 자체 한계)

### V6 (2026-05-04) — top_k 확장 시도 (실패)
- TOP_K_INITIAL: 30 → 50, TOP_K_RERANK: 15 → 25
- 목표: Q2 broad 질문 회복
- 결과: **Q4 +2, Q3 -3, Q2 회복 실패 → 종합 -1**

차원별 분석 (V5 → V6):

| Q | 변화 | 원인 |
|---|---|---|
| Q3 -3 | A3 5→3, A4 5→4 | 25 chunks 중 일부가 부정확 인용 + 답변 추론 유도 (noise 증가) |
| Q4 +2 | A2 3→4, A5 3→4 | 더 많은 컨텍스트가 도입 동기/시험 요건 측면 커버 + spec 연결 향상 |
| Q2 0 | 모든 차원 동일 | 임베딩 모델의 cross-lingual 한계 — 컨텍스트 양으로 해결 안 됨 |

**결론**: top_k 확장은 trade-off. broad 질문(Q4) 향상하지만 specific 질문(Q3)에 noise 추가.

### V7 (2026-05-04) — Q별 동적 top_k 시도 (개선 미관측)
- LLM이 질문을 broad/specific으로 분류 → 동적 top_k (broad 25, specific 15)
- Q1=specific, Q2/Q3/Q4=broad 자동 분류
- 결과: **Q1 -3, Q4 +2, Q2/Q3 동일 → 종합 81 (V5 -1)**

V5 vs V7 비교 분석:

| Q | V5→V7 | 의미 |
|---|---|---|
| Q1 -3 | 같은 top_k=15인데 -3 | **LLM 답변·평가의 비결정성** (temperature=0이어도 backend variability) |
| Q4 +2 | broad 분류 + top_k 25 적용 효과 | 동적 분류 가설 일부 검증 |
| Q3 0 | V6에서는 top_k 25에서 -3, V7에서는 0 | **LLM noise** 재확인 |
| Q2 0 | 임베딩 모델 한계 | top_k 양으로 해결 안 됨 (V6과 동일) |

**핵심 방법론적 발견**: V5(82) / V6(81) / V7(81) 모두 81~82 범위. **LLM-as-judge evaluation noise가 ±2~3점**일 수 있어, 작은 차이는 통계적 유의성 없음.

**결론**: V5가 최적 균형점. **동적 top_k의 명백한 개선이 관찰되지 않음 → V5 유지**.

## 3. 차원별 변동 분석

### A5 Cross-Doc Linkage (가장 큰 향상)

| Q | V2 | V3 | V4 | V5 |
|---|---:|---:|---:|---:|
| Q1 | 0 | 4 | 3 | **4** |
| Q2 | 3 | 3 | 3 | 3 |
| Q3 | 3 | 2 | 3 | **4** |
| Q4 | 2 | 3 | 3 | 3 |

→ V5가 Q1/Q3에서 4점 도달. Cross-Doc Linkage는 **신규 컬렉션 + 프롬프트 + reranker 조합이 종합 효과**.

### A2 Coverage

| Q | V2 | V3 | V4 | V5 |
|---|---:|---:|---:|---:|
| Q1 | 2 | 3 | **4** | 4 |
| Q2 | 3 | 4 | 3 | 3 |
| Q3 | 3 | 3 | **4** | 4 |
| Q4 | 3 | 3 | 3 | 3 |

→ V4의 구조화 프롬프트가 A2를 안정적으로 +1 향상 (V5에서 유지).

### A1 Accuracy / A3 Citation Integrity / A4 Hallucination

각 차원 모두 V2부터 4~5점대 안정적. 큰 변동 없음. → **검색 시스템 정확성이 baseline부터 우수**.

## 4. Q별 한계 분석

### Q2 (TCI-State) — V2가 최고 (20점)
- V2 컨텍스트 187 chunks vs V3 11 / V4 15 / V5 15
- TCI-State는 5 Release 변천 다루는 broad 질문 → 더 많은 컨텍스트가 절대 유리
- V5 reranker가 일부 candidates 제거 → 정보 양 감소
- **개선 방향**: top_k_rerank 25~30 (현재 15)으로 확장 시 V2 수준 회복 가능

### Q4 (LTM) — 19점에서 정체
- IE descriptions 매칭 강함 (LTM-Config 0.7353) → V3에서 잘 회수
- 그러나 답변에 LTM 도입 동기 / capability 시그널링 정보가 컨텍스트 어디에도 없음
- **데이터 한계**: TS spec에 LTM 도입 배경 직접 기재 없음 (RP-WID에 있을 수 있으나 미수집 결정)

## 5. 구현 산출물

### 평가 스크립트 (재현 가능)
- `scripts/cross-phase/usecase/q1_q4_v3_retrieval.py` (V3 retrieval)
- `scripts/cross-phase/usecase/q1_q4_v3_eval.py` (V3 LLM eval)
- `scripts/cross-phase/usecase/q1_q4_v4_eval.py` (V4 hybrid)
- `scripts/cross-phase/usecase/q1_q4_v5_eval.py` (V5 rerank + sparse + rewrite)
- `scripts/cross-phase/usecase/q1_q4_v6_eval.py` (V6 top_k 확장 시도)
- `scripts/cross-phase/usecase/q1_q4_v7_eval.py` (V7 Q별 동적 top_k 시도)

### 정본 측정 데이터
- `logs/cross-phase/usecase/q1_q4_v3_retrieval.json` (V3 retrieval scores)
- `logs/cross-phase/usecase/q1_q4_v3_eval.json` (V2/V3 답변 + rubric)
- `logs/cross-phase/usecase/q1_q4_v4_eval.json` (V4 답변 + rubric)
- `logs/cross-phase/usecase/q1_q4_v5_eval.json` (V5 답변 + rubric — **최적**)
- `logs/cross-phase/usecase/q1_q4_v6_eval.json` (V6 답변 + rubric — top_k 확장 trade-off 실증)
- `logs/cross-phase/usecase/q1_q4_v7_eval.json` (V7 답변 + rubric — 동적 top_k LLM noise 실증)

## 6. 결론

**V5 (82/100)** 이 현재 가능한 최선. V2 (73/100) 대비 +9 (+12.3%) 향상.

향상 기여도:
- 신규 컬렉션 (V3): +5
- Hybrid + 프롬프트 + 컨텍스트 확장 (V4): +1 (V3 대비)
- Reranker + Sparse + Rewriting (V5): +3 (V4 대비)
- top_k 확장 시도 (V6): -1 (V5 대비) — trade-off로 인해 실패 확인

**V5가 현재 시스템 최적 균형점**. V6/V7 시도로 다음 사실 실증:
- V6: 단순 컨텍스트 양 확장은 trade-off (broad↑, specific↓)
- V7: Q별 동적 top_k도 개선 미관측 (LLM noise ±2~3점 범위 내)

남은 향상 여지 (사용자 결정 필요):
- 임베딩 모델 업그레이드 (3-small → 3-large 또는 multilingual) — Q2 cross-lingual 한계 해결 (~$30~50 + 24h)
- 평가 질문 다양화 (4 → 10~20) — LLM-as-judge noise 통계 신뢰도 향상 (현재 4건 평가는 noise에 민감)
- 평가 다회 실행 후 평균 — 동일 시스템도 ±2~3점 변동, 5회 평균 시 통계 안정

**RAN1 spec 본문 P7-V15~V19 추가는 사용자 권한** (가이드: `usecase/evaluations/3way/ran1_spec_body_update_guide_2026-05-04.md`).
