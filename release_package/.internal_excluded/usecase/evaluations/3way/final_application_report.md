# 5 WG 본격 적용 결과 보고서 (P1 systemic 개선)

> **작성일**: 2026-04-29
> **참조**: [root_cause_analysis.md](root_cause_analysis.md), [p1_poc_results.md](p1_poc_results.md), [systemic_improvement_plan.md](systemic_improvement_plan.md)

## 1. 결과 요약 (TL;DR)

**5 WG 모두 G1+G2 PASS** (validate_chunk_quality.py --all):

| WG | total chunks | violations | maxToken | ASN.1 컬렉션 | 작업 책임 |
|---|---:|---:|---:|---|---|
| RAN1 | 963 (+11) | **0** | 7,432 | — (정당한 해당없음, PHY) | Claude (코드/chunks/Qdrant), 사용자 (Spec) |
| RAN2 | 2,445 (+130) | **0** | 7,224 | ✅ 2,365 IEs (RRC/LPP) | Claude (전체) |
| RAN3 | 3,553 (+24) | **0** | 7,363 | ✅ 2,995 IEs (NGAP/XnAP/F1AP) | Claude (전체) |
| RAN4 | 16,027 (+249) | **0** | 7,380 | — (정당한 해당없음, RRM/시험) | Claude (전체) |
| RAN5 | 19,504 (+9,575) | **0** | 7,498 | — (정당한 해당없음, 시험) | Claude (전체) |
| **합계** | **42,492** | **0** | — | **2 WG (5,360 IE)** | — |

**핵심**: 이전에 5 WG 합 **748건이 임베딩 한계 초과** 상태였으나 본격 적용 후 **0건**. embedding 효율 손실 100% 해소.

## 2. 적용 단계별 결과

### Layer 0: PoC (2026-04-29 오전)
- P1.2 PoC: 38.306 8 splits, 검색 score +5.3%, eType-II capability 본문 직접 회수
- P1.1 PoC: 38.331 LTM 22 IEs, 검색 score +8.0%, ASN.1 SEQUENCE 본문 직접 회수

### Layer 1: 공통 라이브러리 + 검증 자동화 (2026-04-29 오후)
- ✅ `scripts/cross-phase/common/chunker.py` 작성 (5 WG 공통)
- ✅ `scripts/cross-phase/validation/validate_chunk_quality.py` 작성 (재발 방지 게이트)

### Layer 2: 5 WG 본격 적용

#### 2.1 chunker 코드 패치 (5 WG)
모든 WG의 `scripts/phase-7/RAN{N}/ts-parser/01_parse_ts_sections.py`에:
```python
HARD_MAX = 7_500  # P7-V11
EMBEDDING_MODEL = "openai/text-embedding-3-small"  # P7-V12

from common.chunker import split_giant_section_v2 as _split_v2

def split_giant_section(...):
    return _split_v2(paragraphs, target=target, overlap=overlap, hard_max=HARD_MAX)
```

→ **다음 phase-7 재실행 시 자동으로 hard_max 적용** (재발 방지).

#### 2.2 chunks.json P1.2 후처리 (in-place split)
| WG | 거대 chunk | split 결과 |
|---|---:|---|
| RAN1 | 6 | 5 splits (38.212 1, 38.213 1, 38.214 3) |
| RAN2 | 8 | 8 splits (38.306 §4.2.7.x 다수) |
| RAN3 | 6 | (이전 백그라운드 실행으로 split 완료) |
| RAN4 | 30 | (백그라운드 실행으로 split 완료) |
| RAN5 | 698 | **698 splits** (38.521-1 95, 38.523-1 585, 기타) |
| 합계 | 748 | 748 splits |

#### 2.3 Main 컬렉션 재인덱싱 (Qdrant in-place)
- RAN1: 952 → 963 (chunks.json 11 추가)
- RAN2: 2,315 → 2,445 (+130)
- RAN3: 3,529 → 3,553 (+24)
- RAN4: 15,778 → 16,027 (+249)
- RAN5: 9,929 → 19,504 (+9,575)

#### 2.4 ASN.1 IE 별도 컬렉션 (RAN2/3만 해당)
- ✅ `ran2_ts_asn1_chunks`: 2,365 IEs (38.331 RRC 2,255 + 38.355 LPP 110)
- ✅ `ran3_ts_asn1_chunks`: 2,995 IEs (38.413 NGAP 931 + 38.423 XnAP 898 + 38.473 F1AP 1,166)
- (RAN1/4/5: ASN.1 IE 본문 docx에 0건, 정당한 해당없음 — 실측 검증)

### Layer 3: 5 WG Spec 정정

| WG | spec 파일 | 정정 내용 | 상태 |
|---|---|---|:---:|
| RAN1 | `docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md` | P7-V11/V12 추가 | ⏳ 사용자 직접 (Spec 보호) |
| RAN2 | `docs/RAN2/phase-7/specs/tdoc_vectordb_specs(TS).md` | P7-V11/V12 + ASN.1 V2 정책 (§1.8.1) | ✅ Claude |
| RAN3 | `docs/RAN3/phase-7/specs/tdoc_vectordb_specs(TS).md` | P7-V11/V12 + ASN.1 V2 정책 | ✅ Claude |
| RAN4 | `docs/RAN4/phase-7/specs/tdoc_vectordb_specs(TS).md` | P7-V11/V12 + ASN.1 V2 정책 | ✅ Claude |
| RAN5 | `docs/RAN5/phase-7/specs/tdoc_vectordb_specs(TS).md` | P7-V11/V12 (ASN.1 V2 권장 — 실제 IE 0건) | ✅ Claude |

### Layer 4: 표준 + 교훈 문서

- ✅ `docs/cross-phase/standards/chunking_standards.md` 신설
- ✅ `docs/common/implementation_process.md` 교훈 53/54 추가
- ✅ phase-7 완료 게이트 신규 항목 (`validate_chunk_quality.py --all` PASS)

## 3. PoC vs 본격 적용 효과 비교 (Q4 검증)

### Q4 LTM-Config 검색 (RAN2 ASN.1 컬렉션 활용)

| 쿼리 | BEFORE main | AFTER main | AFTER asn1 (NEW) |
|---|---:|---:|---:|
| LTM-Config IE 필드 | 0.6059 | 0.6059 | **0.5964 + LTM-Config-r18 SEQUENCE 본문 직접** |
| ltm-CandidateToAddModList | 0.6280 | 0.6281 | **0.6913 (LTM-Candidate-r18 SEQUENCE)** |
| TCI-State QCL qcl-Type1/2 | 0.5024 | 0.5024 | **0.7161 (TCI-State IE 본문)** |
| BeamFailureRecoveryConfig enumerated | 0.4883 | 0.4883 | **0.6643 (BFR-Config IE)** |
| csi-Type-II UE capability | 0.5814 | 0.6096 (P1.2 split 효과) | **0.6327 (CodebookParameterseType2Ext-r19)** |

→ **ASN.1 컬렉션이 모든 IE 본문 쿼리에서 압도적 우위** (+0.13 ~ +0.21 score). main 컬렉션도 P1.2 split으로 +0.028 개선.

## 4. P2 추가 개선 (2026-04-29 후속, ✅ 완료)

### 4.0 P2 결과 요약

| 항목 | P1 적용 후 | P2 적용 후 | 변화 |
|---|---:|---:|---|
| zero vector | 36건 | **0건** | -36 (100% 해소) |
| 5 WG max token (실측 tiktoken) | 약 8,000~10,000 | **6,494** | < HARD_MAX 6,500 |
| 5 WG validate PASS | RAN2/RAN3만 ASN.1 OK | **5 WG 모두 G1+G2 PASS** | 100% |
| Total chunks (5 WG main) | 42,492 | **50,075** (+7,583) | P2 split 추가 |
| ASN.1 컬렉션 (RAN2/3) | 5,360 IEs | 5,360 IEs (보존) | 변동 없음 |

### 4.1 P2 액션

| 액션 | 결과 |
|---|---|
| HARD_MAX 7,500 → **6,500** (chunker.py + chunking_standards.md + 4 WG spec) | ✅ |
| count_tokens: `len/4` → **tiktoken 정확 측정 + fallback `len/2`** | ✅ |
| validate_chunk_size: payload tokenCount → **직접 text 측정** (stale payload false positive 방지) | ✅ |
| 5 WG chunks.json + Qdrant 재인덱싱 (RAN1 +39 / RAN2 +6 / RAN3 +7 / RAN4 +221 / RAN5 +7,310) | ✅ |
| 임베딩 비용 추가 | 약 $0.4 |
| 작업 시간 추가 | 약 30분 |

### 4.2 Q1~Q4 본격 재평가 결과 (P2 적용 후)

| Q | 쿼리 수 | hits | avg score | max score | ASN.1 hits |
|---|---:|---:|---:|---:|---:|
| Q1 Type-II codebook | 5 | 21 | 0.534 | 0.670 | 3 |
| Q2 TCI-state | 5 | 24 | 0.536 | **0.739** | 6 |
| Q3 BFD/BFR | 5 | 21 | 0.519 | 0.703 | 6 |
| Q4 LTM | 5 | 24 | **0.617** | **0.768** | 6 |

### 4.3 Q1~Q4 답변 본격 재생성 (v2, 2026-04-29 오후)

이전 1차 답변(`usecase/answers/tracer/qN_*.md`)을 P2 적용 + ASN.1 컬렉션 활용한 v2 로 갱신. v1은 `.v1.md` 백업 보존.

| Q | v1 → v2 변화 | 핵심 IE/본문 신규 인용 |
|---|---|---|
| **Q1 Type-II codebook** | 278 → 452 lines (+174) | ★ `CodebookConfig` IE + `CodebookConfig-r16` SEQUENCE (typeII-r16, paramCombination-r16, n1-n2-codebookSubsetRestriction-r16, numberOfPMI-SubbandsPerCQI-Subband-r16). 38.331 영역 低 → 高 |
| **Q2 TCI-state** | 247 → 293 lines | ★ Release × 문서 24칸 매트릭스 **13✅ → 20✅ (54% → 83%)**. 11 IE 본문(`TCI-State`, `QCL-Info`, `PDSCH-Config`, `PDCCH-Config`, `ControlResourceSet`, `TCI-UL-State-r17`, `CandidateTCI-State-r18`, `LTM-QCL-Info-r18` 등) + 38.306 96 TCI cap 행 |
| **Q3 BFD/BFR** | 323 → 갱신 | ★ 정량값 미답 6건 → **인용 가능 9건 해소** (`beamFailureInstanceMaxCount {n1..n10}`, `beamFailureDetectionTimer {pbfd1..pbfd10}`, `beamFailureRecoveryTimer {ms10..ms200}`, `ssb-perRACH-Occasion`, `ra-ResponseWindow {sl1..sl2560}`, `rootSequenceIndex-BFR`, `ra-PreambleIndex` 등 enumerated 절대값). 9 IE 본문 (`BeamFailureRecoveryConfig`, `RadioLinkMonitoringConfig`, `BFR-SSB-Resource` 등) |
| **Q4 LTM** | 259 lines + §11 P2 부록 | ★ LTM IE 22개 SEQUENCE 본문 직접 인용 (`LTM-Config-r18` 1,168 chars verbatim, `LTM-Candidate-r18` 2,154, `LTM-CSI-ReportConfig-r18` 2,756, `LTM-ConfigNRDC-r19`, `LTM-CandidateReportConfig-r19` 등). LTM-CSI-ReportConfig CHOICE(periodic/semiPersistent/eventTriggered) 구조 노출 |

### 4.4 답변 가능 수준 변화 (Coverage 정량)

| Q | v1 (P1) | v2 (P2+ASN.1) | A2 추정 점수 |
|---|---|---|---:|
| Q1 | 70% (38.331/38.306 미회수) | **90%** (CodebookConfig IE 본문 직접) | 3.8 → **4.5** |
| Q2 | Rel-15~18 상, Rel-19 중, Rel-20 하 | Rel-15~19 **상** 격상, Rel-20 정직 미답 | 4.0 → **4.7** |
| Q3 | 절차/연결고리 인용 가능, 정량값 부분 | 절차 + **enumerated 정량값 9건 직접 인용** | 4.0 → **4.6** |
| Q4 | Rel-18 상, Rel-19 중, Rel-20 study | Rel-18/19 **상**, Rel-20 정직 미답 + LTM IE SEQUENCE 본문 | 4.0 → **4.7** |

**A2 Coverage 평균**: 3.95 → **약 4.625** (+0.68)

### 4.5 종합 점수 (5축, Q1~Q4 v2 본격 평가 후 — 2026-05-02 실측)

| 축 | P1 후 | **P2 + v2 답변 후 (실측)** |
|---|---:|---:|
| A1 Accuracy | 4.55 | **4.78** (IE 본문 verbatim 인용 정확성 향상) |
| A2 Coverage | 3.95 | **4.68** (+0.73, IE/cap 본문 직접 인용) |
| A3 Citation Integrity | 4.83 | **4.95** (chunkIndex 표기 정확성 보강) |
| A4 Hallucination Control | 4.85 | **4.93** (Rel-20 정직 유지 + 정량값 학습지식 미사용) |
| A5 Cross-Doc Linkage | 4.58 | **4.81** (RRC IE → MAC-CE → PHY 트레이스 폐쇄 루프) |
| **종합** | **4.55** | **4.84** (Q1 4.8 / Q2 4.9 / Q3 4.84 / Q4 4.83) |

→ **+0.29 종합 상승 실측. Claude(3.65)·GPT(3.28) 격차 +1.19/+1.56 으로 결정적 확대** (v1 격차 +0.90/+1.27 대비).

### 4.6 Tier A 완료 — 4Q v2 평가 산출물

| 파일 | 역할 |
|---|---|
| `evaluations/3way/q1_3way_comparison_v2.md` | Q1 v2 5축 + 권위 검증 (sharetechnote / ATIS V16.2.0 등) |
| `evaluations/3way/q2_3way_comparison_v2.md` | Q2 v2 + 24칸 매트릭스 13✅→20✅ + Claude TCI-State-r20 hallucination 그대로 검증 |
| `evaluations/3way/q3_3way_comparison_v2.md` | Q3 v2 + 정량값 9건 검증 + Claude typical/default 위장 단정 4건 식별 |
| `evaluations/3way/q4_3way_comparison_v2.md` | Q4 v2 + LTM-Config IE 본문 인용 + Claude RP-234037 hallucination 그대로 |
| `evaluations/3way/summary_v2.md` | 4Q 종합 + 솔직 평가 (사용자 시선) + 실무 활용 가이드 |

### 4.7 Tier B/C 결정 (2026-05-02 실측)

| Tier | 결정 | 이유 |
|---|---|---|
| **Tier B** (38.306 cap 행 chunking) | **Skip 권장 → 정책 변경 후 진행** | (2026-05-02 사용자 정확성 우선 지시로 진행) |
| **Tier C** (RP-WID 컬렉션) | **진행 불가** | data 디렉토리 grep 결과 RP-WID 본문 docx **부재**. 진행하려면 Phase-0 신규 수집 (별도 트랙). |

## 5. P3 — IE descriptions + Capability rows + 정규 프로세스 audit (2026-05-02)

### 5.1 사용자 핵심 지적

> "IE field description 표 별도 적재 안 됨" / "이게 모든 RAN에 걸쳐서 있는거야? 전수 조사해서 근본적으로 해결할 해결책을 찾아줘"

5 WG × 12 phase × 6 패턴 전수 검수. 자동 검증 도구 신설.

### 5.2 결함 매트릭스 (audit_extraction_completeness.py)

| 패턴 | 5 WG docx | 컬렉션 적재 | 누락 |
|---|---:|---:|---:|
| ASN.1 IE field descriptions 표 | RAN2 755 | 2 | **99.7%** |
| IE 정의 헤더 | RAN2 642 | 0 | **100%** |
| Capability "UE supports" | RAN2 1,174 | 150 | **87%** |
| 시험 케이스 본문 | RAN4/5 합 2,626 | 712 | **73%** |
| RP-WID reference | 5 WG 합 12,587 | 2 | **99.98%** |

### 5.3 Root Cause (4개 직교)

1. RAN1 정책 5 WG 상속
2. KG-VDB 책임 분리 가정 실패
3. Chunker 정책 일관성 부재
4. 데이터 수집 범위 불일치

### 5.4 P3 적용 (2026-05-02)

| 액션 | 결과 |
|---|---|
| **P1.1b**: ASN.1 IE description 표 추출 → `ran{N}_ts_ie_descriptions` | RAN2 700 (38.331 670 + 38.355 30), RAN5 3 |
| **P1.1c**: 38.306 capability 행 단위 chunking → `ran{N}_ts_capabilities` | RAN2 1,716 (1 chunk 안 22행 → 1,716행 완전 분리) |
| **P2.b**: phase-6/8/9 선별 재처리 (HARD_MAX 초과 5,041건만) | 진행 중 (RAN4 CR 3,500 가장 큰 영향) |
| **CLAUDE.md** "재임베딩 Step 0 선별 가능 여부 최우선" 추가 | 정책 명문화 |
| **standards 신설** | `extraction_policy.md`, `reembedding_policy.md` |
| **교훈 56/57 추가** | `implementation_process.md` |

### 5.5 4-tier 검색 시스템 완성

| Tier | 컬렉션 | 역할 |
|---|---|---|
| 1 | `ran{N}_ts_sections` | 절차/본문 텍스트 |
| 2 | `ran{N}_ts_asn1_chunks` (RAN2/3) | IE SEQUENCE 구조 |
| 3 | **`ran{N}_ts_ie_descriptions` (NEW)** | IE field 의미 설명 |
| 4 | **`ran{N}_ts_capabilities` (NEW, RAN2)** | Capability 행 단위 |

### 5.6 검증 결과 (검색 score)

- "TCI-State maxNumberConfiguredTCIstates" → `multipleTCI` **0.7539** (capability)
- "ltm-CandidateToAddModList field meaning" → `LTM-Candidate field descriptions` **0.6514** (description)
- "csi-Type-II UE capability" → `CodebookComboParametersCJT-r18` **0.6136** (capability)
- "BeamFailureRecoveryConfig beamFailureInstanceMaxCount" → `BeamFailureRecoveryConfig field descriptions` **0.5559** + 본문 verbatim 회수

### 5.7 핵심 도구 (재발 방지)

- `scripts/cross-phase/validation/audit_extraction_completeness.py` — 5 WG × 5 컬렉션 추출 누락 자동 검출
- `scripts/cross-phase/usecase/improvements/p1_1b_extract_ie_descriptions.py`
- `scripts/cross-phase/usecase/improvements/p1_1c_extract_capability_rows.py`
- `scripts/cross-phase/usecase/improvements/p2b_selective_reembed.py` (선별 재처리)
- `docs/cross-phase/standards/extraction_policy.md` (PRESERVE/EXCLUDE 화이트리스트)
- `docs/cross-phase/standards/reembedding_policy.md` (Step 0 선별 최우선)

**핵심 검색 효과** (Q4 LTM 사례):
- "LTM-Config IE candidate cell Rel-18" → main 0.611 + ASN.1 **0.652** (LTM-Config-r18 SEQUENCE 직접)
- "LTM Cell Switch Command MAC CE 38.321" → main **0.717** (§5.18.35 정확)
- "LTM cell switch delay D_LTM 38.133" → main **0.768** (§6.3.1.2 정확)
- "ltm-CSI-ReportConfig L1 measurement candidate" → ASN.1 **0.664** (LTM-CandidateReportConfig-r19), main **0.630** (§5.2.4a)

→ **이전 P1 시점 false positive (§5.5.1 Introduction 같은 무관 절) 거의 사라짐**. ASN.1 컬렉션 활용으로 IE 본문 직접 인용 가능.

### 4.3 다음 작업 (사용자 직접만)

- ⏳ `docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md`에 P7-V11(HARD_MAX=6,500) / P7-V12 추가 (5분, [ran1_user_guide.md](ran1_user_guide.md) 참조)

## 4.x (구) 후속 개선 사항 (P2로 해소된 항목)

### 4.x.1 Zero vector 문제 (zero_vector_suspect 36건) — ✅ P2로 0건 달성

| WG | zero vec | 원인 | 권장 |
|---|---:|---|---|
| RAN1 | 4 | 38.211/38.213/38.214 일부 chunk text 14K~26K chars (추정 토큰 < 7,500인데 실제 > 8K) | HARD_MAX 6,500으로 보수 조정 |
| RAN3 | 1 | 동일 | 동일 |
| RAN4 | 31 | 38.101 시리즈 inter-band config 표 | 동일 + count_tokens 정확도 개선 |
| RAN5 | 0 | (해당 없음) | — |

**원인**: `count_tokens(text) = len(text) // 4` 추정이 실제 토큰과 차이. 실제 영어 텍스트는 4 chars/token이지만 표/수식이 많은 chunk는 더 많은 토큰 (예: 20K chars = 7K 추정 토큰이지만 실제 9K 토큰).

**권장 조치 (다음 세션)**:
1. **HARD_MAX = 7,500 → 6,500 으로 보수 조정** (chunker.py + 5 WG spec)
2. **`count_tokens`를 tiktoken 기반 정확 측정으로 교체** (chunker.py)
3. **재인덱싱** (영향 받는 chunk만 식별 후 부분 재처리 또는 5 WG 전체 재처리)

### 4.2 RAN4/5 ASN.1 매핑 정정

`scripts/cross-phase/usecase/improvements/apply_p1_to_wg.py` 의 ASN.1 spec 매핑:
- ❌ 잘못: `"RAN4": ["38.508-1", "38.509-1"]`, `"RAN5": ["38.508-1"]`
- ✅ 정정: 실측 결과 RAN4 docx에 ASN.1 0건, RAN5 38.508-1 cover annex만 (실 IE는 38.508-2/3/4 분책 또는 38.331 import)
- 현재 매핑은 의도와 다름 — 향후 RAN5 38.508-2/38.508-3 적재 시 매핑 정정 필요

### 4.3 사용자 직접 작업 (Spec 보호)

- `docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md`에 P7-V11/V12 추가 (5분 작업)
- 가이드: [ran1_user_guide.md](ran1_user_guide.md)

## 5. 재발 방지 정착

### 5.1 phase-7 완료 게이트 (앞으로 모든 phase-7 작업의 필수 통과)

```bash
python3 scripts/cross-phase/validation/validate_chunk_quality.py --all
# 기대: 5 WG 모두 ✅ G1+G2 PASS, violations=0
```

### 5.2 chunker_v2 라이브러리 사용 강제

- 5 WG `01_parse_ts_sections.py` 모두 `from common.chunker import split_giant_section_v2 as _split_v2` 사용
- 향후 임베딩 모델 변경 시 chunker.py 한 곳만 수정 → 5 WG 자동 반영

### 5.3 재구축 시나리오 검증 (사용자 핵심 요구)

**raw 데이터로 phase-0~7을 다시 실행하면?**
- chunker.py가 hard_max 강제 → 거대 chunk 생성 불가
- validate_chunk_quality.py가 phase-7 완료 게이트 → violations > 0이면 FAIL
- spec 본문에 P7-V11/V12 명문화 → 다음 작업자가 정책 인지

→ **재발 차단 3중 안전망 구축 완료**.

## 6. 변경된 파일 인벤토리

### 새로 작성 (Claude)
- `scripts/cross-phase/common/chunker.py` (5 WG 공통, ~250 lines)
- `scripts/cross-phase/validation/validate_chunk_quality.py` (재발 방지 게이트)
- `scripts/cross-phase/usecase/improvements/apply_p1_to_wg.py` (재현 가능 도구)
- `scripts/cross-phase/usecase/improvements/p1_2_split_giant_chunks.py` (PoC 검증용)
- `scripts/cross-phase/usecase/improvements/p1_2_load_v2_collection.py` (PoC 검증용)
- `scripts/cross-phase/usecase/improvements/p1_1_extract_asn1_ies.py` (PoC 검증용)
- `scripts/cross-phase/usecase/improvements/p1_1_load_asn1_collection.py` (PoC 검증용)
- `docs/cross-phase/standards/chunking_standards.md`
- `usecase/evaluations/3way/root_cause_analysis.md`
- `usecase/evaluations/3way/p1_poc_results.md`
- `usecase/evaluations/3way/systemic_improvement_plan.md`
- `usecase/evaluations/3way/ran1_user_guide.md`
- `usecase/evaluations/3way/final_application_report.md` (본 문서)

### 수정 (Claude)
- `scripts/phase-7/RAN1/ts-parser/01_parse_ts_sections.py` (chunker_v2 import + HARD_MAX)
- `scripts/phase-7/RAN2/ts-parser/01_parse_ts_sections.py` (동일)
- `scripts/phase-7/RAN3/ts-parser/01_parse_ts_sections.py` (동일)
- `scripts/phase-7/RAN4/ts-parser/01_parse_ts_sections.py` (동일)
- `scripts/phase-7/RAN5/ts-parser/01_parse_ts_sections.py` (동일)
- `docs/common/implementation_process.md` (교훈 53/54 추가)
- `docs/RAN2/phase-7/specs/tdoc_vectordb_specs(TS).md` (P7-V11/V12 + ASN.1 V2)
- `docs/RAN3/phase-7/specs/tdoc_vectordb_specs(TS).md` (동일)
- `docs/RAN4/phase-7/specs/tdoc_vectordb_specs(TS).md` (P7-V11/V12)
- `docs/RAN5/phase-7/specs/tdoc_vectordb_specs(TS).md` (P7-V11/V12)
- `vectordb/parsed/ts/RAN{1-5}/{spec}/chunks.json` (P1.2 후처리, 백업 .bak 보존)

### Qdrant 변경
- `ran1_ts_sections`: 952 → 963 chunks (재인덱싱)
- `ran2_ts_sections`: 2,315 → 2,445 chunks (재인덱싱)
- `ran3_ts_sections`: 3,529 → 3,553 chunks (재인덱싱)
- `ran4_ts_sections`: 15,778 → 16,027 chunks (재인덱싱)
- `ran5_ts_sections`: 9,929 → 19,504 chunks (재인덱싱)
- `ran2_ts_asn1_chunks`: 2,365 (신설)
- `ran3_ts_asn1_chunks`: 2,995 (신설)

### 사용자 직접 작업 대기
- `docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md`에 P7-V11/V12 추가 (가이드: ran1_user_guide.md)

## 7. 비용 / 시간

| 항목 | 비용 |
|---|---|
| 임베딩 (5 WG 재인덱싱 + ASN.1 별도) | 약 **$0.5** (OpenRouter, ~25M 토큰) |
| 작업 시간 | 약 **5시간** (PoC 1h + 적용 4h) |
| 영향 받은 chunks | **42,492 chunks 재인덱싱** + 5,360 ASN.1 IE 신규 |

## 8. 결론

| 항목 | 상태 |
|---|---|
| 4Q usecase 평가에서 검출된 chunker 결함 | ✅ 100% 해소 (5 WG violations=0) |
| 38.331 ASN.1 IE 본문 미회수 | ✅ 해소 (ran2_ts_asn1_chunks 2,365 IEs) |
| 38.306 capability 거대 chunk 미회수 | ✅ 해소 (697 → 1 chunk 단위로 split) |
| Q3 정량값 (BLER 등) 미회수 | ✅ ASN.1 컬렉션에 enumerated 본문 회수 가능 |
| 시스템 책임 약점 (R+O) | ✅ 9건 모두 해소 또는 정착 |
| 재발 방지 게이트 | ✅ phase-7 완료 시 자동 검증 |
| 5 WG 일관성 (chunker_v2 공통 라이브러리) | ✅ 5 WG 동일 정책 |

**종합 점수 추정** (4Q usecase 재평가 시):
- 이전: tracer 4.55 / Claude 3.65 / GPT 3.28
- 본격 적용 후: **tracer 4.80+** (Coverage 3.95 → 4.65, A1 4.55 → 4.65, A4 4.85 → 4.95)

**남은 후속 작업** (다음 세션):
1. HARD_MAX 6,500 보수 조정 (zero vector 36건 해소)
2. count_tokens tiktoken 기반 정확도 개선
3. RAN1 spec 사용자 직접 정정
4. Q1~Q4 본격 재평가 (점수 정량 측정)

---

## 9. P3 — 정규 프로세스 누락 패턴 6건 본격 해결 (2026-05-02)

### 9.1 동기 (사용자 지적)

> "지금 IE description이 적재가 안되어 있어? 모든 RAN에 걸쳐서 있는거야? 전수 조사해서 문제점 진단하고 루트 커즈를 찾은 다음에 근본적으로 해결할 해결책을 찾아줘."
> "재 인덱싱 필요한것만 선택적으로 재 인덱싱 하면 되는거 아냐?"

5 WG × 12 phase 전수 검수 (`usecase/evaluations/3way/extraction_completeness_audit.md`) 결과 **6 패턴 50~100% 누락** 확인.

> **🔴 2026-05-04 정정**: 본 audit 초판은 RAN1 spec 본문(§2.2 Out of Scope, §2.3 Graph DB vs Vector DB 경계)을 확인하지 않고 phase-3 KG body 미저장 / phase-4 Track Changes 미수집 / phase-5 [:800] 발췌 등을 "결함"으로 분류. 사용자 지적("spec에 적힌대로 해야지")으로 spec 대조 후 모두 **의도된 설계**로 재분류. 실제 결함은 R3 (chunker HARD_MAX 백포팅 미흡 + stale tokenCount 버그)뿐이며 100% 해소.

### 9.2 적용 결과 (옵션 D — Layer 1+2+3 일괄)

#### Layer 1 (즉시 수정)

| 조치 | 산출물 | 상태 |
|---|---|---|
| **P1.1b** IE field descriptions 별도 컬렉션 | `ran2_ts_ie_descriptions` 700 + `ran5_ts_ie_descriptions` 3 | ✅ 신설 |
| **P1.1c** 38.306 capability 행 단위 컬렉션 | `ran2_ts_capabilities` 1,716 rows | ✅ 신설 |
| **P2** chunker_v2 + tiktoken (HARD_MAX 6,500) | 5 WG ts_sections 위반 0건 | ✅ 백포팅 |
| **P2.b v1** phase-6/8/9 선별 재처리 (Step 0 정책 첫 적용, 2026-05-02) | 5,041 violations → 46,070 new chunks. Residual 2,579. `logs/cross-phase/usecase/post_p2b_violations.json` | ✅ 1차 |
| **chunker.py 버그 수정** (2026-05-04) | `split_existing_chunk`의 stale `tokenCount` 신뢰 버그. tiktoken 재측정 + `_force_split_by_chars` last-resort 추가 | ✅ Root cause 해결 |
| **P2.b v2** 재실행 (2026-05-04) | 2,579 → 11,763 new chunks. Residual **0건 (0.0000%)**. 3.43M chunks 100% 준수. `logs/cross-phase/usecase/post_p2b_v2_violations.json` | ✅ 완전 해소 |

P2.b 비용 효율: 전체 재인덱싱 ($30~50, 24h) 대비 **선별 재처리 ~$0.2, 30분** — 1/200 비용.

#### Layer 2 (게이트)

| 게이트 | 도구 | 상태 |
|---|---|---|
| **G1** chunk size HARD_MAX | `validate_chunk_quality.py --all` | ✅ 5 WG ts_sections 위반 0 |
| **G3** IE field descriptions V2 적재 (RAN2) | spec P7-V14 + `audit_extraction_completeness.py` | ✅ 700 chunks |
| **G4** Capability 행 단위 V2 적재 (RAN2) | spec P7-V15 | ✅ 1,716 rows |
| **G5** extraction completeness audit | `audit_extraction_completeness.py --all --all-collections` | ✅ baseline 정본화 |

#### Layer 3 (Spec/표준 정착)

| 변경 | 위치 |
|---|---|
| **PRESERVE 화이트리스트 + EXCLUDE 정책 명문화** | `docs/cross-phase/standards/extraction_policy.md` (신설) |
| **재임베딩 의사결정 Step 0 — 선별 가능성 최우선** | `docs/cross-phase/standards/reembedding_policy.md` (신설) + CLAUDE.md |
| **RAN2 phase-7 spec V13/V14/V15 정착** | `docs/RAN2/phase-7/specs/tdoc_vectordb_specs(TS).md` |
| **RAN3 phase-7 spec V13 정착, V14/V15 N/A 명시** | `docs/RAN3/phase-7/specs/tdoc_vectordb_specs(TS).md` |
| **RAN4 phase-7 spec V09/V10/V11 N/A 명시** | `docs/RAN4/phase-7/specs/tdoc_vectordb_specs(TS).md` |
| **RAN5 phase-7 spec V16 정착, V15/V17 N/A 명시** | `docs/RAN5/phase-7/specs/tdoc_vectordb_specs(TS).md` |
| **교훈 56 (IE description 99.7% 누락) + 57 (재임베딩 Step 0)** | `docs/common/implementation_process.md` |

### 9.3 P3 단계 누적 효과 (예상)

| 영역 | P1 적용 후 | P3 적용 후 (예상) |
|---|---|---|
| ASN.1 본문 검색 (RAN2/3) | ✅ (5,360 IEs) | ✅ |
| **IE field 의미 (RAN2)** | ❌ 0/755 (0%) | ✅ 700/755 (93%) |
| **38.306 Capability 행 매칭** | ⚠️ 232 chunks (혼재) | ✅ 1,716 rows (단위 분해) |
| phase-6/8/9 chunk size 위반 | 5,041건 (0.150%) | **0건 (0.0000%)** ✅ (P2.b v2 + chunker 버그 수정 후. 3.43M chunks 100% 준수) |

### 9.4 종합 점수 재추정

P1 후 4.80 → **P3 후 4.85+** (Coverage 4.65 → 4.75, A1 4.65 → 4.75).

### 9.5 잔여 작업

1. ~~2,579 residual~~ — **2026-05-04 해소** (chunker.py stale `tokenCount` 버그 수정 + P2.b v2). 3.43M chunks HARD_MAX 100% 준수.
2. ~~RP-WID 본문 수집~~ — **미수집 결정 확정** (2026-05-04, ROI 평가 결과 + 사용자 결정). `docs/cross-phase/standards/data_collection_scope.md` §2.1 참조. 재검토 금지.
3. **RAN1 spec 사용자 직접 정정** (P7-V11/V12 본문 정책 + 향후 신규 P7-V13~V17 본문) — `ran1_user_guide.md` 가이드. **단 Appendix는 2026-05-04부터 Claude 갱신 가능**.
4. **Q1~Q4 재평가** — IE descriptions / Capability rows 컬렉션 활용 시 점수 정량 측정.

### 9.6 정규 프로세스 hardening (2026-05-04 추가)

**핵심**: P2.b는 일회성 patch script. 정규 파이프라인(Phase-6/8/9 parser, Phase-11 incremental)이 같은 chunker를 사용해 같은 위반을 다시 만들면 의미 없음. 본 hardening으로 **정규 프로세스가 자체적으로 HARD_MAX 강제 + 보조 컬렉션 갱신**.

#### 9.6.1 chunker.py에 `enforce_hard_max` hook 추가

5 WG × phase-6/8/9 parser가 chunk 생성 후 `enforce_hard_max(chunks)` 호출하면 HARD_MAX 6,500 토큰 절대 초과 안 함:

```python
from common.chunker import enforce_hard_max, HARD_MAX_DEFAULT
chunks = enforce_hard_max(chunks, hard_max=HARD_MAX_DEFAULT)  # JSON 저장 직전
```

#### 9.6.2 phase-6/8/9 parser 5 WG 통합

| Phase | 적용 위치 | 파일 수 |
|---|---|---|
| Phase-6 (TDoc) | `parse_tdoc_lib.py::save chunks 직전` | 5 (RAN1~5) |
| Phase-8 (CR) | `01_parse_cr_chunks.py::save 직전` | 5 |
| Phase-9 (TR) | `01_parse_tr_chunks.py / 01_parse_tr_sections.py::save 직전` | 5 |
| **합계** | | **15 files** |

#### 9.6.3 Phase-7 보조 파이프라인 정규화 (`run_phase7_auxiliary.py`)

| 보조 단계 | 적용 WG | 컬렉션 |
|---|---|---|
| ASN.1 V2 (P7-V13) | RAN2, RAN3 | `ran2_ts_asn1_chunks` 2,365 / `ran3_ts_asn1_chunks` 2,995 |
| IE descriptions V2 (P7-V14) | RAN2, RAN5 | `ran2_ts_ie_descriptions` 723 / `ran5_ts_ie_descriptions` 3 |
| Capability V2 (P7-V15) | RAN2 | `ran2_ts_capabilities` 1,716 |

Phase-7 메인 적재 후 wrapper로 자동 호출:
```bash
python3 scripts/cross-phase/usecase/improvements/run_phase7_auxiliary.py --wg {RAN2|RAN3|RAN5} --apply
```

#### 9.6.4 Phase-11 ts_vdb.py 5 WG 통합

`scripts/phase-11/RAN{N}/tasks/ts_vdb.py` 의 `run_ts_vdb` 마지막에 보조 파이프라인 hook 추가:
```python
import subprocess as _sp
_sp.run([sys.executable, str(PROJECT_ROOT/"scripts/cross-phase/usecase/improvements/run_phase7_auxiliary.py"),
         "--wg", config.wg_name, "--apply"], cwd=PROJECT_ROOT)
```

→ Phase-11 incremental update에서 TS docx 변경 감지 시 보조 컬렉션 자동 갱신.

#### 9.6.5 정규 프로세스 재실행 시나리오

| 시나리오 | 자동 처리 |
|---|---|
| Phase-7 신규 적재 (메인) | ts_sections HARD_MAX 강제 (chunker_v2 split_giant_section_v2) |
| Phase-6 신규 적재 (TDoc) | tdoc_chunks HARD_MAX 강제 (parse_tdoc_lib.py enforce_hard_max hook) |
| Phase-8 신규 적재 (CR) | cr_chunks HARD_MAX 강제 (01_parse_cr_chunks.py hook) |
| Phase-9 신규 적재 (TR) | tr_sections HARD_MAX 강제 (01_parse_tr_chunks.py hook) |
| Phase-11 incremental TS | 메인 + 보조 컬렉션 동시 갱신 (run_phase7_auxiliary 호출) |
| Phase-11 incremental CR/TR | 메인 갱신 (HARD_MAX 강제) — 보조 컬렉션 없음 |

**재발 차단**: 정규 프로세스 어디서든 HARD_MAX 위반 chunk 생성 불가.

### 9.7 산출물 위치

**Standards 문서**:
- `docs/cross-phase/standards/extraction_policy.md` (신설, §3.2 정규 파이프라인 정책 포함)
- `docs/cross-phase/standards/reembedding_policy.md` (신설)
- `docs/cross-phase/standards/data_collection_scope.md` (신설, RP-WID 미수집 결정)

**보고서**:
- `usecase/evaluations/3way/extraction_completeness_audit.md` §9 (실행 결과 + spec 대조 정정)
- `logs/cross-phase/usecase/post_p2b_v2_violations.json` (정본 측정, 0건)
- `logs/cross-phase/usecase/regular_process_audit.md` (spec 대조 후 재분류)

**코드 (신규)**:
- `scripts/cross-phase/usecase/improvements/p1_1b_extract_ie_descriptions.py` (permissive 패턴 + blacklist)
- `scripts/cross-phase/usecase/improvements/p1_1c_extract_capability_rows.py`
- `scripts/cross-phase/usecase/improvements/p2b_selective_reembed.py`
- `scripts/cross-phase/usecase/improvements/run_phase7_auxiliary.py` (정규 파이프라인 wrapper)
- `scripts/cross-phase/validation/audit_extraction_completeness.py`

**코드 (수정 — 정규 프로세스 hardening, 2026-05-04)**:
- `scripts/cross-phase/common/chunker.py` — stale tokenCount 버그 수정 + `_force_split_by_chars` last-resort + `enforce_hard_max` hook
- `scripts/phase-6/RAN{1-5}/tdoc-parser/parse_tdoc_lib.py` — `enforce_hard_max` 통합 (5 files)
- `scripts/phase-8/RAN{1-5}/cr-parser/01_parse_cr_chunks.py` — `enforce_hard_max` 통합 (5 files)
- `scripts/phase-9/RAN{1-5}/tr-parser/01_parse_tr_*.py` — `enforce_hard_max` 통합 (5 files)
- `scripts/phase-11/RAN{1-5}/tasks/ts_vdb.py` — Phase-7 보조 파이프라인 자동 호출 (5 files)

**Spec 정착 (RAN2~5)**:
- `docs/RAN2/phase-7/specs/tdoc_vectordb_specs(TS).md` — P7-V13/V14/V15 정착 + 100% 커버리지 갱신
- `docs/RAN3/phase-7/specs/tdoc_vectordb_specs(TS).md` — P7-V13 정착, V14/V15 N/A
- `docs/RAN4/phase-7/specs/tdoc_vectordb_specs(TS).md` — P7-V09/V10/V11 N/A
- `docs/RAN5/phase-7/specs/tdoc_vectordb_specs(TS).md` — P7-V16 정착, V15/V17 N/A

**RAN1 spec 정정 가이드 (사용자 권한)**:
- `usecase/evaluations/3way/ran1_user_guide.md`
- 단 Appendix는 2026-05-04부터 Claude 갱신 가능 (CLAUDE.md "🔴🔴🔴 RAN1 Spec 본문 수정 절대 금지" 완화)

**교훈**:
- `docs/common/implementation_process.md` 56 (IE 누락) / 57 (재임베딩 Step 0) / 58 (stale tokenCount) / 59 (audit는 spec Read 선행)

---

## 10. 최종 검증 (2026-05-04)

### 10.1 회귀 검증 (4건 PASS)

| 항목 | 결과 |
|---|---|
| 30개 수정 파일 syntax compile | ✅ 전체 통과 |
| chunker.py 4 함수 functional regression | ✅ stale tokenCount 무시 + force-split 동작 |
| 25 컬렉션 3,488,475 chunks 위반 | ✅ 0건 (0.0000%) — 측정 2회 일치 |
| 도구 동작 (validate_chunk_quality, run_phase7_auxiliary) | ✅ 정상 |

### 10.2 할루시네이션 체크 (3 카테고리, 13건 전부 일치)

- 컬렉션 수치 6건 (38.331 unique IE 693, ts_ie_descriptions 723/3, ts_capabilities 1716, ts_asn1 2365/2995) → 실측 일치
- phase-3/4/5 spec 인용 3건 → 본문 일치
- Q1~Q4 v3 retrieval 점수 4건 → JSON 정본 일치

### 10.3 End-to-end 검증 (Phase-9 RAN3 재실행)

- 12 TR → 644 sections → 486 chunks 재생성
- max token 5,553, **위반 0건**
- `enforce_hard_max` hook 정규 프로세스 작동 확인

### 10.4 정규 프로세스 정착 (5 WG × 4 phase 완료)

| Spec | 추가된 P-V ID | 정책 |
|---|---|---|
| RAN2 phase-6 | P6-V16 / P6-V17 | HARD_MAX + EMBEDDING |
| RAN2 phase-8 | P8-V04 / P8-V05 | HARD_MAX + EMBEDDING |
| RAN2 phase-9 | P9-V08 / P9-V09 | HARD_MAX + EMBEDDING |
| RAN3 phase-6 | P6-V17 / P6-V18 | HARD_MAX + EMBEDDING |
| RAN3 phase-8 | P8-V04 / P8-V05 | HARD_MAX + EMBEDDING |
| RAN3 phase-9 | P9-V08 / P9-V09 | HARD_MAX + EMBEDDING |
| RAN4 phase-6 | P6-V11 / P6-V12 | HARD_MAX + EMBEDDING |
| RAN4 phase-8 | P8-V12 / P8-V13 | HARD_MAX + EMBEDDING |
| RAN4 phase-9 | P9-V08 / P9-V09 | HARD_MAX + EMBEDDING |
| RAN5 phase-6 | P6-V18 / P6-V19 | HARD_MAX + EMBEDDING |
| RAN5 phase-8 | P8-V19 / P8-V20 | HARD_MAX + EMBEDDING |
| RAN5 phase-9 | P9-V13 / P9-V14 | HARD_MAX + EMBEDDING |
| **RAN1 phase-7 (사용자 직접)** | **P7-V15~V19 (대기)** | HARD_MAX + EMBEDDING + V2 정책 N/A |

### 10.5 Q1~Q4 LLM 답변 + 5-tier rubric 평가 (V2 vs V3)

`google/gemini-2.5-flash` 로 답변 생성 + 동일 모델로 rubric 평가:

| Q | 질문 | V2 (basic ASN.1+sections) | V3 (+ie_descriptions+capabilities) | Δ |
|---|---|---|---|---|
| Q1 | Rel-16 Type-II codebook | 15/25 | **21/25** | **+6** |
| Q2 | TCI-State Rel-15~20 | 20/25 | 19/25 | -1 |
| Q3 | BFD/BFR Rel-15~17 | 19/25 | 19/25 | 0 |
| Q4 | Rel-18 LTM | 19/25 | 19/25 | 0 |
| **합계** | | **73/100** | **78/100 (+6.8%)** | **+5** |

**해석**:
- Q1 (Type-II): IE descriptions가 CodebookConfig field 의미 직접 회수 → A5 Cross-Doc Linkage 0→4 점프
- Q2 (TCI): V2가 이미 187 chunks 풍부 → V3 11 chunks의 추가 가치 미미. V2/V3 결합 시 추가 향상 기대
- Q3/Q4: 동일 점수. 기존 V2 컬렉션이 충분히 커버

**핵심 발견**: 신규 컬렉션은 **특정 질문 유형 (IE field 의미 + capability 매트릭스)에서 큰 가치**. 모든 질문에 균일 향상은 아님. 결합 검색 (V2 + V3) 전략이 최적.

산출물:
- `logs/cross-phase/usecase/q1_q4_v3_eval.json` (정본)
- `scripts/cross-phase/usecase/q1_q4_v3_eval.py` (재현 가능)
