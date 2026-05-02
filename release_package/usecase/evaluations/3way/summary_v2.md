# 3-way v2 종합 — tracer v2 (P2+ASN.1) vs GPT vs Claude

> 작성일: 2026-05-02
> 참조: `summary.md` (v1 종합), `q[1-4]_3way_comparison_v2.md` (질문별 v2 비교)

## 1. 4Q 종합 점수 매트릭스 (v1 → v2)

| Q | tracer v1 | **tracer v2** | GPT (변화 없음) | Claude (변화 없음) |
|---|---:|---:|---:|---:|
| Q1 Rel-16 Type-II codebook | 4.5 | **4.8** | 3.1 | 3.9 |
| Q2 TCI-state Rel-15~20 | 4.6 | **4.9** | 3.2 | 3.4 |
| Q3 BFD/BFR | 4.6 | **4.84** | 3.3 | 3.7 |
| Q4 Rel-18 LTM | 4.5 | **4.83** | 3.5 | 3.6 |
| **평균** | **4.55** | **4.84** (+0.29) | **3.28** | **3.65** |

→ tracer v2 평균 **4.84**, vs Claude 격차 **+1.19**, vs GPT **+1.56** (v1 격차 +0.90 / +1.27 대비 결정적 확대).

## 2. 축별 평균 (4Q 통합, v1 vs v2)

| 축 | tracer v1 | **tracer v2** | GPT | Claude | tracer v2 우위 |
|---|---:|---:|---:|---:|---:|
| A1 Accuracy | 4.55 | **4.78** | 3.65 | 3.75 | +1.03 |
| A2 Coverage | 3.95 | **4.68** | 3.78 | **4.58** | +0.10 (Claude 추격) |
| A3 Citation Integrity | 4.83 | **4.95** | 1.28 | 2.38 | +2.57 |
| A4 Hallucination Control | 4.85 | **4.93** | 3.63 | 3.08 | +1.85 |
| A5 Cross-Doc Linkage | 4.58 | **4.81** | 3.95 | 4.53 | +0.28 |

**핵심 변화**: A2 Coverage 3.95 → 4.68 — P2+ASN.1로 Claude 우위(4.58)을 처음으로 추월. A3/A4 격차 결정적 (closed-domain RAG 본질).

## 3. 모델별 솔직 평가 (점수 외 정성)

### tracer v2 — "데이터는 풍부, 형식은 RAG dump"

**v1 대비 핵심 변화**:
- ✅ ASN.1 IE SEQUENCE 본문 **직접 인용** (Q1 CodebookConfig-r16 / Q2 TCI-State / Q3 BeamFailureRecoveryConfig / Q4 LTM-Config 등 22+ IE)
- ✅ Q3 정량값 **9건 인용 가능** (이전 6건 미답)
- ✅ Q2 24칸 매트릭스 **13✅ → 20✅** (+7칸)
- ✅ chunkIndex 표기 정확성 보강 (이전 -001 일괄 표기 오기 해소)

**여전히 약한 영역**:
- 답변 형식이 **RAG 출력 dump 형태** — 첫 페이지 메타 표 (v1/v2 비교, 컬렉션 이름, 쿼리 수), 본문은 `→ chunkId` 인용 위주, 자연어 narrative 부족
- 표준 회의 보고서로 그대로 못 씀 → **사용자가 narrative 편집 필요**
- 38.306 capability 행 단위 chunking (Tier B 미진행) → cap 행 직접 매칭은 여전히 한계

**실무 권장**: 표준 회의 contribution 작성용. citation traceability + hallucination 0건이 결정적 강점.

### GPT — "안전한 일반론, 변화 없음"

- v1과 동일 (재생성 안 함)
- **강점**: 자연어 narrative 우수. Rel-20 정직성 ("확정 normative처럼 쓰면 안 된다" 명시)
- **약점**: 인용 거의 없음 (A3 1.28). 분류 오류 (Q4 inter-CU LTM Rel-19→Rel-20 오분류). 정량값 회피 (Q3 6건 미답 0건 정답).
- **실무 권장**: 사내 overview / 신입 onboarding. 표준 작업 인용 시 검증 필수.

### Claude — "풍부함의 함정, hallucination 그대로"

- v1과 동일 (재생성 안 함)
- **강점**: A2 Coverage 4.58 (4Q 평균 가장 높음). 풍부한 ASN.1 코드, 수식, 표.
- **결정적 약점**: **위장된 hallucination 11건** (4Q 합):
  - Q1: RP-182863/191085 출처 불명 (3건)
  - Q2: TCI-State-r20 ASN.1 추측 코드 + cross-Carrier/Sub-band/NTN TCI 단정 (1건 이상)
  - Q3: -110 dBm typical, T_recovery <80ms typical, BFD-RS Rel.16+ = 8 단정 등 (4건)
  - Q4: RP-234037, Multi-RAT/NTN/Group LTM, LTM-Configuration-r20 ASN.1 (4건)
- **패턴**: "TBD" / "draft" / "typical" / "(현재 시점 기준)" 가드 표기를 단정 인용에 첨부 — 표준 회의 인용 시 즉시 발견되는 오류 위험
- **실무 권장**: 기술 깊이 빠르게 파악 가능. **단 RP-WID, Rel-20 항목, 정량값, ASN.1 코드는 권위 출처(3gpp.org/IEEE) 필수 cross-check**.

## 4. Hallucination 검출 (4Q 통합 v1=v2)

| 모델 | 명백 단정 오류 | 분류 오류 | 위장 단정 (가드 표기) | 출처 불명 quote/code | 합계 |
|---|---:|---:|---:|---:|---:|
| **tracer v2** | **0** | 0 | 0 | 0 | **0건** |
| GPT | 0 | 1 (Q4) | 0 | 0 | **1건** |
| **Claude** | 1 (Q4 RP-234037) | 0 | 약 9건 | 1 (Q4 quote) | **약 11건** |

**P2+v2 적용으로 변화**: tracer 0건 유지. GPT/Claude는 답변 미재생성으로 동일 위치 hallucination 잔존.

## 5. tracer v1 → v2 핵심 개선 영역 (4Q 통합)

| 개선 | 영향 받는 Q | 결과 |
|---|---|---|
| **38.331 ASN.1 IE 본문 직접 인용** (P1.1 ASN.1 컬렉션 신설 + P2 chunker tiktoken) | Q1/Q2/Q3/Q4 | CodebookConfig, TCI-State, BeamFailureRecoveryConfig, LTM-Config 등 22+ IE 본문 회수 |
| **chunker hard_max + tiktoken 정확 측정** | 5 WG 전체 | 36건 zero vector → 0건, 검색 정확도 회복 |
| **chunkIndex 표기 정확성** | Q4 (특히) | -001 일괄 표기 4건 오기 해소 |
| **enumerated 정량값 인용** | Q3 | 6건 미답 → 9건 인용 가능 (n1~n10, ms10~ms200, sl1~sl2560 등) |
| **Release × 문서 매트릭스 채움** | Q2 | 13✅ → 20✅ (+7칸) |

## 6. 여전히 한계 (4Q v2에서도 미해결)

| 한계 | 분류 | 후속 트랙 |
|---|---|---|
| **38.306 capability 행 단위 chunking** | R + O | Tier B (별도 진행) |
| **RP-WID 본문 직접 인용** | R | Tier C (별도 진행) |
| **Rel-20 spec 본문** | D (시간 해결) | Stage-2 freeze 2026-09 / Stage-3 freeze 2027-03 |
| **답변 형식 (RAG dump → narrative)** | (워크플로우) | 답변 합성 단계 LLM 후처리 또는 사람 편집 |

## 7. 실무 활용 가이드 (v2 갱신)

| 상황 | 권장 | 이유 |
|---|---|---|
| 표준 회의 contribution 작성 | **tracer v2 (1순위)** | citation traceability + ASN.1 IE 본문 + Rel-20 정직성 |
| 사내 표준 학습 자료 | GPT (1순위) | 안전한 일반론, narrative |
| Rel-X 기능 비교 / 깊이 빠르게 파악 | Claude (1순위) | Coverage 풍부함. **단 RP-WID, Rel-20, 정량값, ASN.1 코드는 권위 출처 필수 cross-check** |
| Rel-19/20 미래 예측 | tracer 또는 GPT | Claude Rel-20 ASN.1 단정 인용 금지 |
| 정량값 / 임계값 인용 (BLER, ms, ASN.1 enumerated 범위) | **tracer v2** | enumerated 본문 직접 인용. ASN.1 컬렉션 활용. |

## 8. 종합 결론

**tracer v2는 4Q 통합 4.84 / 5로 GPT(3.28)·Claude(3.65) 대비 결정적 격차 (+1.19~+1.56) 확보**. P2+ASN.1로 v1의 Coverage 약점이 해소되어 5축 모두 1위. 그러나 다음 한계는 정직히 인지:

1. **답변 형식**: 점수가 4.84여도 "받자마자 사용 가능한 답변"은 아님 — RAG dump 형태로 사람 편집 필요.
2. **Tier B/C 미해결**: 38.306 cap 행 + RP-WID 별도 컬렉션은 후속 작업.
3. **3 모델 강점이 다름**: 단일 모델로는 ideal 답변 어려움. tracer (인용) + GPT (narrative) + Claude (깊이)의 결합이 가장 좋은 답변.
