# 정규 프로세스 추출 완전성 — 5 WG × 12 Phase 전수 검수 (2026-05-02)

> **작성 동기**: 사용자 지적 — IE field description (RAN2 docx 755건 vs 우리 chunk 0건) 누락 발견 → 다른 phase/RAN에 같은 패턴이 있는지 전수 검수 + 근본 원인 + 해결책.
> 참조: `logs/cross-phase/usecase/regular_process_audit.md` (코드 audit 상세), `logs/cross-phase/usecase/extraction_audit_all_phases.json` (정량 측정 raw)

## 1. 결과 요약 (TL;DR)

> **🔴 2026-05-04 정정**: 본 문서 초판은 RAN1 spec §2.2 (Out of Scope) / §2.3 (Graph DB vs Vector DB 경계)을 확인하지 않고 작성하여 **의도된 설계를 "결함"으로 오분류**. spec 대조 후 **실제 결함은 HARD_MAX 부재 + 일부 PATTERN 공백뿐**으로 확정. spec 명시 정책에 따른 phase-3/4/5 metadata-only 분리는 결함 아님.

**최초 정량 측정**: phase-7 결과 6 패턴 51~100% 누락 → 다른 phase 검증 → **HARD_MAX 부재 + IE/Capability 패턴 공백 두 가지가 실제 결함**. 데이터 부재 아님 (docx에 모두 있음). 정책 정착 미흡 책임.

| 카테고리 | 누락 비율 | 대표 예 |
|---|---:|---|
| IE field descriptions 표 (`XXX field descriptions`) | RAN2 99.7% | LTM-Config / CodebookConfig / TCI-State 의 field 의미 |
| IE 정의 헤더 (`XXX information element`) | RAN2 100% | 642건 → 0건 |
| Capability "UE supports" 패턴 | RAN2 87% | 38.306 1,162건 → 150건 |
| 시험 케이스 본문 (Test purpose/Procedure) | RAN4 83% / RAN5 54% | 38.521-3 715건 등 |
| RP-WID reference (Plenary) | 99.98% | 5 WG 합 12,587건 → 2건 |
| ASN.1 SEQUENCE/CHOICE 정의 | RAN2 19% / RAN3 33% | NGAP/XnAP/F1AP 일부 |

## 2. 5 WG × 5 컬렉션 정량 매트릭스 (실측)

`scripts/cross-phase/validation/audit_extraction_completeness.py --all --all-collections`

### 2.1 docx 합계 vs 컬렉션 적재 (chunks 단위)

| WG | A_field_desc | B_asn1_def | C_capability | D_test_purpose | E_ie_header | F_rp_wid |
|---|---|---|---|---|---|---|
| RAN1 | docx=0 ⇒ 적재=0 (정당) | 0 (정당) | 0 (정당) | 0 (정당) | 2 ⇒ ts_main 2 (100%) | docx=1,026 ⇒ **0건 (0%)** |
| **RAN2** | **755 ⇒ 2 (0.3%)** ⚠️ | 2,622 ⇒ 2,124 (81%) | **1,174 ⇒ 150 (13%)** ⚠️ | 0 (정당) | **642 ⇒ 0 (0%)** ⚠️ | **3,340 ⇒ 1 (0%)** ⚠️ |
| RAN3 | 0 (정당, 다른 키워드) | 4,319 ⇒ 2,886 (67%) | 0 (정당) | 0 (정당) | 150 ⇒ 150 (100%) | **1,987 ⇒ 0 (0%)** ⚠️ |
| RAN4 | 0 (정당) | 0 (정당) | 0 (정당) | **1,704 ⇒ 291 (17%)** ⚠️ | 14 ⇒ 13 (93%) | **6,210 ⇒ 1 (0%)** ⚠️ |
| RAN5 | 3 ⇒ 11 (split 중복) | 911 ⇒ 4,854 (split) | 64 ⇒ 12 (19%) | **922 ⇒ 421 (46%)** | 13 ⇒ 27 (split) | **24 ⇒ 0 (0%)** |

**해석 주의**: RAN5 일부 패턴이 100% 초과 — chunk split 중복 카운트. 그러나 RAN2 누락 (0%, 13%, 0%) / RAN4 D_test_purpose (17%) / 5 WG F_rp_wid (0%)는 명백한 누락.

### 2.2 phase-6/7/8/9 컬렉션별 흥미로운 발견

| 패턴 | RAN2 ts_main | RAN2 ts_asn1 | RAN2 tdoc | **RAN2 cr** | RAN2 tr |
|---|---:|---:|---:|---:|---:|
| A_field_desc | 2 | 0 | 507 | **16,141** | 0 |
| B_asn1_def | 19 | 2,105 | 17,169 | **23,763** | 2 |
| E_ie_header | 0 | 0 | 11,672 | **19,661** | 0 |

→ **CR 컬렉션에 IE description 패턴이 풍부히 등장** (CR이 spec 본문을 인용하기 때문). 즉 **현재도 CR 컬렉션 우회 검색은 부분 가능**하나 **체계적이지 않고 산재**. IE description 표 직접 적재 대비 정확도 낮음.

## 3. Phase별 처리 (코드 audit + Spec 대조 — 2026-05-04 정정)

> 본 §3은 초판에서 spec 대조 없이 "결함"으로 분류한 항목을 RAN1 spec 정책과 대조하여 정정한 결과. 상세 정정 표는 `logs/cross-phase/usecase/regular_process_audit.md` 참조.

### 3.1 의도된 설계 (결함 아님)

| Phase | 처리 | RAN1 spec 정책 |
|---|---|---|
| phase-0 | TSG_RAN Plenary 미수집 | `data_collection_scope.md` §2.1 미수집 결정 |
| phase-3 | KG에 body text 미저장 (메타만) | spec §2.2: "Section 본문 텍스트 = Vector DB 영역, Out of Scope" |
| phase-3 | ASN.1 정의 섹션 Section 단위 제외 | spec §3.9.4 명시 정책 (별도 컬렉션으로 회수) |
| phase-4 | CR Track Changes 본문 KG 미저장 | spec §2.2: "Track Changes 변경 블록 = Vector DB 영역" |
| phase-5 | Scope/Conclusions `[:800]` 발췌 | spec §2: "1-10문장 짧은 요약 메타데이터" — 800자 ≈ 정책 구현 |
| phase-6/7/8/9 | Foreword/References/Change History 등 DROP | 각 spec 명시 정책 (검색 노이즈 제거) |
| phase-10/11 | 다른 phase parser 재사용 | 의도된 DRY 설계 |

### 3.2 실제 정책 공백/구현 결함 (보강 작업 진행)

| Phase | 항목 | 정책 공백/결함 분류 | 보강 |
|---|---|---|---|
| phase-3/7 | IE field description 표 별도 추출 안 함 | 정책 공백 (RAN2 38.331 docx 755건 미회수) | ✅ P1.1b — `ran2_ts_ie_descriptions` 700 chunks (P7-V14 정착) |
| phase-7 | 38.306 capability 행 단위 분해 안 함 | 정책 공백 | ✅ P1.1c — `ran2_ts_capabilities` 1,716 rows (P7-V15 정착) |
| phase-6/8/9 | HARD_MAX 부재 (Spec V1 미반영) | 구현 결함 (5,041 위반) | ✅ P2.b v2 (chunker.py 버그 수정 후) — 0건 (3.43M chunks 100% 준수) |
| phase-7 (RAN2 38.331) | IE descriptions 7% 패턴 매칭 누락 | 추출 정규식 한계 | ⏳ 진행 예정 (55/755) |

### Phase-10/11 (증분 업데이트)

phase-3/6/7/8/9 모듈을 **재사용**하므로 모든 정책 공백·구현 결함을 그대로 전파. 즉 신규 미팅 추가 시에도 같은 패턴 적용 — 따라서 정책 공백을 별도 컬렉션 보강 + chunker.py 수정으로 해결한 후에는 phase-10/11도 자동 반영됨.

## 4. Root Cause — Spec 대조 후 정정 (2026-05-04)

> 초판은 4개 root cause로 정리했으나, spec 대조 후 R1/R2/R4는 의도된 설계로 재분류. 실제 root cause는 R3(chunker 정책 백포팅 미흡) + 일부 정책 공백뿐.

### R1. ~~5 RAN의 정책 상속~~ → **의도된 설계 + 일부 정책 공백**

- KG-VDB 책임 분리는 RAN1 spec §2.2/§2.3에 명시된 정책 (모든 phase에 일관 적용).
- RAN2 38.331 IE description 표는 정책이 명시되지 않은 공백 영역 → P1.1b로 별도 컬렉션 보강 (P7-V14 정착).
- RAN5 38.5xx 시험 케이스 패턴도 동일 (P7-V16).
- **정책 공백은 R1이 아니라 spec 명시 누락 카테고리에 한정**.

### R2. ~~KG-VDB 책임 분리 실패~~ → **분리 가정은 정상, 일부 별도 컬렉션 미신설이 원인**

- KG = 메타/구조, VDB = 본문 분리는 **spec 명시 정책** (phase-3 §2.2, phase-4 §2.2, phase-5 §2 모두 명시).
- 누락 영역(IE description 표, capability 행)은 분리 가정 실패가 아니라 **별도 컬렉션이 spec에 명시되지 않았음**.
- 해결책: 4-tier 검색 시스템 정착 (main + asn1 + ie_descriptions + capabilities) + spec V2 정착 (P7-V13~V17).

### R3. **Chunker 정책 일관성 부재** ✅ 실제 root cause

- HARD_MAX=6,500 (P2 정책)이 phase-7에만 적용, phase-6/8/9 미적용 → 5,041 위반.
- 추가로 `split_existing_chunk`의 stale `tokenCount` 신뢰 버그 (2026-05-04 식별) → P2.b v1에서 1,815건 silent skip.
- ✅ **2026-05-04 chunker.py 수정 + P2.b v2로 100% 해소** (3.43M chunks 0 위반).

### R4. ~~데이터 수집 범위 불일치~~ → **의도된 미수집 결정**

- TSG_RAN Plenary 미수집은 ROI 평가 + 사용자 결정으로 확정 (`data_collection_scope.md` §2.1).
- 5 WG TDoc 본문이 RP-WID 도입 배경을 인용하므로 우회 인용은 현재도 가능.
- **재검토 금지** (2026-05-04 결정).

### Root Cause 종합 (정정)

→ 실제 단일 root cause는 **chunker.py HARD_MAX 백포팅 + stale tokenCount 버그 (R3)**이며 100% 해소됨. 그 외는 의도된 설계 또는 정책 공백 보강 (별도 컬렉션 신설).

## 5. 근본 해결책 (3계층 설계)

### Layer 1: 즉시 수정 (Today / This Week)

| 액션 | 영향 받는 phase / WG | 비용 |
|---|---|---|
| **L1.1 P1.1b**: P1.1 ASN.1 추출기에 description 표 추출 추가 (regex 확장 + IE name 다음 표 매칭) | RAN2 38.331 +755 description, RAN5 38.523 +3 | 2시간 + 임베딩 ~$0.005 |
| **L1.2 chunker_v2 백포팅**: phase-6/8/9 chunker가 cross-phase/common/chunker.py 사용. HARD_MAX=6,500 강제 | phase-6/8/9 × 5 WG (10 컬렉션) | 4시간 + 재인덱싱 ~$1.5 |
| **L1.3 phase-3 body text 분리 파일**: parse_ts_docx.py에서 본문 텍스트를 별도 파일로 출력 (`{spec}_body.json` 또는 chunks.json) | 5 WG phase-3 | 4시간 |
| **L1.4 RP-WID 수집** (선택, 핵심 30~50건만): RP-221799, RP-211661 등 핵심 feature WID + Phase-0 수집 단계 추가 | phase-0 | 2시간 + 임베딩 ~$0.01 |

### Layer 2: Phase 완료 게이트 (재발 방지)

| 게이트 | 강제 시점 |
|---|---|
| **G1: extraction coverage audit** | phase-3/6/7/8/9 완료 시 — `audit_extraction_completeness.py --wg X` PASS (각 패턴 누락 < 20%) |
| **G2: chunk quality (이미 있음)** | phase-7 완료 시 — `validate_chunk_quality.py --wg X` PASS (HARD_MAX 6,500) |
| **G3: phase 간 정합성** | phase-10/11 완료 시 — 증분 데이터에 같은 패턴 결함 미발생 검증 |

### Layer 3: Spec/표준 정착 (장기)

| 변경 | 위치 | 효과 |
|---|---|---|
| **EXCLUDE_PATTERNS 중앙화** | `docs/cross-phase/standards/extraction_policy.md` 신설 — DROP 정책 + PRESERVE 화이트리스트 (RP-WID, IE description 표 등 명시) | 새 정책 추가 시 5 WG 일관 |
| **공통 chunker 강제** | `scripts/cross-phase/common/chunker.py` 외 별도 chunker 작성 금지 (CI 검증) | drift 방지 |
| **데이터 수집 카테고리 spec화** | `docs/cross-phase/standards/data_collection_scope.md` — TSG_RAN/RAN1~5/CR/TR/RP-WID 각 카테고리의 수집 정책 명문화 | phase-0 누락 재발 방지 |
| **6 패턴 회귀 검증 ground truth** | `logs/cross-phase/baselines/extraction_completeness_baseline_2026-05-02.json` — 본 측정값 정본 보존 | 향후 정규 프로세스 변경 시 회귀 자동 감지 |

## 6. 사용자 결정 필요 (실행 우선순위)

| 옵션 | 시간 | 핵심 가치 |
|---|---|---|
| **A**: L1.1 + L1.2 만 (2일) | 6시간 | RAN2 38.331 IE description 회수 (Q1/Q2/Q4 큰 영향) + phase-6/8/9 안정화 |
| **B**: A + L1.3 (3일) | 1일 | KG에서 IE 의미 조회도 가능 — 더 근본적 해결 |
| **C**: A + L1.4 (RP-WID 핵심 30건만) (2.5일) | 8시간 | RP-221799 등 도입배경 직접 인용 가능 |
| **D**: A+B+C+L2 (1주) | 1주 | 게이트까지 정착 — 재발 방지 완성 |

**Claude 권장**: **B (L1.1 + L1.2 + L1.3)** — phase-3/6/7/8/9 일관성 확보가 핵심. RP-WID는 별도 트랙(우선순위 낮음).

## 7. 사용자 핵심 요구 부합 점검

> "근본적으로 해결할 해결책을 찾아줘"

본 문서가 다루는 것:
1. ✅ 전수 검수 (5 WG × 12 phase)
2. ✅ Root cause 분석 (4개 직교 원인)
3. ✅ 근본 해결책 3계층 (즉시 / 게이트 / 표준)
4. ✅ 재발 방지 자동화 (Layer 2 게이트)
5. ✅ 정량 측정 baseline (Layer 3 ground truth)

**미해결 (사용자 결정 필요)**:
- 어느 옵션(A/B/C/D)으로 실행 진행할지

---

## 8. 산출물 위치

- `scripts/cross-phase/validation/audit_extraction_completeness.py` — 정량 측정 도구 (재실행 가능)
- `logs/cross-phase/usecase/extraction_audit_all_phases.json` — 5 WG × 5 컬렉션 raw 데이터
- `logs/cross-phase/usecase/regular_process_audit.md` — 5 WG × 12 phase 코드 audit
- `usecase/evaluations/3way/extraction_completeness_audit.md` — 본 문서 (종합)

## 9. 실행 결과 (2026-05-02 진행)

### 9.1 옵션 D 선택 — 사용자 지시 "성능과 정확성 최우선, 비용·시간 무관"

L1.1 (P1.1b/P1.1c) + L1.2 (chunker_v2 백포팅 P2/P2.b) + L2 (게이트) + L3 (Spec/표준 정착) 모두 진행.

### 9.2 P1.1b — IE field descriptions 별도 컬렉션 (Layer 1)

| 컬렉션 | chunks | Status |
|---|---|---|
| `ran2_ts_ie_descriptions` | **700** | ✅ 신설 (38.331 docx 755건 → 700 chunks 적재. P7-V14 신설) |
| `ran5_ts_ie_descriptions` | **3** | ✅ 신설 (정합성 차원, P7-V16 신설) |

도구: `scripts/cross-phase/usecase/improvements/p1_1b_extract_ie_descriptions.py` (camelCase IE name + "field descriptions" 헤더 패턴 — case-sensitive).

### 9.3 P1.1c — Capability 행 단위 별도 컬렉션 (Layer 1)

| 컬렉션 | rows | Status |
|---|---|---|
| `ran2_ts_capabilities` | **1,716** | ✅ 신설 (38.306 §4.2.7.x/§5.4/§5.6 표 행 단위 분해. P7-V15 신설) |

도구: `scripts/cross-phase/usecase/improvements/p1_1c_extract_capability_rows.py`.

### 9.4 P2.b — phase-6/8/9 컬렉션 선별 재처리 (Layer 1, Step 0 정책 첫 적용)

전체 재인덱싱 ($30~50, 24시간) 대신 HARD_MAX 위반 chunks만 split → delete → upsert.

| 컬렉션 | 위반 → split | upsert |
|---|---|---|
| ran1_tdoc_chunks | 61 → 2 | 10 |
| ran1_cr_chunks | 65 → 38 | (4 del + new upsert) |
| ran2_tdoc_chunks | 3 → 0 | 0 (split 불가, residual) |
| ran2_cr_chunks | **652 → 623** | **10,083** |
| ran2_tr_sections | 17 → 14 | 107 |
| ran3_cr_chunks | 42 → 32 | 291 |
| ran4_tdoc_chunks | 498 → 0 | 0 (split 불가, residual) |
| ran4_cr_chunks | **3,500 → 1,685** | **35,150** |
| ran4_tr_sections | 26 → 11 | 83 |
| ran5_tdoc_chunks | 2 → 0 | 0 (split 불가, residual) |
| ran5_cr_chunks | 88 → 52 | 283 |
| ran5_tr_sections | 12 → 6 | 63 |

**합계**: 5,041 위반 → 46,070 new chunks (P2.b v1, 2026-05-02). Residual **2,579 (0.0753%)** 발생 후 chunker.py 버그 식별 → P2.b v2로 100% 해소.

### 9.4.1 P2.b v1 결과 (2026-05-02)

| 컬렉션 | v1 residual | 최대 토큰 |
|---|---:|---:|
| ran4_cr_chunks | 1,815 (70%) | 16,689 |
| ran4_tdoc_chunks | 498 (19%) | 8,596 |
| ran1_cr_chunks | 61 | 10,660 |
| ran1_tdoc_chunks | 59 | 7,884 |
| ran1_tr_sections | 42 | 10,530 |
| 그 외 9 컬렉션 합 | 104 | — |
| **합계** | **2,579** | — |

**Root cause** (2026-05-04 식별): `split_existing_chunk(chunk)` 함수가 chunk payload의 `tokenCount` 필드를 그대로 신뢰. 이 필드는 이전 chunker가 `len/4` 추정으로 계산해 stale 상태 (실측 7,265 토큰 → stored 3,079). 그 결과 `token_count <= hard_max` 조건 위배되지 않아 split 시도조차 안 함.

### 9.4.2 chunker.py 버그 수정 (2026-05-04)

`scripts/cross-phase/common/chunker.py` 2가지 패치:

1. **`split_existing_chunk` 항상 tiktoken 재측정** (stale `tokenCount` 무시)
2. **`_force_split_by_chars` 신규** (last-resort char-level split, 자연 break point 없을 때 hard_max 절대 준수 — bisection으로 chars/token 비율 적응)

### 9.4.3 P2.b v2 결과 (2026-05-04, chunker fix 후)

P2.b v2 재실행:

| 컬렉션 | v1 residual | v2 split → new | v2 residual |
|---|---:|---|---:|
| ran1_tdoc_chunks | 59 | 59→178 | **0** ✅ |
| ran2_tdoc_chunks | 3 | 3→7 | **0** ✅ |
| ran3_tdoc_chunks | 0 | — | **0** ✅ |
| ran4_tdoc_chunks | 498 | 498→1,156 | **0** ✅ |
| ran5_tdoc_chunks | 2 | 2→4 | **0** ✅ |
| ran1_cr_chunks | 61 | 61→309 | **0** ✅ |
| ran2_cr_chunks | 29 | 29→113 | **0** ✅ |
| ran3_cr_chunks | 10 | 10→41 | **0** ✅ |
| ran4_cr_chunks | 1,815 | 1,815→9,519 | **0** ✅ |
| ran5_cr_chunks | 36 | 36→140 | **0** ✅ |
| ran1_tr_sections | 42 | 42→182 | **0** ✅ |
| ran2_tr_sections | 3 | 3→15 | **0** ✅ |
| ran3_tr_sections | 0 | — | **0** ✅ |
| ran4_tr_sections | 15 | 15→74 | **0** ✅ |
| ran5_tr_sections | 6 | 6→25 | **0** ✅ |
| **합계** | **2,579** | **2,579 → 11,763** | **0 (0.0000%)** ✅ |

15 컬렉션 3,430,598 chunks 중 HARD_MAX 6,500 토큰 위반 **0건 (100% 준수)**. 정본: `logs/cross-phase/usecase/post_p2b_v2_violations.json`.

### 9.5 최종 검증 (Layer 2 게이트)

`validate_chunk_quality.py --all` 결과:

| WG | ts_sections chunks | max tok | 위반 | ASN.1 V2 |
|---|---:|---:|---:|---|
| RAN1 | 1,002 | 6,473 | 0 | N/A |
| RAN2 | 2,451 | 6,431 | 0 | ✅ 2,365 |
| RAN3 | 3,560 | 5,612 | 0 | ✅ 2,995 |
| RAN4 | 16,248 | 6,476 | 0 | N/A (RF/EMC) |
| RAN5 | 26,814 | 6,494 | 0 | N/A (3건 미만) |

**종합 PASS** — 5 WG ts_sections 컬렉션 HARD_MAX 6,500 토큰 한도 100% 준수.

### 9.6 Layer 3 — Spec/표준 정착

- ✅ `docs/cross-phase/standards/extraction_policy.md` 신설 (PRESERVE 화이트리스트 + EXCLUDE 정책 + 4-tier 검색 + 게이트)
- ✅ `docs/cross-phase/standards/reembedding_policy.md` 신설 (Step 0: 선별 가능성 최우선 검토)
- ✅ `CLAUDE.md` "🔴 재임베딩 의사결정 체크리스트 Step 0" 추가
- ✅ RAN2 phase-7 spec — P7-V13 (ASN.1 V2) / P7-V14 (IE descriptions V2) / P7-V15 (Capability V2) 정착
- ✅ RAN3 phase-7 spec — P7-V13 (ASN.1 V2) 정착, P7-V14/V15 해당없음 명시
- ✅ RAN4 phase-7 spec — P7-V09/V10/V11 해당없음 명시
- ✅ RAN5 phase-7 spec — P7-V16 (IE descriptions, 3 chunks) 정착, P7-V15/V17 해당없음 명시
- ✅ `docs/common/implementation_process.md` 교훈 56 (IE description 99.7% 누락) + 57 (재임베딩 Step 0) 추가

### 9.7 잔여 작업

- RAN1 spec 정정은 사용자 권한 (CLAUDE.md "🔴🔴🔴 RAN1 Spec 본문 수정 금지"). 단 Appendix는 2026-05-04부터 Claude 갱신 가능. `usecase/evaluations/3way/ran1_user_guide.md` 가이드 참조.
- ~~TDoc residual~~: 2026-05-04 chunker.py stale tokenCount 버그 수정으로 0건 해소.
- ~~RP-WID 본문 수집~~: **미수집 결정 확정** (2026-05-04). `docs/cross-phase/standards/data_collection_scope.md` §2.1 참조. ROI 평가 + 사용자 결정으로 재검토 금지.
