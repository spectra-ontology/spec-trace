# Step-1: TR Parsing & JSON-LD Generation

## 개요

RAN1 TR 26개의 docx 에서 메타데이터와 범위(Scope) · 결론(Conclusions)을 뽑고(`01_parse_tr_docs.py`), `tr_impact_mapping.csv` 의 TR → TS 영향과 합쳐 JSON-LD 를 만든 뒤(`02_generate_tr_jsonld.py`), 그 JSON-LD 를 점검한다(`03_validate_jsonld.py`). 스크립트는 모두 `scripts/tsg/RAN/formal/RAN1/phase-5/tr-parser/` 에 있다.

## 입력 데이터

| 입력 | 위치 | 크기 |
|------|------|------|
| TR docx | `ontology/input/tsg/RAN/formal/TR/RAN1/{TR 번호}/*.docx` | 폴더 26개 · docx 45개 |
| TR → TS 영향 | `ontology/input/tsg/RAN/formal/TR/RAN1/tr_impact_mapping.csv` | 37행 |
| TR → Work Item | `ontology/input/tsg/RAN/formal/TR/RAN1/tr_workitem_mapping.csv` | 26행(Step-2 에서 읽는다) |

두 CSV 는 사람이 손으로 만든 입력이고, 저장소에는 만드는 스크립트가 없다.

## 01: TR 문서 파싱

### 처리 순서

1. 폴더 이름 → `trNumber`
2. 본문 docx 선택(아래)
3. 파일 이름의 버전 코드(`j00` → 19.0.0) → `trVersion`. 파일 이름에서 버전을 못 얻으면(또는 0.0.0 이면) 표지 첫 줄 「3GPP TR XX.YYY VN.x.y」에서 읽는다. 표지는 python-docx 문단에 잡히지 않아 docx 를 zip 으로 열어 XML 을 직접 읽는다
4. 버전으로 `trStatus` 를 정한다. 주 번호가 0 이면 `Draft`, 부 번호와 수정 번호가 모두 0 이면 `Completed`, 그 밖은 `Living`
5. 표지의 「(Release N)」, 없으면 Scope · Introduction 의 `Rel-NN` → `targetRelease`
6. 1단계 제목(Heading 1) 단위로 절을 나눈다. 숫자로 시작하고 이름에 「Scope」가 든 절 → `scope`, 이름에 「Conclusion」이 든 절 → `conclusions`. 둘 다 첫 10문단을 이어 800자까지만 담는다
7. 제목(`trTitle`)은 표지에서 「(Release N)」 앞까지의 문단을 이어 만든다(머리 문구 「3rd Generation Partnership Project」 · 「Technical Specification Group」 · 「Technical Report」 · 「3GPP TR」은 뺀다). 표지에서 못 얻으면 Introduction · Scope 의 「Study on …」, 첫 50문단, Scope 키워드 순으로 찾는다
8. `RP-NNNNN[N]` → `studyItemRpNumber` · `workItemRpNumber`. References 문단에서 후보를 모으고, 한 역할의 후보가 없으면 Scope · Introduction 문단에서 모은다. RP 번호가 하나뿐이고 LS·Liaison 표지가 없는 문단만 본다. 그 문단에 SID·Study Item 표지만 있으면 Study Item 후보, WID·Work Item 표지만 있으면 Work Item 후보다(둘 다 있거나 둘 다 없으면 후보가 아니다). 한 역할의 후보 번호가 정확히 하나일 때만 그 값을 쓰고, 둘 이상이거나 없으면 비운다. 같은 번호가 두 역할의 후보이면 둘 다 비운다. 번호가 몇 번째로 나왔는지는 역할을 정하지 않는다
9. References 에서 「3GPP TR XX.YYY」 · 「TR XX.YYY」 꼴로 인용한 번호 가운데 이 코퍼스에 있는 TR → `referencesTR`

### 본문 docx 선택

`select_main_docx` 가 정한다. 먼저 표지 파일을 후보에서 빼고(`scripts/tsg/RAN/formal/common/docx_pick.py` 의 `prefer_body`), 같은 폴더에 정리판(이름 끝 `cl`)이 있으면 그 짝인 수정 표시판(이름 끝 `rm`)도 뺀다. 수정 표시판은 삭제된 글을 `w:del` 로 포함하고 있어 본문으로 읽으면 지운 문장까지 섞이기 때문이다. 남은 후보 가운데 TR 번호와 이름이 맞고 Annex 가 아닌 파일을 고르고, 그런 파일이 없으면 Annex · `R*-` 꼴이 아닌 파일 가운데 이름이 가장 짧은 것을 고른다.

지금 입력에서 정리판 · 수정 표시판 짝이 있는 TR 은 38.760-1 하나다. 지금 코드는 38.760-1 을 `38760-1-010_cl.docx` 에서 읽고, 저장된 `tr_metadata.json` 의 `sourceFile` 도 이 파일이다. 두 판을 파싱해 비교하면 다른 값은 `sourceFile` · `paragraphCount` 뿐이고 Neo4j 에 들어가는 속성은 같다.

### 파싱 결과

`ontology/output/tsg/RAN/formal/parsed_tr/RAN1/tr_metadata.json` 에서 센 값이다.

| 항목 | 값 |
|------|-----|
| TR | 26 |
| trStatus | Completed 19 · Living 6 · Draft 1(38.760-1) |
| trTitle | 26(모두 표지에서 얻었다) |
| targetRelease | 26 |
| scope | 26 |
| conclusions | 21(없는 TR: 38.760-1 · 38.802 · 38.867 · 38.900 · 38.901) |
| studyItemRpNumber | 24 |
| workItemRpNumber | 1 |
| referencesTR | TR 13개 · 인용 25개 |

## 02: JSON-LD 생성

### tr_impact_mapping.csv

열은 `trNumber,impactType,impactsSpec,impactsSection,impactDescription` 다. 실제 행 예:

```csv
38.769,NewTS,38.291,,Ambient IoT - 새로운 TS 38.291 생성. ~1µW 및 ≤few hundred µW 디바이스를 위한 air interface 설계.
38.889,NewSection,38.211,16,NR-U (Unlicensed) - 38.211에 Section 16 (Physical layer procedures for NR-U) 추가
38.901,NoChange,,,Channel Model - 채널 모델 참조 문서. TS 변경 없음 (Living document)
```

| impactType | 행 수 | TR 수 |
|------------|------|------|
| NewTS | 1 | 1 |
| NewSection | 15 | 6 |
| ExtendSection | 13 | 10 |
| NoChange | 8 | 8 |

CSV 에는 26개 가운데 25개 TR 이 있다. 38.857 은 행이 없다.

### 생성 규칙

- TechnicalReport 는 TR 마다 하나, ID 는 `tr:{TR 번호}` 다
- TRImpact 는 NoChange 가 아닌 행마다 하나다. NoChange 8행은 TRImpact 를 만들지 않는다. ID 는 `trimpact:{TR 번호}-{스펙 번호}`, 절 번호가 있으면 뒤에 `-S{절 번호}` 를 붙인다
- `affectedSection` 에는 CSV 의 절 번호를 그대로 담는다
- `impactsSection` 은 그 절 번호를 Phase-3 release-aware 절(`sections.jsonld`)에서 같은 스펙 · 같은 번호의 최신 Release 절로 바꿀 수 있을 때만 단다. 못 바꾸면 빼고, 그 수를 화면과 `generation_metadata.json` 에 남긴다
- 영향받은 스펙이 Phase-1 에 없으면 그 Spec 을 `spec_section_dynamic.jsonld` 에 만든다. 지금은 해당이 없어 파일이 없다

생성기는 CSV 에 아래 결함이 있으면 그 행을 밝히고 멈춘다. 건너뛰거나 덮어쓰면 영향 항목 하나가 누락되어도 드러나지 않기 때문이다.

- 머리줄보다 열이 많은 행(설명 안의 쉼표를 따옴표로 감싸지 않은 경우). 그대로 읽으면 설명이 쉼표 앞에서 잘린다
- NoChange 가 아닌데 `impactsSpec` 이 빈 행
- `trImpactId` 가 겹치는 행. 적재기가 `trImpactId` 로 MERGE 하므로 하나로 합쳐진다

### 생성 결과

| 파일 | 내용 | 수 |
|------|------|-----|
| `technical_reports.jsonld` | TechnicalReport | 26 |
| `tr_impacts.jsonld` | TRImpact(NewSection 15 · ExtendSection 13 · NewTS 1) | 29 |
| `generation_metadata.json` | 생성 수치 | |

절 번호가 있는 TRImpact 28개 가운데 21개가 release-aware 절로 바뀌었다. 바뀌지 않은 7개는 38.889 → 38.211 · 38.212 · 38.214 §16, 38.875 → 38.213 §8.9, 38.869 → 38.211 §17, 38.765 → 38.211 §18, 38.867 → 38.211 §19 이다.

주의: CSV 의 절 번호는 사람이 적은 값이라 바뀐 21개도 내용이 맞는지는 보장되지 않는다. 예를 들어 38.864(energy saving) → 38.213 §8 은 「Random access procedure」, 38.875(RedCap) → 38.212 §5.5 는 「Code block concatenation」 절에 이어진다. 절 제목과 설명의 일치 여부를 점검하는 절차는 현재 없다.

## 03: JSON-LD 점검

- JSON-LD 문법
- 필수 속성: TechnicalReport 는 `trNumber` · `trVersion` · `trTitle` · `trStatus`, TRImpact 는 `trImpactId` · `impactType` · `impactOfTR` · `impactsSpec`. `@id` 접두(`tr:` · `trimpact:`)도 본다
- 열거값: `impactType` 이 NewTS · NewSection · ExtendSection 밖이면 오류, `trStatus` 가 Draft · Completed · Living 밖이면 경고(파서는 버전을 읽지 못하면 `Unknown` 을 낸다)
- 관계: `impactOfTR` 이 없는 TR 을 가리키면 오류, `impactsSpec` 이 Phase-1 Spec 과 동적 Spec 어디에도 없으면 경고

## 실행

```bash
python3 scripts/tsg/RAN/formal/RAN1/phase-5/tr-parser/01_parse_tr_docs.py
python3 scripts/tsg/RAN/formal/RAN1/phase-5/tr-parser/02_generate_tr_jsonld.py
python3 scripts/tsg/RAN/formal/RAN1/phase-5/tr-parser/03_validate_jsonld.py
```

## 출력

```
ontology/output/tsg/RAN/formal/parsed_tr/RAN1/
└── tr_metadata.json              # 01 출력

ontology/output/tsg/RAN/formal/instances/phase-5/RAN1/
├── technical_reports.jsonld      # TechnicalReport 26개
├── tr_impacts.jsonld             # TRImpact 29개
├── generation_metadata.json      # 생성 수치
└── spec_section_dynamic.jsonld   # 동적 Spec, 있을 때만
```

## 관련 문서

- [README](README.md)
- [TR Ontology Spec](design-spec/tdoc_ontology_specs%28TR%29.md)
- [Step-2: Neo4j Loading](step2_neo4j_loading.md)
- [Step-3: CQ Validation](step3_validation.md)
