# 독립 의미 검수

고정된 30개 문항에서 **질문·출력 필드·gold·참조 SQL의 의미가 모두 일치**했다. builder 작성·후보 선정·질문 작성·gold 생성에 관여하지 않은 검수자가 30개 전체와 builder 112행을 직접 읽고, builder를 import하거나 그 gold 생성 함수를 재사용하지 않는 별도 SQL 30개를 작성해 실제 DB에서 확인했다. 모델 writer의 출력은 열람하거나 실행하지 않았다.

| 검수 | 실제 결과 |
|---|---:|
| 참조 SQL 재실행과 gold의 정확 행 집합 일치 | 30/30 |
| 독립 구현 SQL과 gold의 정확 행 집합 일치 | 30/30 |
| 잘못된 연산으로 바꾼 결과가 gold와 달라짐 | 25/25 |
| 원본·실행 DB의 실행 전후 SHA 일치 | 5/5 WG |
| writer 스키마·전체 disposition 값 도메인과 DB 일치 | 5/5 WG |

질문은 작성된 분석 문항으로 명시되어 있고, 문서 표시 번호·pack membership·typed section의 규격/release/clause를 올바르게 요청한다. 선택 pack의 모든 member는 해당 WG 문서이고 표시 번호가 실제 document.number와 일치했다. 관련 section ID는 모두 NULL 없는 typed triple로 해석되며, 해당 범위에서 한 triple이 여러 ID에 대응하는 경우도 없었다. `largest_clause_footprint`는 section ID의 distinct count와 모든 최댓값 동률을 포함한다. `members_without_clause_records`는 snapshot 내 링크 부재를 묻는 닫힌 세계 조건을 명시한다. 검수 범위에서 질문/gold의 의미상 모호성이나 수정이 필요한 불일치는 발견하지 않았다.

## 연산 비퇴화 확인과 실제 경계

의미 일치와 선택 항목의 연산 분별력은 별개로 확인했다. 다음 다섯 잘못된 연산을 각 WG의 항목에 실행한 25개 모두가 gold와 다른 정확 행 집합을 반환했다. 실제 잘못된 SQL·반환 집합·gold-only/mutation-only 행은 [검수 JSON](semantic_validation.json)에 보존했다. 실행 오류로 “다르다”고 센 항목은 없다.

| 계열 | 잘못된 연산 | gold와 다른 결과 |
|---|---|---:|
| shared_clauses | INTERSECT → UNION | 5/5 |
| exclusive_clauses | EXCEPT → INTERSECT | 5/5 |
| both_clause_documents | 두 section 모두 → 어느 하나; pack 제한 유지 | 5/5 |
| largest_clause_footprint | 최댓값 문서 → count가 양수인 모든 문서 | 5/5 |
| members_without_clause_records | NOT EXISTS → EXISTS | 5/5 |

히스토그램 5개는 실제로 모두 `agreed` 단일 그룹이다. `GROUP BY`를 제거한 잘못된 SQL도 5개 전부 같은 gold를 반환했다. 따라서 이 선택은 여러 code 그룹을 구별하는 처리를 검증하지 않는다. distinct-document count 자체는 RAN1에서 raw joined rows 3 대 distinct documents 2, RAN2에서 37 대 24로 달랐고, 나머지 세 WG에서는 두 수가 같았다.

최댓값의 실제 동률은 RAN1 2개, RAN2 4개, RAN4 2개로 세 항목에서 나타났다. RAN3·RAN5는 단일 최댓값이었다. 다섯 최댓값 항목에서 release를 합쳐 `(specification, clause)`만 세는 대체 계산은 원 gold를 바꾸지 않았다. 참조 구현과 문장은 release를 보존하지만, 이 다섯 선택으로 release 병합 오류의 검출 능력까지 입증하지는 않는다.

## 실행과 고정 상태

Python 3.10.12 / SQLite 3.37.2에서 하나의 작업자로 순차 실행했다. DB는 원본 hash가 확인된 `mode=ro&immutable=1`, `query_only=ON`, WG별 16 MiB cache로 열었다. 질의마다 60초 progress-handler 상한, 프로세스 2 GiB 상한을 적용했다. 참조 30개·독립 SQL 30개·잘못된 연산 25개·GROUP BY 생략 5개를 실제 실행했다. 실행 오류·시간초과가 없었다. 검수와 진단 SQL 실행은 약 0.41초, 최대 RSS는 98,204 KiB였고 모든 원본·실행 DB의 사후 hash가 유지됐다. 원본·frozen 입력은 수정하지 않았고 출력은 이 검수 JSON/MD 두 파일에 한정했다.

- selection/gold SHA256: `0a7fe9a499d740d170a6b475c9a8fde5b5949ee7b3d70fc500a140a1461e9c3b`
- writer questions SHA256: `c8cb2e70fc95b1910f922bef7fd2970d4c98962f913bef1072ce644eb3898b79`
- writer schema SHA256: `3e2bbfc09056f6bee85c99a1fc5be3e2eea7d920d0f7e4053941f4e8208ed20d`
- 검수 JSON SHA256: `f2c78a8c2ff4f4c6e4214b9ccdef77b5688dbe41db244f5d86cc5b39f7cae824`

다음 writer 실행의 의미 검증 게이트는 통과한다. 보고 범위는 균형 있게 선택한 작성 문항 30개의 의미 일치와 위의 구체적인 연산 분별력이며, 사람 질문 분포·다중 code grouping·일반 모델 능력의 입증으로 확대하지 않는다.
