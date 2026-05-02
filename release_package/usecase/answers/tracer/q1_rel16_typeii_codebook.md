# Q1. Rel-16 Enhanced Type-II Codebook 표준 아이템 정리

> 본 문서는 spec-trace (3gpp-tracer) 의 Qdrant + Neo4j 검색 결과만으로 작성된다. 외부 웹 검색 / 모델 일반 지식 사용 금지. 모든 사실 문장은 retrieved chunk 인용을 동반한다 (`[spec §sec, chunkId=...]` 또는 `[tdoc, meeting, agenda, type]`).
>
> **v2 갱신 (2026-05-01, P2 시스템 + ASN.1 컬렉션 활용)**: 본 답변은 P2 적용 후 시스템(`ran{1,2,4,5}_ts_sections` + `ran2_ts_asn1_chunks`)으로 5 핵심 쿼리를 재실행하여 보강했다. 가장 큰 개선은 **38.331 `CodebookConfig` / `CodebookConfig-r16` IE 본문**이 ASN.1 컬렉션에서 직접 회수되어, v1의 §7 미발견 항목이 해소된 점이다 (§7-1, §13 변화 비교). v1 답변은 `q1_rel16_typeii_codebook.v1.md` 에 보존.

## 0. 메타

| 항목 | 값 (v2 = P2 + ASN.1 / v1 비교) |
|------|------|
| 질문 | Rel-16 enhanced Type-II codebook 표준 아이템 정리 (WID, 38.211/212/214/306/331/521-4 + 연결고리) |
| 임베딩 모델 | `openai/text-embedding-3-small` (OpenRouter) |
| top_k | v2: 5 (compact 재실행) / v1: 10 |
| 사용 컬렉션 (v2 추가) | **`ran2_ts_asn1_chunks`** (2,365 IE), `ran1_ts_sections` (1,002), `ran2_ts_sections` (2,451), `ran4_ts_sections` (16,248), `ran5_ts_sections` (26,814) |
| 사용 컬렉션 (v1 그대로) | `ran1_ts_sections`, `ran2_ts_sections`, `ran4_ts_sections`, `ran5_ts_sections`, `ran1_tdoc_chunks`, `ran2_tdoc_chunks` |
| v2 쿼리 | **5 vector 쿼리 + 4 ASN.1 ieName 정확 회수 + 4 38.306 text-match probe** = 13건 |
| v1 쿼리 | TS 21 + TS-literal 2 + TDoc 7 = 30건 |
| v2 retrieved | 5 쿼리 × 5 hits = **25 hits**, ASN.1 정확 회수 4 IE (CodebookConfig 985~2944자 본문 전체) |
| 사용자 표기 "38.512-4" | spec-trace 내 적재 부재. **38.521-4** 로 대체 검색 결과 사용 (상세 §8) |
| Retrieval log | v2: `logs/cross-phase/usecase/q1_retrieval_log_v2.json` / v1: `logs/cross-phase/usecase/q1_retrieval_log.json` |

---

## 1. 3gpp-tracer 검색 결과 요약

| 항목 | 컬렉션 | spec 필터 | 대표 hit (top-1) | top score |
|------|--------|-----------|------------------|-----------|
| 38.211 CSI-RS | `ran1_ts_sections` | 38.211 | §8.4.1.5.3 Mapping to physical resources `[chunkId=38.211-8.4.1.5.3-001]` | 0.597 |
| 38.211 antenna ports | `ran1_ts_sections` | 38.211 | §8.2.4 Antenna ports `[38.211-8.2.4-001]` | 0.527 |
| 38.212 two-part UCI | `ran1_ts_sections` | 38.212 | §6.3.2.1.2 CSI `[38.212-6.3.2.1.2-014]` | 0.606 |
| 38.212 CSI report Type II | `ran1_ts_sections` | 38.212 | §6.3.1.1.3 HARQ-ACK/SR and CSI `[38.212-6.3.1.1.3-001]` | 0.583 |
| 38.214 Type II codebook | `ran1_ts_sections` | 38.214 | §5.2.2.2.7 Further enhanced Type II port selection codebook `[38.214-5.2.2.2.7-001]` | 0.559 |
| 38.214 Enhanced Type II (Rel-16) | `ran1_ts_sections` | 38.214 | §5.2.2.2.5 Enhanced Type II Codebook `[38.214-5.2.2.2.5-001]` | 0.465 |
| 38.214 codebookType typeII-r16 | `ran1_ts_sections` | 38.214 | §5.2.2.2.5a Refined eType II / §5.2.2.2.5 Enhanced Type II `[38.214-5.2.2.2.5-001]` | 0.554 / 0.465 |
| 38.306 capability | `ran2_ts_sections` | 38.306 | §4.2.7.10 Phy-Parameters `[38.306-4.2.7.10-001]` | 0.455 |
| 38.331 CodebookConfig | `ran2_ts_sections` | 38.331 | (직접 매칭 없음 — 한계 §10) | 0.46~0.57 |
| 38.521-4 Type II 성능 | `ran5_ts_sections` | 38.521-4 | §6.3.2.2.6 2Rx TDD FR1 Multiple PMI with 16Tx Enhanced TypeII codebook `[38.521-4-6.3.2.2.6-001]` | 0.514 |
| 38.521-4 PMI reporting | `ran5_ts_sections` | 38.521-4 | §6.3.2.1.6 / §6.3.3.1.6 Enhanced TypeII PMI test `[38.521-4-6.3.2.1.6-001]` | 0.512 |
| 38.512-4 (사용자 표기) | (모든 RAN5/4 컬렉션) | 38.512-4 | **0 hits — 적재 부재 확인** | — |
| WID/eT2 도입 (Rel-16) | `ran1_tdoc_chunks` | release=Rel-16 | R1-2202121 RAN1#108-e ai=7.2.6 discussion | 0.697 |
| DFT-based 압축 합의 | `ran1_tdoc_chunks` | release=Rel-16 | R1-1909583 RAN1#98 ai=7.2.8.1 discussion | 0.640 |
| eT2 UCI partitioning | `ran1_tdoc_chunks` | release=Rel-16 | R1-2112195 RAN1#107-e ai=7.2.6 discussion | 0.689 |

전체 30 쿼리 중 **TS-literal 2건만 0 hit, 나머지 28건 모두 10 hits 회수**.

---

## 2. WID 도입 배경 (Rel-16)

spec-trace 의 RAN1 TDoc 컬렉션에서 회수된 discussion/요약 문서로 도입 배경을 정리한다. spec-trace 에는 별도의 WID(`type=WID`) 청크가 본 검색 범위에서는 직접 회수되지 않았고 (한계 §10), Rel-16 MIMO WI 를 직접 인용한 discussion 문서가 대신 회수되었다.

- "The work item on Rel-16 MIMO enhancements has been specified [1]. ... The WI for Rel-16 covers several key features aimed at enhancing multibeam operation" `[R1-1903044, RAN1#96, ai=7.2.8.3, type=discussion, release=Rel-16]`. 본문은 RAN plenary 의 WI 문서 RP-182067 을 인용하면서 Rel-16 MIMO 향상 항목을 열거한다.
- 도입 동기 (overhead reduction) 가 합의된 시점:
  "For Rel-16 NR, agree on DFT-based compression as the adopted Type II rank 1-2 overhead reduction (compression) scheme ... determined from a set of predefined DFT vectors" `[R1-1909583, RAN1#98, ai=7.2.8.1, type=discussion, release=Rel-16]` 및 동일 본문 `[R1-1909918, RAN1#98, ai=7.2.8]`.
- Rel-16 으로 도입된 두 코드북:
  "Enhanced Type II codebook and Enhanced port-selection Type II codebook are introduced Rel-16. In CSI feedback based on these two codebooks, the actual number of coefficients ... is reported by UE" `[R1-2202121, RAN1#108-e, ai=7.2.6, type=discussion, release=Rel-16]`, 동일 표현 `[R1-2112195, RAN1#107-e, ai=7.2.6, type=discussion, release=Rel-16]`.
- 회사 입장 / 압축 기법 비교:
  "we provide some frequency-domain compression methods. ... several schemes towards Type II overhead reduction for rank 1 and 2 are listed, mainly including frequency-domain (FD) compression" `[R1-1812322, RAN1#95, ai=7.2.8.1, type=discussion, release=Rel-16]`.
  "ALT3 achieves the highest compression ratio compared to the other quantization schemes" `[R1-1902123, RAN1#96, ai=7.2.8.1, type=discussion, release=Rel-16]`.

요지 (retrieved 인용 기반):
1. Rel-16 MIMO WI 의 한 축으로 **Type II overhead reduction (rank 1/2)** 이 다루어졌다 `[R1-1903044]`.
2. 합의된 핵심 압축 기법은 **DFT-based frequency-domain compression** 이다 `[R1-1909583/1909918]`.
3. 결과적으로 **Enhanced Type II codebook** 과 **Enhanced port-selection Type II codebook** 두 코드북이 Rel-16 에 도입되었다 `[R1-2202121, R1-2112195]`.

---

## 3. 38.211 — CSI-RS resource configuration

retrieved 청크는 38.211 의 CSI-RS 매핑·자원 정의를 보여준다. (Rel-16 Type II 라는 단어가 38.211 본문에 직접 반복되지는 않으며, Type II 가 활용하는 일반 CSI-RS 자원 정의가 retrieved 된다.)

- "Zero-power (ZP) and non-zero-power (NZP) CSI-RS are defined — for a non-zero-power CSI-RS configured by the NZP-CSI-RS-Resource IE or by the CSI-RS-Resource-Mobility field in the CSI-RS-ResourceConfigM..." `[38.211 §7.4.1.5.1 General, chunkId=38.211-7.4.1.5.1-001]`.
- "Mapping to resource elements shall be done according to clause 7.4.1.5.3 with the following exceptions: only 1 and 2 antenna ports are supported, X∈{1,2}; only density ρ=1 is supported; zero-power CS..." `[38.211 §8.4.1.5.3 Mapping to physical resources, chunkId=38.211-8.4.1.5.3-001]` — sidelink CSI-RS 제약 조건을 보여주는 구절로, downlink 8.4.1.5.3 이 7.4.1.5.3 을 참조하는 구조를 retrieved 결과로 확인할 수 있다.

retrieved 결과 한계: 38.211 에서 Type II codebook 과의 직접적 결합 (port 수 N1·N2, oversampling O1/O2 의 CSI-RS 자원 정의) 은 별도 표 청크로 회수되지 않았다. **38.214 §5.2.2.2.5** 가 "PCSI-RS = 2·N1·N2" 와 antenna port {3000, …, 3031} 형태로 38.211 의 CSI-RS port 번호 규약을 직접 사용하고 있는 것이 retrieved 본문에서 드러난다 `[38.214 §5.2.2.2.5, 38.214-5.2.2.2.5-001]` (§4 참조).

---

## 4. 38.214 — Codebook 정의 (Enhanced Type II = Rel-16)

본 항목이 spec-trace 에서 가장 풍부하게 회수된 영역이다.

### 4-1. Enhanced Type II Codebook 본문

- "For 4 antenna ports {3000, 3001, …, 3003}, 8 antenna ports {3000, …, 3007}, 12, 16, 24, 32 antenna ports, and UE configured with higher layer parameter codebookType set to **'typeII-r16'** —
  - The values of N1 and N2 are configured with the higher layer parameter **n1-n2-codebookSubsetRestriction-r16** ...
  - The values of L, β and pυ are determined by the higher layer parameter **paramCombination-r16**, where the mapping is given in Table 5.2.2.2.5-1.
  - The UE is not expected to be configured with paramCombination-r16 equal to 3, 4, 5, 6, 7, or 8 when PCSI-RS=4; 7 or 8 when PCSI-RS<32; 7 or 8 when typeII-RI-Restriction-r16 is configured with ri=1 for any i>1; 7 or 8 when R=2.
  - The parameter R is configured with the higher-layer parameter **numberOfPMI-SubbandsPerCQI-Subband**." `[38.214 §5.2.2.2.5 Enhanced Type II Codebook, chunkId=38.214-5.2.2.2.5-001]`

이 청크 한 건이 Rel-16 Enhanced Type II 의 가장 핵심적인 spec 정의다. retrieved 본문에서 다음을 추출할 수 있다:
- 코드북 식별자: `codebookType = 'typeII-r16'` `[38.214 §5.2.2.2.5, 38.214-5.2.2.2.5-001]`.
- 안테나 포트 집합: 4/8/12/16/24/32 ports `[동일]`.
- 파라미터 조합 표: Table 5.2.2.2.5-1 (`paramCombination-r16` → L, β, pυ) `[동일]`.
- 부분 정밀도 제약: paramCombination 3..8 의 사용 조건 `[동일]`.
- subband 단위 정밀도 R: numberOfPMI-SubbandsPerCQI-Subband, R=1 / R=2 동작 `[동일]`.

### 4-2. 인접 절들 (retrieved)

- §5.2.2.2.3 **Type II Codebook** (Rel-15 기본형) `[38.214-5.2.2.2.3-001]` — Rel-16 enhanced 와 비교 baseline.
- §5.2.2.2.4 **Type II Port Selection Codebook** `[38.214-5.2.2.2.4-001]` — port selection 변종.
- §5.2.2.2.7 **Further enhanced Type II port selection codebook** `[38.214-5.2.2.2.7-001]` — Rel-17 이후 추가.
- §5.2.2.2.5a **Refined eType II Codebook** `[38.214-5.2.2.2.5a-001]` — `'eTypeII-r19'` (Rel-19 확장).
- §5.2.2.2.10 / §5.2.2.2.11 / §5.2.2.2.11a **Enhanced Type II codebook for predicted PMI** (`typeII-Doppler-r19`) `[각각 38.214-5.2.2.2.10-001, -5.2.2.2.11-001, -5.2.2.2.11a-001]` — 예측 기반 변종.

retrieved 본문에서 W1/W2/Wf 를 구체적으로 명시하는 청크는 chunk-001 범위에서 안 잡혔다 (각 절은 chunkIndex 0 만 회수됨). 본 답변은 chunk-001 본문에서 확인 가능한 사실에만 한정한다.

### 4-3. PMI 우선순위·CSI part2 분할 정의 (38.214 ↔ 38.212 연결)

- 38.212 §6.3.2.1.2 의 PMI 필드 분할 본문은 "based on the corresponding function Pril,i,f defined in **clause 5.2.3 of TS 38.214** [6]" 라고 38.214 를 직접 참조한다 `[38.212 §6.3.2.1.2, chunkId=38.212-6.3.2.1.2-014]`.

→ 38.212 의 UCI partitioning 규칙은 38.214 의 우선순위 함수에 의해 정의된다. spec-trace retrieved 결과에서 두 spec 의 연결고리가 본문 인용으로 직접 확인된다.

---

## 5. 38.212 — UCI field (two-part CSI report)

- "If none of the CSI reports for transmission on a PUCCH is of two parts, the UCI bit sequence is generated according to the following ..." `[38.212 §6.3.1.1.3 HARQ-ACK/SR and CSI, chunkId=38.212-6.3.1.1.3-001]` — two-part CSI 와 그 외 케이스의 분기.
- "CSI report #n CSI part 2, group 0 | PMI fields X1 ...
   CSI report #n CSI part 2, group 1 | The following PMI fields X2 ... i2,3,l, i1,5, i1,6,l ... and max(0, KNZ2-υ)×3 highest priority bits of i2,4,l ...
   CSI report #n CSI part 2, group 2 | The following PMI fields X2 ..." `[38.212 §6.3.2.1.2 CSI, chunkId=38.212-6.3.2.1.2-014]`.
- "(M-MR)-th reported CRI, if pmi-FormatIndicator= subbandPMI ... Subbands for given CSI report n indicated by the higher layer parameter csi-ReportingBand are numbered continuously" `[38.212 §6.3.2.1.2, 38.212-6.3.2.1.2-014]`.
- 본 청크는 38.214 §5.2.3 의 우선순위 함수 `Pri_l,i,f` 를 인용한다 (§4-3 동일 인용).

retrieved 결과로부터 38.212 의 핵심 사실:
- Type II CSI 는 **two-part UCI** 형태로 보고된다 (Part 1 + Part 2) `[38.212 §6.3.1.1.3, 38.212-6.3.1.1.3-001]`.
- Part 2 는 **3 개 group (group 0/1/2)** 으로 우선순위가 분할되며, X1 (광대역) 과 X2 (서브밴드) 필드, 비-제로 계수 (KNZ, KNZ2) 의 우선순위 비트 조각이 group 별로 매핑된다 `[38.212 §6.3.2.1.2, 38.212-6.3.2.1.2-014]`.
- 우선순위 함수 자체의 정의는 **38.214 §5.2.3** 에 위임된다 `[동일]`.
- PUSCH 에 다중화될 때는 §6.3.2.6 절차를 따른다 `[38.212 §6.3.2.6, 38.212-6.3.2.6-001]`.

---

## 6. 38.306 — UE capability

### 6-1. v2 결과 (P2 vector + text-match)

P2 시스템에서 vector top score 가 v1 0.45–0.51 → **0.62–0.63** 으로 상승했으나 (`ran2_ts_sections / 38.306` 필터), top hits 의 의미적 매칭 자체는 여전히 Type II 직접 항목이 아니다.

- top hits (vector, query="csi-Type-II UE capability feature group"):
  - §4.2.7.10 Phy-Parameters `[38.306-4.2.7.10-009]` score 0.6299 — `type1-HARQ-ACK-Codebook-r16` 등 type1/type2 HARQ-ACK 관련.
  - §4.2.7.2 BandNR parameters `[38.306-4.2.7.2-054]` score 0.6267 — `type2-HARQ-Codebook-r17` 등.
  - §4.2.7.10 Phy-Parameters `[38.306-4.2.7.10-001]` score 0.6255 — `absoluteTPC-Command` 등 일반 capability 항목 헤더.
  - §4.2.7.4 CA-ParametersNR `[38.306-4.2.7.4-036]` score 0.6242 — `totalCSI-RS-ResourceL1-Meas-r19` 등 LTM 관련.
  - §4.2.7.2 BandNR parameters `[38.306-4.2.7.2-053]` score 0.6205.
- text-match probe (정확 키워드 `typeII` / `eTypeII` / `paramCombination` / `csi-Type-II`, MatchText) → **모두 0 chunks** `[logs/cross-phase/usecase/q1_retrieval_log_v2.json: ts306_cap_probes]`.

retrieved 본문에 한정한 사실:
- vector 검색은 의미적 인접 항목(type1-HARQ-ACK-Codebook, type2-HARQ-Codebook 등)을 회수하는 데 그쳤다 — Type II codebook capability 와 단어 일치는 있으나 항목 자체는 다르다 `[38.306-4.2.7.10-009, 38.306-4.2.7.2-054]`.
- 정확 키워드 text-match 가 0 인 것은 **38.306 청크의 `text` payload 에 `typeII` / `eTypeII` / `csi-Type-II` 토큰이 포함되어 있지 않음**을 의미한다 (P2 system 의 chunk text 인덱싱 결과).
- TDoc 컬렉션에서도 RAN2 가 Type II capability 를 직접 다루는 chunk 는 v1 검색에서 false positive 만 회수 (msg3 eMTC).

→ **3gpp-tracer P2 시스템에서도 38.306 의 Type II capability 항목명/세부 비트 정의는 직접 미발견** (한계 §10). v1 대비 차이는 **vector top score 가 0.62 대로 상승**했으나 의미적 매칭 정확도는 동일하다는 점이다.

### 6-2. (참고) v1 회수 결과

(v1 §6 본문은 `q1_rel16_typeii_codebook.v1.md` 참조.) §4.2.7.4 / §4.2.7.10 / §4.2.7.6 chunk-001 들이 회수되었으나 Type II 항목 자체는 미명시.

---

## 7. 38.331 — RRC parameter (★ v2 핵심 보강)

### 7-1. ASN.1 컬렉션에서 직접 회수된 IE 본문 (v2 신규)

P2 시스템에 새로 추가된 `ran2_ts_asn1_chunks` 컬렉션에서 **`CodebookConfig`** 와 **`CodebookConfig-r16`** IE 본문이 정확 ieName 매칭으로 직접 회수되었다.

#### `CodebookConfig` (Rel-15 base IE) 본문 — `[38.331 ASN.1 IE, chunkId=38.331-asn1-CodebookConfig-001]`

```asn.1
CodebookConfig ::= SEQUENCE {
  codebookType CHOICE {
    type1 SEQUENCE { ... typeI-SinglePanel / typeI-MultiPanel ... },
    type2 SEQUENCE {
      subType CHOICE {
        typeII SEQUENCE {
          n1-n2-codebookSubsetRestriction CHOICE {
            two-one BIT STRING (SIZE (16)),
            two-two BIT STRING (SIZE (43)),
            four-one BIT STRING (SIZE (32)),
            three-two BIT STRING (SIZE (59)),
            six-one BIT STRING (SIZE (48)),
            four-two BIT STRING (SIZE (75)),
            eight-one BIT STRING (SIZE (64)),
            four-three BIT STRING (SIZE (107)),
            six-two BIT STRING (SIZE (107)),
            twelve-one BIT STRING (SIZE (96)),
            four-four BIT STRING (SIZE (139)),
            eight-two BIT STRING (SIZE (139)),
            sixteen-one BIT STRING (SIZE (128))
          },
          typeII-RI-Restriction BIT STRING (SIZE (2))
        },
        typeII-PortSelection SEQUENCE {
          portSelectionSamplingSize ENUMERATED {n1, n2, n3, n4} OPTIONAL,
          typeII-PortSelectionRI-Restriction BIT STRING (SIZE (2))
        }
      },
      phaseAlphabetSize ENUMERATED {n4, n8},
      subbandAmplitude BOOLEAN,
      numberOfBeams ENUMERATED {two, three, four}
    }
  }
}
```

(전체 본문 2,944자, retrieved log 의 `asn1_by_name[CodebookConfig]` 참조 — 위는 typeII / typeII-PortSelection 부분 발췌.)

#### `CodebookConfig-r16` (Rel-16 enhanced IE) 본문 — `[38.331 ASN.1 IE, chunkId=38.331-asn1-CodebookConfig-r16-001]`

```asn.1
CodebookConfig-r16 ::= SEQUENCE {
  codebookType CHOICE {
    type2 SEQUENCE {
      subType CHOICE {
        typeII-r16 SEQUENCE {
          n1-n2-codebookSubsetRestriction-r16 CHOICE {
            two-one BIT STRING (SIZE (16)),
            two-two BIT STRING (SIZE (43)),
            four-one BIT STRING (SIZE (32)),
            three-two BIT STRING (SIZE (59)),
            six-one BIT STRING (SIZE (48)),
            four-two BIT STRING (SIZE (75)),
            eight-one BIT STRING (SIZE (64)),
            four-three BIT STRING (SIZE (107)),
            six-two BIT STRING (SIZE (107)),
            twelve-one BIT STRING (SIZE (96)),
            four-four BIT STRING (SIZE (139)),
            eight-two BIT STRING (SIZE (139)),
            sixteen-one BIT STRING (SIZE (128))
          },
          typeII-RI-Restriction-r16 BIT STRING (SIZE (4))
        },
        typeII-PortSelection-r16 SEQUENCE {
          portSelectionSamplingSize-r16 ENUMERATED {n1, n2, n3, n4},
          typeII-PortSelectionRI-Restriction-r16 BIT STRING (SIZE (4))
        }
      },
      numberOfPMI-SubbandsPerCQI-Subband-r16 INTEGER (1..2),
      paramCombination-r16 INTEGER (1..8)
    }
  }
}
```

(전체 본문 985자, full IE.)

retrieved 본문에 한정한 사실 (v2 신규):

1. **Rel-16 Enhanced Type II 코드북의 RRC IE 는 `CodebookConfig-r16` 으로 별도 정의되어 있다** (Rel-15 base `CodebookConfig` 와 분리) `[38.331-asn1-CodebookConfig-r16-001]`.
2. **`typeII-r16` SEQUENCE** 가 enhanced Type II 본형, **`typeII-PortSelection-r16`** 가 port selection 변종 `[동일]`.
3. **`n1-n2-codebookSubsetRestriction-r16`** 는 N1·N2 조합 13 가지 (two-one ~ sixteen-one) 별로 BIT STRING 크기가 다른 CHOICE 구조 — 38.214 §5.2.2.2.5 의 antenna port 4/8/12/16/24/32 와 매핑 `[동일]`.
4. **`typeII-RI-Restriction-r16`** 는 `BIT STRING (SIZE (4))` 로 Rel-15 의 `BIT STRING (SIZE (2))` 대비 확장 (rank 4 까지 지원) `[CodebookConfig vs CodebookConfig-r16 본문 비교]`.
5. **`paramCombination-r16 INTEGER (1..8)`** 가 38.214 §5.2.2.2.5 의 Table 5.2.2.2.5-1 (L, β, p_υ 매핑) 의 입력 인덱스 `[38.331-asn1-CodebookConfig-r16-001]` ↔ `[38.214-5.2.2.2.5-001]`.
6. **`numberOfPMI-SubbandsPerCQI-Subband-r16 INTEGER (1..2)`** 가 38.214 §5.2.2.2.5 의 R 파라미터 (R=1 / R=2) 정의의 RRC 측 IE `[동일]`.

### 7-2. vector 쿼리 추가 회수 (CodebookConfig 변종)

ASN.1 vector top-5 (query="CodebookConfig IE typeII-r16 SEQUENCE"):

| score | ieName | spec |
|------|--------|------|
| 0.6851 | `CodebookConfig-r16` | 38.331 |
| 0.6779 | `CodebookConfig-r19` | 38.331 |
| 0.6757 | `CodebookConfig-v1730` | 38.331 |
| 0.6704 | `CodebookConfig-r17` | 38.331 |
| 0.6635 | `CodebookComboParametersAdditionPerBC-r16` | 38.331 |

→ **Rel-16 (`-r16`), Rel-17 (`-r17`), Rel-19 (`-r19`), v1730** 의 IE 변종이 모두 ASN.1 컬렉션에 존재 함을 v2 에서 확인 `[logs/cross-phase/usecase/q1_retrieval_log_v2.json: queries[0]]`.

### 7-3. v1 한계 해소

v1 §7 에서 미발견으로 분류했던 항목들:
- ✅ `CodebookConfig` IE 본문 — v2 §7-1 에서 정확 회수.
- ✅ `codebookType typeII-r16` ASN.1 분기 — v2 §7-1 의 `CodebookConfig-r16` typeII-r16 SEQUENCE 본문.
- ✅ `n1-n2-codebookSubsetRestriction-r16` IE 본문 — v2 §7-1 에 13 가지 N1·N2 조합 BIT STRING 크기 명시.
- ✅ `paramCombination-r16` IE 본문 — v2 §7-1 에 `INTEGER (1..8)` 명시.
- ✅ `typeII-RI-Restriction-r16` IE 본문 — v2 §7-1 에 `BIT STRING (SIZE (4))` 명시.

→ **v1 §7 의 미발견 항목은 v2 ASN.1 컬렉션에서 모두 해소.**

### 7-4. v1 vector 결과 (참고)

(v1 §7 본문은 `q1_rel16_typeii_codebook.v1.md` 참조.) §8.5 Padding, §11.2.1 General, §9.2.1 Default SRB 등 의미적 무관 절들만 회수되었다. 이는 v1 시스템이 **section 단위 청킹** 만 보유했기 때문이며, IE-level 청킹 (`ran2_ts_asn1_chunks`) 도입 후 해결되었다.

---

## 8. 38.512-4 / 38.521-4 — 성능 (UE conformance) requirement

### 8-1. 사용자 표기 "38.512-4" 검토

- spec-trace Qdrant 의 `ran5_ts_sections` 와 `ran4_ts_sections` 양쪽에서 `specNumber == "38.512-4"` 필터로 검색한 결과 **0 hits** `[logs/cross-phase/usecase/q1_retrieval_log.json: ts_queries_literal_user_typo[0..1]]`.
- **3gpp-tracer 에서 38.512-4 미발견.** 동일 의미 (UE conformance Performance) 의 적재된 spec 은 **38.521-4** (`ran5_ts_sections`, 617 points) 로 확인되며, 본 §8 은 38.521-4 결과에 한정한다.

### 8-2. 38.521-4 retrieved 본문 (Enhanced Type II 성능)

- "To test the accuracy of the Precoding Matrix Indicator (PMI) reporting such that the system throughput is maximized based on the precoders configured according to the UE reports.
  This test applies to all types of NR UE release 16 and forward supporting **Enhanced Type II codebook with at least 16 ports per CSI-RS resource**.
  This test also applies to all types of EUTRA UE release 16 and forward supporting EN-DC and Enhanced Type II codebook with at least 16 ports per CSI-RS resource.
  ...
  The normative reference for this requirement is **TS 38.101-4 [5], clause 6.3.2.2.6**." `[38.521-4 §6.3.2.2.6 2Rx TDD FR1 Multiple PMI with 16Tx Enhanced TypeII codebook for both SA and NSA, chunkId=38.521-4-6.3.2.2.6-001]`.
- 동일 시험의 FDD 변종 / 4Rx 변종:
  - §6.3.2.1.6 "2Rx FDD FR1 Multiple PMI with 16Tx Enhanced TypeII codebook" `[38.521-4-6.3.2.1.6-001]`
  - §6.3.3.1.6 "4Rx FDD FR1 Multiple PMI with 16Tx Enhanced TypeII codebook" `[38.521-4-6.3.3.1.6-001]`
- 시험 파라미터 발췌:
  "Bandwidth | MHz | 40; Subcarrier spacing | kHz | 30; Duplex Mode | TDD; TDD DL-UL configurations | FR1.30-1 ...; Antenna configuration | XP Medium 16 x 2 (N1,N2) = (4,2); CDM Type | CDM4 (FD2, TD2); ..." `[38.521-4 §6.3.2.2.6, 38.521-4-6.3.2.2.6-001]`.
- 주변 CQI reporting 시험 (Enhanced Type II 전용은 아님):
  - §6.2A.3.1.0 "Minimum requirement for periodic CQI reporting" `[38.521-4-6.2A.3.1.0-001]`
  - §8.2A.3.1.0 동명 `[38.521-4-8.2A.3.1.0-001]`

retrieved 본문에 한정한 사실:
- Rel-16 Enhanced Type II codebook 에 대한 demodulation/RF performance 시험은 **38.521-4 §6.3.x.x.6** ("Multiple PMI with 16Tx Enhanced TypeII codebook") 절들에 정의되어 있다 `[38.521-4-6.3.2.2.6-001, -6.3.2.1.6-001, -6.3.3.1.6-001]`.
- 정합성 (normative) 참조 spec 은 **TS 38.101-4 §6.3.2.2.6** 이라고 본문에 명시 `[38.521-4 §6.3.2.2.6, 38.521-4-6.3.2.2.6-001]`. (38.101-4 자체는 spec-trace 에서 본 검색 범위에서는 별도 회수되지 않았다.)
- 시험 대상 UE 범주는 **Rel-16 이후 NR UE / EN-DC EUTRA UE, ≥16 CSI-RS port 지원** `[동일]`.

---

## 9. 연결고리 (retrieved 근거 기반)

retrieved 본문 인용으로 확인 가능한 spec 간 직접 참조만 표기. 점선 화살표는 본문에 명시되지 않았으나 파라미터 이름 일치만 retrieved 로 확인되는 경우다.

| From | → | To | 근거 (retrieved) |
|------|---|----|-----------------|
| 38.214 §5.2.2.2.5 (Enhanced Type II 정의) | 사용 | 38.211 CSI-RS port 번호 {3000,…,3031}, PCSI-RS=2·N1·N2 | `[38.214 §5.2.2.2.5, 38.214-5.2.2.2.5-001]` 본문에 antenna port 번호와 PCSI-RS 식 직접 명시 |
| 38.214 §5.2.2.2.5 | 호출 | RRC higher-layer parameter `codebookType=typeII-r16`, `paramCombination-r16`, `n1-n2-codebookSubsetRestriction-r16`, `typeII-RI-Restriction-r16`, `numberOfPMI-SubbandsPerCQI-Subband` | `[38.214-5.2.2.2.5-001]` 본문 |
| 38.212 §6.3.2.1.2 (CSI Part 2 PMI 필드 분할) | 정의 위임 | 38.214 §5.2.3 우선순위 함수 `Pri_l,i,f` | `[38.212 §6.3.2.1.2, 38.212-6.3.2.1.2-014]` 본문 "defined in clause 5.2.3 of TS 38.214 [6]" |
| 38.212 §6.3.2.6 | 다중화 | PUSCH UCI 다중화 절차 (§6.2.7) | `[38.212 §6.3.2.6, 38.212-6.3.2.6-001]` |
| 38.521-4 §6.3.2.2.6 (Enhanced Type II 시험) | normative ref | TS 38.101-4 §6.3.2.2.6 | `[38.521-4 §6.3.2.2.6, 38.521-4-6.3.2.2.6-001]` 본문 명시 |
| RAN1 WI agreement (R1-1909583/1909918) | adopted scheme | 38.214 §5.2.2.2.5 typeII-r16 (DFT-based FD compression) | `[R1-1909583, RAN1#98, ai=7.2.8.1, type=discussion, release=Rel-16]` "agree on DFT-based compression as the adopted Type II rank 1-2 overhead reduction scheme" + `[38.214-5.2.2.2.5-001]` codebookType='typeII-r16' |
| **38.214 §5.2.2.2.5 (Enhanced Type II 정의)** | **양면 매핑 (★ v2)** | **38.331 `CodebookConfig-r16` IE (`typeII-r16` SEQUENCE)** | `[38.214-5.2.2.2.5-001]` 의 higher layer parameter (`paramCombination-r16` `INTEGER (1..8)` / `n1-n2-codebookSubsetRestriction-r16` 13 조합 / `typeII-RI-Restriction-r16 BIT STRING (4)` / `numberOfPMI-SubbandsPerCQI-Subband-r16 INTEGER (1..2)`) ↔ `[38.331-asn1-CodebookConfig-r16-001]` IE 본문에서 동일 필드명·정확한 도메인 직접 인용 (양 spec 본문이 모두 retrieved) |
| (점선) 38.214 §5.2.2.2.5 파라미터명 | 동명 | 38.306 capability 항목 | 38.306 측 직접 청크 미회수 (§6 — v2 도 한계 지속) |

요약 다이어그램 (retrieved 근거만 사용):

```
[Rel-16 MIMO WI / RP-182067]               ← R1-1903044
        │
        ▼
[RAN1#95~#98 합의: DFT-based FD compression]  ← R1-1812322 / R1-1902123 / R1-1909583/918
        │
        ▼
38.214 §5.2.2.2.5 Enhanced Type II Codebook (codebookType='typeII-r16')   ← 38.214-5.2.2.2.5-001
        │                            │
        │ (parameter names)          │ (priority function 5.2.3)
        ▼                            ▼
38.331 CodebookConfig-r16  ← 38.331-asn1-CodebookConfig-r16-001 (★ v2 신규)
   typeII-r16 SEQUENCE {                                        38.212 §6.3.2.1.2 CSI Part 2 PMI X1/X2     ← 38.212-6.3.2.1.2-014
     n1-n2-codebookSubsetRestriction-r16 (13 N1·N2 조합),               │
     typeII-RI-Restriction-r16 BIT STRING (SIZE (4)),                   ▼
     paramCombination-r16 INTEGER (1..8),                       38.212 §6.3.2.6 Multiplexing onto PUSCH    ← 38.212-6.3.2.6-001
     numberOfPMI-SubbandsPerCQI-Subband-r16 INTEGER (1..2) }
[38.306 UE capability — 미회수 (§6 v2 도 한계)]
        │
        ▼
38.521-4 §6.3.2.x.6 Multiple PMI w/ 16Tx Enhanced TypeII test            ← 38.521-4-6.3.2.2.6-001
        │
        └─ normative ref → TS 38.101-4 §6.3.2.2.6                         ← 동일 청크
```

---

## 10. 커버리지 및 한계

### 잘 회수된 항목

- **38.214 codebook 정의** (Rel-16 Enhanced Type II): §5.2.2.2.5 chunk-001 본문이 retrieved 되어 `codebookType='typeII-r16'`, `paramCombination-r16` 등 핵심 파라미터를 직접 인용 가능 `[38.214-5.2.2.2.5-001]`. **답변 가능 수준 高**.
- **38.212 UCI two-part CSI**: §6.3.2.1.2 / §6.3.1.1.3 / §6.3.2.6 chunk-001 들이 retrieved. X1/X2/Part 2 group 0/1/2 우선순위 분할이 본문에 직접 노출. **답변 가능 수준 高**.
- **38.521-4 Enhanced Type II 성능 시험**: §6.3.2.2.6 / §6.3.2.1.6 / §6.3.3.1.6 chunk-001 들이 retrieved. 시험 조건 + 38.101-4 normative ref 까지 회수. **답변 가능 수준 高**.
- **WID/Discussion 도입 배경**: R1-2202121, R1-2112195, R1-1909583, R1-1909918, R1-1812322, R1-1902123, R1-1903044 등 RAN1#95~#108 의 release=Rel-16 discussion chunk 풍부. **답변 가능 수준 中~高** (단, `type=WID` 의 정식 work item description chunk 자체는 본 검색 범위에서 매칭되지 않았다).

### 약하게 회수된 항목

- **38.211 CSI-RS resource configuration (Type II 전용)**: 38.211 의 일반 CSI-RS / port 번호 청크가 회수되지만, "Type II 용 CSI-RS port 매핑" 을 직접 다룬 청크는 chunk-001 범위에서 강하게 매칭되지 않았다. 38.214 §5.2.2.2.5 본문이 38.211 의 antenna port 규약을 사용하고 있다는 것으로 우회 인용. **답변 가능 수준 中**.

### 미발견 항목 (retrieved chunk 에 직접 본문이 없음) — v2 갱신

- ~~38.331 `CodebookConfig` / `codebookType typeII-r16` ASN.1 IE 본문~~ → **✅ v2 §7-1 에서 해소**: `ran2_ts_asn1_chunks` 컬렉션에서 `CodebookConfig` (2,944자) 와 `CodebookConfig-r16` (985자) IE 본문 정확 회수.
- **38.306 `csi-Type-II` / `eTypeII` capability 표 항목명** — v2 vector top score 0.62 까지 상승했으나 의미적 매칭은 type1/type2 HARQ-ACK 등 false positive. text-match (`typeII` / `eTypeII` / `paramCombination`) **모두 0 chunks** `[logs/cross-phase/usecase/q1_retrieval_log_v2.json: ts306_cap_probes 4건 0 rows]`. → **38.306 의 Type II 전용 capability 항목명은 청크 본문에 그대로 노출되지 않음** (한계 지속).
- **38.512-4** — 사용자 표기, spec-trace 에 적재 부재 (확인). 본 답변은 **38.521-4** 로 대체. `[ts_queries_literal_user_typo: 0 hits]`
- **TS 38.101-4** — 38.521-4 가 normative reference 로 인용하지만, spec-trace 검색 범위 (이번 쿼리 set) 에서 본 spec 의 별도 청크는 회수되지 않았다.
- **정식 `type=WID` 청크** — 본 검색 (`type` 필터 미사용) 에서 회수 결과는 모두 `type=discussion` 또는 `type=CR` 였다.

### 미발견 사유 분류 (v2 갱신)

| 항목 | v1 사유 | v2 상태 |
|------|---------|---------|
| 38.512-4 | spec-trace 에 적재 부재 (실제 38.521-4). | 동일 (v1 한계 유지) |
| 38.331 IE 본문 | section 단위 청킹 한계, ASN.1 vs 자연어 mismatch | **✅ 해소** — `ran2_ts_asn1_chunks` (IE-level 청킹) 도입으로 정확 회수 |
| 38.306 capability 항목 | chunk-001 한정 표 본문 미노출 | **부분 보강** — vector top 0.62 (v1 0.51), 그러나 text-match 0 → Type II 전용 항목명은 청크 텍스트에 부재 |
| 38.101-4 | 본 쿼리 set 미검색 | 동일 (RAN4 ts collection 에 적재 여부 별도 확인 필요) |
| 정식 WID chunk | type 필터 미사용 | 동일 (TDoc 컬렉션은 v2 에서 재실행 안 함) |

---

## 11. 자가 검증

- 본 답변의 모든 사실 문장 끝에 `[spec §sec, chunkId=...]` 또는 `[Rxxx, RANx#N, ai=..., type=..., release=...]` 인용이 부착되어 있다 (§2~§9). v2 신규 §7-1 본문도 정확한 IE chunkId (`38.331-asn1-CodebookConfig-001`, `38.331-asn1-CodebookConfig-r16-001`) 를 부착했다 — v1 시절의 일괄 `-001` 표기 오류 회피.
- 미발견 항목 (38.512-4, 38.306 capability 항목명, 38.101-4) 은 모두 §10 에 명시했으며 추측으로 채워넣지 않았다. 38.331 IE 본문은 v2 에서 해소되어 §10 에서 ✅ 처리.
- "사용자 표기 38.512-4" 는 자체 판단으로 38.521-4 로 치환하지 않고, **양쪽 spec 번호를 모두 검색** → 38.512-4 = 0 hits 사실을 §8-1 에 기록하고 38.521-4 결과만 사용했다.

## 12. 부속 자료

- 검색 스크립트:
  - v2: `scripts/cross-phase/usecase/q1_search_typeii_codebook_v2.py` (5 vector + 4 ASN.1 fetch + 4 text-match probe)
  - v1: `scripts/cross-phase/usecase/q1_search_typeii_codebook.py`
- Retrieval log:
  - v2: `logs/cross-phase/usecase/q1_retrieval_log_v2.json` (25 vector hits + 4 IE rows + 0 text-match rows)
  - v1: `logs/cross-phase/usecase/q1_retrieval_log.json` (전체 280 hits)
- v1 답변 백업: `docs/usecase/answers/tracer/q1_rel16_typeii_codebook.v1.md`
- 질문 원문에 대응하는 항목별 직접 청크 ID (v2 갱신):
  - 38.211 → `38.211-8.4.1.5.3-001`, `38.211-7.4.1.5.1-001` (v1)
  - 38.212 → `38.212-6.3.2.1.2-014`, `38.212-6.3.1.1.3-001`, `38.212-6.3.2.6-001` (v1) + `38.212-6.3.2.4.2.2-001` / `38.212-6.3.2.4.2.3-001` (v2 신규: CSI part 1 / part 2)
  - 38.214 → `38.214-5.2.2.2.5-001` (Enhanced Type II 핵심, v1) + `38.214-5.2.2.2.6-001` (Enhanced Type II Port Selection, v2 신규) + `38.214-5.2.2.2.8-001` (Enhanced Type II for CJT, v2 신규)
  - 38.306 → `38.306-4.2.7.10-001`, `-009` / `38.306-4.2.7.2-053`, `-054` / `38.306-4.2.7.4-036` (v2, 매칭 약함)
  - **38.331 → `38.331-asn1-CodebookConfig-001`, `38.331-asn1-CodebookConfig-r16-001` (★ v2 ASN.1 신규 — v1 미발견 해소)**
  - 38.521-4 → `38.521-4-6.3.2.2.6-001`, `38.521-4-6.3.2.1.6-001`, `38.521-4-6.3.3.1.6-001` (v1) + `38.521-4-10.3B.1.1-001`, `-10.3B.1.2-001`, `-F.1.3.3-003` (v2 신규)
  - WID/도입 → `R1-1903044/RAN1#96`, `R1-1909583/RAN1#98`, `R1-2202121/RAN1#108-e` (v1, TDoc 재실행 안 함)

---

## 13. v1 → v2 변화 비교 (P2 + ASN.1 효과)

### 13-1. 새로 인용 가능해진 IE/spec 행

| 항목 | v1 상태 | v2 상태 |
|------|---------|---------|
| 38.331 `CodebookConfig` IE 본문 | ❌ 미발견 (top hits 모두 무관 절) | ✅ 본문 2,944자 회수, typeII / typeII-PortSelection 분기 인용 가능 `[38.331-asn1-CodebookConfig-001]` |
| 38.331 `CodebookConfig-r16` IE 본문 | ❌ 미발견 | ✅ 본문 985자 회수, typeII-r16 / typeII-PortSelection-r16 / paramCombination-r16 인용 가능 `[38.331-asn1-CodebookConfig-r16-001]` |
| `n1-n2-codebookSubsetRestriction-r16` BIT STRING 크기 매핑 | ❌ 38.214 본문에 이름만 등장 | ✅ 13 가지 N1·N2 조합 × BIT STRING SIZE 정확 인용 가능 `[38.331-asn1-CodebookConfig-r16-001]` |
| `paramCombination-r16` 도메인 | ❌ 38.214 본문에 이름만 | ✅ `INTEGER (1..8)` 명시 `[동일]` |
| `typeII-RI-Restriction` BIT STRING SIZE 변화 | ❌ 미회수 | ✅ Rel-15 SIZE(2) → Rel-16 SIZE(4) 본문 비교 가능 `[CodebookConfig vs -r16]` |
| `numberOfPMI-SubbandsPerCQI-Subband-r16` IE 본문 | ❌ 38.214 본문에 이름만 | ✅ `INTEGER (1..2)` 명시 `[38.331-asn1-CodebookConfig-r16-001]` |
| `CodebookConfig-r17` / `-r19` / `-v1730` 변종 존재 | ❌ 미회수 | ✅ ieName 으로 존재 확인 (Rel-17/Rel-19 추가 IE 식별) `[q1_retrieval_log_v2.json: queries[0]]` |
| 38.214 §5.2.2.2.6 Enhanced Type II Port Selection 본문 | △ section title 만 | ✅ 본문 600자 회수, `typeII-PortSelection-r16` `portSelectionSamplingSize-r16` 인용 가능 `[38.214-5.2.2.2.6-001]` |
| 38.214 §5.2.2.2.8 Enhanced Type II for CJT 본문 | △ section title 만 | ✅ 본문 600자 회수, `typeII-CJT-r18` 와 `n1-n2-codebookSubsetRestrictionList-r18` 인용 가능 `[38.214-5.2.2.2.8-001]` |
| 38.212 §6.3.2.4.2.2 / §6.3.2.4.2.3 (CSI part 1/2 PUSCH 다중화) | ❌ 미회수 | ✅ 본문 회수, rate matching/CRC 처리 인용 가능 `[38.212-6.3.2.4.2.2-001, -6.3.2.4.2.3-001]` |
| 38.521-4 §10.3B.1.x EN-DC 시험 | ❌ 미회수 | △ 본문은 회수 (preview empty 이지만 chunkId 확보) `[38.521-4-10.3B.1.1-001 등]` |
| 38.306 capability 행 | ❌ Type II 항목 직접 미발견 | ❌ 동일 (vector score 만 0.51 → 0.62 상승, text-match 여전히 0) |

### 13-2. 답변 가능 수준 변화

| 영역 | v1 | v2 |
|------|----|----|
| 38.214 codebook 정의 (§5.2.2.2.5 Enhanced Type II) | 高 | 高 (§5.2.2.2.6, §5.2.2.2.8 추가 회수) |
| 38.212 UCI two-part CSI | 高 | 高 (§6.3.2.4.2.2/.3 추가) |
| 38.521-4 성능 시험 | 高 | 高 (§10.3B EN-DC 추가) |
| **38.331 RRC IE 본문** | **低 (미발견)** | **高 (★ ASN.1 컬렉션으로 IE 본문 직접 인용)** |
| 38.306 capability 항목 | 中-低 | 中-低 (개선 미미) |
| 38.211 CSI-RS Type II 전용 | 中 | 中 (v2 재검색 안 함) |
| WID/Discussion (Rel-16) | 中-高 | 中-高 (v2 TDoc 재실행 안 함) |

### 13-3. 핵심 결론

**P2 + ASN.1 컬렉션 도입의 가장 큰 가치는 v1 §7 의 38.331 IE 본문 미발견 한계가 해소된 것이다.** ASN.1 IE-level 청킹은 section 단위 청킹의 chunk-001 경계 한계와 자연어-vs-ASN.1 mismatch 를 동시에 해결한다. 38.214 ↔ 38.331 의 파라미터명 일치를 v1 처럼 "이름만 일치" 로 우회 인용하지 않고, **양쪽 본문을 직접 인용한 양면 매핑**을 구성할 수 있게 되었다 (§4 ↔ §7-1).
