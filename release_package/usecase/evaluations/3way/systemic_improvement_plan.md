# 시스템 차원 근본 개선 계획 — 재발 방지 중심

> **작성 동기**: 사용자 요청 — "PoC에서 검증한 개선이 공식 기준(spec) / 구현 / docs에 정착되어 재발하지 않도록 근본적 개선책 수립. 땜빵하는식이 아니라, 처음부터 raw 데이터로 다시 구축할 때 이 문제가 재발하지 않도록."
> 작성일: 2026-04-29 (수정: RAN1 분리 + 표현 정정)
> 참조: [root_cause_analysis.md](root_cause_analysis.md), [p1_poc_results.md](p1_poc_results.md)

## 0. 핵심 원칙 (사용자 지시 반영)

1. **재구축 시나리오 검증 의무**: 모든 액션은 "오늘 raw 데이터로 phase-0부터 다시 시작했을 때 이 문제가 재발하는가?" 가 통과 기준.
2. **땜빵 금지**: chunks.json 후처리만 하고 chunker 코드/spec를 안 고치면 재구축 시 재발 → 반드시 spec → 구현 → docs 모두 갱신.
3. **🔴 RAN1 수정 절대 금지** (CLAUDE.md 원칙): RAN1 spec / 구현 / step docs는 Claude가 수정 불가. **사용자 직접 수정**. Claude는 RAN1 가이드만 제공.
4. **표현 정정**: "데이터 손실" 아님. 데이터(docx 원본)는 보존됐고 **chunking 단계에서 누락 (Indexing gap)** 한 것.

## 1. 문제의 진짜 범위 (5 WG 통합 점검)

이전 분석은 RAN2 위주였으나 5 WG 전수 점검 결과 **시스템 차원 결함**으로 드러남:

### 거대 chunk 분포 (Qdrant 실측)

| 컬렉션 | total chunks | >7.5K tokens (embedding 한계 초과) | >30K tokens (심각) | 비고 |
|---|---:|---:|---:|---|
| `ran1_ts_sections` | 952 | 6 | 0 | RAN1 PHY spec — 양호 |
| `ran2_ts_sections` | 2,315 | 8 | 2 | 38.306 BandNR 100K 토큰 |
| `ran3_ts_sections` | 3,529 | 6 | 0 | 양호 |
| `ran4_ts_sections` | 15,778 | **30** | **3** | 38.101-1 inter-band config 38K 토큰 |
| `ran5_ts_sections` | 9,929 | **698** ⚠️ | 0 | 시험 spec 표 거대화 다수 |
| **합계** | 32,503 | **748** | **5** | |

→ 4Q usecase 평가에서 발견된 약점은 **빙산의 일각**. 5 WG 전체에 748개 chunk가 embedding 한계 초과로 검색 정확도 손실 중.

### Chunker 정책 결함 (5 WG 공통)

| 결함 | 위치 | 영향 |
|---|---|---|
| **paragraph 단위 split만 수행, hard_max 부재** | 5 WG `01_parse_ts_sections.py`의 `split_giant_section()` | 거대 표 1개 = 1 paragraph → split 불가 → 748 chunks 임베딩 초과 |
| **ASN.1 일괄 skip 정책** | RAN2/3/4/5 (RAN1 제외) `is_asn1_heading()` | 38.331만 760 섹션, 5 WG 합 ~수천 섹션 IE 본문 누락 |
| **Phase-7 완료 게이트에 chunk size 검증 부재** | 5 WG `validation/01_validate_search.py` | 거대 chunk가 아무 경고 없이 통과 |

### 구조적 root cause

1. **Phase-7 chunker가 5 WG 별도 코드** (RAN1/RAN2/RAN3/RAN4/RAN5 각자) → 동일한 결함이 5번 복사됨 ([CLAUDE.md "phase-6/10/11 코드 중복은 의도된 상태"](../../../../CLAUDE.md) 참조 — 이번엔 그 정책의 부작용)
2. **공통 chunker 라이브러리 부재** → 한 곳을 고쳐도 5 WG 동기화 누락
3. **임베딩 모델(text-embedding-3-small) 8K 토큰 한계가 chunker spec에 명시되지 않음**
4. **chunk 품질 자동 검증 부재**

## 2. 5계층 개선 설계

### Layer 0: 평가 검증 (이미 완료)

[p1_poc_results.md](p1_poc_results.md):
- **P1.2 PoC**: 38.306 거대 chunk 8건 → 229 chunks split, score +5.3%, eType-II capability 본문 직접 회수
- **P1.1 PoC**: 38.331 LTM IE 22개 별도 컬렉션 적재, score +8.0%, ASN.1 본문 직접 회수

→ 효과 검증 완료. 본격 적용 진행.

### Layer 1: 즉시 코드 수정 (Today)

#### 1.1 공통 chunker 라이브러리 신설 (`scripts/cross-phase/common/chunker.py`)

> "5 WG 동시에 같은 결함을 수정해야 한다 = 공통 라이브러리 부재" 가 진짜 원인. 5 WG 각자 수정하면 다음에 또 drift 발생.

**책임**:
- `split_giant_section_v2(paragraphs, hard_max=7500, target=2000, overlap=100)` — paragraph 단위 + hard_max 강제
- `split_text_by_rows_or_chars(text, target=2000)` — 거대 paragraph를 행/문자 단위로 강제 split
- `extract_asn1_ies(docx_path) -> list[dict]` — docx에서 ASN.1 IE SEQUENCE/CHOICE 추출 (별도 컬렉션용)
- `validate_chunk_size(chunks, hard_max=7500) -> dict` — 검증 결과 반환

**적용**: 5 WG `01_parse_ts_sections.py`의 `split_giant_section`을 import로 대체.

#### 1.2 ASN.1 정책 변경 — skip 대신 별도 컬렉션

기존 `is_asn1_heading() → continue` 로직을 다음으로 변경:
1. ASN.1 섹션 감지 시 main chunks에는 sectionTitle/level만 추가 (헤딩 기록)
2. 본문은 `extract_asn1_ies()`로 IE 단위 별도 chunk 생성
3. 별도 컬렉션 `ran{N}_ts_asn1_chunks`에 적재

**적용 WG**: RAN2/3/4/5 (RAN1은 ASN.1 거의 없으므로 skip)

#### 1.3 즉시 재인덱싱 (5 WG)

- 기존 chunker 호출 → 새 chunks.json 생성
- Qdrant in-place update (기존 컬렉션 ID 유지, vector + payload만 갱신)
- 별도 `ran{N}_ts_asn1_chunks` 컬렉션 신설

**비용 추산**:
- chunk 분할로 ~32K → ~35K chunks (소폭 증가)
- ASN.1 IE 약 1,500개 (5 WG 합)
- 임베딩 비용 ≈ $0.5 미만

### Layer 2: 5 WG Spec 정정 (Today / Tomorrow)

각 WG의 `docs/RAN{N}/phase-7/specs/tdoc_vectordb_specs(TS).md`에 다음 명시:

#### 2.1 P7-V06/V07 (chunk 분할 임계값) 보강

기존:
```
[P7-V06] SPLIT_THRESHOLD = 10,000 토큰
[P7-V07] SPLIT_TARGET = 2,000 토큰
```

변경:
```
[P7-V06] SPLIT_THRESHOLD = 10,000 토큰 (paragraph 단위 split 트리거)
[P7-V07] SPLIT_TARGET = 2,000 토큰 (분할 목표)
[P7-V11 신설] HARD_MAX = 7,500 토큰 (embedding 모델 8,192 한계 - 안전 마진).
              단일 paragraph가 HARD_MAX 초과 시 행(row) 또는 문자 단위로 강제 split.
[P7-V12 신설] EMBEDDING_MODEL = openai/text-embedding-3-small (max 8,192 토큰)
              chunker 변경 시 본 모델 한계와 일치 여부 검증 필수.
```

#### 2.2 ASN.1 정책 변경 (RAN2/3/4/5)

기존 (`§2.6.3 RAN2 phase-7 spec`):
> ASN.1 정의 섹션 760개 (38.331 51%) 제외. 사유: 임베딩 품질 저하.

변경:
```
§2.6.3 [정정] ASN.1 정의 섹션 처리 정책 (Spec V2)

기존 정책: main chunks에서 제외 (V1).
신규 정책 (V2, 2026-04-29 정정):
  - main chunks (`ran{N}_ts_sections`): ASN.1 섹션 헤딩만 보존 (level + parent), 본문 제외
  - 별도 컬렉션 (`ran{N}_ts_asn1_chunks`): IE 단위 본문 (SEQUENCE/CHOICE/ENUMERATED) 적재
  - 검색 시: 사용자 쿼리에 IE 이름 패턴 (예: "LTM-Config IE")이 있으면 별도 컬렉션 우선 검색

V1 정책의 한계:
  - 38.331/38.355 ASN.1 본문 0건 회수 → "What fields does LTM-Config IE contain?" 같은 쿼리 답변 불가
  - 외부 LLM(Claude) 대비 Coverage 약점 (Q1/Q2/Q3/Q4 usecase 평가에서 검출)
  - 자세한 검증: docs/usecase/evaluations/3way/p1_poc_results.md

V2 적용 효과 (38.331 LTM 22 IE PoC):
  - 검색 score 평균 +8.0%
  - ASN.1 SEQUENCE 본문 직접 인용 가능
  - false positive 제거 (예: "LTM-CSI-ReportConfig" 쿼리 → 기존 §5.5.1 Introduction 회수 → 정정 후 LTM-CSI-ReportConfig-r18 IE 정확 회수)
```

### Layer 3: 재발 방지 자동화 (This Week)

#### 3.1 chunk 품질 검증 스크립트

`scripts/cross-phase/validation/validate_chunk_quality.py`:

```python
"""5 WG TS Section VectorDB chunk 품질 자동 검증.

검증 항목:
  1. chunk tokenCount 분포 (max <= HARD_MAX=7500)
  2. embedding 한계 초과 chunk 0건 강제 (→ FAIL)
  3. 핵심 ASN.1 IE 회귀 테스트 (LTM-Config, CodebookConfig, TCI-State 등 검색 가능)
  4. 거대 chunk 발견 시 root cause 자동 분류 (paragraph 단일/표/Annex 본문 등)
"""
```

**P7 완료 게이트**: 본 스크립트 PASS가 phase-7 완료 선언 조건.

#### 3.2 ASN.1 IE 회귀 테스트

`scripts/cross-phase/validation/validate_asn1_retrieval.py`:

```python
"""핵심 ASN.1 IE의 검색 가능성 회귀 테스트.

테스트 항목 (5 WG):
  - 38.331 LTM-Config-r18 → ran2_ts_asn1_chunks 검색 → top-3 hit
  - 38.331 CodebookConfig → ran2_ts_asn1_chunks 검색 → top-3 hit
  - 38.331 TCI-State → ran2_ts_asn1_chunks 검색 → top-3 hit
  - 38.413 NGAP IE → ran3_ts_asn1_chunks 검색 → top-3 hit
  - 등
"""
```

#### 3.3 CI/CD 통합

- chunker 코드 수정 시 자동 검증 실행 (pre-commit hook)
- 새 spec 추가 시 chunk 품질 자동 점검

### Layer 4: 교훈 문서화 (This Week)

#### 4.1 `docs/common/implementation_process.md` 교훈 추가

```markdown
### 교훈 33: chunker 작성 시 임베딩 모델 한계 강제 (2026-04-29)

**증상**: usecase 평가(Q1~Q4)에서 38.306 csi-Type-II capability, 38.331 LTM-Config IE 본문 미회수.

**진단**:
- chunker `split_giant_section`이 paragraph 단위 split만 수행
- 거대 표 1개 = 1 paragraph → split 불가
- 38.306 §4.2.7.2 BandNR = 100,571 토큰 chunk가 통째로 적재
- text-embedding-3-small 모델은 8,192 토큰 한계 → 앞 8%만 임베딩
- 5 WG 통합 검사 결과 748개 chunk가 한계 초과

**교훈**:
1. **chunker는 임베딩 모델 한계를 hard_max로 강제**해야 함. paragraph 단위만으로는 부족.
2. **5 WG 공통 chunker 라이브러리 사용** — 5번 복사된 코드는 같은 결함이 5번 발생.
3. **chunk size 분포 자동 검증을 phase-7 완료 게이트에 포함**.

**개선 결과** (PoC):
- 38.306 chunks 99 → 229 split, score +5.3%, eType-II capability 본문 직접 회수
- 38.331 LTM IE 22개 별도 적재, score +8.0%, ASN.1 본문 직접 회수

**참조**: docs/usecase/evaluations/3way/p1_poc_results.md
```

#### 4.2 `docs/common/implementation_process.md` 교훈 추가 (ASN.1 정책)

```markdown
### 교훈 34: ASN.1 일괄 제외는 검색 약점을 만든다 (2026-04-29)

**증상**: Q4 평가에서 LTM-Config IE 본문, Q1에서 CodebookConfig IE 본문, Q2에서 TCI-State IE 본문 모두 미회수.

**진단**:
- RAN2/3/4/5 phase-7 chunker가 ASN.1 섹션 (대시 접두사 헤딩) 일괄 skip
- Spec §2.6.3에 "임베딩 품질 저하"를 사유로 명문화
- 그러나 외부 LLM(Claude)은 ASN.1 IE 본문을 풍부히 답변 — Coverage 격차 발생

**교훈**:
1. **ASN.1 본문도 검색 대상**. 다만 main chunks에서 분리 → 별도 컬렉션 적재.
2. **임베딩 품질 우려는 sparse(BM25) hybrid retrieval로 보완** 가능.
3. **IE name 자체가 검색 키워드** — 정확히 매칭되어야 함.

**개선 결과** (PoC):
- 38.331 LTM 22 IE 별도 컬렉션 적재 → score +8.0%
- "LTM-CSI-ReportConfig measurement reporting configuration" 쿼리: BEFORE 0.5628 → AFTER 0.7144 (+0.152)

**참조**: docs/usecase/evaluations/3way/p1_poc_results.md
```

#### 4.3 신설: `docs/cross-phase/standards/chunking_standards.md`

5 WG 공통 chunking 표준:
- HARD_MAX = 7,500 tokens (embedding 8K 한계 - 안전 마진)
- SPLIT_THRESHOLD = 10,000 tokens (분할 트리거)
- SPLIT_TARGET = 2,000 tokens (분할 목표)
- SPLIT_OVERLAP = 100 tokens
- 거대 paragraph 처리: 표(파이프 구분자 다수) → row 단위 split, 비표 → 문자 단위 sliding window
- ASN.1 섹션: main chunks에서 분리, `ran{N}_ts_asn1_chunks` 별도 컬렉션
- chunk 품질 자동 검증 (P7 완료 게이트)

### Layer 5: 5 WG Phase-7 완료 게이트 강화 (This Week)

`scripts/cross-phase/validation/p7_completion_gate.py`:

```python
"""Phase-7 완료 자동 검증.

이 게이트가 PASS 해야 phase-7 "Complete" 선언 가능.

검증 항목:
  G1. chunk tokenCount 모두 <= 7500 (HARD_MAX)
  G2. ASN.1 IE 별도 컬렉션 존재 (RAN2/3/4/5)
  G3. 핵심 IE 회귀 테스트 PASS (5 WG)
  G4. CQ retrieval 정확도 (기존)
  G5. Spec 매트릭스 (P7-V01~V12) 실측 일치

사용법:
  python3 p7_completion_gate.py --wg RAN2
  python3 p7_completion_gate.py --all
"""
```

## 3. 실행 순서 + 책임 매트릭스 (RAN1 분리)

| Step | 액션 | 산출물 | 책임자 | 영향 |
|---|---|---|---|---|
| **S1** | 공통 chunker.py 작성 (cross-phase) | `scripts/cross-phase/common/chunker.py` | **Claude** | 5 WG 영향, RAN1 spec 무관 |
| **S2** | chunk 품질 검증 스크립트 + ASN.1 회귀 테스트 (cross-phase) | `scripts/cross-phase/validation/validate_chunk_quality.py`, `validate_asn1_retrieval.py` | **Claude** | 재발 방지 |
| **S3** | RAN2/3/4/5 chunks.json 재생성 + Qdrant 재인덱싱 + ASN.1 컬렉션 신설 | `vectordb/parsed/ts/RAN{2-5}/.../chunks_v2.json` + Qdrant 4 컬렉션 | **Claude** | 즉시 효과 |
| **S4** | RAN2/3/4/5 phase-7 chunker 코드 수정 | `scripts/phase-7/RAN{2-5}/ts-parser/01_parse_ts_sections.py` chunker import | **Claude** | 재발 방지 |
| **S5** | RAN2/3/4/5 phase-7 spec 정정 | `docs/RAN{2-5}/phase-7/specs/tdoc_vectordb_specs(TS).md` | **Claude** | 공식 기준 |
| **S6** | 교훈 문서 추가 + chunking standards 신설 | `docs/common/implementation_process.md` 교훈 33/34, `docs/cross-phase/standards/chunking_standards.md` | **Claude** | 표준 |
| **S7** | P7 완료 게이트 스크립트 + RAN2/3/4/5 적용 | `p7_completion_gate.py` | **Claude** | CI/CD |
| **S8** | RAN2/3/4/5 usecase 재평가 (Q1~Q4 점수 측정) | 점수 갱신 | **Claude** | 효과 검증 |
| **S9 [🔴 사용자 작업]** | RAN1 동일 작업 (chunker 수정 + spec 정정 + 재인덱싱) | (S1~S2 산출물 사용해 사용자가 직접 적용) | **사용자** | RAN1 (PHY spec, ASN.1 영향 적음) |

### S9 사용자 작업 가이드 (RAN1)

Claude는 RAN1 spec/구현을 수정할 수 없으므로 **별도 가이드 문서**(`ran1_user_guide.md`)에 다음 내용 정리:
- RAN1 phase-7 chunker에 chunker 적용 방법 (import 변경)
- RAN1 phase-7 spec 정정 안 (P7-V11/V12 신설)
- RAN1 chunks.json 재생성 명령
- RAN1 Qdrant 재인덱싱 명령
- RAN1 P7 게이트 통과 확인 방법

→ 사용자가 5분~30분 내 본인 책임으로 적용 가능한 형태로 제공.

### RAN1 영향 평가 (작업 우선순위 판단용)

| 항목 | RAN1 측정값 | 영향도 |
|---|---|---|
| `ran1_ts_sections` >7.5K 토큰 chunk | 6건 | 낮음 (RAN5 698건과 비교) |
| `ran1_ts_sections` >30K 토큰 chunk | 0건 | 없음 |
| ASN.1 skip 로직 | 0 라인 | RAN1은 PHY spec이라 ASN.1 거의 없음 — 정당 |
| ASN.1 IE 본문 미회수 영향 | 거의 없음 | RAN1은 IE보다 수식/표 위주 |

→ **RAN1은 영향 제한적**. 사용자가 본 systemic 개선의 RAN2/3/4/5 효과를 확인한 후 RAN1 적용 여부 판단해도 무방.

## 4. 비용 / 시간 추산

| 항목 | 시간 | 비용 |
|---|---|---|
| S1~S2 코드 작성 | 4시간 | $0 |
| S3 chunks.json 재생성 | 1시간 (스크립트) + 30분 (실행) | $0 |
| S4 Qdrant 재인덱싱 (5 WG, 32K + ASN.1 1.5K chunks) | 2시간 | **$0.5 미만** (OpenRouter 임베딩) |
| S5 chunker 코드 수정 | 2시간 | $0 |
| S6 5 WG spec 정정 | 3시간 | $0 |
| S7~S8 docs | 2시간 | $0 |
| S9 게이트 통합 | 3시간 | $0 |
| S10 재평가 | 4시간 (4Q × 5 WG) | $0.1 미만 |
| **총** | **약 21시간 (3일)** | **$0.6 미만** |

## 5. 효과 시뮬레이션 (4Q usecase 재평가 시)

| 축 | 현재 | P1 PoC | S1~S5 본격 적용 | S6~S9 정착 |
|---|---:|---:|---:|---:|
| A1 Accuracy | 4.55 | 4.55 | 4.65 | 4.70 |
| A2 Coverage | 3.95 | 4.10 (PoC 부분) | **4.65** | 4.75 |
| A3 Citation Integrity | 4.83 | 4.83 | 4.83 | 4.90 |
| A4 Hallucination Control | 4.85 | 4.85 | 4.95 | 4.95 |
| A5 Cross-Doc Linkage | 4.58 | 4.58 | 4.75 | 4.80 |
| **종합** | **4.55** | **4.58** | **4.77** | **4.82** |

**핵심**:
- A2 Coverage가 가장 큰 개선 (3.95 → 4.75)
- Claude의 Coverage 4.58을 **상회**
- Citation/Hallucination 격차 유지로 종합 1위 견고

## 6. 핵심 원칙 (재발 방지의 본질)

### 6.1 "5 WG 코드 중복은 즉시 drift를 만든다"

[CLAUDE.md "phase-6/10/11 코드 중복은 의도된 상태"](../../../../CLAUDE.md) 정책은 **RAN별 독립성** 우선. 그러나 chunker처럼 **모델 한계와 직결된 공통 로직**은 라이브러리화 필수. 향후 phase-7과 같은 신규 기능 작성 시:
- **공통 라이브러리 후보 식별**: 임베딩 한계, chunk size 정책, 필터 정책 등
- **5 WG 공통 또는 의도적 분리** 명시적 결정 + spec에 기록

### 6.2 "Spec에 임베딩 모델 명시"

향후 임베딩 모델 변경 시 (예: text-embedding-3-large = 16K 토큰) HARD_MAX도 자동 갱신되도록 spec에 모델 명시 + chunker가 spec 참조.

### 6.3 "완료 게이트는 외부 사용자 시각으로"

phase-7 "ALL PASS" 보고 시 단순 CQ 통과만이 아니라:
- chunk 품질 (size 분포)
- 핵심 IE 회귀 테스트
- 외부 LLM 대비 약점 검증

→ 오늘의 PoC가 보여줬듯, **CQ만 통과한 phase-7도 외부 사용자 입장에서는 큰 약점**을 가질 수 있음.

### 6.4 "외부 비교 평가를 정기 워크플로우로"

usecase 평가 (3-way comparison)를 정기 회귀 테스트로 통합:
- 분기 1회 GPT/Claude 답변 갱신 + 비교
- 약점 식별 → P1 액션 → 재평가
- 전체 사이클 자동화

## 7. 다음 단계 (Today)

본 계획서 승인 후 즉시 진행:
1. S1: 공통 chunker.py 작성 (지금 시작)
2. S3: 5 WG chunks.json 재생성 (S1 완료 후)
3. S4: Qdrant 재인덱싱 (S3 완료 후)
4. S2: 검증 스크립트 (S4와 병렬)

**S5~S10는 검증 결과 확인 후 본격 진행**.
