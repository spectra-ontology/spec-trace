# 실행 전 타당성 및 검증 설계

현재 상태는 **과학 설계 승인, 구현 검토 대기**입니다. `design_review.json`이 설계와 95-cell 별도 진단 범위를 승인했습니다. 새 symbolic control 결과, signature, detection count/rate 또는 SQL 결과를 아직 계산하지 않았습니다. 코드는 작성·정적 syntax 확인만 허용하며 실행은 protocol/implementation SHA를 명시한 별도 parent 승인 receipt가 있어야 시작합니다.

## 고정 자산의 적절성

기존 `unavailable_cell_analysis/analyze_portable.py`는 raw 관계에서 95개 cell의 후보 identity, properties, gate를 재생성하고 2,269,290개 frozen archive 행과 대조한 코드입니다. 이를 수정하지 않고 pinned module로 가져와 enumeration·raw relation 읽기에만 재사용할 수 있습니다. 새 control interpreter는 별도 코드로 작성합니다. `witness_selection_value/measure.py`의 원래 cohort/parser·control mapping·full-rowset normalization을 직접 대조했으며 SQL 감사에서는 pinned original builder의 family templates를 그대로 anchor에 instantiate합니다. Frozen 132 task slots에서 생성된 SQL 문자열이 원본 문자열과 정확히 같아야 계속합니다.

주 비교는 원래 66 available cell의 200 control slots입니다. 29 unavailable cell에는 frozen task slot이 없으므로 eligible policy의 값을 `NA`로 보존합니다. 95개 전체 후보의 계산 요구를 충족하기 위해 unavailable cell에서도 같은 family의 기존 control **종류와 연산**을 별도 diagnostic으로 적용하는 범위를 parent가 승인했습니다. 이는 추가된 200-control 관측치가 아니며, 전체 95-cell family-diagnostic 수를 원래 200이라고 부르지 않습니다. Primary aggregate에는 언제나 원래 66/200만 들어갑니다.

## 정확하게 가능한 것

Typed sets, document sets, per-code distinct counts와 raw multiplicity를 사용하면 fixed family의 `UNION`/`INTERSECT`/`EXCEPT`, typed/broad membership, conjunction/disjunction, grouping, maximum/tie/limit, absence control을 직접 평가할 수 있습니다. 전체 normalized rowsets를 비교하며 first-row·count-only 비교로 대체하지 않습니다. 평균과 PMF는 Python integer 및 `Fraction`으로 계산해 exact numerator/denominator를 저장합니다.

`omit_group_by`만 SQL bare-column 선택 경계가 있습니다. 다중 code에서는 정확한 literal code 하나가 SQL 언어 정의로 결정되지 않습니다. 이 경우 symbolic 결과를 `[(c,distinct_documents)]` for each admitted code `c`라는 허용 family로 보존합니다. 참조/다른 control과의 full-rowset equality partition 및 inequality indicator는 모든 허용 선택에서 같아야 합니다. 선택 불변성을 증명·검사할 수 없는 경우에는 해당 candidate를 제거하거나 임의 값으로 채우지 않고 전체 측정을 실패 상태로 중단합니다. 실제 SQLite 반환 row는 SQL 감사에서 family membership으로 검증합니다.

검출 불변성의 경우를 나누면 명확합니다. Qualifying code 집합이 비었을 때 grouped reference/count-star는 0행이고 bare aggregate는 `(NULL,0)` 1행입니다. Code가 하나이면 bare code는 고정이며 distinct count도 그 code의 참조 count와 같습니다; count-star와의 equality는 raw multiplicity가 정합니다. Code가 둘 이상이면 reference/count-star가 각각 code당 1행으로 적어도 2행이고 bare aggregate는 언제나 1행이므로, 어느 admitted code를 택해도 두 비교에서 unequal입니다. 따라서 이 family의 모든 pairwise equality와 detection은 choice invariant입니다. 구현은 이 증명을 가정하고 값을 채우는 대신 모든 admitted rowset의 Cartesian 비교도 검사합니다.

Raw NULL·type·identifier/collation 조건은 실행 후 시작 gate에서 확인합니다. 해석 대상 source 열은 non-NULL text와 binary collation이어야 하며 문서 표시는 SQL의 `REPLACE`를 그대로 사용합니다. 현 symbolic semantics가 다루지 않는 입력을 발견하면 fail closed하며 승인된 protocol의 개정 없이 exclusion이나 대체 규칙을 추가하지 않습니다. 이 gate 자체도 parent 승인 후에만 실행합니다.

## Signature와 SQL 감사

여기서 outcome signature는 literal rowset SHA가 아니라 **reference와 모든 family control의 전체 normalized rowset에 대한 equality partition**, output cardinality의 0/1/many 구간, interpreter의 선언된 branch tags입니다. 이 정의가 없으면 anchor별 literal 값이 달라 거의 모든 후보가 별도 signature가 되어 SQL 절감 목적을 잃을 수 있습니다. 이 signature는 detection indicators를 완전히 결정하지만 대표 감사가 모든 후보 SQL 실행을 대신하는 형식 증명이라는 뜻은 아닙니다.

모든 `(WG,cell,eligible-status,signature)`에서 canonical candidate JSON이 가장 작은 대표를 한 개 고정합니다. 대표를 favorable detection이나 runtime에 따라 바꾸지 않습니다. 모든 대표의 reference와 해당 family control을 SQLite 3.37.2에서 60-second cap으로 실행하고 full rowsets·partition·indicator를 대조합니다. 동일 WG/exact SQL SHA의 실행은 결과 cache로 재사용하되 모든 audit slot과 이유를 기록합니다. signature representative가 ineligible인 경우도 모두 유지합니다. 별도로 frozen witness/hash의 132 task slots와 400 control slots를 전수 감사하며 archived full rows까지 대조합니다.

실행 순서는 모든 원본 132/400 SQL 문자열 및 direct control-name 일치 preflight → raw 후보 전수 symbolic census → signature inventory SHA 동결 → 모든 대표 및 132/400 SQL 감사 → exact aggregate입니다. Original builder의 task 함수는 내부적으로 자체 gold를 만들지만, 새 rowset 계산·검출·확률에는 그 gold를 사용하지 않습니다. SQL literal 생성에만 재사용하고 새 결과의 정본은 별도 raw-set interpreter입니다.

어느 audit가 mismatch/timeout/error면 그 결과를 보존하고 primary conclusion을 `validation_incomplete_or_failed`로 표시합니다. Anchor 교체·SQL 수정·control 삭제·재추첨 없이 원인을 보고합니다. 성공한 부분만 골라 aggregate를 발표하지 않습니다. 마지막 audit까지 통과해야 census를 검증 완료로 표시합니다.

## 자원과 중단 경계

2.27M row enumeration 자체는 이미 수십 초 규모로 실행된 자산이지만 새 symbolic outcomes 및 SQL 감사의 완료 시간은 아직 측정하지 않았습니다. 후보를 전부 SQL로 실행하지 않고 family/anchor raw set 연산과 signature 대표 감사를 사용합니다. PMF degree는 control-weighted all의 경우 200이며 cell-weighted는 cell별 control 수의 LCM으로 integer lattice를 만들어 정확히 합성합니다. 한 cell 안 controls의 상관은 detected-count histogram으로 보존합니다.

실제 signature 수는 새 결과이므로 사전 측정하지 않습니다. Parent 승인 이후 signature inventory를 먼저 동결하고 모든 대표를 감사합니다. 구현은 단일 process/4 GiB address-space cap이며 대표 수에 따른 표본 cut-off를 두지 않습니다. 자동 resume는 구현하지 않았고, 중단된 run의 모든 artifact와 receipt를 보존한 뒤 동일 승인된 코드의 fresh output child에서 전부 replay할 수 있습니다. 메모리·디스크·시간이 부족하면 누락된 범위와 incomplete 상태를 보고하며 임의 sample로 완전 검증을 대체하지 않습니다.

모델·네트워크·과금 API 호출은 0입니다. 원고/P/이전 리뷰/동결 author 분석은 읽기 전용이며 모든 새 산출물은 `full_candidate_sensitivity/` 아래에만 둡니다.
