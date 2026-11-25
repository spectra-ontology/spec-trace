# 사전 원문 대조: fixed-source finite census

이 문서는 신규 측정의 실행 전 설계입니다. 기존 paired 결과와 controls를 이미 알고 있는 저자 분석이며, 이전 reviewer 판정의 변경·재평가가 아닙니다. 여기에는 새 control 출력이나 detection 결과가 없습니다.

**Zhong, Yu, Klein (2020), Sections 2–4.** [Primary paper](https://aclanthology.org/2020.emnlp-main.29.pdf)의 denotation distinction 정의, neighbor 변형, schema/type/foreign-key를 지키는 random database 생성, 새로운 neighbor를 구별하면 database를 suite에 더하는 greedy distillation을 다시 대조했습니다. 쿼리의 결과를 구별하는 입력을 찾는 원리는 기존 기여입니다. 이번 분석은 고정된 source-faithful DB의 선언된 후보 전체에서 같은 known controls의 결과 차이를 세고 두 균등 anchor 정책의 정확한 평균·분포를 구합니다. 새 equivalence algorithm, test-suite 원리, unseen-query 성능 또는 최초 census를 주장하지 않습니다. 기존 단일 hash 비교의 특수성을 제거하는 유한 모집단의 추가 측정입니다.

**SemBench, Sections 3.1–3.3 및 scenario 예시.** 로컬 primary `e5_lao_sembench.pdf` pp. 3–5의 본문을 다시 읽었습니다. [Primary paper](https://doi.org/10.14778/3811243.3811249)는 annotated data와 일부 synthetic tabular data, semantic operators, quality/cost/scale를 결합합니다. 추가 census의 분석 단위는 새 operator taxonomy나 system ranking이 아니라, 이미 정해진 operator error가 같은 고정 데이터 안에서 anchor에 따라 언제 드러나는지입니다. Operator coverage를 데이터 조건과 연결하는 적용 차이를 주장할 수 있습니다.

**Bench-U, Sections 3.2–3.4의 관련 본문.** 로컬 primary `e6_deng_unstructured.pdf` pp. 5–7의 dataset, labeling, query-construction 부분을 다시 대조했습니다. [Primary paper](https://doi.org/10.14778/3819518.3819559)는 relational ground truth와 operator/predicate/join 구조별 query generation을 이미 제공합니다. 이번 분석은 relational gold나 query-interface 공통 평가를 새 발명으로 취급하지 않습니다. 기존 fixed source에서 알려진 control semantics를 유지한 채 candidate별 구별 여부의 조건부 유한 분포를 측정하는 점이 정확한 추가 범위입니다.

**SQLite의 bare aggregate 규칙.** [Official SELECT documentation, §2.4–2.5](https://www.sqlite.org/lang_select.html#bareagg)는 GROUP BY 없는 aggregate가 입력이 비어도 한 행을 반환하고, bare column은 선택된 입력 row에서 취한다고 명시합니다. 따라서 `omit_group_by`의 bare `code`를 임의의 고정 값으로 만들지 않습니다. 두 개 이상의 code group에서는 참조가 여러 행·control이 한 행이므로 full-rowset inequality가 code 선택에 무관합니다. 한 code/empty 입력은 정확한 rowset을 쓸 수 있습니다. SQL 감사는 다중 code의 실제 결과가 선언된 허용 rowset family에 속하는지와 discrimination의 선택 불변성을 함께 확인합니다.

## 허용되는 결과 해석

- 같은 66 available cell, 동일 200 frozen control slots, 고정된 DB에서의 uniform-U / uniform-E 기대값과 분포입니다.
- 113 direct-control / 87 other-control 분해는 설계와 같은 시점에 정한 known controls의 분해입니다.
- 전수 count이므로 해당 유한 정책의 평균에는 sampling error가 없으며, 논문의 domain 전체·미래 data·자연 발생 model error에는 이 성질을 옮기지 않습니다.
- Cell 간 독립 균등 anchor 선택은 분포 계산을 위한 명시적 hypothetical policy입니다. 원래 deterministic hash가 실제 확률 표본이었다는 가정은 사용하지 않습니다.
- 결과 방향·크기와 무관하게 모든 cell·분포·검증 실패·불리한 결과를 보존합니다. 기존 결과를 삭제하거나 seed·anchor·control을 바꾸지 않습니다.

## 읽은 범위와 증거

새 설계를 위해 primary Zhong Sections 2–4, SQLite §2.4–2.5, SemBench pp. 3–5의 관련 본문, Bench-U pp. 5–7의 관련 본문을 다시 확인했습니다. Local PDF의 이전 extraction이나 reviewer 결과를 새 연구 근거로 대체하지 않았습니다. 이 문서의 비교는 본문에 직접 나타난 설계 차이에 한정합니다.
