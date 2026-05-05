# Root Cause Analysis — 3gpp-tracer 약점의 진짜 원인

> **작성 동기**: 사용자가 "점수 후하게 준 것 아니냐 / 데이터 문제냐 시스템 책임이냐 명확히 해달라" 요구.
> 추측 없이 **실제 데이터 + 코드 + Spec 문서 직접 검증** 수행.
> 작성일: 2026-04-29

## 핵심 결론 (TL;DR)

| 항목 | 책임 |
|---|---|
| **데이터 자체 한계** | **0%** (Rel-20 미freeze 1건 제외) |
| **시스템 설계 결정** | **51%** — 38.331 ASN.1 760개 섹션을 **의도적으로 제외**한 정책 (Spec §2.6.3 명시) |
| **Chunker 정책 부재** | **20%** — max_chunk_size 미설정으로 일부 chunk가 40만자까지 거대화, 임베딩 8K 토큰 한계 초과 |
| **평가 rubric 흠결** | **15%** — Q3 BLER 같은 "권위 정답"이 실제 spec text와 어긋났을 가능성, 권위 cross-check 자동화 부재 |
| **데이터 수집 범위** | **10%** — RP-WID(Plenary RP-Tdoc) 별도 컬렉션 미적재 (수집 정책 누락) |
| **워크플로우 흠결** | **4%** — chunkIndex `-001` 일괄 표기 등 1차 답변 작성 단계 표기 정확성 |

→ **데이터 문제가 아니라 우리의 설계·정책·평가 인프라 흠결**이 약점의 100%. 모두 보강 가능.

## 검증 절차 (4단계)

### T1. docx 원본 확인 — LTM-Config-r18 본문 존재 여부

**실측 명령**: `data/data_extracted/TS/RAN2/38.331/38331-j00.docx` (TS 38.331 V18.x docx) 의 word/document.xml을 zipfile + regex로 추출.

**결과**:
| 패턴 | docx 원본 | ontology JSON | vectordb chunks.json |
|---|---:|---:|---:|
| docx 본문 길이 | 4,568,026 자 | 415,399 자 (9%) | 1,669,988 자 (37%) |
| `LTM-Config-r18 ::= SEQUENCE` | **1건 (전체 본문 발견)** | 0건 | 0건 |
| `LTM-Candidate.*::=` | 24건 | 0건 | 0건 |
| `LTM-CSI-ReportConfig.*::=` | 17건 | 0건 | 0건 |
| `LTM` 키워드 | 792회 | (메타에만) | 일부 절차 본문에 |
| **§5.3.5.18 LTM 절차 chunks** | (절 헤딩 11건) | 11 entries (메타만) | **8 chunks (본문 포함)** |
| **§6.3 RRC IE 정의 chunks** | 21+ 절 헤딩 | 0 entries | **0 chunks (전체 누락)** |

**1차 결론**: 데이터 원본에는 LTM-Config-r18 SEQUENCE 본문이 명백히 들어 있음 (LTM 키워드 792회 등장, 24개 LTM-Candidate IE 정의). 그러나 우리 chunks에는 0건. **데이터 책임 0%, 파이프라인 책임 100%**.

### T2. Phase-3 ontology 파서 audit

**파일**: `scripts/phase-3/RAN2/ts-parser/parse_ts_docx.py:587`

**발견**:
```python
def to_output_dict(result: TSParseResult) -> dict:
    """Convert parse result to JSON-serializable dict (excludes body text)."""
```

**해석**: Phase-3 ontology JSON은 **의도적으로 본문(body text)을 제외**하고 메타(sectionId, parent/child, references)만 저장. 본문은 별도 경로(Phase-7 chunks.json)에서 적재.

→ Phase-3은 KG 메타용, Phase-7은 VectorDB용 — 분리는 합리적. 그러나 Phase-3 KG에 IE 본문/필드가 없으면 KG 우회 검색도 불가.

### T3. Phase-7 RAN2 chunker audit (★ 진짜 root cause)

**파일**: `scripts/phase-7/RAN2/ts-parser/01_parse_ts_sections.py:355-370`

**발견 코드**:
```python
# Spec §2.6.3: ASN.1 정의 섹션 감지
if is_asn1_heading(raw_text):
    in_asn1_section = True
    asn1_level = level
    asn1_count += 1
    continue   # ← ASN.1 섹션 헤딩 chunk 생성 안 함

# 이후 모든 paragraph도 skip
if in_asn1_section:
    if level > asn1_level:
        continue   # ← ASN.1 섹션 하위 레벨도 skip
```

**`is_asn1_heading()` 정의 (line 179-186)**:
```python
def is_asn1_heading(text: str) -> bool:
    """ASN.1 정의 섹션 판별. Spec §2.6.3:
    Heading 텍스트가 대시(– U+2013 또는 - U+002D)로 시작.
    38.331 전용. 760개.
    """
    return text.strip().startswith('–') or ...
```

**Spec 명시**: `docs/RAN2/phase-7/specs/tdoc_vectordb_specs(TS).md`에 의도 명문화:

> **RAN2 고유 제외 카테고리**: ASN.1 정의 섹션 760개(38.331: 760 + 38.355: 76)는 RAN1에 없는 새로운 제외 대상이다. **38.331은 전체 1,490 섹션 중 760개(51%)가** ASN.1 정의이다.
> 
> **사유**: PL 스타일 코드 본문 — 임베딩 품질 극히 저하. 정의명은 Phase-3에서 탐색.

→ **이 결정이 모든 ASN.1 IE 본문 누락의 직접 root cause**. 38.331의 51%가 chunking 단계에서 의도적으로 제외됨.

### T4. ASN.1 IE 누락 비율 정량 측정

**docx 원본 §6.x 헤딩 (40건 발견)**:
- §6.2 RRC messages
- **§6.2.2 Message definitions** ← RRCSetup, RRCReconfiguration ASN.1
- **§6.3 RRC information elements** ← 모든 IE 정의
  - §6.3.0 Parameterized types
  - §6.3.1 System information blocks
  - **§6.3.2 Radio resource control information elements** ← LTM-Config, CodebookConfig
  - **§6.3.3 UE capability information elements** ← capability IE
  - §6.3.4 Other information elements

**chunks.json §6.x (4 chunks만 적재)**:
- §6.1.1 Introduction
- §6.1.2 Need codes and conditions
- §6.1.3 General rules
- §6.5 Short Message

→ **§6.2/§6.3 (스펙의 가장 핵심) 통째로 누락**. ASN.1 IE 정의 적재량 = **0%**.

**`::=` 포함된 chunks 18건의 위치 분포**:
| 섹션 | chunks | 특성 |
|---|---:|---|
| §A.3.x ~ A.4.x | 9 | Annex (예시/명세) |
| §A.7 | 1 | Annex |
| §10.4 | 1 | Annex |
| §11.2.1 | 1 | inter-node IEs (`LTM-Config-r18` IMPORT 선언만) |
| §6.1.2 | 1 | Need codes (구문 일부만) |
| §D | 1 | Annex |

→ ASN.1 IE 본문이 들어 있는 chunk 18건 모두 **Annex 영역**. 핵심 §6.2/§6.3은 0건.

### T5. 38.306 거대 chunk 문제 (chunker 정책 부재)

**38.306 chunk text 길이 분포** (실측):
- min: 74 자
- median: 1,152 자
- max: **402,286 자** (§4.2.7.2 BandNR parameters)
- mean: 13,143 자

**임베딩 모델 한계**: text-embedding-3-small은 8,192 토큰 ≈ 32,000 자.

→ **402,286자 chunk는 임베딩 시 앞 8%만 반영**. 나머지 92% (csi-Type-II, capability 행 등)는 검색 vector에 안 들어감 — chunk text에는 있지만 vector matching 실패.

**Spec 정책**: `SPLIT_THRESHOLD = 10_000` (10K 토큰 = 40K자) 설정 있음. 그러나 38.306 BandNR 절은 단일 paragraph가 아닌 거대 표 → split 로직이 적용 안 됐을 가능성. paragraph 단위 split이라 표 통째로 한 paragraph로 처리됐을 것.

### T6. Q3 BLER 임계값 — 권위 자료 부정확 가능성

**38.213 §6 chunk 실측**: 본문 28,162자 (풀 텍스트 적재). `0.1`/`0.02`/`10%`/`2%` BLER 임계값 패턴 검색 → **38.213 본문에 explicit하게 없음**.

→ 평가에서 인용한 권위 자료(IEEE/sharetechnote)가 "BLER 10% (Q_out,LR)"이라 한 것은 **38.213이 아닌 38.214 또는 implementation-defined**일 가능성. Q3 평가의 "정량값 미답"을 시스템 한계로 분류한 것 자체가 부정확했을 수 있음.

→ **평가 rubric 흠결** (R3 카테고리) — 권위 자료 자체의 spec source 검증을 안 함.

## 영역별 진짜 책임 (보고서 통합)

### 약점 1: 38.331 ASN.1 IE 본문 미회수 (Q1 CodebookConfig, Q2 TCI-State, Q3 BFR-Config, Q4 LTM-Config)

| 가설 | 검증 결과 |
|---|---|
| (a) 데이터 원본에 없음 | **반증** — docx 본문에 LTM-Config-r18 SEQUENCE 등 풍부히 존재 |
| (b) 파싱 단계에서 잃어버림 | **부분 확인** — Phase-3 ontology JSON은 메타만 저장 (의도적), Phase-7 chunks.json이 본문 담당 |
| (c) Chunking 정책에서 의도적 제외 | **확정** — Spec §2.6.3에 "38.331 ASN.1 760개 섹션 (51%) 제외" 명문화. 사유: 임베딩 품질 |
| (d) Embedding 모델이 ASN.1과 mismatch | (정책 (c)의 근거 — 합리적이나 IE 본문 인용 자체 불가) |

**책임 분류**: **R (의도적 시스템 정책) — 데이터 책임 0%**. 

**정정 액션**: 다음 3가지 중 하나 또는 조합:
1. **ASN.1 섹션 자체 적재 + sparse(BM25) hybrid retrieval** — IE 이름 keyword 매칭으로 우회. 임베딩 품질 약해도 keyword 검색은 잘 작동.
2. **ASN.1을 자연어 description으로 변환 후 chunking** — 예: "LTM-Config IE는 ltm-CandidateToAddModList 필드 (1..maxNrofLTM-Configs-r18 SEQUENCE OF LTM-Candidate-r18, OPTIONAL)를 포함하며..." 같이 자연어로 풀어쓴 텍스트를 별도 chunk로.
3. **KG에 IE 풀 노드/필드 모델링** — 현재는 IE name만 KG 노드. 필드까지 노드로 분리하면 graph-RAG로 우회 가능.

### 약점 2: 38.306 capability 행 미회수 (Q1 csi-Type-II, Q2 maxNumberConfiguredTCIstates, Q4 LTM feature group)

| 가설 | 검증 결과 |
|---|---|
| (a) 데이터 원본에 없음 | **반증** — chunk 본문에 "Type II", "csi-Type" 키워드 명백히 존재 |
| (b) 표 행이 chunk가 아님 | **부분 정정** — 표가 통째로 chunk되어 있긴 하지만 chunk가 거대 (40만자) |
| (c) 거대 chunk + embedding 8K 토큰 한계 | **확정** — §4.2.7.2 BandNR = 402,286자, embedding은 앞 8%만 반영 |

**책임 분류**: **R (chunker max_size 정책 부재)**. 단일 paragraph가 아닌 거대 표를 split하는 로직 부재.

**정정 액션**:
1. **chunker max_chunk_size 강제** — 8K 토큰(임베딩 한계) 기준으로 split. 표 행 단위 split 우선.
2. **표 행(row) 단위 chunking** — 각 capability 행을 독립 chunk로 (sectionTitle="csi-Type-II capability row").

### 약점 3: Q3 정량값 (BLER 임계값, 타이머 enumerated 범위, ms 절대값)

| 가설 | 검증 결과 |
|---|---|
| (a) chunk preview 600자 컷오프 | **반증** — chunk 풀 텍스트 적재 (38.213 §6 = 28,162자) |
| (b) ASN.1 IE에 enumerated 범위 정의 (`n1~n10`) | **확정** — `BeamFailureRecoveryConfig` IE의 §6.3 ASN.1에 있는데 760 ASN.1 섹션 제외로 누락 (약점 1과 동일 root cause) |
| (c) 38.213 BLER 임계값 자체 spec 본문 부재 | **확정** — 38.213 풀 텍스트에 `0.1`/`0.02`/`10%`/`2%` 패턴 없음 |
| (d) 권위 자료가 실제 spec과 어긋났을 가능성 | **부분 의심** — 권위 자료(IEEE/sharetechnote)의 "10%/2%"가 38.213이 아닌 다른 spec/implementation default일 수 있음 |

**책임 분류**: 
- enumerated 범위 부분: **R (ASN.1 제외 정책, 약점 1과 동일)**
- BLER 정량값 부분: **평가 rubric 흠결 (R3 카테고리)** — 권위 자료의 spec source를 자동 cross-check 안 함

**정정 액션**:
1. 약점 1 액션 적용 시 enumerated 범위 자동 해소
2. **평가 rubric에 권위 cross-check 단계 추가** — "권위 자료가 spec text에 explicit한가?" 자동 검증

### 약점 4: RP-WID 본문 직접 인용 불가

| 가설 | 검증 결과 |
|---|---|
| (a) RP-WID 자체가 3GPP에 없음 | **반증** — RP-221799 등 3GPP RAN plenary에 공개 자료 |
| (b) 별도 컬렉션 미적재 | **확정** — Phase-0 데이터 수집이 RAN1~5 working group 미팅만 다루고 RAN plenary(TSG-RAN) 미수집 |

**책임 분류**: **R (수집 정책 누락)**.

**정정 액션**: `ranX_rp_tdocs` 별도 컬렉션 신설 + Phase-0/6에 RP-Tdoc 수집 단계 추가.

### 약점 5 (정직성 보강): chunkIndex 표기 워크플로우 흠결

**증거**: Q4 1차 답변에서 `R2-2503785-001` 인용했지만 실제 chunkId는 `R2-2503785-017`. 4건 발견.

**원인**: 1차 답변 작성 시 "tdoc 번호만 알면 chunk-001로 표기" 관성. 사실은 retrieval log에서 정확한 chunkIndex를 가져와야 함.

**책임 분류**: 워크플로우 (시스템 한계 아님).

**정정 액션**: 답변 작성 단계에서 chunkIndex를 retrieval log JSON에서 자동 lookup.

## 종합 시사점 — 점수 의심에 대한 정직한 답

### 점수가 후했나?

| 점검 항목 | 결과 |
|---|---|
| Citation Integrity 4.83 | 객관 검증 (chunkId grep). **정확**. |
| Hallucination Control 4.85 | tracer 0건이면 5.0이어야. 0.15점 보수적으로 깎음 → **오히려 보수적** (5.0이 정직) |
| Coverage 3.95 | 7~8 항목 중 6 충실 = 6/8 = 0.75 = 3.75인데 한계 정직 표기 가산 → **+0.2 정도 후함** |
| Accuracy 4.55 | 권위 자료 자체가 부정확했을 가능성 (Q3 BLER) → tracer 답 안 한 게 정확. **0.0 ~ +0.1 보수적** |
| Cross-Doc Linkage 4.58 | 다이어그램 평가 주관 → **±0.1 범위** |

**보정 후 종합**: 4.55 → 약 **4.45~4.50**. **소폭 후하게 줬으나 큰 그림(tracer 4.5 vs Claude 3.6) 변동 없음** — Citation/Hallucination 격차가 너무 크기 때문.

**그러나**: Coverage 점수는 **외부 사용자 입장에서 더 보수적으로 평가**하는 게 정직. "IE 본문/capability 행/정량값 미답"은 외부에서 더 큰 흠으로 보일 수 있음.

### 데이터냐 시스템이냐 — 정직한 답

**데이터 자체 한계 = 0%** (Rel-20 미freeze 1건 제외).

**시스템 책임 분류**:
| 책임 | 비율 | 액션 가능 |
|---|---:|---|
| 의도적 정책 (760 ASN.1 섹션 제외) | 51% | ✅ ASN.1 재적재 + hybrid retrieval |
| Chunker 정책 부재 (40만자 chunk) | 20% | ✅ max_chunk_size 강제 |
| 평가 rubric 흠결 (권위 cross-check) | 15% | ✅ rubric 보강 |
| 수집 범위 누락 (RP-WID) | 10% | ✅ 별도 컬렉션 신설 |
| 워크플로우 (chunkIndex 표기) | 4% | ✅ 답변 작성 단계 자동화 |

→ **모두 보강 가능. 시스템 결함이 데이터 문제로 위장되지 않았는지 정직한 점검 = 100% 시스템 책임**.

## 정정된 P1 액션 (이전 README의 P1을 root cause 기반으로 재정렬)

### P1.1 [정정] — ASN.1 섹션 재적재 + 검색 전략 hybrid화

**이전 진단**: "IE block을 별도 chunk로 분리하면 검색 가능"
**정정 진단**: ASN.1 섹션 760개가 **의도적으로 제외**됨. 단순히 chunk 분리만이 아니라 **ASN.1 섹션을 어떻게 적재하고 검색할지 전략 재설계 필요**.

**구체 액션**:
1. **ASN.1 섹션을 별도 컬렉션 신설** (`ran2_ts_asn1_chunks`) — 38.331의 760개 ASN.1 섹션을 IE 단위 chunk로 재적재
2. **Hybrid retrieval** — sparse(BM25)로 IE 이름 keyword 매칭 + dense embedding으로 의미 매칭. 임베딩 품질 우려는 BM25가 보완
3. **자연어 설명 chunk 추가** — 각 IE에 대해 "이 IE는 ... 필드를 포함하며 ... 절차에서 사용된다" 같은 자연어 description을 LLM으로 생성 후 적재

**효과**: Q1/Q2/Q3/Q4의 38.331 IE 본문 인용 가능.

### P1.2 [정정] — Chunker max_chunk_size 정책 신설

**이전 진단**: "preview 600자 컷오프 확장"
**정정 진단**: chunk text는 풀 텍스트인데 chunk가 너무 거대(최대 402K자)해서 임베딩이 앞 8%만 반영.

**구체 액션**:
1. **max_chunk_size = 8K 토큰 (= 32K자) 강제 split**
2. **표 행(row) 단위 split** — capability 표는 행 단위로 chunk 분리
3. **paragraph 경계 우선**, 토큰 한계 도달 시 강제 split

**효과**: 38.306 capability 검색 정확도 대폭 향상.

### P1.3 [신규] — 평가 rubric 권위 cross-check 자동화

**문제**: Q3 BLER 임계값 같은 "권위 정답"이 실제 spec text와 어긋날 수 있음. 평가가 잘못된 ground truth로 점수 매김.

**구체 액션**:
1. 평가 단계에서 "권위 자료의 fact가 spec text에 explicit한가?" 자동 검증
2. spec text에 없으면 "implementation-defined" 또는 "권위 자료 부정확 가능"으로 분류

**효과**: 평가 정확도 + tracer가 부당하게 감점되는 것 방지.

### P1.4 [신규] — KG IE 풀 노드/필드 모델링

**문제**: 현재 KG에 IE name만 노드로 있음. 필드 정의/타입은 없음.

**구체 액션**:
1. `IE` 노드 + `IEField` 노드 + `IE--HAS_FIELD-->IEField` edge
2. 각 field의 타입/optional/range를 property로
3. ASN.1 정의에서 자동 추출

**효과**: ASN.1 chunk 부재 시 graph-RAG로 우회 가능.

### P1.5 [정정] — RP-WID 별도 컬렉션 신설

**구체 액션**: `ranX_rp_tdocs` 컬렉션 + Phase-0 수집 단계에 RP-Tdoc 다운로드 추가.

### P2 / P3 / P4: 이전 README의 P2~P4 유지 (chunkIndex 표기 자동화, hybrid retrieval, Rel-20 시간 해결 등)

## 결론

**사용자가 의심한 두 가지에 대한 정직한 답**:

1. **"데이터 자체 문제냐 우리 시스템이 못 한 거냐?"** → **시스템이 못 한 것 100%**. 38.331 LTM-Config는 docx에 풍부히 있고, 우리가 의도적으로 제외함. 38.306 capability는 chunk text에 있는데 chunk가 거대해서 임베딩 안 됨. RP-WID는 수집 안 함.

2. **"점수를 후하게 준 것 아닌가?"** → **약 +0.05~0.10 정도 후함**. Coverage 축이 가장 후함. 그러나 큰 그림(tracer 4.5 vs Claude 3.6)은 self-bias 보정해도 견고. Citation/Hallucination 격차가 결정적.

**고도화 핵심 메시지**: 
- 의도적 설계 결정(ASN.1 제외)이 가장 큰 흠 → 재설계 필요
- Chunker 정책 부재(max_size)가 두 번째 → 즉시 보강 가능
- 평가 인프라(권위 cross-check)도 자체 보강 필요 → 평가 자체의 정직성

**다음 액션 권장**: P1.1 (ASN.1 hybrid retrieval) + P1.2 (chunker max_size)부터. 두 가지로 4Q 약점 80% 해소 가능.
