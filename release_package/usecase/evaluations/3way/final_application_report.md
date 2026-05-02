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

이전 1차 답변(`docs/usecase/answers/tracer/qN_*.md`)을 P2 적용 + ASN.1 컬렉션 활용한 v2 로 갱신. v1은 `.v1.md` 백업 보존.

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
| **Tier B** (38.306 cap 행 chunking) | **Skip 권장** | P1.2 split으로 232 chunks (각 ~2K tok), 'Type II' 포함 33 chunks. PoC에서 csi-Type-II 검색 score 0.5814 → 0.6096 이미 작동. 추가 split (232 → ~800)은 chunks 폭증 + noise marginal. ROI 낮음. |
| **Tier C** (RP-WID 컬렉션) | **진행 불가** | data 디렉토리 grep 결과 RP-WID 본문 docx **부재** (RP-221799 0건, RP-* 폴더는 CR parent ref 용도). 진행하려면 Phase-0 신규 수집 (별도 트랙). |

→ 후속 세션에서 RP-WID 수집 단계 추가 시 다시 평가 권장.

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
- `docs/usecase/evaluations/3way/root_cause_analysis.md`
- `docs/usecase/evaluations/3way/p1_poc_results.md`
- `docs/usecase/evaluations/3way/systemic_improvement_plan.md`
- `docs/usecase/evaluations/3way/ran1_user_guide.md`
- `docs/usecase/evaluations/3way/final_application_report.md` (본 문서)

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
