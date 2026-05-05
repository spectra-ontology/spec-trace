# RAN1 Phase-7 Spec 본문 정정 가이드 (사용자 직접 적용)

> **작성일**: 2026-05-04
> **권한**: RAN1 spec **본문(§1~§N)** 수정은 사용자 전용. Claude 작성 불가.
> **대상 파일**: `docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md`
> **본 가이드**: Claude가 보조 자료로 작성한 변경안. 사용자 검토 후 직접 적용.

---

## 1. 변경 동기

RAN2~5 phase-7 spec에 2026-04-29~2026-05-04 정착된 정책을 RAN1 spec에도 반영하여 5 WG 일관성 확보.

신설 정책 (RAN2~5에 정착된 것):
- **HARD_MAX 6,500 토큰** (chunker_v2, P2 정책)
- **EMBEDDING_MODEL = `openai/text-embedding-3-small`**
- **ASN.1 IE 본문 V2 정책** (RAN2/3 별도 컬렉션, RAN1은 해당없음)
- **IE field descriptions V2 정책** (RAN2 별도 컬렉션, RAN1은 해당없음)
- **Capability 행 단위 V2 정책** (RAN2 별도 컬렉션, RAN1은 해당없음)

RAN1은 PHY 도메인이라 ASN.1/IE/Capability 패턴 부재 — N/A로 명시.

---

## 2. 추가할 위치와 ID

### 2.1 현재 RAN1 phase-7 spec 사용 ID (참고)

| 사용 중 ID | 항목 |
|---|---|
| P7-V01 | 전체 섹션 수 |
| P7-V02 | Void 섹션 수 |
| P7-V03 | 컨테이너 섹션 수 |
| P7-V04 | 초대형 섹션 수 (10K+) |
| P7-V05 | 총 청크 수 |
| P7-V06 | 분할 임계값 |
| P7-V07 | 분할 시 조각 크기 |
| P7-V08 | 오버랩 |
| P7-V09 | 최소 청크 |
| P7-V10 | 대상 TS 수 |
| P7-V11 | 처리 대상 section 합계 |
| P7-V12 | Section 토큰 구간 분포 |
| P7-V13 | 초대형 (10K+) Section inventory |
| P7-V14 | spec별 chunks 분포 |

→ 다음 가용 ID는 **P7-V15** 부터.

### 2.2 추가 위치

`docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md` 파일의 `## Appendix A: 기준 수치` 표 마지막 (현재 P7-V14 행 다음, 1393번 줄 이후)에 **5개 행 추가**.

---

## 3. 추가할 행 (그대로 복사)

```markdown
    | P7-V15 | HARD_MAX (절대 상한) | 6,500 토큰 | 2026-04-29 신설, 2026-05-04 chunker.py stale tokenCount 버그 수정. 임베딩 모델 한계(8,192) 기반 안전 마진. 단일 paragraph가 초과 시 행/문자 단위 강제 split (`scripts/cross-phase/common/chunker.py::split_existing_chunk` + `_force_split_by_chars`). 임베딩 모델 변경 시 조정 가능. 정본 측정: `logs/cross-phase/usecase/post_p2b_v2_violations.json` (3.43M chunks 0건 위반) |
    | P7-V16 | EMBEDDING_MODEL | `openai/text-embedding-3-small` | 2026-04-29 신설. max 8,192 토큰. chunker 변경 시 본 모델 한계와 일치 여부 검증 필수. 정책 근거: `docs/cross-phase/standards/extraction_policy.md` |
    | P7-V17 | ASN.1 IE 본문 V2 정책 | (해당없음) | 2026-05-02 검토. RAN1은 PHY spec(38.201/38.202/38.211/38.212/38.213/38.214/38.215/38.291)으로 ASN.1 IE 정의 부재 → 별도 컬렉션 미적용 (`docs/cross-phase/standards/extraction_policy.md` §1.3). RAN2/3은 ✅ 적용 |
    | P7-V18 | IE field descriptions V2 정책 | (해당없음) | 2026-05-02 검토. RAN1 PHY spec에 38.331 형식의 IE field descriptions 표 부재 → 미적용. RAN2 38.331 ✅ (700 chunks), RAN5 38.523-1/3 ✅ (3 chunks) |
    | P7-V19 | Capability 행 단위 V2 정책 | (해당없음) | 2026-05-02 검토. RAN1은 38.306 형식의 capability 표 부재 → 미적용. RAN2 38.306 ✅ (1,716 rows) |
```

> 들여쓰기 주의: 기존 표 행과 동일하게 4-space 들여쓰기 + 첫 글자 `|`.
> 노션 렌더링: 첫 줄(`- **phase-7:`) 외 모든 줄 4-space 시작 — 본 행도 동일.

---

## 4. 적용 방법

### 4.1 GUI 편집 (권장)

1. `docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md` 파일 열기
2. 1393번 줄(`P7-V14 | spec별 chunks 분포 ...`) 다음에 위 §3의 5개 행 그대로 붙여넣기
3. 저장

### 4.2 검증 (적용 후)

```bash
# 라인 수 확인 (5 lines 증가 확인)
wc -l "docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md"

# P7-V19까지 등장 확인
grep "P7-V1[5-9]" "docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md"
```

---

## 5. 본문 §3 (청킹 정책 표) — 선택 추가

`§3.2 청킹 정책 표` 또는 동급 위치에 P7-V15/V16를 정책 본문으로 인용하고 싶으면 다음 형식으로 추가 가능:

```markdown
    | HARD_MAX (절대 상한) | [P7-V15] 토큰 | 모든 청크 | 단일 paragraph가 초과 시 행/문자 단위 강제 split. 임베딩 모델 변경 시 조정 가능 |
    | EMBEDDING_MODEL | [P7-V16] | 임베딩 단계 | max 8,192 토큰 |
```

> **선택사항**: 본문에 인용할지는 spec 일관성 차원에서 결정. RAN2/3/5 spec은 본문에 P7-V11/V12 인용함. RAN1도 동일 일관성 원할 시 추가.

---

## 6. 변경 영향 (참고)

- **본 변경**은 spec 의미를 변경하지 않음 (정책 명문화만)
- 코드는 이미 `chunker.py` + phase-6/8/9 parser hook으로 정책 강제 중 (RAN1 데이터 영향 없음)
- 실측: RAN1 ts_sections 1,002 chunks 모두 HARD_MAX 6,500 미만 (max 6,473) — 위반 0건

---

## 7. RAN2~5 정착 현황 (참고용)

| WG | HARD_MAX | EMBEDDING | ASN.1 V2 | IE desc V2 | Cap V2 |
|---|---|---|---|---|---|
| RAN2 | P7-V12 | (전제 정책) | P7-V13 ✅ | P7-V14 ✅ | P7-V15 ✅ |
| RAN3 | P7-V12 | (전제 정책) | P7-V13 ✅ | N/A | N/A |
| RAN4 | P7-V08 | (전제 정책) | N/A | N/A | N/A |
| RAN5 | P7-V14 | (전제 정책) | N/A | P7-V16 ✅ | N/A |
| RAN1 | **P7-V15 (추가 예정)** | **P7-V16 (추가 예정)** | P7-V17 N/A | P7-V18 N/A | P7-V19 N/A |

> WG별 ID 번호 차이는 각 spec의 기존 사용 ID에 따른 자연 결과 — spec 내 일관성만 유지하면 됨.

---

## 8. 적용 체크리스트

- [ ] §3의 5개 행을 Appendix A 표 마지막에 추가 (P7-V14 다음)
- [ ] (선택) 본문 §3 청킹 정책 표에 P7-V15/V16 인용 행 추가
- [ ] 노션 동기화 (들여쓰기 검증)
- [ ] git commit 후 검증
