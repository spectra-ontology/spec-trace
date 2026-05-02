# RAN1 사용자 직접 작업 가이드 — Phase-7 Spec 정정 (코드는 Claude 완료)

> **정정 (2026-04-29)**: 이전 버전은 RAN1 전체를 사용자 작업으로 잘못 분리했음. 정확한 보호 범위는 **Spec 본문만**(CLAUDE.md "🟢 RAN1 코드는 Claude 수정 가능. Spec만 사용자 권한").
>
> **Claude 완료 항목** (이번 세션):
> - ✅ RAN1 chunker 코드 패치 (`scripts/phase-7/RAN1/ts-parser/01_parse_ts_sections.py`)
> - ✅ RAN1 chunks.json P1.2 split 적용 (5 splits, 38.212/38.213/38.214 각 1~3건)
> - ✅ RAN1 main 컬렉션 재인덱싱 (`ran1_ts_sections`: 952 → 1,002 chunks, P1+P2 누적)
> - ✅ RAN1 검증 (validate_chunk_quality.py PASS, P2 적용 후 max 6,473 토큰, violations=0)
> - ✅ count_tokens tiktoken 정확 측정 적용 (이전 `len/4` 추정 → 실측 기반)
>
> **사용자 직접 작업 (Spec만)**:
> - ⏳ `docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md` P7-V11/V12 추가 + ASN.1 V2 정책 (필요 시)

## RAN1 Spec 정정 가이드 (사용자 직접)

`docs/RAN1/phase-7/specs/tdoc_vectordb_specs(TS).md`에 다음을 추가하시면 5 WG 일관성 완성됩니다.

### 추가할 내용 (청크 정책 표 또는 §3.x 내)

```markdown
| **🔴 [P7-V11] HARD_MAX (2026-04-29 신설)** | **6,500 토큰 (2026-04-29 P2 정정값, 이전 7,500)** | **모든 청크 (절대 상한)** | **embedding 모델 8,192 토큰 한계 - 안전 마진. 단일 paragraph가 HARD_MAX 초과 시 행/문자 단위 강제 split. P7 완료 게이트에서 violations=0 강제.** |
| **[P7-V12] EMBEDDING_MODEL** | **`openai/text-embedding-3-small`** | **임베딩 단계** | **max 8,192 토큰. chunker 변경 시 본 모델 한계와 일치 여부 검증 필수.** |

> **[P7-V11/V12 신설 배경 (2026-04-29)]**: 4Q usecase 평가에서 chunker 결함 검출 — paragraph 단위 split만 수행하여 거대 표 split 불가. RAN1은 영향 6건으로 적었으나 5 WG 통합 시 748건. 5 WG 공통 라이브러리 `scripts/cross-phase/common/chunker.py` 사용.
> **검증**: `validate_chunk_quality.py --wg RAN1` PASS (P2 적용 후 max 6,473 토큰, violations=0).
> **참조**: `docs/cross-phase/standards/chunking_standards.md`, `docs/usecase/evaluations/3way/root_cause_analysis.md`
```

### ASN.1 V2 정책 (RAN1은 해당 없음)

RAN1은 PHY spec이라 ASN.1 IE 본문이 거의 없음. ASN.1 별도 컬렉션(`ran1_ts_asn1_chunks`) 신설 불필요.
다른 WG의 spec에는 ASN.1 V2 섹션을 추가했으나, RAN1 spec에는 추가하지 않으셔도 됨 (해당 사항 없음).

## 작업 시간

- Spec 본문에 위 표 항목 2개 + 설명 1단락 추가: 약 5분

## 검증 (적용 후)

```bash
python3 scripts/cross-phase/validation/validate_chunk_quality.py --wg RAN1
# 기대 결과: ✅ G1+G2 PASS (이미 PASS 상태, spec 정정과 무관하게 유지)
```

## 참조

- 이번 세션 root cause: [root_cause_analysis.md](root_cause_analysis.md)
- 5계층 개선 계획: [systemic_improvement_plan.md](systemic_improvement_plan.md)
- chunking 표준: `docs/cross-phase/standards/chunking_standards.md`
- 교훈: `docs/common/implementation_process.md` 교훈 53/54
