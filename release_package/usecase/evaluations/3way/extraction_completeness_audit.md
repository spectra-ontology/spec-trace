# 정규 프로세스 추출 완전성 — 5 WG × 12 Phase 전수 검수 (2026-05-02)

> **작성 동기**: 사용자 지적 — IE field description (RAN2 docx 755건 vs 우리 chunk 0건) 누락 발견 → 다른 phase/RAN에 같은 패턴이 있는지 전수 검수 + 근본 원인 + 해결책.
> 참조: `logs/cross-phase/usecase/regular_process_audit.md` (코드 audit 상세), `logs/cross-phase/usecase/extraction_audit_all_phases.json` (정량 측정 raw)

## 1. 결과 요약 (TL;DR)

**현재 정규 프로세스가 5 WG × 8 처리 phase에서 42건 결함, 6 패턴이 50~100% 누락**. 단일 root cause 아님 — **4개 직교 원인** 식별. 데이터 부재 아님 (docx에 모두 있음). 시스템 파이프라인 책임.

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

## 3. Phase별 결함 (코드 audit 기반)

audit agent의 `regular_process_audit.md` 요약:

### 가장 심각한 Phase 3개

| 순위 | Phase | 결함 | 영향 |
|---|---|---|---|
| 1 | **phase-3 (TS Section KG)** | 5 WG 모두 `to_output_dict()`에서 body text 자체 미저장 (parse_ts_docx.py:587) — JSON에 메타만 | KG에서 IE 의미 정보 부재 (Cypher로 IE 의미 조회 불가) |
| 2 | **phase-7 (TS Section VDB)** | ASN.1 섹션 760개 의도적 DROP + IE description 표 추출 패턴 부재 + 컨테이너 판정 | 사용자 측정 6 패턴 51~100% 누락 직접 원인 |
| 3 | **phase-0 (Data Collection)** | TSG_RAN(Plenary) 디렉토리 미수집 → RP-WID 본문 자체 부재 | 12,587건 reference만 존재, 본문 0 |

### Phase 결함 매트릭스 (요약)

- 결함 합계: **약 42건** (5 WG × 8 처리 phase)
- 패턴 분포:
  - **EXCLUDE 메타만 (M)**: 약 20건 — JSON에 본문 미저장 (Phase-3 패턴이 모든 RAN에 복제)
  - **DROP (D)**: 약 25건 — chunker가 의도적 skip (ASN.1, container, foreword, change history)
  - **HARD_MAX 부재 (H)**: 4건 × 5 WG = 20건 — phase-6/8/9에 P7-V11 미적용 (P2 작업이 phase-7만 했음)
  - **TRUNCATE (T)**: 5건 — RAN5 시험 chunk가 sectionTitle만 임베딩하는 의도적 정책
  - **PATTERN 누락 (P)**: 6건 — P1.1 등 추출기가 SEQUENCE만 매칭, description 표 무시
  - **수집 누락 (C)**: 5건 — phase-0 RP-WID/일부 카테고리 미수집

### Phase-10/11 (증분 업데이트)

phase-3/6/7/8/9 모듈을 **재사용**하므로 모든 root cause를 그대로 전파. 즉 신규 미팅 추가 시에도 같은 결함 누적.

## 4. Root Cause — 4개 직교 원인

### R1. **5 RAN의 정책 상속** (RAN1 베이스 정책이 RAN2~5로 복제됨)

- RAN1 phase-7 chunker (PHY spec, ASN.1 거의 없음)에서 만들어진 정책이 RAN2~5에 그대로 이식됨
- RAN2 38.331 (RRC, 2,365 IEs)에는 RAN1과 다른 정책이 필요한데 동일 로직 사용
- 결과: ASN.1 일괄 skip, IE description 표 무시 등

### R2. **KG-VDB 책임 분리 가정 실패**

- 설계 의도: Phase-3 KG = 메타/구조, Phase-7 VDB = 본문
- 실제: 양쪽 모두 빠진 영역이 존재 (예: IE description 표 — KG에 메타로도 안 들어가고 VDB에도 본문 없음)
- 즉 **분리 가정이 누락 영역을 만듦**

### R3. **Chunker 정책 일관성 부재 (phase 간 + Spec V2 미백포팅)**

- HARD_MAX=6,500 (P2 정책)은 **phase-7만 적용**
- phase-6 (TDoc 1M+ chunks), phase-8 (CR 193K), phase-9 (TR 572)에 미적용 → embedding 한계 초과 가능성
- chunker_v2 라이브러리는 신설했지만 공통 라이브러리 강제 사용 게이트 없음

### R4. **데이터 수집 범위 불일치**

- Phase-0 정책: working group 미팅(RAN1~5) TDoc만 수집
- TSG_RAN(Plenary) RP-WID 본문 미수집
- 결과: 5 WG 합 RP 번호 12,587건이 working group 본문에 reference로 등장하지만 **WID 본문 자체 부재**

### Root Cause 종합

→ **단일 fix로 안 됨**. 4개 직교 원인이 phase-10/11을 통해 신규 데이터에 계속 전파되는 구조.

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
- `docs/usecase/evaluations/3way/extraction_completeness_audit.md` — 본 문서 (종합)
