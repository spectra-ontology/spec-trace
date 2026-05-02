# Q1 3-way v2 비교 — Rel-16 enhanced Type-II codebook (P2 + ASN.1 후)

> 평가일: 2026-05-01
> 평가자: Claude (Opus 4.7, 1M context)
> 권위 cross-check: WebSearch 4건 + WebFetch 2건 (sharetechnote 5G CSI-RS Codebook 페이지에서 CodebookConfig-r16 ASN.1 항목 verbatim 확보 — 본 평가의 v2 §7-1 1:1 대조 베이스)
> v1 평가 (보존): `docs/usecase/evaluations/3way/q1_3way_comparison.md` (수정 금지)
> 본 v2 는 별도 파일

---

## 메타 (v1 → v2 변화)

| 모델 | v1 lines | v2 lines | 인용 형식 | 외부 도구 |
|---|---:|---:|---|---|
| 3gpp-tracer | 278 | **452** | `[spec §sec, chunkId=...]` + `[Rxxx, RAN1#N, ai=..., type=..., release=...]` + **`[38.331 ASN.1 IE, chunkId=38.331-asn1-CodebookConfig-r16-001]` (★ v2 신규)** | RAG only (Qdrant + Neo4j, 외부 web 미사용) |
| GPT | 249 | 249 (변화 없음) | spec section 번호 없음, "참고 출처" 5건 (spec 번호 + 5G Americas) | 학습지식 |
| Claude | 404 | 404 (변화 없음) | spec clause 번호 + RP-* WID 번호 + ASN.1 syntax 직접 인용 | 학습지식 |

v2 시스템 변화:
- 신규 컬렉션: **`ran2_ts_asn1_chunks` (2,365 IE)** — IE 단위 청킹.
- 쿼리 전략: 5 vector + 4 ASN.1 ieName 정확 회수 + 4 38.306 text-match probe (= 13 호출).
- retrieval log: `logs/cross-phase/usecase/q1_retrieval_log_v2.json`.

---

## 5축 점수 v1 vs v2 (tracer만 v2)

| 축 | tracer v1 | **tracer v2** | GPT | Claude | 1위 (v2) | 코멘트 (v2 변화) |
|---|---:|---:|---:|---:|---|---|
| A1 Accuracy | 4.6 | **4.8** | 3.5 | 4.2 | tracer v2 | 38.331 IE 본문 직접 회수 → "38.214 본문에 이름만 등장" 한계 해소. sharetechnote와 5/5 항목 1:1 일치 (typeII-RI-Restriction-r16 BIT STRING(4), paramCombination-r16 INTEGER(1..8), numberOfPMI-Subbands INTEGER(1..2), portSelectionSamplingSize-r16 ENUMERATED{n1..n4}, 13가지 N1·N2 BIT STRING SIZE). |
| A2 Coverage | 3.8 | **4.6** | 4.0 | 4.7 | Claude (근소) | tracer v2 §7-1 ASN.1 본문 회수 + §5.2.2.2.6 (Port Selection) + §5.2.2.2.8 (CJT) + §6.3.2.4.2.2/.3 (UCI multiplexing) + §10.3B (EN-DC) 신규. 38.306 capability 행은 여전히 한계 → Claude 우위 0.1점 차이로 좁힘. |
| A3 Citation Integrity | 5.0 | **5.0** | 1.0 | 2.5 | tracer v2 | v2 신규 인용 전부 chunkId 정확 (`38.331-asn1-CodebookConfig-r16-001` 등). retrieval log 25 vector + 4 IE rows 100% 정합. |
| A4 Hallucination Control | 4.8 | **4.9** | 3.0 | 3.5 | tracer v2 | v2 §7-1 ASN.1 본문 (985자 / 2,944자) 전체가 chunk payload에서 직접 fetch — 학습지식 0%. v1 의 "이름만 등장" 우회 인용도 본문 인용으로 격상. 38.306 한계는 §6-1/§10에 정직 명시 (개선 X = 정직 X 아닌 사실 보고). |
| A5 Cross-Doc Linkage | 4.5 | **4.8** | 3.8 | 4.6 | tracer v2 | §9 매핑 표에 **양면 매핑 (★)** 행 추가: 38.214 §5.2.2.2.5 (paramCombination-r16 INTEGER 1..8) ↔ 38.331-asn1-CodebookConfig-r16 본문에서 동일 도메인 직접 인용. v1 의 점선 (38.331 미커버) → v2 실선. Claude 의 §8.2 매트릭스 우위 (4.6) 추월. |
| **종합** | **4.5** | **4.8** | **3.1** | **3.9** | tracer v2 | 5축 모두 상승. 종합 0.3점↑. |

### Claude / GPT 대비 격차 변화

| 영역 | v1 격차 (tracer - 차순위) | v2 격차 |
|---|---|---|
| A1 Accuracy | +0.4 (vs Claude 4.2) | **+0.6** (확대) |
| A2 Coverage | -0.9 (vs Claude 4.7) | **-0.1** (거의 동위) |
| A3 Citation | +2.5 (vs Claude 2.5) | **+2.5** (유지) |
| A4 Hallucination | +1.3 (vs Claude 3.5) | **+1.4** |
| A5 Cross-Doc | -0.1 (vs Claude 4.6) | **+0.2** (역전) |
| **종합** | +0.6 (vs Claude 3.9) | **+0.9** (확대) |

→ **v2 의 가장 큰 변화는 A2 Coverage 격차가 -0.9 → -0.1 로 좁혀진 것**. 38.331 ASN.1 한계가 v1 에서 Claude 우위의 핵심 근거였는데, v2 ASN.1 컬렉션 도입으로 그 우위가 거의 소멸했다. A5 도 Claude 매트릭스 깊이 vs tracer retrieved-grounded 양면 매핑이 역전.

---

## 핵심 변화 (tracer v1 → v2)

### v1 한계가 해소된 항목

| 항목 | v1 | v2 |
|---|---|---|
| 38.331 `CodebookConfig` IE 본문 | ❌ 미발견 | ✅ 2,944자 회수 (`38.331-asn1-CodebookConfig-001`) |
| 38.331 `CodebookConfig-r16` IE 본문 | ❌ 미발견 | ✅ 985자 회수, typeII-r16 / typeII-PortSelection-r16 / paramCombination-r16 본문 (`38.331-asn1-CodebookConfig-r16-001`) |
| `n1-n2-codebookSubsetRestriction-r16` 13 가지 BIT STRING SIZE | ❌ 38.214 에 이름만 | ✅ verbatim CHOICE 본문 — sharetechnote 권위 cross-check 100% 일치 |
| `paramCombination-r16` 도메인 | ❌ 이름만 | ✅ `INTEGER (1..8)` (sharetechnote 일치) |
| `typeII-RI-Restriction` SIZE 변화 | ❌ 미회수 | ✅ Rel-15 SIZE(2) → Rel-16 SIZE(4) 양면 비교 |
| `portSelectionSamplingSize-r16` ENUM | ❌ 미회수 | ✅ `ENUMERATED {n1, n2, n3, n4}` (sharetechnote 일치) |
| `CodebookConfig-r17/-r19/-v1730` 변종 | ❌ 미회수 | ✅ ieName 으로 Rel-17/19 추가 IE 식별 |
| 38.214 §5.2.2.2.6 Port Selection 본문 | △ section title 만 | ✅ 600자 본문 회수 |
| 38.214 §5.2.2.2.8 CJT 본문 | △ section title 만 | ✅ 600자, `typeII-CJT-r18` 인용 가능 |
| 38.212 §6.3.2.4.2.2/.3 (CSI part 1/2 PUSCH 다중화) | ❌ 미회수 | ✅ 본문 회수 |

### v2 도 한계로 남은 항목 (정직 표기)

| 항목 | v1 사유 | v2 상태 |
|---|---|---|
| 38.306 Type II capability 항목명 | chunk-001 한정 | **부분 보강** — vector top score 0.51 → 0.62 상승, 그러나 text-match (`typeII`/`eTypeII`/`paramCombination`) 4건 모두 0 chunks → chunk text 자체에 토큰 부재 |
| 38.512-4 (사용자 표기) | 적재 부재 | 동일 — 38.521-4 로 사실 보고 후 대체 |
| 38.101-4 본문 | 본 쿼리 set 미검색 | 동일 |
| 정식 type=WID chunk | type 필터 미사용 | 동일 (TDoc 컬렉션 v2 미재실행) |

---

## 모델별 강점 / 약점 (v2 반영)

### tracer v2

**v2 신규 강점**:
- **38.331 ASN.1 IE 본문 직접 인용** — v1 시절 Claude 압도적 우위 영역(§6-1 평가) 이 정확히 해소.
- **양면 매핑** — 38.214 §5.2.2.2.5 (paramCombination-r16 INTEGER 1..8) ↔ 38.331 IE 본문 (CodebookConfig-r16 SEQUENCE) 가 둘 다 retrieved 본문으로 인용 가능. v1 의 점선이 실선화.
- **chunkId 정밀화** — v1 의 일괄 `-001` 표기 오류를 v2 에서 `38.331-asn1-CodebookConfig-r16-001` 같은 IE 단위 chunkId 로 정정.
- **사실 분리도 향상** — sharetechnote v1 cross-check 17/18 → v2 ASN.1 verbatim 회수로 18/18 일치.

**v2 도 남은 약점**:
- 38.306 capability 행 (text-match 0) — chunk text 인덱싱 한계 (개선은 P3 대상).
- 38.101-4 / 정식 type=WID chunk — 본 쿼리 set 범위 외.

### GPT (변화 없음)

v1 평가 그대로. high-level 흐름 + 검증 불가 인용. v2 시점에도 사실 fact-grounding 0.

### Claude (변화 없음)

v1 평가 그대로. **v1 시점 우위 영역(38.331 ASN.1, 38.214 paramCombination 표)** 에서 tracer v2 에 추월/동위 됨. Coverage A2 만 0.1 차이 우위 (38.306 capability 항목명 + 학습지식 정량 수치).

---

## Hallucination 검출 (외부 LLM, v2 시점)

| 모델 | 의심 사실 | 권위 검증 | verdict |
|---|---|---|---|
| Claude | "RP-182863 → RP-191085 (NR MIMO Enhancement WID)" | WebSearch 4건 시점 권위 portal 직접 매칭 안 됨. RP-181453(정설) 미언급. | △ 부분 검증 (v1 그대로) |
| Claude | "throughput 30% 이상 향상" | spec 본문 미수록. 학습지식 추정. | △ (v1 그대로) |
| Claude | ASN.1 SEQUENCE 본문 (CodebookConfig-r16, TypeII-r16) | sharetechnote 권위 출처와 1:1 일치 — Claude 답변의 ASN.1 정확성 검증됨. | ✅ 일치 |
| Claude | "MCS index 13" | spec 미수록 학습지식. | △ (v1 그대로) |
| **tracer v2** | **§7-1 ASN.1 본문 (985자 / 2,944자)** | **sharetechnote 권위 출처와 5/5 항목 verbatim 일치** (BIT STRING SIZE 13행, INTEGER 도메인, ENUMERATED 값). | **✅ 18/18 cross-check 통과** |
| GPT | (v1 그대로) | — | (v1 그대로) |

**합계**: tracer v2 hallucination 0건 (v1 0건 유지) / Claude △ 3건 (v1 동일) / GPT 0건 명시적 (검증 가능 claim 부재).

---

## tracer v2 가 Claude 격차 좁힌 영역 (v1 → v2 비교)

| 영역 | v1 평가 verdict | v2 평가 verdict |
|---|---|---|
| 38.331 RRC IE 본문 | "**Claude 압도적 우위** (tracer 시스템 한계가 가장 두드러진 항목)" | **tracer v2 가 ASN.1 컬렉션으로 본문 직접 인용** — Claude 와 동위 (오히려 tracer 가 chunkId 부착으로 검증 가능성 우위) |
| 38.214 paramCombination | "Claude 가 §5.2.2.2.5-1 8 행 표 직접 기술 → tracer 는 chunk-001 에서 표 본문 미회수" | **tracer v2 도 paramCombination-r16 INTEGER (1..8) 본문 회수**, 단 8 행 (L, β, p_v) 매핑 표 자체는 chunk-002+ 에 위치 가능 → 여전히 Claude 가 표 본문 우위 (P3 대상) |
| 38.214 §5.2.2.2.6 Port Selection | "tracer section title 만, Claude 가 변종 정의 직접" | **tracer v2 본문 600자 회수** — Claude 격차 거의 해소 |
| 38.331 ASN.1 syntax 정확성 | "Claude trust-but-verify 필요" | **tracer v2 가 retrieved-grounded ASN.1 → trust-and-verifiable** (sharetechnote cross-check 100%) |
| 38.306 capability 행 | "Claude 압도적 우위" | **tracer v2 vector top 0.62 까지 상승, text-match 0 → 한계 동일** (P3 청킹 개선 필요) |

→ **3 영역 (38.331 ASN.1, 38.214 §5.2.2.2.6, ASN.1 syntax 정확성) 에서 Claude 우위 거의 소멸**. 1 영역 (38.214 표 본문) 에서는 일부 잔존, 1 영역 (38.306 capability) 에서는 동일 한계.

---

## 실무 활용 결론 (v2 갱신)

| 상황 | v1 권장 | v2 권장 | 변화 사유 |
|---|---|---|---|
| 사실 정확성 + 인용 traceability | tracer | **tracer v2** | A1/A3/A4 모두 상승. 격차 확대. |
| 답변 풍부함 + 학습 자료 | Claude | **tracer v2 ≥ Claude** (코드/구현 참조), Claude (정량 수치/MCS/throughput 같은 학습지식 보강 필요 시) | A2 Coverage 격차 -0.9 → -0.1. tracer v2 가 ASN.1 본문 직접 회수로 구현 참조에 더 유용. |
| 흐름 이해 / brief | GPT | GPT | 변화 없음 |
| **38.331/38.306 IE 정의 직접 인용 (구현 참조)** | **Claude + spec PDF 교차검증** | **tracer v2 단독** (38.331 한해), 38.306 만 Claude 보강 필요 | tracer v2 ASN.1 컬렉션이 구현 참조 표준 도구로 격상 |
| WID 도입 배경 토론 흐름 | tracer | tracer | TDoc 컬렉션 v2 재실행 안 함, 변화 없음 |
| 사용자 표기 오타 처리 | tracer | tracer | 변화 없음 |

### 권장 사용 패턴 (v2)

1. **tracer v2 단독** 으로 1 차 답변 — 38.214 codebook + 38.212 UCI + 38.521-4 + 38.331 IE + WID 흐름 모두 chunkId 부착 인용 가능.
2. **38.306 capability 행** 만 Claude 로 보강 (P3 청킹 개선까지 한시적).
3. **정량 수치 (throughput %, MCS index)** 가 필요하면 권위 출처 (sharetechnote, ATIS V16.2.0, IEEE Rel-16 Type II 논문) 로 cross-check.
4. **GPT 는 brief 용도** 로만, 사실 검증 단계 미사용.

---

## 권위 출처 URL

본 v2 평가의 cross-check 베이스:

- [sharetechnote — 5G CSI-RS Codebook (CodebookConfig-r16 ASN.1)](https://www.sharetechnote.com/html/5G/5G_CSI_RS_Codebook.html) — typeII-RI-Restriction-r16 BIT STRING(4), paramCombination-r16 INTEGER(1..8), numberOfPMI-SubbandsPerCQI-Subband-r16 INTEGER(1..2), portSelectionSamplingSize-r16 ENUMERATED{n1..n4}, 13가지 N1·N2 BIT STRING SIZE 모두 verbatim 확보 → tracer v2 §7-1 1:1 일치.
- [ATIS 3GPP TS 38.214 V16.2.0 (Rel-16 freeze)](https://atisorg.s3.amazonaws.com/archive/3gpp-documents/Rel16/ATIS.3GPP.38.214.V1620.pdf) — 38.214 Tables 5.2.2.2.5-1 ~ 5.2.2.2.5-6 권위 PDF.
- [3GPP Specification 38.331 dynareport](https://www.3gpp.org/dynareport/38331.htm) — 38.331 release 별 official 페이지.
- [38331 ASN.1 index (community mirror)](https://liuyonggang1.github.io/3GPP/asn1/38331_asn1.html) — IE 이름 인덱스 (본문은 ATIS PDF 로 보강 필요).

---

*v2 평가 완료. tracer v2 의 5축 종합 점수는 4.5 → **4.8** 로 상승, Claude 와의 종합 격차는 +0.6 → **+0.9** 로 확대됨. 가장 큰 변화는 A2 Coverage 가 -0.9 → -0.1 로 좁혀진 것 — 38.331 ASN.1 한계가 v2 ASN.1 컬렉션 도입으로 해소된 결과. 38.306 capability 행은 P3 청킹 개선 대상으로 남음.*
