# Frozen implementation review guide

이 디렉터리는 AUTHOR의 새 finite-candidate 측정 준비본입니다. 과학 설계 승인은 `design_review.json`에 있으며, 실행에는 별도의 parent 작성 `execution_approval.json`이 필요합니다. 준비 단계에서는 Python syntax compilation과 metadata/hash 확인만 수행했습니다. 새 control 평가·signature·SQL·검출률 결과는 아직 없습니다.

코드의 경계는 다음과 같습니다.

- `symbolic.py`: 원시 relation의 set/multiset에서 reference 및 known control의 full rowsets를 독립 계산합니다. Original SQL builder와 archived execution 결과를 읽지 않습니다. Bare aggregate는 허용 family와 choice-invariant equality를 사용합니다.
- `exact_stats.py`: cell별 joint-count histogram을 정수 다항식으로 합성하고 `Fraction`으로 평균·PMF·support bound·policy quantile을 계산합니다. 같은 cell의 controls는 같은 anchor를 공유합니다. Cell 간 독립 선택은 명시한 가상 정책의 분포 가정입니다.
- `run_census.py`: hash-bound 승인 gate, input type/collation gate, 원본132/400 SQL literal preflight, 모든 frozen candidate 재검산, full-rowset census, 전체 signature inventory 동결, 모든 대표/원본 anchor SQL 감사, 감사 통과 후 aggregate를 순서대로 수행합니다. All95/66/29 및 200/113/87을 assert합니다. Original raw enumerator는 읽기/열거/원래 source predicates에만 쓰며 새 control semantics에는 쓰지 않습니다.

Parent가 최종 protocol/implementation manifest SHA를 확인하고 승인 receipt를 작성한 뒤에만 아래 명령이 허용됩니다. `TASK_ANALYSIS`와 `TASK_RELEASE`는 아래 예시에 쓰는 작업별 shell 변수이며 실제 shell 명령은 모두 `free -h`로 시작합니다.

```bash
free -h
TASK_ANALYSIS=logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/final/next_cycle/work/review/external_review_revision/full_candidate_sensitivity
TASK_RELEASE=logs/publication/paper/ongoing/vldb-2027-experiment-analysis-benchmark/release_preparation/vldb_release
/usr/bin/python3 "$TASK_ANALYSIS/run_census.py" \
  --release "$TASK_RELEASE" \
  --enumerator "$TASK_ANALYSIS/../unavailable_cell_analysis/analyze_portable.py" \
  --protocol "$TASK_ANALYSIS/protocol.json" \
  --approval "$TASK_ANALYSIS/execution_approval.json" \
  --materialized-db-dir /tmp/spectra-witness-first-databases \
  --out "$TASK_ANALYSIS/run"
```

`--materialized-db-dir`를 생략하면 source gzip을 `--out/.databases/` 아래에 직접 풀어 cold replay합니다. 입력은 protocol의 정확한 release-relative SHA 목록과 외부 enumerator 한 파일입니다. Original 26-file unavailable analysis input package의 raw JSON/parser sources는 이 census에는 필요하지 않습니다. 최소 release 파일 목록은 `minimal_inputs.json`에 기록합니다. Bundle의 code/docs/catalog/manifest/protocol/parent approval와 pinned enumerator를 함께 복사하면 외부 project import 없이 cold replay할 수 있습니다. Output은 이 bundle 아래의 fresh child 디렉터리여야 하며 release 안에는 쓸 수 없습니다.

실행 산출물은 모든 candidate의 detection vector/signature annotation, signature inventory 및 freeze, 모든 SQL full-rowset audit, 검증 상태, cell별 exact 확률/PMF 및 두 weighting의 primary aggregate, 원래 두 anchor-arm replay, receipt와 SHA 목록입니다. 어느 실패도 삭제하거나 favorable reroll하지 않습니다. 검증 실패 시 `analysis.json`을 만들지 않고 unvalidated/partial candidate 결과와 실패 receipt를 보존합니다. 이 분석은 고정 source/known-control uniform 정책의 정확한 기댓값과 분포를 측정하며, 새로운 model 성공률이나 unseen-error 검증으로 해석하지 않습니다.
